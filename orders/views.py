from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from decimal import Decimal
from .models import Cart, CartItem, Order, OrderItem
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer
from accounts.permissions import IsAdmin, IsVendor, IsCustomer


class CartView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def post(self, request):
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartItemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(cart=cart)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CartItemDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        cart_item = get_object_or_404(CartItem, pk=pk, cart__user=request.user)
        cart_item.delete()
        return Response({"message": "Item removed from cart."}, status=status.HTTP_204_NO_CONTENT)


class CheckoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        cart = get_object_or_404(Cart, user=request.user)
        if not cart.items.exists():
            return Response({"error": "Cart is empty."}, status=status.HTTP_400_BAD_REQUEST)

        # assume one vendor per order (split-cart logic can be added later)
        first_item = cart.items.first()
        vendor = first_item.product.vendor

        total = Decimal(0)
        order = Order.objects.create(
            user=request.user,
            vendor=vendor,
            total_price=0,
            commission=0,
            status="pending"
        )

        for item in cart.items.all():
            price = item.product.price * item.quantity
            OrderItem.objects.create(
                order=order,
                product=item.product,
                variant=item.variant,
                quantity=item.quantity,
                price=item.product.price
            )
            total += price

        # Apply commission (10%)
        commission = total * Decimal("0.10")
        order.total_price = total
        order.commission = commission
        order.status = "paid"  # simulate instant payment success
        order.save()

        # Clear cart
        cart.items.all().delete()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Order.objects.all()
        elif user.role == "vendor":
            return Order.objects.filter(vendor=user.vendor_profile)
        return Order.objects.filter(user=user)


class OrderStatusUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        order = get_object_or_404(Order, pk=pk)

        # Vendor can only update their own orders
        if request.user.role == "vendor" and order.vendor != request.user.vendor_profile:
            return Response({"error": "You cannot update this order."}, status=403)

        # Customer can only mark delivered/cancelled
        if request.user.role == "customer":
            if request.data.get("status") not in ["delivered", "cancelled"]:
                return Response({"error": "Customers can only mark orders delivered or cancelled."}, status=403)
            if order.customer != request.user:
                return Response({"error": "Not your order."}, status=403)

        new_status = request.data.get("status")
        if new_status not in Order.Status.values:
            return Response({"error": "Invalid status."}, status=400)

        order.status = new_status
        order.save()
        return Response(OrderSerializer(order).data, status=200)
