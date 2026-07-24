"""Lightweight PayPal Express Checkout facade using the REST Orders API.

This is a self-contained integration for the Oscar sandbox (Oscar 4.1 /
Django 5.2) that does NOT depend on the legacy ``django-oscar-paypal``
package (which only supports Oscar 2.x + Django 2.2). It talks to PayPal's
``v2/checkout/orders`` endpoints with plain ``requests``.

Credentials are read from Django settings:
    PAYPAL_CLIENT_ID, PAYPAL_CLIENT_SECRET, PAYPAL_MODE ('sandbox' | 'live')
"""
import time
import uuid

import requests
from requests.exceptions import SSLError, ConnectionError, Timeout
from urllib3.util.retry import Retry

from django.conf import settings


class PayPalError(Exception):
    """Raised when PayPal's API returns a non-success response."""


# Transient (connection-level) failures that are always safe to retry,
# including the intermittent SSL EOF ('UNEXPECTED_EOF_WHILE_READING') that
# PayPal's sandbox occasionally returns mid-response. A retried request has
# not been processed by PayPal yet, so re-sending is safe.
_TRANSIENT_EXCEPTIONS = (SSLError, ConnectionError, Timeout)

# How many times to retry a transient failure, and the exponential backoff
# base (seconds). Configurable via Django settings if needed.
_PAYPAL_MAX_RETRIES = getattr(settings, 'PAYPAL_MAX_RETRIES', 3)
_PAYPAL_RETRY_BACKOFF = getattr(settings, 'PAYPAL_RETRY_BACKOFF', 0.5)


