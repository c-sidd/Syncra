"""Django settings for Syncra."""

import os
import environ
from pathlib import Path

env = environ.Env()
BASE_DIR = Path(__file__).resolve().parent.parent
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = env('DJANGO_SECRET_KEY')
CREDENTIAL_ENCRYPTION_KEY = env('CREDENTIAL_ENCRYPTION_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list(
    'ALLOWED_HOSTS',
    default=[
        'localhost',
        '127.0.0.1',
        'syncra-production-84c8.up.railway.app',
    ]
)

INSTALLED_APPS = ['django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'rest_framework', 'rest_framework.authtoken', 'corsheaders', 'users.apps.UsersConfig', 'folders.apps.FoldersConfig', 'files.apps.FilesConfig']
MIDDLEWARE = ['corsheaders.middleware.CorsMiddleware', 'django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware', 'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.debug', 'django.template.context_processors.request', 'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'

if env('DATABASE_URL', default=''):
    DATABASES = {'default': env.db('DATABASE_URL')}
else:
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', 'NAME': env('DB_NAME', default='driveclone'), 'USER': env('DB_USER', default='postgres'), 'PASSWORD': env('DB_PASSWORD', default=''), 'HOST': env('DB_HOST', default='127.0.0.1'), 'PORT': env('DB_PORT', default='5432')}}

AUTH_PASSWORD_VALIDATORS = [{'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'}, {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'}, {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'}, {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'}]
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True
STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=['http://localhost:3000', 'http://127.0.0.1:3000', 'http://localhost:5173', 'http://127.0.0.1:5173'])
REST_FRAMEWORK = {'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework.authentication.TokenAuthentication']}

# Sensible API limits protect public login/register endpoints and prevent a
# single browser session from accidentally flooding AWS with requests.
REST_FRAMEWORK.update({
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {'anon': '20/minute', 'user': '240/minute'},
})

# Keep local development convenient while making production HTTPS-only by
# default. Railway and similar proxies set X-Forwarded-Proto.
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Explicit environment switches avoid breaking local/CI HTTP test clients.
    # Production must set both values in its secret configuration.
    SECURE_SSL_REDIRECT = env.bool('SECURE_SSL_REDIRECT', default=False)
    SECURE_HSTS_SECONDS = env.int('SECURE_HSTS_SECONDS', default=0)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
REFERRER_POLICY = 'same-origin'

# Reject oversized uploads before they reach application/S3 storage.
# Override with MAX_UPLOAD_SIZE_BYTES in production if needed.
MAX_UPLOAD_SIZE_BYTES = env.int('MAX_UPLOAD_SIZE_BYTES', default=100 * 1024 * 1024)
