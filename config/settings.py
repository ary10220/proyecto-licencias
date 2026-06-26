import os
import stripe
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

def _load_env(path):
    if not path.exists():
        return
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'y', 'on'}


def _env_list(name, default=None):
    value = os.environ.get(name, '')
    if not value:
        return default or []
    return [item.strip() for item in value.split(',') if item.strip()]


_load_env(BASE_DIR / '.env')


SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-local-dev-only-change-me')

DEBUG = _env_bool('DEBUG', True)

ALLOWED_HOSTS = _env_list(
    'ALLOWED_HOSTS',
    ['joseagc.pythonanywhere.com', '127.0.0.1', 'localhost'],
)


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
    'facturacion.apps.FacturacionConfig',
    'gestion_global.apps.GestionGlobalConfig',
    'asistente.apps.AsistenteConfig',
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


EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = _env_bool('EMAIL_USE_TLS', True)
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)


OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')

STRIPE_PUBLIC_KEY = 'pk_test_51Tc5FXR9Wz6slWaNeuH4AGQqWGAjlQ7luu98uqC0rfl8jKDunmE0NBZ6h5SguicsOfVSUNSVEvbOQGKf2aeZcqSh00uasCg6dJ'
STRIPE_SECRET_KEY = 'sk_test_51Tc5FXR9Wz6slWaNIjuGNGdpakQ6syneIW2WBdMjJ8uXwhQGM2OyFfSMSnPRIMcw89iHecn4dJglCmmDDgvM84r400tk1dGDQc'

# Dias antes del vencimiento en los que se envia la alerta automatica (management command enviar_alertas).
# Se avisa cuando faltan EXACTAMENTE estos dias para el vencimiento de una licencia.
ALERTAS_DIAS_AVISO = [30, 15, 7, 1]


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# LOGGING
# Habilita logging en consola para los modulos del proyecto.
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
