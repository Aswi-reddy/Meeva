web: cd Meeva && python manage.py collectstatic --noinput && python manage.py migrate && python create_superuser.py && gunicorn meeva.wsgi --bind 0.0.0.0:$PORT --log-file -
