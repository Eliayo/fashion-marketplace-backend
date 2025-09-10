from django.urls import path
from .views import (CartView, CartItemDeleteView,
                    CheckoutView, OrderListView, OrderStatusUpdateView, OrderDetailView,
                    PaystackInitializePaymentView, PaystackWebhookView)

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/item/<int:pk>/delete/",
         CartItemDeleteView.as_view(), name="cart-item-delete"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("<int:pk>/status/", OrderStatusUpdateView.as_view(),
         name="order-status-update"),
    path("<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    # Paystack
    path("paystack/<int:order_id>/initialize/",
         PaystackInitializePaymentView.as_view(), name="paystack-init"),
    path("paystack/webhook/", PaystackWebhookView.as_view(),
         name="paystack-webhook"),
]
