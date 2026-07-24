from django.urls import path

from apps.paypal_express.views import (
    PayPalStartView,
    PayPalReturnView,
    PayPalCancelView,
)

app_name = 'paypal_express'
urlpatterns = [
    path('paypal/start/', PayPalStartView.as_view(), name='start'),
    path('paypal/return/', PayPalReturnView.as_view(), name='return'),
    path('paypal/cancel/', PayPalCancelView.as_view(), name='cancel'),
]
