import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - keeps settings importable before deps install
    load_dotenv = None


BASE_DIR = Path(__file__).resolve().parent.parent


def load_env_file(path):
    if not path.exists():
        return
    if load_dotenv is not None:
        load_dotenv(path, override=False)
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def env(name, default=None, required=False, aliases=()):
    value = os.environ.get(name)
    for alias in aliases:
        if value is not None and value != "":
            break
        value = os.environ.get(alias)
    if value is None or value == "":
        if required:
            raise RuntimeError(f"Missing required environment variable: {name}")
        return default
    return value


def env_bool(name, default=False, aliases=()):
    value = env(name, aliases=aliases)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def env_int(name, default=0, aliases=()):
    value = env(name, aliases=aliases)
    if value is None:
        return default
    return int(value)


def env_list(name, default=None, required=False, aliases=()):
    value = env(name, required=required, aliases=aliases)
    if value is None:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


load_env_file(BASE_DIR / ".env")

DJANGO_ENV = env("DJANGO_ENV", "development").strip().lower()
DEBUG = env_bool("DEBUG", DJANGO_ENV != "production", aliases=("DJANGO_DEBUG",))
IS_PRODUCTION = DJANGO_ENV == "production" or not DEBUG

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    "django-insecure-local-development-only-change-me",
    required=IS_PRODUCTION,
)
ALLOWED_HOSTS = env_list(
    "ALLOWED_HOSTS",
    ["127.0.0.1", "localhost"],
    required=IS_PRODUCTION,
    aliases=("DJANGO_ALLOWED_HOSTS",),
)
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.inspection",
]

LOGIN_URL = "admin:login"
LOGIN_REDIRECT_URL = "inspection:dashboard"
LOGOUT_REDIRECT_URL = "admin:login"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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
                "apps.inspection.i18n.context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("DB_NAME", required=True, aliases=("POSTGRES_DB",)),
        "USER": env("DB_USER", required=True, aliases=("POSTGRES_USER",)),
        "PASSWORD": env("DB_PASSWORD", required=True, aliases=("POSTGRES_PASSWORD",)),
        "HOST": env("DB_HOST", required=True, aliases=("POSTGRES_HOST",)),
        "PORT": env("DB_PORT", "5432", required=True, aliases=("POSTGRES_PORT",)),
        "CONN_MAX_AGE": env_int("DB_CONN_MAX_AGE", 60, aliases=("POSTGRES_CONN_MAX_AGE",)),
        "OPTIONS": {
            "sslmode": env("DB_SSLMODE", "prefer", aliases=("POSTGRES_SSLMODE",)),
        },
    }
}

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

LANGUAGE_CODE = "th"
TIME_ZONE = "Asia/Bangkok"
USE_I18N = True
LANGUAGES = [
    ("th", "ไทย"),
    ("en", "English"),
]
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", False)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", not DEBUG)
SECURE_HSTS_SECONDS = env_int("DJANGO_SECURE_HSTS_SECONDS", 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", not DEBUG)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", not DEBUG)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

if env_bool("DJANGO_USE_X_FORWARDED_PROTO", True):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

