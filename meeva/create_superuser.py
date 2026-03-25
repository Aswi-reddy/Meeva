import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meeva.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

admin_email = os.environ.get('ADMIN_EMAIL')
admin_password = os.environ.get('ADMIN_PASSWORD')

if admin_email and admin_password:
    # Determine the username field dynamically
    username_field = getattr(User, 'USERNAME_FIELD', 'username')
    
    if username_field == 'email':
        if not User.objects.filter(email=admin_email).exists():
            print(f"Creating superuser with email {admin_email}")
            User.objects.create_superuser(email=admin_email, password=admin_password)
        else:
            print("Superuser already exists.")
    else:
        username = admin_email.split('@')[0]
        if not User.objects.filter(username=username).exists():
            print(f"Creating superuser {username}")
            User.objects.create_superuser(username=username, email=admin_email, password=admin_password)
        else:
            print("Superuser already exists.")
else:
    print("ADMIN_EMAIL or ADMIN_PASSWORD not set. Skipping superuser creation.")
