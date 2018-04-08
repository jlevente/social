# Social authenticator and data collector

A django web app for social authentication and a data collector class to retrieve contributions of authorized users from diferent social apps


### Prerequisites

You will need a PostgreSQL instalce with postgis and pipenv.


### Installing

Pull the `django-allauth` package from [my repo](https://github.com/jlevente/django-allauth) that contains additional oauth providers, such as OSM, Mapillary and Strava. Install it with pipenv

```
cd some_path
git clone https://github.com/jlevente/django-allauth
cd path_to_django_webapp
pipenv install -e some_path/django-allauth
pipenv sync
pipenv shell
```

Set the following environmental variables: `DJANGO_SOCIAL_SECRET`, `DJANGO_SOCIAL_DEFAULT_DB_[x]`, `DJANGO_SOCIAL_DATA_DB_[x]`, where `x` corresponds to `NAME`, `USER`, `PASS`, `HOST` and `PORT`.

```
cd socialcollector

```

Create a django superuser with `python manage.py createsuperuser`. Run `python manage.py migrate` and `python manage.py runserver`. You can now check your developement instance at [http://127.0.0.1:8000](http://127.0.0.1:8000). Add your social app credentials (client key, secret) at [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin).

### Set up data db.

TODO

