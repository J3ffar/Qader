from .base import *

# Override settings for testing
LANGUAGE_CODE = "en"

# Use synchronous password hasher for faster tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Use in-memory channel layer for testing WebSockets
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# Optional: Speed up tests by using SQLite in memory if not already doing so
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable logging noise during tests if desired
# LOGGING = {} # Or configure specific loggers

# Ensure DEBUG is False for testing production-like behavior where relevant
DEBUG = False
