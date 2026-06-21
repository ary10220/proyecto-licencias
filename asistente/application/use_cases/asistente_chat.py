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
from .interpretar_consulta import ESTADOS, ORIGENES, REGLAS_FILTROS, filtros_vacios, normalizar_filtros

SYSTEM_PROMPT = (
    'Sos el asistente del sistema de Gestion de Licencias de software (control de TI corporativo, multiempresa).\n'
    'Segun el MENSAJE del usuario decidi su intencion y respondé SOLO con los campos del esquema:\n\n'
    '- intencion = "filtros": cuando el usuario quiere VER o BUSCAR datos: una lista de licencias, un reporte, '
    'el dashboard, o filtrar por empresa, estado, tipo, proveedor, origen, etc. Completá los campos de filtro y '
    'poné en "respuesta" una frase corta confirmando el filtro.\n'
    '- intencion = "ayuda": cuando el usuario PREGUNTA como funciona algo, donde esta algo, que hace un modulo o '
    'pide una explicacion/instrucciones. Poné la explicacion en "respuesta" (2 a 5 frases o pasos cortos) y dejá '
    'TODOS los filtros en 0 o "".\n\n'
    'Ante la duda: si pide ver/listar/mostrar/filtrar datos -> "filtros"; si pregunta como/donde/que es/para que '
    'sirve -> "ayuda".\n\n'
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
        'vista': {'type': 'string', 'enum': ['reportes', 'lista', 'ninguna']},
        'tenant': {'type': 'integer'},
        'empresa': {'type': 'integer'},
        'tipo': {'type': 'integer'},
        'proveedor': {'type': 'integer'},
        'estado': {'type': 'string', 'enum': ESTADOS},
        'origen': {'type': 'string', 'enum': ORIGENES},
        'texto': {'type': 'string'},
    },
    'required': [
        'intencion', 'respuesta', 'vista', 'tenant', 'empresa',
        'tipo', 'proveedor', 'estado', 'origen', 'texto',
    ],
}


class AsistenteChat:
    """Asistente unico: clasifica la intencion y responde en una sola llamada."""

    def execute(self, consulta: str, rol: str = '') -> dict:
        consulta = (consulta or '').strip()
        if not consulta:
            return self._fallback(
                'Escribí tu consulta. Puedo explicarte cómo usar el sistema o mostrarte un reporte.'
            )

        catalogo = cat.construir_catalogo()
        user = (
            (f'Rol del usuario: {rol}.\n\n' if rol else '')
            + 'Catalogo (usa estos ids para los filtros):\n'
            + json.dumps(catalogo, ensure_ascii=False)
            + '\n\nMensaje del usuario:\n'
            + consulta
        )

        try:
            texto_modelo = ai.chat(
                system=SYSTEM_PROMPT, user=user, schema=SCHEMA,
                schema_name='asistente', temperature=0, max_tokens=600, timeout=25,
            )
        except ai.AsistenteNoConfigurado:
            return self._fallback('El asistente todavía no está configurado (falta la clave OPENAI_API_KEY).')
        except ai.AsistenteError:
            return self._fallback('No pude consultar al asistente en este momento. Probá de nuevo.')

        try:
            parsed = json.loads(texto_modelo)
        except (json.JSONDecodeError, TypeError):
            parsed = None
        if not isinstance(parsed, dict):
            return self._fallback('No entendí bien tu consulta. ¿La podés reformular?')

        if parsed.get('intencion') == 'filtros':
            return {'ok': True, 'intencion': 'filtros', **normalizar_filtros(parsed, catalogo, consulta)}

        respuesta = (parsed.get('respuesta') or '').strip() or 'No entendí bien tu pregunta. ¿La podés reformular?'
        return {'ok': True, 'intencion': 'ayuda', 'respuesta': respuesta, **filtros_vacios()}

    @staticmethod
    def _fallback(mensaje: str) -> dict:
        return {'ok': False, 'intencion': 'ayuda', 'respuesta': mensaje, **filtros_vacios()}
