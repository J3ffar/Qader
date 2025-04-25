from datetime import timedelta
from pathlib import Path
from decouple import config, Csv
import dj_database_url
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config("SECRET_KEY")
OPENAI_API_KEY = config("OPENAI_API_KEY", default=None)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party apps
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "django_filters",
    "taggit",
    # Project apps
    "apps.api",
    "apps.users",
    "apps.learning",
    "apps.study",
    "apps.gamification",
    "apps.challenges",
    "apps.content",
    "apps.community",
    "apps.blog",
    "apps.support",
    "apps.admin_panel",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "corsheaders.middleware.CorsMiddleware",
]

ROOT_URLCONF = "qader_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
            ],
        },
    },
]

WSGI_APPLICATION = "qader_project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": dj_database_url.config(default=config("DATABASE_URL"), conn_max_age=600)
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-us"  # Or 'ar' if primary language is Arabic
TIME_ZONE = "UTC"  # Or your relevant timezone like 'Asia/Riyadh'
USE_I18N = False
USE_L10N = True
USE_FORMAT_REPLICATION = True
USE_TZ = True

LANGUAGES = [
    ("ar", _("Arabic")),
    ("en", _("English")),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # For production collection
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Media files (User uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email configuration
EMAIL_BACKEND = config(
    "EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend"
)
# EMAIL_HOST = config("EMAIL_HOST", default="")
# EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
# EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
# EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
# EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
# DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="webmaster@localhost")

# Django REST Framework
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    # "EXCEPTION_HANDLER": "apps.api.exceptions.custom_exception_handler",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "PAGE_SIZE_QUERY_PARAM": "page_size",
    "MAX_PAGE_SIZE": 100,
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
        "rest_framework.filters.SearchFilter",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1"],
}

# DRF Spectacular (OpenAPI Schema) Settings
SPECTACULAR_SETTINGS = {
    "TITLE": "Qader Platform API",
    "DESCRIPTION": "API documentation for the Qader Learning Platform",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    # Define Tag order and descriptions
    "TAGS": [
        {
            "name": "Authentication",
            "description": "User registration, login, logout, password reset.",
        },
        {
            "name": "User Profile",
            "description": "Manage current user profile and settings.",
        },
        {
            "name": "Public Content",
            "description": "Endpoints for publicly accessible content (Pages, FAQ, Partners, Contact).",
        },
        {
            "name": "Learning Content",
            "description": "Access learning structure (Sections, Subsections, Skills, Questions).",
        },
        {
            "name": "Study & Progress",
            "description": "Endpoints for user study activities, tests, and progress tracking.",
        },
        {
            "name": "Gamification",
            "description": "Endpoints related to points, streaks, badges, and rewards.",
        },
        {"name": "Challenges", "description": "Endpoints for user-vs-user challenges."},
        {
            "name": "Student Community",
            "description": "Endpoints for the community forum.",
        },
        {
            "name": "Blog",
            "description": "Endpoints for blog posts and advice requests.",
        },
        {
            "name": "Support (User)",
            "description": "Endpoints for users to manage their support tickets.",
        },
        # --- Admin Panel Tags ---
        {
            "name": "Admin Panel - User Management",
            "description": "Endpoints for administrators to manage users, sub-admins, points, and passwords.",
        },
        {
            "name": "Admin Panel - Learning Management",
            "description": "Endpoints for administrators to manage learning content (Sections, Subsections, Skills, Questions).",
        },
        {
            "name": "Admin Panel - Content Management",
            "description": "Endpoints for administrators to manage public content (Pages, FAQ, Partners, Contact Messages).",
        },
        {
            "name": "Admin Panel - Support Management",
            "description": "Endpoints for administrators to manage all support tickets.",
        },
        {
            "name": "Admin Panel - Serial Code Management",
            "description": "Endpoints for administrators to manage subscription serial codes.",
        },
    ],
    "SWAGGER_UI_SETTINGS": {  # Fine-tune Swagger UI appearance/behavior
        "deepLinking": True,
        "persistAuthorization": True,
        "displayRequestDuration": True,
        "filter": True,
        "docExpansion": "list",
    },
    "PREPROCESSING_HOOKS": [],
    "POSTPROCESSING_HOOKS": [],
}

# --- Simple JWT Settings ---
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=config("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=60, cast=int)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=config("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=1, cast=int)
    ),
    "ROTATE_REFRESH_TOKENS": True,  # Issue new refresh token when refreshing
    "BLACKLIST_AFTER_ROTATION": True,  # Blacklist old refresh token
    "UPDATE_LAST_LOGIN": True,  # Update user's last_login field on token refresh
    "ALGORITHM": "HS256",
    "SIGNING_KEY": config(
        "JWT_SIGNING_KEY", default=SECRET_KEY
    ),  # Use separate key ideally
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "JWK_URL": None,
    "LEEWAY": 0,
    "AUTH_HEADER_TYPES": (
        "Bearer",
    ),  # Standard header: "Authorization: Bearer <token>"
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "USER_AUTHENTICATION_RULE": "rest_framework_simplejwt.authentication.default_user_authentication_rule",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "TOKEN_USER_CLASS": "rest_framework_simplejwt.models.TokenUser",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(
        minutes=5
    ),  # Not typically used with Access/Refresh pair
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),  # Not typically used
}

# CORS Settings
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="", cast=Csv())

# --- Gamification Point Constants ---
POINTS_QUESTION_SOLVED_CORRECT = config(
    "POINTS_QUESTION_SOLVED_CORRECT", default=1, cast=int
)
POINTS_TEST_COMPLETED = config("POINTS_TEST_COMPLETED", default=10, cast=int)
POINTS_LEVEL_ASSESSMENT_COMPLETED = config(
    "POINTS_LEVEL_ASSESSMENT_COMPLETED", default=25, cast=int
)
POINTS_STREAK_BONUS_MAP = {  # More flexible than individual settings
    2: config("POINTS_STREAK_BONUS_2_DAYS", default=5, cast=int),
    10: config("POINTS_STREAK_BONUS_10_DAYS", default=20, cast=int),
    # Add more milestones here: 30: config(...)
}
POINTS_BADGE_EARNED = config("POINTS_BADGE_EARNED", default=15, cast=int)
POINTS_CHALLENGE_PARTICIPATION = config(
    "POINTS_CHALLENGE_PARTICIPATION", default=5, cast=int
)
POINTS_CHALLENGE_WIN = config("POINTS_CHALLENGE_WIN", default=10, cast=int)
POINTS_REFERRAL_BONUS = config("POINTS_REFERRAL_BONUS", default=25, cast=int)  # Example

# Define Badge Slugs constants (optional but good practice)
BADGE_SLUG_5_DAY_STREAK = config("BADGE_SLUG_5_DAY_STREAK", default="5-day-streak")
BADGE_SLUG_10_DAY_STREAK = config(
    "BADGE_SLUG_10_DAY_STREAK", default="10-days-studying"
)  # Matches description
BADGE_SLUG_FIRST_FULL_TEST = config(
    "BADGE_SLUG_FIRST_FULL_TEST", default="first-full-test"
)
BADGE_SLUG_50_QUESTIONS = config(
    "BADGE_SLUG_50_QUESTIONS", default="50-questions-solved"
)
