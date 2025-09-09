from django.core.management.base import BaseCommand
from products.models import Category


class Command(BaseCommand):
    help = "Seed initial categories"

    def handle(self, *args, **kwargs):
        categories = [
            {"name": "Men", "slug": "men"},
            {"name": "Women", "slug": "women"},
            {"name": "Kids", "slug": "kids"},
            {"name": "Accessories", "slug": "accessories"},
        ]

        for cat in categories:
            obj, created = Category.objects.get_or_create(
                name=cat["name"], slug=cat["slug"]
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"Category '{cat['name']}' created."))
            else:
                self.stdout.write(self.style.WARNING(
                    f"Category '{cat['name']}' already exists."))
