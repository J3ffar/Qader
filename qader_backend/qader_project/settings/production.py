from .base import *

DEBUG = False  # Explicitly False for production

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())  # Load production hosts from env

# Security settings for production
# Ensure HTTPS is enforced by the web server (Nginx/Apache) or load balancer
# SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') # If behind a proxy
# SECURE_SSL_REDIRECT = True # Redirect HTTP to HTTPS (if not handled by webserver)
SESSION_COOKIE_SECURE = True  # Send session cookie only over HTTPS
CSRF_COOKIE_SECURE = True  # Send CSRF cookie only over HTTPS
# SECURE_HSTS_SECONDS = 31536000 # 1 year - Enable HTTP Strict Transport Security (start small)
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True
# SECURE_BROWSER_XSS_FILTER = True
# SECURE_CONTENT_TYPE_NOSNIFF = True
# X_FRAME_OPTIONS = 'DENY' # Default is SAMEORIGIN, DENY is more secure if not embedding

# Static files storage for production (using WhiteNoise)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_ROOT = BASE_DIR / "staticfiles"  # Collect static files here for whitenoise

# Production Email Backend (configure via .env)
EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.smtp.EmailBackend"
)

# Logging Configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "file": {
            "level": "WARNING",  # Log warnings and errors to a file
            "class": "logging.FileHandler",
            "filename": BASE_DIR
            / "logs/django_production.log",  # Ensure logs directory exists
            "formatter": "verbose",
        },
        "mail_admins": {  # Send critical errors to ADMINS
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],  # Log Django output to console and file
            "level": "INFO",  # Adjust Django's log level
            "propagate": True,
        },
        "django.request": {  # Send emails for server errors (5xx)
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "apps": {  # Your custom app logging
            "handlers": ["console", "file"],
            "level": "INFO",  # Adjust level for your apps
            "propagate": True,
        },
    },
}

# Define ADMINS and MANAGERS for error reporting
# ADMINS = [('Your Name', 'your_admin_email@example.com')]
# MANAGERS = ADMINS
