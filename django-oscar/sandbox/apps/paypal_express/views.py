"""PayPal Express Checkout views wired into Oscar's checkout flow.

This is a self-contained integration for Oscar 4.1 / Django 5.2 that does
NOT use the legacy ``django-oscar-paypal`` package (which only supports
Oscar 2.x + Django 2.2). It plugs into Oscar's standard
``OrderPlacementMixin`` hooks so the resulting order carries a proper PayPal
payment source + payment event, exactly like a real gateway integration.
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.views import View

from oscar.apps.checkout.views import PaymentDetailsView
from oscar.apps.order.utils import OrderNumberGenerator
from oscar.apps.payment.models import Source, SourceType

from apps.paypal_express.facade import PayPalFacade, PayPalError


class PayPalStartView(View):
    """Step 1: create a PayPal order for the current basket and redirect."""
    def get(self, request, *args, **kwargs):
        basket = request.basket
        if not basket or basket.is_empty:
            return redirect('basket:summary')
        facade = PayPalFacade()
        return_url = request.build_absolute_uri(reverse('paypal_express:return'))
        cancel_url = request.build_absolute_uri(reverse('paypal_express:cancel'))
        try:
            order_id, approve_url = facade.create_order(
                basket, basket.currency, return_url, cancel_url)
        except PayPalError as e:
            # Without real sandbox credentials the call fails; surface it on
            # the payment page instead of crashing, so the wiring is visible.
            request.session['paypal_error'] = str(e)
            return redirect('checkout:payment-details')
        request.session['paypal_order_id'] = order_id
        return redirect(approve_url)


class PayPalCancelView(View):
    """Step 3 (cancel): user aborted on PayPal, return to payment details."""
    def get(self, request, *args, **kwargs):
        return redirect('checkout:payment-details')


class PayPalReturnView(PaymentDetailsView):
    """Step 3 (success): user approved on PayPal, capture and place order."""
    def get(self, request, *args, **kwargs):
        self.request = request
        basket = request.basket
        if not basket or basket.is_empty:
            return redirect('basket:summary')
        self.basket = basket
        self.paypal_order_id = (
            request.GET.get('token') or request.session.get('paypal_order_id'))
        if not self.paypal_order_id:
            return redirect('checkout:payment-details')

        # Build the Oscar submission dict (basket is read from request.basket
        # by build_submission itself; Oscar 4.1 has no get_basket() helper).
        submission = self.build_submission()
        order_number = (
            submission.get('order_number')
            or self.checkout_session.get_order_number()
            or OrderNumberGenerator().order_number(basket)
        )
        try:
            # Capture the PayPal order exactly once. handle_order_placement()
            # (below) calls place_order(), which does NOT re-invoke
            # handle_payment, so the capture happens a single time.
            self.handle_payment(
                order_number, submission.get('order_total'),
                **submission.get('payment_kwargs', {}))
        except PayPalError as e:
            # Payment failed at PayPal (e.g. already captured, declined).
            # Restore the basket so the customer can retry and bounce back.
            self.restore_frozen_basket()
            request.session['paypal_error'] = str(e)
            return redirect('checkout:payment-details')
        return self.handle_order_placement(
            order_number,
            submission['user'],
            submission['basket'],
            submission['shipping_address'],
            submission['shipping_method'],
            submission['shipping_charge'],
            submission['billing_address'],
            submission['order_total'],
            surcharges=submission['surcharges'],
            **submission['order_kwargs'],
        )

    def handle_payment(self, order_number, total, **kwargs):
        facade = PayPalFacade()
        capture = facade.capture_order(self.paypal_order_id)
        captures = (
            capture.get('purchase_units', [{}])[0]
            .get('payments', {}).get('captures', [{}]))
        capture_id = captures[0].get('id') if captures else None
        source_type, _ = SourceType.objects.get_or_create(name='PayPal')
        basket = self.basket
        source = Source(
            source_type=source_type,
            currency=basket.currency,
            amount_allocated=basket.total_incl_tax,
            amount_debited=basket.total_incl_tax,
            reference=capture_id or self.paypal_order_id,
        )
        self.add_payment_source(source)
        self.add_payment_event(
            'captured', basket.total_incl_tax,
            reference=capture_id or self.paypal_order_id)
