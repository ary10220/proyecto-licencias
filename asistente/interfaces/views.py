"""
Endpoints del asistente de IA (AJAX, POST).

  - /asistente/ayuda/   -> chatbot de onboarding (texto).
  - /asistente/filtros/ -> interpreta lenguaje natural -> filtros del tablero.

Ambos requieren sesion activa. La consulta llega por form-data (`consulta`) o
por cuerpo JSON (`{"consulta": "..."}`).
"""
from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ..application.use_cases import AsistenteAyuda, AsistenteChat, InterpretarConsulta


def _leer_consulta(request) -> str:
    consulta = (request.POST.get('consulta') or '').strip()
    if not consulta and 'application/json' in (request.headers.get('Content-Type') or ''):
        try:
            body = json.loads(request.body or b'{}')
        except (json.JSONDecodeError, TypeError, ValueError):
            body = {}
        if isinstance(body, dict):
            consulta = str(body.get('consulta') or '').strip()
    return consulta


@login_required
@require_POST
def asistente_ayuda(request):
    consulta = _leer_consulta(request)
    rol = ', '.join(request.user.groups.values_list('name', flat=True))
    return JsonResponse(AsistenteAyuda().execute(consulta, rol))


@login_required
@require_POST
def asistente_filtros(request):
    consulta = _leer_consulta(request)
    return JsonResponse(InterpretarConsulta().execute(consulta))


@login_required
@require_POST
def asistente_chat(request):
    """Endpoint unificado: el modelo decide si responde ayuda o arma filtros.

    Los filtros/reportes solo se habilitan si el usuario tiene permiso para ver
    el tablero de licencias; la ayuda esta disponible para cualquier sesion.
    """
    consulta = _leer_consulta(request)
    rol = ', '.join(request.user.groups.values_list('name', flat=True))
    puede_ver_licencias = request.user.is_superuser or request.user.has_perm('licencias.view_licencia')
    resultado = AsistenteChat().execute(consulta, rol, puede_ver_licencias=puede_ver_licencias)

    if consulta:
        from bitacora.actions import log_asistente_consulta
        intencion = resultado.get('intencion')
        aplico_filtro = bool(resultado.get('aplicar')) if intencion == 'filtros' else False
        log_asistente_consulta(
            request, consulta=consulta, intencion=intencion,
            respuesta=resultado.get('respuesta'), aplico_filtro=aplico_filtro,
        )

    return JsonResponse(resultado)
