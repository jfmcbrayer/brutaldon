"""
Django settings for brutaldon project.

Generated by 'django-admin startproject' using Django 2.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "6lq9!52j^)=m89))umaphx9ac%)b$k^gs%x1rkk^v^$u9zjz$@"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "widget_tweaks",
    "sanitizer",
    "django.contrib.humanize",
    "brutaldon",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "brutaldon.middleware.timezone.TimezoneMiddleware",
]

ROOT_URLCONF = "brutaldon.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "brutaldon.context_processors.bookmarklet_url",
            ]
        },
    }
]

WSGI_APPLICATION = "brutaldon.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {"()": "django.utils.log.RequireDebugFalse"},
        "require_debug_true": {"()": "django.utils.log.RequireDebugTrue"},
    },
    "formatters": {
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[%(server_time)s] %(message)s",
        }
    },
    "handlers": {
        "console": {
            "level": "INFO",
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
        },
        "console_debug_false": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "logging.StreamHandler",
        },
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "console_debug_false", "mail_admins"],
            "level": "INFO",
        },
        "django.server": {
            "handlers": ["django.server"],
            "level": "INFO",
            "propagate": False,
        },
    },
}


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "America/New_York"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Sanitizer settings
SANITIZER_ALLOWED_TAGS = [
    "a",
    "p",
    "img",
    "br",
    "i",
    "strong",
    "em",
    "pre",
    "code",
    "ul",
    "li",
    "ol",
    "blockquote",
    "del",
    "span",
    "u",
]
SANITIZER_ALLOWED_ATTRIBUTES = ["href", "src", "title", "alt", "class", "lang"]

# File upload settings.
# Important: media will not work if you change this.
FILE_UPLOAD_HANDLERS = ["django.core.files.uploadhandler.TemporaryFileUploadHandler"]

# Session serialization
# Important: whatever you choose has to be able to serialize DateTime, so not JSON.
SESSION_SERIALIZER = "django.contrib.sessions.serializers.PickleSerializer"

# URL to redirect users to when not logged in
ANONYMOUS_HOME_URL = "about"

# URL to redirect galaxy brain users to
RICKROLL_URL = "https://invidio.us/watch?v=dQw4w9WgXcQ"

# Function to check if trying to add an account should trigger a special response
def CHECK_INSTANCE_URL(url, redirect):
    if "gab.com" in url:
        return redirect(RICKROLL_URL)
    elif "shitposter.club" in url:
        return redirect(RICKROLL_URL)


# Version number displayed on about page
BRUTALDON_VERSION = "2.14.1"

# Load custom settings outside repository tracked files, so private settings
# don't get added to the repository
import sys
def paths():
    sys.path.append('???')
    try:
        from xdg import XDG_CONFIG_HOME, XDG_CONFIG_DIRS
    except ImportError:
        try:
            from pathlib import Path
        except ImportError:
            home = os.environ['home']
        else:
            home = Path.home()
        sys.path[-1] = os.path.join(home, ".config")
        yield
        sys.path[-1] = home
        yield
    else:
        sys.path[-1] = XDG_CONFIG_HOME
        yield
        for directory in XDG_CONFIG_DIRS:
            sys.path[-1] = directory
            yield
    finally:
        sys.path.pop(-1)

for _ in paths():
    try:
        from brutaldon_settings import *
    except ImportError: pass
    else:
        break
