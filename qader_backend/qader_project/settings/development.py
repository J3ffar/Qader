# qader_project/settings/development.py
import os
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Explicitly True for development

# Add development-specific apps
INSTALLED_APPS += [
    "debug_toolbar",
]

# Add development-specific middleware
MIDDLEWARE += [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# Debug Toolbar settings
INTERNAL_IPS = [
    "127.0.0.1",
]

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"].append(
    "rest_framework.renderers.BrowsableAPIRenderer"
)

# Use console email backend for development
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Use SQLite for simpler local dev if needed (but Postgres parity is better)
if not config("DATABASE_URL"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Less strict password hashing for faster tests/dev
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",  # Adjust level for verbosity
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
            "propagate": False,
        },
    },
}

# Disable password validators during development for faster user creation
AUTH_PASSWORD_VALIDATORS = []

print("--- Development Settings Loaded ---")
