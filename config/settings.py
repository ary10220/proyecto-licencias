import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-#^yxj0*56r=-^0@9n+z66mu0$+t#_l_6v+y0#j8w7bfmo1=6^t'

DEBUG = True

ALLOWED_HOSTS = ['joseagc.pythonanywhere.com', '127.0.0.1', 'localhost']


INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'bitacora',
    'user',
    'empleados',
    'licencias.apps.LicenciasConfig',
    'axes',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware',
    # Si un usuario fue creado con clave temporal, forzamos cambio en el primer ingreso.
    'user.interfaces.middleware.ForcePasswordChangeMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'config.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # Usado por `templates/base.html` para disparar el modal de cambio de contraseña.
                'user.interfaces.context_processors.force_password_change',
            ],
        },
    },
]


WSGI_APPLICATION = 'config.wsgi.application'


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
        'OPTIONS': {
            'timeout': 20,
        },
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'es-bo'
TIME_ZONE = 'America/La_Paz'
USE_I18N = True
USE_TZ = True


AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'django.contrib.auth.backends.ModelBackend',
]


AXES_FAILURE_LIMIT = 3
AXES_LOCK_OUT_AT_FAILURE = True
AXES_RESET_ON_SUCCESS = True
AXES_COOLOFF_TIME = 0.05
AXES_LOCKOUT_PARAMETERS = ['username', 'ip_address']
AXES_LOCKOUT_URL = '/desbloqueo-seguro/'


SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_SAVE_EVERY_REQUEST = True


# Cache:
# - En local usamos memoria para evitar depender de una tabla (createcachetable) y errores de SQLite/OneDrive.
# - En servidor puedes setear `DJANGO_CACHE_BACKEND=db` para usar DatabaseCache (requiere createcachetable).
if os.environ.get('DJANGO_CACHE_BACKEND', '').lower() == 'db':
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': os.environ.get('DJANGO_CACHE_TABLE', 'my_cache_table'),
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'local-dev',
        }
    }

AXES_CACHE = 'default'


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'arianyclaure@gmail.com'
EMAIL_HOST_PASSWORD = 'pusuvtrgfykwdila'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# LOGGING
# Habilita logging en consola para los modulos del proyecto.
# Util para ver fallos de SMTP (envio de tokens de desbloqueo) en development.
# En produccion, redirigir a un archivo o a un sistema externo (Sentry, etc.).
# ---------------------------------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] [{levelname}] {name}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'licencias': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'bitacora': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'user': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
