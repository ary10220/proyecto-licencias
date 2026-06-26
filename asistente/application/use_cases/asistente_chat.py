"""
Asistente UNIFICADO: un solo chat que, segun el mensaje del usuario, decide por
si mismo si debe RESPONDER UNA AYUDA (como funciona / donde esta algo) o ARMAR
UN FILTRO/REPORTE del tablero. El usuario ya no elige el modo: lo descubre el
modelo en una sola llamada (salida estructurada con un campo `intencion`).

Reutiliza las piezas ya existentes:
  - la guia de modulos (`GUIA_MODULOS`) para responder ayuda,
  - las reglas y validacion de filtros (`REGLAS_FILTROS`, `normalizar_filtros`).
"""
from __future__ import annotations

import json

from ...infrastructure import catalogo as cat
from ...infrastructure import openai_client as ai
from .asistente_ayuda import GUIA_MODULOS
from .interpretar_consulta import (
    ACCIONES,
    ESTADOS,
    FORMATOS,
    ORIGENES,
    REGLAS_FILTROS,
    VISTAS,
    filtros_vacios,
    interpretar_local,
    normalizar_filtros,
)

SYSTEM_PROMPT = (
    'Sos el asistente del sistema de Gestion de Licencias de software (control de TI corporativo, multiempresa).\n'
    'REGLA DE ORO: si el usuario te da una ORDEN de ver/filtrar/mostrar datos del dashboard de licencias, intencion='
    '"filtros" y VOS HACÉS EL FILTRO (NUNCA le das pasos manuales para que filtre el solo). Si te hace una PREGUNTA '
    'de como/donde/que (quiere aprender a usar el sistema), intencion="ayuda" y le explicás los pasos.\n\n'
    '- intencion = "filtros": cuando te PIDE ver o filtrar el dashboard de licencias (ordenes como "filtrame...", '
    '"mostrame...", "quiero ver...", "dame las licencias..."). Resolvé contra el catalogo SOLO estos criterios y '
    'devolvé el id/enum exacto: tenant, empresa, tipo de licencia, origen, estado (disponible / asignada / vencida / '
    'por vencer / suspendida / pendiente de activacion / revocada) y proveedor.\n'
    '  Si NO podés resolver ningun filtro concreto —porque no dio un valor (ej. "filtra por empresa" sin decir cual) '
    'o porque pidio algo que el dashboard NO soporta (ordenar por "mas recientes", por precio o por fecha; buscar por '
    'nombre o CI)— dejá TODOS los filtros en 0/"" y en "respuesta" escribí una ACLARACION breve: reconocé lo que pidio, '
    'aclarale que el dashboard se filtra por tenant, empresa, tipo de licencia, origen, estado o proveedor (no por '
    'recencia, precio ni nombre) y preguntale por cual querés filtrar. NUNCA des pasos manuales aca: el filtro lo hacés vos.\n'
    '  Si el usuario pide QUITAR / LIMPIAR los filtros o VER TODO el inventario sin filtros (ej. "limpia los filtros", '
    '"quita los filtros", "ver todo", "mostrame todas las licencias", "sin filtros"), intencion="filtros" con '
    'accion="limpiar" y TODOS los filtros en 0/"" (vos limpias el tablero).\n'
    '- intencion = "ayuda": SOLO cuando el usuario PREGUNTA como funciona, como se hace, donde esta o que es algo '
    '(quiere aprender), o pregunta por otros modulos (empleados, facturacion, usuarios, roles, bitacora, gestion '
    'global, asignaciones). En "respuesta" EXPLICÁ COMO HACERLO con PASOS NUMERADOS y accionables (1., 2., 3. ...): el '
    'primer paso indica el modulo del menu lateral y el boton por donde empezar; los siguientes que cargar o tocar '
    'hasta terminar (3 a 6 pasos). Basate UNICAMENTE en la guia de abajo: NO inventes pantallas ni pasos. '
    'Dejá los filtros en 0/"".\n\n'
    '== REGLAS PARA LOS FILTROS (solo si intencion="filtros") ==\n'
    + REGLAS_FILTROS
    + '\n\n== GUIA DEL SISTEMA (para responder cuando intencion="ayuda") ==\n'
    'No inventes funciones que no esten aca. Si te preguntan algo ajeno al sistema, decilo con amabilidad.\n'
    + GUIA_MODULOS
)

SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'intencion': {'type': 'string', 'enum': ['ayuda', 'filtros']},
        'respuesta': {'type': 'string'},
        'vista': {'type': 'string', 'enum': VISTAS},
        'tenant': {'type': 'integer'},
        'empresa': {'type': 'integer'},
        'tipo': {'type': 'integer'},
        'proveedor': {'type': 'integer'},
        'estado': {'type': 'string', 'enum': ESTADOS},
        'origen': {'type': 'string', 'enum': ORIGENES},
        'texto': {'type': 'string'},
        'accion': {'type': 'string', 'enum': ACCIONES},
        'formato': {'type': 'string', 'enum': FORMATOS},
    },
    'required': [
        'intencion', 'respuesta', 'vista', 'tenant', 'empresa',
        'tipo', 'proveedor', 'estado', 'origen', 'texto', 'accion', 'formato',
    ],
}


class AsistenteChat:
    """Asistente unico: clasifica la intencion y responde en una sola llamada."""

    def execute(self, consulta: str, rol: str = '', puede_ver_licencias: bool = True) -> dict:
        """
        `puede_ver_licencias`: si es False (el usuario no tiene el permiso
        `licencias.view_licencia`), el asistente NO arma filtros ni expone el
        catalogo; solo responde ayuda.
        """
        consulta = (consulta or '').strip()
        if not consulta:
            return self._fallback(
                'Escribí tu consulta. Puedo explicarte cómo usar el sistema o mostrarte un reporte.'
            )

        # Solo se incluye el catalogo (y se habilitan los filtros) si el usuario
        # tiene permiso para ver el tablero de licencias.
        catalogo = cat.construir_catalogo() if puede_ver_licencias else None
        system = SYSTEM_PROMPT
        if not puede_ver_licencias:
            system += (
                '\n\nIMPORTANTE: el usuario NO tiene permiso para ver el tablero de licencias. '
                'NUNCA uses intencion="filtros"; respondé siempre intencion="ayuda".'
            )

        user = (f'Rol del usuario: {rol}.\n\n' if rol else '')
        if catalogo is not None:
            user += 'Catalogo (usa estos ids para los filtros):\n' + json.dumps(catalogo, ensure_ascii=False) + '\n\n'
        user += 'Mensaje del usuario:\n' + consulta

        try:
            texto_modelo = ai.chat(
                system=system, user=user, schema=SCHEMA,
                schema_name='asistente', temperature=0, max_tokens=600, timeout=25,
            )
        except ai.AsistenteNoConfigurado:
            if puede_ver_licencias and catalogo is not None:
                return {'ok': True, 'intencion': 'filtros', **normalizar_filtros(interpretar_local(consulta, catalogo), catalogo, consulta)}
            return self._fallback('El asistente todavia no esta configurado (falta la clave OPENAI_API_KEY).')
        except ai.AsistenteError:
            if puede_ver_licencias and catalogo is not None:
                return {'ok': True, 'intencion': 'filtros', **normalizar_filtros(interpretar_local(consulta, catalogo), catalogo, consulta)}
            return self._fallback('No pude consultar al asistente en este momento. Proba de nuevo.')

        try:
            parsed = json.loads(texto_modelo)
        except (json.JSONDecodeError, TypeError):
            parsed = None
        if not isinstance(parsed, dict):
            if puede_ver_licencias and catalogo is not None:
                return {'ok': True, 'intencion': 'filtros', **normalizar_filtros(interpretar_local(consulta, catalogo), catalogo, consulta)}
            return self._fallback('No entendi bien tu consulta. La podes reformular?')

        if parsed.get('intencion') == 'filtros' and puede_ver_licencias and catalogo is not None:
            normalizado = normalizar_filtros(parsed, catalogo, consulta)
            if not normalizado.get('aplicar'):
                local = normalizar_filtros(interpretar_local(consulta, catalogo), catalogo, consulta)
                if local.get('aplicar'):
                    normalizado = local
            return {'ok': True, 'intencion': 'filtros', **normalizado}

        # Si pidio filtros pero no tiene permiso, lo reconducimos a ayuda.
        if parsed.get('intencion') == 'filtros' and not puede_ver_licencias:
            return {
                'ok': True, 'intencion': 'ayuda', **filtros_vacios(),
                'respuesta': 'No tenés permiso para ver el tablero de licencias, pero puedo explicarte cómo usar el sistema.',
            }

        respuesta = (parsed.get('respuesta') or '').strip() or 'No entendí bien tu pregunta. ¿La podés reformular?'
        return {'ok': True, 'intencion': 'ayuda', 'respuesta': respuesta, **filtros_vacios()}

    @staticmethod
    def _fallback(mensaje: str) -> dict:
        return {'ok': False, 'intencion': 'ayuda', 'respuesta': mensaje, **filtros_vacios()}
