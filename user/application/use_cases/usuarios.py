from __future__ import annotations

from dataclasses import dataclass

from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from bitacora.actions import (
    log_usuario_crear,
    log_usuario_editar,
    log_usuario_reset_password,
    log_usuario_toggle,
)

from ...infrastructure import repositories as repo


@dataclass(frozen=True)
class PasswordResetResult:
    ok: bool
    status: int = 200
    message: str | None = None
    email: str | None = None
    username: str | None = None


def uc_listar_usuarios():
    return repo.list_usuarios()


def uc_crear_usuario(request, form) -> User:
    usuario = form.save()
    log_usuario_crear(request, usuario)
    return usuario


def uc_editar_usuario(request, form) -> User:
    usuario = form.save()
    log_usuario_editar(request, usuario, password_changed=getattr(form, 'password_changed', False))
    return usuario


def uc_toggle_usuario(request, usuario: User) -> tuple[User, str]:
    usuario = repo.toggle_usuario_activo(usuario)
    estado = "activado" if usuario.is_active else "desactivado"
    log_usuario_toggle(request, usuario, estado)
    return usuario, estado


def uc_reset_password_usuario(request, usuario: User) -> PasswordResetResult:
    email = (usuario.email or '').strip()
    if not email:
        return PasswordResetResult(ok=False, status=400, message='El usuario no tiene correo registrado.')

    lock_key = f"pwreset_lock:user:{usuario.pk}"
    if not cache.add(lock_key, "1", timeout=20):
        return PasswordResetResult(
            ok=False,
            status=429,
            message="Ya se envio un enlace recientemente. Espera unos segundos e intenta nuevamente.",
        )

    uid = urlsafe_base64_encode(force_bytes(usuario.pk))
    token = default_token_generator.make_token(usuario)
    protocol = 'https' if request.is_secure() else 'http'
    domain = request.get_host()
    reset_path = reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})

    context = {
        'user': usuario,
        'protocol': protocol,
        'domain': domain,
        'uid': uid,
        'token': token,
        'reset_path': reset_path,
    }

    subject = render_to_string('registration/password_reset_subject.txt', context).strip().replace('\n', '')
    body = render_to_string('registration/password_reset_email.txt', context)

    try:
        send_mail(subject, body, None, [email], fail_silently=False)
    except Exception:
        return PasswordResetResult(ok=False, status=500, message='No se pudo enviar el correo de restablecimiento.')

    log_usuario_reset_password(request, usuario, email)
    return PasswordResetResult(ok=True, status=200, email=email, username=usuario.username)

