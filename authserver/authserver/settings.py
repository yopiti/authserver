import os
from typing import List

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from authserver.vault_db_credentials import VaultCredentialProvider, VaultAuthentication

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

INSTALLED_APPS = [
    'mailauth.MailAuthApp',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'authserver.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'authserver.wsgi.application'

DEBUG = False  # overridden by factorise() if defined

import authserver.vendor.django12factor as django12factor
globals().update(django12factor.factorise())

if DEBUG and not VaultAuthentication.has_envconfig():
    SECRET_KEY = "secretsekrit"  # FOR DEBUG ONLY!
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': 'mnusers.sqlite3',
        }
    }
else:
    VAULT = VaultAuthentication.fromenv()
    CREDS = VaultCredentialProvider("https://vault.local:8200/", VAULT,
                                    "postgresql/creds/authserver", os.getenv("VAULT_CA", None), True,
                                    DEBUG)

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'mnusers',
            'USER': CREDS.username,
            'PASSWORD': CREDS.password,
            'HOST': '127.0.0.1',
            'PORT': '5432',
        }
    }


if DEBUG:
    ALLOWED_HOSTS = []  # type: List[str]
else:
    ALLOWED_HOSTS = ["cas.maurus.net", ]

AUTH_USER_MODEL = "mailauth.MNUser"

# Validate email addresses against our special DB structure
AUTHENTICATION_BACKENDS = ['mailauth.auth.MNUserAuthenticationBackend']

# we use our own modular crypt format sha256 hasher for maximum compatibility
# with Dovecot, OpenSMTPD etc.
PASSWORD_HASHERS = ['mailauth.auth.UnixCryptCompatibleSHA256Hasher']

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/
STATIC_URL = '/static/'