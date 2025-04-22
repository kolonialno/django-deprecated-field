from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

DEBUG = True
USE_TZ = True

INSTALLED_APPS = [
    # Django
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Apps
    "tests.app",
    # Third party
    "django_deprecated_field",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

DEPRECATED_FIELD_STRICT = False
DEPRECATED_FIELD_USE_STRUCTLOG = True
