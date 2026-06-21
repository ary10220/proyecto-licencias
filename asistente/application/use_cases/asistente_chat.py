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
    '- intencion = "filtros": SOLO cuando el usuario quiere VER el DASHBOARD / REPORTES de licencias filtrado '
    'por alguno de estos criterios del tablero: tenant, empresa, tipo de licencia, origen, estado '
    '(disponible / asignada / vencida / por vencer / suspendida / pendiente de activacion / revocada) o proveedor. '
    'Completá esos campos y poné en "respuesta" una frase corta confirmando que abris el dashboard con ese filtro.\n'
    '- intencion = "ayuda": para TODO lo demas. Como funciona o donde esta algo, como usar cualquier modulo '
    '(empleados, facturacion, usuarios, roles, bitacora, gestion global, asignaciones), buscar a alguien por '
    'nombre o CI, etc. Poné la explicacion en "respuesta" (2 a 5 frases o pasos) y dejá los filtros en 0 o "".\n\n'
    'IMPORTANTE: los filtros SOLO aplican al dashboard de reportes y SOLO con esos 6 criterios. Si el pedido no se '
    'puede resolver con ellos (p. ej. buscar por nombre, ver empleados, una factura puntual), respondé como "ayuda".\n\n'
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
            return self._fallback('El asistente todavía no está configurado (falta la clave OPENAI_API_KEY).')
        except ai.AsistenteError:
            return self._fallback('No pude consultar al asistente en este momento. Probá de nuevo.')

        try:
            parsed = json.loads(texto_modelo)
        except (json.JSONDecodeError, TypeError):
            parsed = None
        if not isinstance(parsed, dict):
            return self._fallback('No entendí bien tu consulta. ¿La podés reformular?')

        if parsed.get('intencion') == 'filtros' and puede_ver_licencias and catalogo is not None:
            return {'ok': True, 'intencion': 'filtros', **normalizar_filtros(parsed, catalogo, consulta)}

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
