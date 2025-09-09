from django.urls import path
from .views import CartView, CartItemDeleteView, CheckoutView, OrderListView

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("cart/item/<int:pk>/delete/",
         CartItemDeleteView.as_view(), name="cart-item-delete"),
    path("checkout/", CheckoutView.as_view(), name="checkout"),
    path("orders/", OrderListView.as_view(), name="order-list"),
]
