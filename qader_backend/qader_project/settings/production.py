import os
from .base import *  # noqa F403

# --- Debugging ---
# CRITICAL: DEBUG must be False in production.
DEBUG = False

# --- Allowed Hosts ---
# Load from environment variable. This is CRITICAL for security.
# Example .env: ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())
if not ALLOWED_HOSTS:
    raise ValueError("ALLOWED_HOSTS environment variable must be set in production.")

# --- Security Settings (Uncomment and configure as appropriate) ---
# Ensure HTTPS is enforced by your web server (Nginx/Apache) or load balancer.
SECURE_PROXY_SSL_HEADER = (
    "HTTP_X_FORWARDED_PROTO",
    "https",
)  # If behind a reverse proxy
SECURE_SSL_REDIRECT = config(
    "SECURE_SSL_REDIRECT", default=True, cast=bool
)  # Redirect HTTP to HTTPS

SESSION_COOKIE_SECURE = config(
    "SESSION_COOKIE_SECURE", default=True, cast=bool
)  # Send session cookie only over HTTPS
CSRF_COOKIE_SECURE = config(
    "CSRF_COOKIE_SECURE", default=True, cast=bool
)  # Send CSRF cookie only over HTTPS
CSRF_COOKIE_HTTPONLY = config(
    "CSRF_COOKIE_HTTPONLY", default=True, cast=bool
)  # Prevent JS access to CSRF cookie

# HTTP Strict Transport Security (HSTS) - BE CAREFUL: start with small values for SECURE_HSTS_SECONDS
# SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=60, cast=int) # e.g., 31536000 for 1 year
# SECURE_HSTS_INCLUDE_SUBDOMAINS = config("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=bool)
# SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=True, cast=bool)

# Other security headers
SECURE_BROWSER_XSS_FILTER = config(
    "SECURE_BROWSER_XSS_FILTER", default=True, cast=bool
)  # Deprecated in modern browsers, but harmless
SECURE_CONTENT_TYPE_NOSNIFF = config(
    "SECURE_CONTENT_TYPE_NOSNIFF", default=True, cast=bool
)
X_FRAME_OPTIONS = config("X_FRAME_OPTIONS", default="DENY")  # Or 'SAMEORIGIN'

# --- Static Files ---
# WhiteNoise for serving static files efficiently from Django.
# Ensure 'whitenoise.middleware.WhiteNoiseMiddleware' is high in MIDDLEWARE list,
# typically right after SecurityMiddleware.
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")  # type: ignore
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# STATIC_ROOT is already defined in base.py and used by collectstatic.

# --- Admins for Error Reporting ---
ADMINS = []
admin_names_emails = config("ADMINS", default="")
if admin_names_emails:
    ADMINS = [tuple(admin.split(":")) for admin in admin_names_emails.split(",")]
# Example .env: ADMINS="Admin Name:admin@example.com,Other Admin:other@example.com"
MANAGERS = ADMINS

# --- Logging Configuration for Production ---
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)  # Ensure logs directory exists

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple_prod": {
            "format": "[{asctime}] {levelname} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {  # For environments like Docker that capture stdout/stderr
            "class": "logging.StreamHandler",
            "formatter": "simple_prod",
        },
        "file_django": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "django.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "file_app": {
            "level": "INFO",  # Or DEBUG for more verbosity from your apps
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "app.log",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
            "formatter": "verbose",  # Optional: use a specific formatter for emails
        },
    },
    "root": {  # Catch-all logger
        "handlers": ["console", "file_app"],  # Default for unspecified loggers
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file_django"],
            "level": config("DJANGO_LOG_LEVEL_PROD", default="INFO"),
            "propagate": False,  # Do not propagate to root if handled here
        },
        "django.request": {  # Specifically for request errors (5xx)
            "handlers": ["mail_admins", "file_django"],  # Also log to file
            "level": "ERROR",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["mail_admins", "file_django"],
            "level": "ERROR",
            "propagate": False,
        },
        # Your project's apps (e.g., "apps" if they are all under an "apps" namespace)
        "apps": {
            "handlers": ["console", "file_app"],
            "level": config("APP_LOG_LEVEL_PROD", default="INFO"),
            "propagate": True,  # Allow propagation if you want root to also handle it
        },
        # Example for a specific app
        # "apps.users": {
        #     "handlers": ["console", "file_app"],
        #     "level": "INFO",
        #     "propagate": False,
        # },
    },
}

# --- Caching ---
# IMPORTANT: Configure a robust cache backend for production.
# Using Redis is highly recommended.
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config(
            "REDIS_CACHE_URL",
            default=f"redis://{config('REDIS_HOST', '127.0.0.1')}:{config('REDIS_PORT', 6379)}/0",
        ),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "PASSWORD": config("REDIS_PASSWORD", default=None),
            "CONNECTION_POOL_KWARGS": {"max_connections": 50},
        },
    }
}

# --- Simple JWT Signing Key ---
# CRITICAL: Use a unique, strong secret for JWT signing, different from SECRET_KEY.
# Load it from an environment variable.
SIMPLE_JWT["SIGNING_KEY"] = config("JWT_SIGNING_KEY")  # type: ignore
if SIMPLE_JWT["SIGNING_KEY"] == SECRET_KEY:  # type: ignore
    # Only raise error if JWT_SIGNING_KEY was not explicitly set to be the same as SECRET_KEY
    if not config(
        "JWT_SIGNING_KEY", default=None
    ):  # Check if it fell back to SECRET_KEY default
        raise ValueError(
            "In production, JWT_SIGNING_KEY must be set to a unique secret "
            "and be different from SECRET_KEY."
        )


# --- Template loading in Production ---
# To improve performance, use the cached template loader.
# Ensure TEMPLATES[0]['APP_DIRS'] is True or 'loaders' is correctly configured.
TEMPLATES[0]["APP_DIRS"] = False
TEMPLATES[0]["OPTIONS"]["loaders"] = [  # type: ignore
    (
        "django.template.loaders.cached.Loader",
        [
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        ],
    )
]

# --- Health Check (Optional, but good practice) ---
# If you use a health check library like `django-health-check`:
# HEALTH_CHECK = { ... }
