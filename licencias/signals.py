import random

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.mail import send_mail
from django.dispatch import receiver

from axes.signals import user_locked_out


@receiver(user_locked_out)
def preparar_desbloqueo(sender, request, username, **kwargs):
    """
    Cuando Axes bloquea el acceso (3 intentos fallidos), guardamos el username en
    sesión para habilitar la pantalla de desbloqueo.

    Nota: NO enviamos correo aquí para evitar spam/duplicados; el envío se hace
    bajo demanda desde /solicitar-token/ (botón en la pantalla de desbloqueo).
    """
    user = User.objects.filter(username=username).first()
    if not user:
        return

    request.session['usuario_bloqueado_nombre'] = username

    # Envío automático (una sola vez) al bloquear, con rate-limit para evitar duplicados.
    # Mantenemos el botón "Solicitar código" como reenvío bajo demanda.
    ip = request.META.get('REMOTE_ADDR') or ''
    lock_key = f"unlock_autosend_lock:{username}:{ip}"
    if not cache.add(lock_key, "1", timeout=60):
        return

    email = (user.email or '').strip()
    if not email:
        return

    token = str(random.randint(100000, 999999))
    cache.set(f"token_desbloqueo_{username}", token, timeout=300)  # 5 minutos

    subject = "Acceso protegido - Código de desbloqueo"
    message = (
        f"Hola {user.username},\n\n"
        "Tu cuenta fue bloqueada tras 3 intentos fallidos de inicio de sesión.\n"
        f"Tu código de desbloqueo es: {token}\n\n"
        "Este código es válido por 5 minutos."
    )

    send_mail(subject, message, getattr(settings, 'DEFAULT_FROM_EMAIL', None), [email], fail_silently=False)
