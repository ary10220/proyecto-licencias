from django.apps import AppConfig


class LicenciasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'licencias'

    def ready(self):
        # Activa los signals (Axes lockout desbloqueo).
        import licencias.signals  # noqa: F401

