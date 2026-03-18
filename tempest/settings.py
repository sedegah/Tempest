from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-=6z01d@l62utez2f%=+2*hdf$z*35n@=1d%xhk*3r_72(9a^+w'
DEBUG = True
ALLOWED_HOSTS = []

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'fileshare',
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

SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'False') == 'True'
SESSION_COOKIE_SECURE = SECURE_SSL_REDIRECT
CSRF_COOKIE_SECURE = SECURE_SSL_REDIRECT
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

ROOT_URLCONF = 'tempest.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'fileshare' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'tempest.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

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

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

FILES_ENCRYPTION_KEY = os.environ.get('FILES_ENCRYPTION_KEY', '1dHIzIgFg1We4ahnZ_qoKEmcDcAinwCyOJrOxPh-2yQ=')

CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'memory://')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'cache+memory://')
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

CELERY_BEAT_SCHEDULE = {
    'delete-expired-files-every-5-minutes': {
        'task': 'fileshare.tasks.delete_expired_files',
        'schedule': 300.0,
    },
}

USE_S3 = os.environ.get('USE_S3', 'False') == 'True'

if USE_S3:
    CLOUDFLARE_R2_ACCOUNT_ID = os.environ.get('CLOUDFLARE_R2_ACCOUNT_ID', '065fc200f5c2cb1f51dd59426f19012c')
    CLOUDFLARE_R2_ACCESS_KEY_ID = os.environ.get('CLOUDFLARE_R2_ACCESS_KEY_ID')
    CLOUDFLARE_R2_SECRET_ACCESS_KEY = os.environ.get('CLOUDFLARE_R2_SECRET_ACCESS_KEY', 'q80U1FFuq8M9ObfVCROLIOi2Dl20361eec2FjGuC')
    CLOUDFLARE_R2_STORAGE_BUCKET_NAME = os.environ.get('CLOUDFLARE_R2_STORAGE_BUCKET_NAME', 'tempest-fileshare')
    CLOUDFLARE_R2_ENDPOINT_URL = os.environ.get('CLOUDFLARE_R2_ENDPOINT_URL')
    
    STORAGES = {
        "default": {
            "BACKEND": "fileshare.storage.CloudflareR2Storage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
else:
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }

