from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from decimal import Decimal
from .models import Cart, CartItem, Order, OrderItem, VendorEarning, WithdrawalRequest
from .serializers import CartSerializer, CartItemSerializer, OrderSerializer
from accounts.permissions import IsAdmin, IsVendor, IsCustomer
from .services import send_order_email
from paystackapi.transaction import Transaction
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from django.http import JsonResponse
from collections import defaultdict
from django.db import transaction
import uuid
from django.utils import timezone


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

        # Group cart items by vendor
        vendor_groups = defaultdict(list)
        for item in cart.items.all():
            vendor_groups[item.product.vendor].append(item)

        # Shared transaction reference
        transaction_ref = f"txn_{uuid.uuid4().hex[:12]}"

        created_orders = []

        with transaction.atomic():
            for vendor, items in vendor_groups.items():
                total = Decimal(0)
                order = Order.objects.create(
                    user=request.user,
                    vendor=vendor,
                    total_price=0,
                    commission=0,
                    status="pending",
                    transaction_ref=transaction_ref
                )

                for item in items:
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
                order.save()

                created_orders.append(order)

        # Clear cart
        cart.items.all().delete()

        # 🔔 Notify customer once
        send_order_email(
            subject="Order Confirmation",
            message=f"Hi {request.user.username},\n\nYou placed {len(created_orders)} orders. Transaction reference: {transaction_ref}\n\nThank you for shopping with us!",
            recipient_list=[request.user.email],
        )

        return Response(
            {
                "transaction_ref": transaction_ref,
                "orders": OrderSerializer(created_orders, many=True).data,
            },
            status=status.HTTP_201_CREATED,
        )


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

        # 🔔 Notify customer
        send_order_email(
            subject="Order Status Update",
            message=f"Hi {order.user.username},\n\nYour order #{order.id} status has been updated to '{order.status}'.",
            recipient_list=[order.user.email],
        )

        return Response(OrderSerializer(order).data, status=200)


class OrderDetailView(generics.RetrieveAPIView):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == "admin":
            return Order.objects.all()
        elif user.role == "vendor":
            return Order.objects.filter(vendor=user.vendor_profile)
        return Order.objects.filter(user=user)


class PaystackInitializePaymentView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, order_id):
        order = get_object_or_404(Order, id=order_id, user=request.user)

        if order.status != "pending":
            return Response({"error": "Order is not pending."}, status=400)

        # Amount in kobo (Naira × 100)
        amount_kobo = int(order.total_price * 100)

        response = Transaction.initialize(
            reference=f"order_{order.id}",
            email=request.user.email,
            amount=amount_kobo,
            callback_url="http://localhost:3000/payment/callback",  # frontend route
        )

        if response["status"] is True:
            return Response(response["data"], status=200)
        return Response(response, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class PaystackWebhookView(APIView):
    permission_classes = [permissions.AllowAny]  # Paystack needs access

    def post(self, request):
        payload = json.loads(request.body)
        event = payload.get("event")

        if event == "charge.success":
            reference = payload["data"]["reference"]

            # Verify payment
            result = Transaction.verify(reference)
            if result["status"] and result["data"]["status"] == "success":
                transaction_ref = reference  # our generated uuid string
                orders = Order.objects.filter(
                    transaction_ref=transaction_ref, status="pending")
                for order in orders:
                    order.status = "paid"
                    order.save()

                    # Credit vendor
                    vendor_earning, _ = VendorEarning.objects.get_or_create(
                        vendor=order.vendor)
                    vendor_share = order.total_price - order.commission
                    vendor_earning.credit(vendor_share)

                    send_order_email(
                        subject="Payment Successful",
                        message=f"Your order #{order.id} has been paid successfully!",
                        recipient_list=[order.user.email],
                    )

        return JsonResponse({"status": "success"}, status=200)


class VendorEarningView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def get(self, request):
        earning, _ = VendorEarning.objects.get_or_create(
            vendor=request.user.vendor_profile)
        return Response({
            "balance": earning.balance,
            "total_withdrawn": earning.total_withdrawn,
            "updated_at": earning.updated_at
        })


class WithdrawalRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def post(self, request):
        amount = Decimal(request.data.get("amount", "0.00"))
        vendor_profile = request.user.vendor_profile
        earning, _ = VendorEarning.objects.get_or_create(vendor=vendor_profile)

        if amount <= 0:
            return Response({"error": "Invalid amount"}, status=400)

        if amount > earning.balance:
            return Response({"error": "Insufficient balance"}, status=400)

        withdrawal = WithdrawalRequest.objects.create(
            vendor=vendor_profile,
            amount=amount
        )

        return Response({
            "id": withdrawal.id,
            "amount": withdrawal.amount,
            "status": withdrawal.status,
            "created_at": withdrawal.created_at,
        }, status=201)

    def get(self, request):
        withdrawals = WithdrawalRequest.objects.filter(
            vendor=request.user.vendor_profile).order_by("-created_at")
        data = [
            {
                "id": w.id,
                "amount": w.amount,
                "status": w.status,
                "created_at": w.created_at,
                "processed_at": w.processed_at,
            }
            for w in withdrawals
        ]
        return Response(data, status=200)


class WithdrawalApprovalView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def patch(self, request, pk):
        withdrawal = get_object_or_404(WithdrawalRequest, pk=pk)

        action = request.data.get("action")  # "approve" or "reject"
        if action not in ["approve", "reject"]:
            return Response({"error": "Invalid action"}, status=400)

        if action == "approve":
            withdrawal.status = "approved"
            withdrawal.processed_at = timezone.now()
            withdrawal.save()
        else:
            withdrawal.status = "rejected"
            withdrawal.processed_at = timezone.now()
            withdrawal.save()

        return Response({"message": f"Withdrawal {withdrawal.status}"}, status=200)


class WithdrawalMarkPaidView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def patch(self, request, pk):
        withdrawal = get_object_or_404(WithdrawalRequest, pk=pk)

        if withdrawal.status != "approved":
            return Response({"error": "Withdrawal must be approved first"}, status=400)

        earning = VendorEarning.objects.get(vendor=withdrawal.vendor)
        try:
            earning.debit(withdrawal.amount)
        except ValueError:
            return Response({"error": "Insufficient balance"}, status=400)

        withdrawal.status = "paid"
        withdrawal.processed_at = timezone.now()
        withdrawal.save()

        return Response({"message": f"Withdrawal {withdrawal.amount} marked as paid"}, status=200)
