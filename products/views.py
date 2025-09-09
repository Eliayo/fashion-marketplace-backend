from rest_framework import generics, permissions, status
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer
# reuse your custom admin permission
from accounts.permissions import IsAdmin, IsVendor


class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]  # anyone can view categories


class CategoryCreateView(generics.CreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdmin]  # only admin can create


class CategoryUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdmin]


class ProductListView(generics.ListAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]


class ProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def perform_create(self, serializer):
        vendor = self.request.user.vendor_profile
        if not vendor.verified:
            raise PermissionDenied("Your seller account is not approved yet.")
        serializer.save(vendor=vendor)


class ProductUpdateView(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def perform_update(self, serializer):
        product = self.get_object()
        if product.vendor != self.request.user.vendor_profile:
            raise PermissionDenied("You can only update your own products.")
        serializer.save(approved=False)  # re-approval needed on edit


class ProductDeleteView(generics.DestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsVendor]

    def perform_destroy(self, instance):
        if instance.vendor != self.request.user.vendor_profile:
            raise PermissionDenied("You can only delete your own products.")
        instance.delete()


class ProductApprovalView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def patch(self, request, pk):
        """
        Approve or reject a product.
        Admin can set 'is_active' = True (approve) or False (reject).
        """
        product = get_object_or_404(Product, pk=pk)

        action = request.data.get("action", "approve")  # default approve

        if action == "approve":
            product.is_active = True
            message = f"Product '{product.name}' approved successfully."
        elif action == "reject":
            product.is_active = False
            message = f"Product '{product.name}' rejected."
        else:
            return Response(
                {"error": "Invalid action. Use 'approve' or 'reject'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        product.save()
        return Response({"message": message}, status=status.HTTP_200_OK)


class ProductRejectView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        try:
            product = Product.objects.get(pk=pk)
            product.is_active = False
            product.save()
            return Response({"message": f"Product '{product.name}' rejected/disabled."})
        except Product.DoesNotExist:
            return Response({"error": "Product not found."}, status=404)


class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    permission_classes = [permissions.AllowAny]
