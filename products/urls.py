from django.urls import path
from .views import (CategoryListView, CategoryCreateView,
                    CategoryUpdateDeleteView, ProductListView, ProductCreateView,
                    ProductApprovalView, ProductRejectView, ProductUpdateView, ProductDeleteView,
                    ProductDetailView
                    )

urlpatterns = [
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/create/", CategoryCreateView.as_view(), name="category-create"),
    path("categories/<int:pk>/", CategoryUpdateDeleteView.as_view(),
         name="category-detail"),
    path("", ProductListView.as_view(), name="product-list"),
    path("create/", ProductCreateView.as_view(), name="product-create"),
    path("approve/<int:pk>/", ProductApprovalView.as_view(), name="product-approve"),
    path("reject/<int:pk>/", ProductRejectView.as_view(), name="product-reject"),

    path("<int:pk>/update/", ProductUpdateView.as_view(), name="product-update"),
    path("<int:pk>/delete/", ProductDeleteView.as_view(), name="product-delete"),
    path("<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
]
