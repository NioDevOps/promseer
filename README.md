django-admin startproject promeseer
django-admin startapp webserver
python manage.py migrate
python manage.py createsuperuser --email admin@example.com --username admin


# start app
python manage.py runserver

# check db schema change
python manage.py makemigrations

# migrate db
python manage.py migrate