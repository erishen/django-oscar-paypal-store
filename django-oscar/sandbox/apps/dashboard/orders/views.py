"""Forked dashboard orders views.

Overrides ``OrderDetailView._create_payment_event`` so that a *refunded*
payment event on an order paid with PayPal triggers a **real** PayPal
refund (via the local facade) before the local ledger entry is written.

Flow for a "refunded" event on a PayPal order:
  1. Validate the event locally first (quantities / status) -- cheap, and
     avoids calling PayPal when the event would be rejected anyway.
  2. Check the refundable balance on the payment Source.
  3. Call PayPal ``/v2/payments/captures/{id}/refund`` (with retry/backoff
     handled inside the facade).
  4. Only after PayPal confirms, write the local payment event (with the
     PayPal refund id as reference) and update ``Source.amount_refunded``.

Any other event type (or non-PayPal orders) falls through to the stock
Oscar behaviour (local bookkeeping only).
"""
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from oscar.apps.dashboard.orders.views import (  # noqa: F401
    OrderDetailView as CoreOrderDetailView,
)
from oscar.apps.order import exceptions as order_exceptions
from oscar.apps.order.models import PaymentEventType
from oscar.apps.payment.exceptions import PaymentError
from oscar.apps.payment.models import Source

from apps.paypal_express.facade import PayPalError, PayPalFacade

REFUND_EVENT_CODE = 'refunded'


class OrderDetailView(CoreOrderDetailView):

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _get_paypal_source(self, order):
        """Return the PayPal payment Source of the order, or None."""
        return (
            Source.objects.filter(
                order=order, source_type__name__iexact='paypal')
            .exclude(reference='')
            .first()
        )

    # ------------------------------------------------------------------
    # overridden dispatch of payment events
    # ------------------------------------------------------------------
    def _create_payment_event(self, request, order, amount,
                              lines=None, quantities=None):
        code = request.POST.get('payment_event_type')

        # Only intercept refunds; everything else keeps stock behaviour.
        if code != REFUND_EVENT_CODE:
            return super()._create_payment_event(
                request, order, amount, lines, quantities)

        source = self._get_paypal_source(order)
        if source is None:
            # Not a PayPal order -- local bookkeeping only, as before.
            return super()._create_payment_event(
                request, order, amount, lines, quantities)

        try:
            event_type = PaymentEventType._default_manager.get(code=code)
        except PaymentEventType.DoesNotExist:
            messages.error(
                request, _("The event type '%s' is not valid") % code)
            return self.reload_page()

        handler = self.get_handler()

        # 1) Local validation BEFORE touching PayPal, so an invalid
        #    event can never trigger a real refund.
        try:
            handler.validate_payment_event(
                order, event_type, amount, lines, quantities)
        except order_exceptions.InvalidPaymentEvent as e:
            messages.error(
                request, _("Unable to create payment event: %s") % e)
            return self.reload_page()

        # 2) Refundable balance check against the payment source.
        refundable = source.amount_debited - source.amount_refunded
        if amount <= 0 or amount > refundable:
            messages.error(
                request,
                _("Refund amount %(amount)s exceeds the refundable "
                  "balance %(refundable)s on the PayPal source.") % {
                    'amount': amount, 'refundable': refundable,
                })
            return self.reload_page()

        # 3) Real PayPal refund (capture id lives on Source.reference).
        try:
            refund = PayPalFacade().refund_capture(
                source.reference,
                amount=amount,
                currency=order.currency,
                note=f'Refund for order {order.number}',
            )
        except PayPalError as e:
            messages.error(
                request, _("PayPal refund failed: %s") % e)
            return self.reload_page()

        refund_id = refund.get('id', '')
        refund_status = refund.get('status', '')

        # 4) PayPal confirmed -- now write the local ledger.
        try:
            handler.handle_payment_event(
                order, event_type, amount, lines, quantities,
                reference=refund_id,
            )
        except (PaymentError, order_exceptions.InvalidPaymentEvent) as e:
            # Money HAS been refunded at PayPal; surface loudly so the
            # operator can reconcile manually instead of retrying.
            messages.error(
                request,
                _("PayPal refund %(rid)s succeeded but local bookkeeping "
                  "failed: %(err)s -- do NOT retry the refund; reconcile "
                  "manually.") % {'rid': refund_id, 'err': e})
            return self.reload_page()

        source.amount_refunded += amount
        source.save()

        messages.success(
            request,
            _("PayPal refund %(rid)s %(status)s -- %(amount)s %(cur)s "
              "returned to the buyer.") % {
                'rid': refund_id, 'status': refund_status,
                'amount': amount, 'cur': order.currency,
            })
        return self.reload_page()
