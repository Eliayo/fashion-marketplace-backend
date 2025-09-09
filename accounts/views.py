from rest_framework import generics, status
from .models import User
from .serializers import RegisterSerializer, AdminUserSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .permissions import IsAdmin, IsSeller, IsCustomer


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
    permission_classes = [IsAuthenticated, IsSeller]

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
        if new_role not in [User.Roles.CUSTOMER, User.Roles.SELLER]:
            return Response(
                {"detail": "Invalid role. Only 'customer' or 'seller' allowed."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.role = new_role
        user.save()
        return Response({"detail": f"User {user.username} role updated to {user.role}."})
