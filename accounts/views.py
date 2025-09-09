from rest_framework import generics, status, permissions
from .models import User, VendorProfile
from .serializers import RegisterSerializer, AdminUserSerializer, VendorProfileSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import IsAdmin, IsVendor, IsCustomer


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            "id": request.user.id,
            "username": request.user.username,
            "email": request.user.email,
            "role": request.user.role,
        })


class SellerOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get(self, request):
        return Response({"message": "Welcome Seller!"})


class AdminOnlyView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        return Response({"message": "Welcome Admin!"})


class CustomerOnlyView(APIView):
    """Example endpoint accessible only to Customers."""
    permission_classes = [IsAuthenticated, IsCustomer]

    def get(self, request):
        return Response({"message": "Welcome Customer!"})


class UserListView(generics.ListAPIView):
    """Admin can view all users."""
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Admin can view, update, or delete any user."""
    queryset = User.objects.all()
    serializer_class = AdminUserSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class UserRoleUpdateView(APIView):
    """Admin can change a user's role (e.g., customer → vendor)."""
    permission_classes = [IsAuthenticated, IsAdmin]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        new_role = request.data.get("role")
        if new_role not in [User.Roles.CUSTOMER, User.Roles.VENDOR]:
            return Response(
                {"detail": "Invalid role. Only 'customer' or 'vendor' allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.role = new_role
        user.save()

        if new_role == User.Roles.VENDOR and not hasattr(user, 'vendor_profile'):
            VendorProfile.objects.create(user=user)

        return Response({"detail": f"User {user.username} role updated to {user.role}."})


class VendorProfileView(APIView):
    permission_classes = [IsAuthenticated, IsVendor]

    def get(self, request):
        serializer = VendorProfileSerializer(request.user.vendor_profile)
        return Response(serializer.data)

    def patch(self, request):
        profile = request.user.vendor_profile
        serializer = VendorProfileSerializer(
            profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VendorListView(generics.ListAPIView):
    queryset = VendorProfile.objects.all()
    serializer_class = VendorProfileSerializer
    permission_classes = [IsAuthenticated, IsAdmin]


class SellerApprovalView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        try:
            seller = VendorProfile.objects.get(pk=pk)
            seller.verified = True
            seller.save()
            return Response({"message": f"Seller '{seller.business_name}' approved successfully."})
        except VendorProfile.DoesNotExist:
            return Response({"error": "Seller not found."}, status=404)


class SellerRejectView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAdmin]

    def post(self, request, pk):
        try:
            seller = VendorProfile.objects.get(pk=pk)
            seller.verification_status = False
            seller.save()
            return Response({"message": f"Seller '{seller.business_name}' rejected/disabled."})
        except VendorProfile.DoesNotExist:
            return Response({"error": "Seller not found."}, status=404)
