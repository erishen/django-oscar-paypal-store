"""Refund a PayPal-captured Oscar order.

Usage:
    python manage.py refund_paypal --order-number 100001
    python manage.py refund_paypal --order-number 100001 --amount 3.00

Full refund by default; pass --amount (with the order's currency) for a
partial refund. The command looks up the PayPal ``Source`` on the order,
calls PayPal's captures refund API, then records the refund as an Oscar
payment event and updates ``Source.amount_refunded``.
"""
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from oscar.apps.order.models import Order
from oscar.apps.payment.models import Source, SourceType
from oscar.apps.order.models import PaymentEvent, PaymentEventType

from apps.paypal_express.facade import PayPalFacade, PayPalError


class Command(BaseCommand):
    help = 'Refund a PayPal-captured Oscar order (full or partial).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--order-number', required=True,
            help='Oscar order number, e.g. 100001')
        parser.add_argument(
            '--amount', default=None,
            help='Partial refund amount (omit for full refund). '
                 'Must match the order currency.')
        parser.add_argument(
            '--note', default='Refund via Oscar PayPal integration',
            help='Note shown to the payer on PayPal.')

    def handle(self, *args, **options):
        number = options['order_number']
        order = Order.objects.filter(number=number).first()
        if not order:
            raise CommandError(f'Order {number} not found')

        paypal = SourceType.objects.filter(name='PayPal').first()
        source = order.sources.filter(source_type=paypal).first()
        if not source:
            raise CommandError(
                f'Order {number} has no PayPal payment source')

        capture_id = source.reference
        if not capture_id:
            raise CommandError('PayPal capture id (Source.reference) missing')

        already = source.amount_refunded or Decimal('0.00')
        if already >= source.amount_debited:
            self.stdout.write(
                self.style.WARNING(
                    f'Order {number} already fully refunded '
                    f'({already} {source.currency}).'))
            return

        # Determine refund amount
        if options['amount'] is not None:
            amount = Decimal(str(options['amount']))
            if amount <= 0 or amount > source.amount_debited - already:
                raise CommandError(
                    f'Invalid amount {amount}; remaining refundable '
                    f'{source.amount_debited - already} {source.currency}')
            refund_amount = amount
        else:
            refund_amount = source.amount_debited - already

        currency = source.currency
        self.stdout.write(
            f'Refunding {refund_amount} {currency} for order {number} '
            f'(capture {capture_id}) ...')

        facade = PayPalFacade()
        try:
            result = facade.refund_capture(
                capture_id,
                amount=refund_amount,
                currency=currency,
                note=options['note'])
        except PayPalError as e:
            raise CommandError(f'PayPal refund failed: {e}')

        refund_id = result.get('id')
        status = result.get('status')
        self.stdout.write(
            self.style.SUCCESS(
                f'PayPal refund {refund_id} -> status {status}'))

        # Record in Oscar ledger
        refunded_type, _ = PaymentEventType.objects.get_or_create(
            name='refunded')
        PaymentEvent.objects.create(
            order=order,
            event_type=refunded_type,
            amount=refund_amount,
            reference=refund_id or capture_id)
        source.amount_refunded = (already + refund_amount)
        source.save(update_fields=['amount_refunded'])

        remaining = source.amount_debited - source.amount_refunded
        if remaining <= 0:
            order.status = 'Refunded'
            order.save(update_fields=['status'])
            self.stdout.write(self.style.SUCCESS(
                f'Order {number} fully refunded.'))
        else:
            self.stdout.write(self.style.SUCCESS(
                f'Order {number} partially refunded; '
                f'{remaining} {currency} still captured.'))
