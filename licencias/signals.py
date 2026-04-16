import random
from django.dispatch import receiver
from axes.signals import user_locked_out
from django.core.mail import send_mail
from django.core.cache import cache
from django.contrib.auth.models import User

@receiver(user_locked_out)
def enviar_token_desbloqueo(sender, request, username, **kwargs):
    user = User.objects.filter(username=username).first()
    
    if user and user.email:
        # 1. Generar token de 6 dígitos
        token = str(random.randint(100000, 999999))
        
        # 2. Guardarlo en cache por 10 minutos
        cache.set(f'token_desbloqueo_{username}', token, timeout=600)
        
        # 3. Guardar el username en la sesión para la vista
        request.session['usuario_bloqueado_nombre'] = username
        
        # 4. Enviar el correo (Usando tu Gmail configurado)
        asunto = '⚠️ Acceso Protegido - Código de Desbloqueo'
        mensaje = f"Hola {user.username},\n\nTu cuenta ha sido bloqueada tras 3 intentos. Usa este código para entrar directamente: {token}"
        
        send_mail(asunto, mensaje, None, [user.email], fail_silently=False)