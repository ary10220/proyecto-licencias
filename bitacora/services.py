from .models import Bitacora

def log_event(request=None, usuario=None, accion=None, modulo=None, descripcion="", extra=None):
    try:
        user = usuario if usuario else (request.user if request else None)

        ip = None
        if request:
            ip = get_client_ip(request)

        Bitacora.objects.create(
            usuario=user if user and user.is_authenticated else None,
            accion=accion,
            modulo=modulo,
            descripcion=descripcion,
            ip=ip 
        )

    except Exception:
        pass


def get_client_ip(request):
    try:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()

        x_real_ip = request.META.get('HTTP_X_REAL_IP')
        if x_real_ip:
            return x_real_ip.strip()

        remote_addr = request.META.get('REMOTE_ADDR')
        return remote_addr.strip() if remote_addr else None

    except Exception:
        return None
