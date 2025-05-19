import os
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True  # Explicitly True for development

# Add development-specific apps
INSTALLED_APPS += [
    "debug_toolbar",
]

# Add development-specific middleware
MIDDLEWARE.insert(  # type: ignore
    MIDDLEWARE.index("django.middleware.common.CommonMiddleware") + 1,
    "debug_toolbar.middleware.DebugToolbarMiddleware",
)

# Debug Toolbar settings
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

if "rest_framework.renderers.BrowsableAPIRenderer" not in REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"]:  # type: ignore
    REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] += (  # type: ignore
        "rest_framework.renderers.BrowsableAPIRenderer",
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
            "format": "{levelname} {asctime} {name} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "[{asctime}] {levelname}: {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
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
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": config("DJANGO_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG and False else "INFO",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": True,
        },
    },
}

# Disable password validators during development for faster user creation
AUTH_PASSWORD_VALIDATORS = []


# For debugging Celery tasks locally without a broker
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# --- Channels ---
# For development, you might want a simpler channel layer backend if Redis isn't running
# For example, an in-memory backend (though Redis is usually preferred for consistency)
# CHANNEL_LAYERS = {
#     "default": {
#         "BACKEND": "channels.layers.InMemoryChannelLayer"
#     }
# }
# However, using Redis as in base.py is generally better for parity with production.
