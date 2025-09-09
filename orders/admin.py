from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem

admin.site.register([Cart, CartItem, Order, OrderItem])
