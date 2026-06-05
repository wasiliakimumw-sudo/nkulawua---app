from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class Command(BaseCommand):
    help = "Create or update the admin superuser, bypassing password validators"

    def handle(self, *args, **options):
        username = "admin"
        password = "admin123"
        email = "admin@example.com"

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "is_superuser": True,
                "is_staff": True,
                "email": email,
            },
        )
        if not created:
            user.is_superuser = True
            user.is_staff = True
            user.email = email

        user.set_password(password)
        user.save(update_fields=["password", "is_superuser", "is_staff", "email"])

        self.stdout.write(self.style.SUCCESS(f"Admin user '{username}' ensured."))
