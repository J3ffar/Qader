# qader_project/settings/development.py
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Explicitly True for development

ALLOWED_HOSTS = ["localhost", "127.0.0.1"] + ALLOWED_HOSTS  # Add local dev hosts

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
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Use SQLite for simpler local dev if needed (but Postgres parity is better)
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
