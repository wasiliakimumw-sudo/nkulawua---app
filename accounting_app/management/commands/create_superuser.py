from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Creates a superuser if not exists"

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "is_superuser": True,
                "is_staff": True,
            }
        )
        user.set_password("admin123")
        user.is_superuser = True
        user.is_staff = True
        user.save()
        if created:
            self.stdout.write(self.style.SUCCESS("Superuser created: admin / admin123"))
        else:
            self.stdout.write(self.style.SUCCESS("Superuser password updated: admin / admin123"))