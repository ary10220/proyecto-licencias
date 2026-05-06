from django.apps import AppConfig


class BitacoraConfig(AppConfig):
    name = 'bitacora'

    def ready(self):
        # Register auth signals (login/logout) for system bitácora.
        import bitacora.interfaces.signals  # noqa: F401
