from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Roles(models.TextChoices):
        CUSTOMER = "customer", "Customer"
        VENDOR = "vendor", "Vendor"
        ADMIN = "admin", "Admin"

    role = models.CharField(
        max_length=20, choices=Roles.choices, default=Roles.CUSTOMER)
    must_change_password = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.role})"


class VendorProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="vendor_profile")
    business_name = models.CharField(max_length=255, blank=True, null=True)
    logo = models.ImageField(upload_to="vendor_logos/", blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    verified = models.BooleanField(default=False)
    contact_email = models.EmailField(blank=True, null=True)

    def __str__(self):
        return self.business_name or f"Vendor {self.user.username}"
