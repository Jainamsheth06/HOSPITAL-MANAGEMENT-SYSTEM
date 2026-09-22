from django.apps import AppConfig
from django.db.models.signals import post_migrate

def ensure_owner_exists(sender, **kwargs):
    try:
        from django.contrib.auth.models import User
        user, created = User.objects.get_or_create(username='MediNEXA')
        user.set_password('MediNEXA_123')
        user.first_name = 'MediNEXA'
        user.last_name = 'Hospital Owner'
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save()
    except Exception:
        pass

class OwnerAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'owner_app'

    def ready(self):
        post_migrate.connect(ensure_owner_exists, sender=self)


