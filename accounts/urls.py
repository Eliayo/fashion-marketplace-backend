from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (RegisterView, ProfileView, SellerOnlyView, AdminOnlyView, CustomerOnlyView,
                    UserListView, UserDetailView, UserRoleUpdateView,
                    VendorProfileView, VendorListView
                    )

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("login/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Role-based test endpoints
    path("seller-only/", SellerOnlyView.as_view(), name="seller-only"),
    path("admin-only/", AdminOnlyView.as_view(), name="admin-only"),
    path("customer-only/", CustomerOnlyView.as_view(), name="customer-only"),

    # Admin user management
    path("users/", UserListView.as_view(), name="user-list"),
    path("users/<int:pk>/", UserDetailView.as_view(), name="user-detail"),
    path("users/<int:pk>/role/", UserRoleUpdateView.as_view(),
         name="user-role-update"),
    # Vendor profile management
    path("vendor/profile/", VendorProfileView.as_view(), name="vendor-profile"),
    path("vendors/", VendorListView.as_view(), name="vendor-list"),
]
