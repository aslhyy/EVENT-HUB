from .base import *
from decouple import config

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = config(
    'ALLOWED_HOSTS',
    default='your-app.onrender.com',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

# Database - Production (Cloud MySQL - PlanetScale/Railway)
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='mysql.connector.django'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
            'ssl': {'ssl_mode': 'REQUIRED'},  # Required for cloud databases
        },
    }
}

# Security Settings for Production
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS Settings for Production
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='',
    cast=lambda v: [s.strip() for s in v.split(',')] if v else []
)
CORS_ALLOW_CREDENTIALS = True

# Email backend for production (SMTP)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# Cache with Redis (optional but recommended for production)
REDIS_URL = config('REDIS_URL', default=None)
if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }

# Static files handling for production
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Logging for production
LOGGING['handlers']['file']['filename'] = '/tmp/eventhub.log'