#!/bin/bash

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files for Django admin
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Create admin user if it doesn't exist
echo "Creating admin user..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()

# Check if admin user already exists
if not User.objects.filter(email='admin@resumeai.com').exists():
    admin_user = User.objects.create_user(
        email='admin@resumeai.com',
        name='Admin User',
        password='admin123456',
        is_staff=True,
        is_superuser=True
    )
    print(f"Admin user created: {admin_user.email}")
else:
    print("Admin user already exists")
EOF

echo "Build completed successfully!"
