from pathlib import Path

# ============================
# BASE DIRECTORY
# ============================

BASE_DIR = Path(__file__).resolve().parent.parent


# ============================
# CORE SECURITY SETTINGS
# ============================

SECRET_KEY = 'django-insecure-change-this-in-production'

DEBUG = True  # 🔴 Change to False in production

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "enyx.omkumarpandey.com.np",
    "www.omkumarpandey.com.np",
]


# ============================
# APPLICATION DEFINITIONS
# ============================

INSTALLED_APPS = [

    # THIRD PARTY
    "jazzmin",
    "corsheaders",
    "rest_framework",

    # DJANGO DEFAULT
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # CUSTOM APPS
    "accounts",
    "main",
    "blogs",
]


# ============================
# MIDDLEWARE CONFIGURATION
# ============================

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# ============================
# CORS CONFIGURATION
# ============================

CORS_ALLOWED_ORIGINS = [
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500",
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:5500",
    "https://enyx.omkumarpandey.com.np",
    "https://www.omkumarpandey.com.np",
]

CORS_ALLOW_CREDENTIALS = True


# ============================
# CSRF CONFIGURATION
# ============================

CSRF_TRUSTED_ORIGINS = [
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:5500",
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:5500",
    "https://enyx.omkumarpandey.com.np",
    "https://www.omkumarpandey.com.np",
]

CSRF_COOKIE_SECURE = False   # ✅ Make True when DEBUG=False
SESSION_COOKIE_SECURE = False  # ✅ Make True when DEBUG=False


# ============================
# URL & WSGI CONFIGURATION
# ============================

ROOT_URLCONF = "ExpTrac.urls"

WSGI_APPLICATION = "ExpTrac.wsgi.application"


# ============================
# TEMPLATE CONFIGURATION
# ============================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "Frontend"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ============================
# DATABASE CONFIGURATION
# ============================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "ExpTrack",
        "USER": "ompandey",
        "PASSWORD": "ompandey@1200",
        "HOST": "localhost",
        "PORT": "5432",
    }
}


# ============================
# PASSWORD VALIDATION
# ============================

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ============================
# LANGUAGE & TIMEZONE SETTINGS
# ============================

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kathmandu"

USE_I18N = True
USE_TZ = True


# ============================
# STATIC FILES CONFIGURATION
# ============================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


# ============================
# MEDIA FILES CONFIGURATION
# ============================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ============================
# DEFAULT PRIMARY KEY FIELD
# ============================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================
# JAZZMIN ADMIN PANEL SETTINGS
# ============================

JAZZMIN_SETTINGS = {
    "site_title": "ExpTrac Admin",
    "site_header": "ExpTrac Control Panel",
    "site_brand": "ExpTrac",
    "welcome_sign": "WELCOME TO EXPTRAC ADMIN",
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
    },
    "theme": "default",
    "dark_mode_theme": "darkly",
}
