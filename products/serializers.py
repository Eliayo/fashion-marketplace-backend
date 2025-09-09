from rest_framework import serializers
from .models import Category, Product, ProductImage, ProductVariant


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "parent", "is_active"]


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ["id", "image"]


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ["id", "size", "color", "stock"]


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True)
    variants = ProductVariantSerializer(many=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "category",
                  "is_active", "images", "variants", "created_at"]

    def create(self, validated_data):
        images_data = validated_data.pop("images", [])
        variants_data = validated_data.pop("variants", [])
        product = Product.objects.create(**validated_data)

        for img in images_data:
            ProductImage.objects.create(product=product, **img)

        for var in variants_data:
            ProductVariant.objects.create(product=product, **var)

        return product
