# jobtracker/settings_test.py
# Settings para tests — usa SQLite para evitar el bug de collation de WSL2

from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Desactivar caché Redis para tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Celery síncrono para tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Clave de cifrado de prueba
ENCRYPTION_KEY = 'dGVzdGtleXRlc3RrZXl0ZXN0a2V5dGVzdGtleXRlc3Q='