class PayPalFacade:
    def __init__(self):
        self.client_id = getattr(settings, 'PAYPAL_CLIENT_ID', '')
        self.secret = getattr(settings, 'PAYPAL_CLIENT_SECRET', '')
        self.mode = getattr(settings, 'PAYPAL_MODE', 'sandbox')
        self.base = (
            'https://api-m.paypal.com'
            if self.mode == 'live'
            else 'https://api-m.sandbox.paypal.com'
        )
        # Reused session: connection pooling keeps a warm TLS connection (which
        # reduces the chance of the intermittent SSL EOF) and a Retry adapter
        # handles 429/5xx on safe methods.
        self.session = self._build_session()

    def _build_session(self):
        retry = Retry(
            total=_PAYPAL_MAX_RETRIES,
            backoff_factor=_PAYPAL_RETRY_BACKOFF,
            status_forcelist=(429, 500, 502, 503, 504),
            # POST is deliberately excluded from status retries: a 5xx on a
            # capture/refund could otherwise risk a double-charge. POST is still
            # retried on connection-level errors via ``_post`` below.
            allowed_methods=frozenset(
                ['GET', 'HEAD', 'PUT', 'DELETE', 'OPTIONS']),
            respect_retry_after_header=True,
            raise_on_status=False,
        )
        adapter = requests.adapters.HTTPAdapter(
            max_retries=retry, pool_connections=5, pool_maxsize=10)
        session = requests.Session()
        session.mount('https://', adapter)
        session.mount('http://', adapter)
        return session

    def _post(self, url, **kwargs):
        """POST with retry on transient (connection-level) errors such as the
        SSL EOF that urllib3's status-based Retry does not cover."""
        last_exc = None
        for attempt in range(1, _PAYPAL_MAX_RETRIES + 1):
            try:
                return self.session.post(url, **kwargs)
            except _TRANSIENT_EXCEPTIONS as exc:
                last_exc = exc
                if attempt < _PAYPAL_MAX_RETRIES:
                    time.sleep(_PAYPAL_RETRY_BACKOFF * attempt)
                    continue
        # All retries exhausted — re-raise the last transient error.
        raise last_exc

    # -- auth -------------------------------------------------------------
    def get_access_token(self):
        resp = self._post(
            f'{self.base}/v1/oauth2/token',
            auth=(self.client_id, self.secret),
            data={'grant_type': 'client_credentials'},
            headers={'Accept': 'application/json', 'Accept-Language': 'en_US'},
            timeout=30,
        )
        if resp.status_code != 200:
            raise PayPalError(f'OAuth failed: {resp.status_code} {resp.text}')
        return resp.json()['access_token']

    # -- order creation ---------------------------------------------------
    def create_order(self, basket, currency, return_url, cancel_url):
        token = self.get_access_token()
        items = []
        for line in basket.all_lines():
            items.append({
                'name': (line.product.title or 'Item')[:127],
                'unit_amount': {
                    'currency_code': currency,
                    'value': f'{line.unit_price_incl_tax:.2f}',
                },
                'quantity': str(line.quantity),
            })
        total = f'{basket.total_incl_tax:.2f}'
        body = {
            'intent': 'CAPTURE',
            'purchase_units': [{
                'amount': {
                    'currency_code': currency,
                    'value': total,
                    'breakdown': {
                        'item_total': {'currency_code': currency, 'value': total},
                    },
                },
            }],
            'application_context': {
                'return_url': return_url,
                'cancel_url': cancel_url,
                'brand_name': 'Oscar Demo Store',
                'landing_page': 'LOGIN',
                'user_action': 'PAY_NOW',
                'shipping_preference': 'NO_SHIPPING',
            },
        }
        resp = self._post(
            f'{self.base}/v2/checkout/orders',
            json=body,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                # IMPORTANT: a *fresh* id per call. Do NOT key this on
                # basket.id — a retry / second click would otherwise reuse
                # PayPal's idempotency and return a *previous* order that may
                # already be APPROVED/CAPTURED (which has no `approve` link),
                # surfacing as "No approve link returned by PayPal".
                'PayPal-Request-Id': f'oscar-create-{uuid.uuid4().hex}',
            },
            timeout=30,
        )
        if resp.status_code not in (200, 201):
            raise PayPalError(
                f'Create order failed: {resp.status_code} {resp.text}')
        data = resp.json()
        order_id = data['id']
        approve_url = next(
            (l['href'] for l in data.get('links', []) if l['rel'] == 'approve'),
            None,
        )
        if not approve_url:
            # Most often this means PayPal returned a prior order (via an
            # idempotency key) that is already approved/captured. Surface the
            # order id + status so it is diagnosable instead of a bare message.
            raise PayPalError(
                f'No approve link returned by PayPal '
                f'(order {order_id}, status {data.get("status")})')
        return order_id, approve_url

    # -- order lookup -----------------------------------------------------
    def get_order(self, order_id):
        """Fetch a PayPal order's current state.

        Used for idempotent capture reconciliation: a prior capture attempt
        may have succeeded (money taken) while its response was lost to a
        transient error, so the safest thing is to ask PayPal what the order
        state actually is before (or instead of) POSTing a capture.
        """
        token = self.get_access_token()
        resp = self.session.get(
            f'{self.base}/v2/checkout/orders/{order_id}',
            headers={'Authorization': f'Bearer {token}'},
            timeout=30,
        )
        if resp.status_code != 200:
            raise PayPalError(f'Get order failed: {resp.status_code} {resp.text}')
        return resp.json()

    @staticmethod
    def _capture_id_from_order(order_data):
        pus = order_data.get('purchase_units', [])
        if not pus:
            return None
        captures = pus[0].get('payments', {}).get('captures', [])
        return captures[0].get('id') if captures else None

    @staticmethod
    def _has_issue(resp, issue_code):
        try:
            body = resp.json()
        except Exception:
            return False
        return any(
            d.get('issue') == issue_code for d in body.get('details', []))

    @staticmethod
    def _synthesized_captured(order_data):
        """Wrap a GET-order response so the caller can read it exactly like a
        real capture response (``purchase_units[0].payments.captures[0].id``)."""
        return {
            'id': order_data.get('id'),
            'status': 'COMPLETED',
            'purchase_units': order_data.get('purchase_units', []),
            'paypal_already_captured': True,
        }

    # -- capture ----------------------------------------------------------
    def capture_order(self, order_id):
        # 1) Idempotency guard: if the order is already captured (a previous
        #    attempt succeeded but its response was lost to a transient error,
        #    or the buyer revisited the return URL), do NOT POST again. Return
        #    the existing capture so Oscar can place the order without taking
        #    more money.
        order_data = self.get_order(order_id)
        if order_data.get('status') == 'COMPLETED':
            return self._synthesized_captured(order_data)

        token = self.get_access_token()
        # 2) PayPal-Request-Id makes the capture POST idempotent: a retried
        #    POST carrying the same id returns the *original* 201 response
        #    instead of ORDER_ALREADY_CAPTURED.
        resp = self._post(
            f'{self.base}/v2/checkout/orders/{order_id}/capture',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'PayPal-Request-Id': f'capture-{order_id}',
            },
            timeout=30,
        )
        if resp.status_code in (200, 201):
            return resp.json()

        # 3) 422 ORDER_ALREADY_CAPTURED: the money was taken (typically on a
        #    retried POST whose original response was lost). Reconcile via GET
        #    and treat it as a success rather than throwing.
        if resp.status_code == 422 and self._has_issue(resp, 'ORDER_ALREADY_CAPTURED'):
            order_data = self.get_order(order_id)
            return self._synthesized_captured(order_data)

        raise PayPalError(f'Capture failed: {resp.status_code} {resp.text}')

    # -- refund -----------------------------------------------------------
    def refund_capture(self, capture_id, amount=None, currency=None,
                       note=None):
        """Refund a captured PayPal payment.

        ``capture_id`` is the PayPal capture id (stored on the Oscar
        ``Source.reference`` for a PayPal payment). Omit ``amount``/
        ``currency`` for a full refund, or pass them for a partial refund.
        Returns the parsed PayPal refund resource (``id``, ``status``, ...).
        """
        token = self.get_access_token()
        body = {}
        if amount is not None and currency is not None:
            body['amount'] = {
                'value': f'{amount:.2f}',
                'currency_code': currency,
            }
        if note:
            body['note_to_payer'] = note
        resp = self._post(
            f'{self.base}/v2/payments/captures/{capture_id}/refund',
            json=body,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
            },
            timeout=30,
        )
        if resp.status_code not in (200, 201):
            raise PayPalError(f'Refund failed: {resp.status_code} {resp.text}')
        return resp.json()
