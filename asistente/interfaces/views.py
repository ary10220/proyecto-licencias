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
    """Endpoint unificado: el modelo decide si responde ayuda o arma filtros."""
    consulta = _leer_consulta(request)
    rol = ', '.join(request.user.groups.values_list('name', flat=True))
    return JsonResponse(AsistenteChat().execute(consulta, rol))
