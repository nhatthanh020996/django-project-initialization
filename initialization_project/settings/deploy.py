from os.path import join
import os

from .default import *
from .logger import LOGGING


# ##### DEBUG CONFIGURATION ###############################
DEBUG = os.environ.get("DEBUG", "False") == "True"

# allow all hosts during development
ALLOWED_HOSTS = ["*"]


# ##### APPLICATION CONFIGURATION #########################

INSTALLED_APPS = DEFAULT_APPS + [
    "core",
    'rest_framework',
]

MIDDLEWARE = DEFAULT_MIDDLEWARE + [
    "core.middlewares.interceptor.InterceptMiddleware",
    "core.middlewares.logging.LoggingMiddleware",
]


ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")


# ##### DATABASE CONFIGURATION ############################
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "dbname"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "123qweQWE!"),
        "HOST": os.environ.get("POSTGRES_HOST", "postgres"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}


# ##### CACHES CONFIGURATION ################
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("REDIS_CACHE_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": os.environ.get("REDIS_CACHE_PWD", ""),
        },
    }
}