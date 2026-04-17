from django.conf import settings
from django.core.validators import validate_ipv46_address
from django.core.exceptions import ValidationError
from .models import Bitacora

def log_event(request=None, usuario=None, accion=None, modulo=None, descripcion="", extra=None):
    try:
        user = usuario if usuario else (request.user if request else None)

        ip = None
        if request:
            ip = get_client_ip(request)

        Bitacora.objects.create(
            usuario=user if user and user.is_authenticated else None,
            accion=(accion or "")[:255],
            modulo=(modulo or "")[:100],
            descripcion=descripcion,
            ip=ip 
        )
        return True

    except Exception as exc:
        if settings.DEBUG:
            print(f"BITACORA_ERROR: {exc}")
        return False


def get_client_ip(request):
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

        if x_forwarded_for:
            return normalize_ip(x_forwarded_for.split(',')[0].strip())

        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        if x_real_ip:
            return normalize_ip(x_real_ip.strip())

        remote_addr = request.META.get('REMOTE_ADDR')
        return normalize_ip(remote_addr.strip() if remote_addr else None)

    except Exception:
        return None


def normalize_ip(ip):
    if not ip:
        return None

    try:
        validate_ipv46_address(ip)
    except ValidationError:
        return None

    return ip
