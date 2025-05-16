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

# Less strict password hashing for faster tests/dev
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",  # Adjust level for verbosity
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


# --- Channels ---
# For development, you might want a simpler channel layer backend if Redis isn't running
# For example, an in-memory backend (though Redis is usually preferred for consistency)
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels.layers.InMemoryChannelLayer"
#     }
# }
# However, using Redis as in base.py is generally better for parity with production.
