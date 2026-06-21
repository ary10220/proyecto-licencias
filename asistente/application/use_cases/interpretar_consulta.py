"""
Interprete de filtros: convierte una consulta en lenguaje natural en filtros
para el dashboard / lista de licencias, validados contra el catalogo real.

Este modulo expone piezas reutilizables (constantes, esquema y la funcion
`normalizar_filtros`) que tambien usa el asistente unificado `AsistenteChat`.

Salida (dict) consumida por el widget JS:
  - vista     : "reportes" (dashboard) | "lista" (gestionar_licencias)
  - tenant    : id de Tenant       (0 si no aplica) -> ruta del dashboard
  - empresa   : id de Empresa      (0 si no aplica) -> dashboard ?empresa=
  - tipo      : id de TipoLicencia (0 si no aplica) -> ?tipo=
  - proveedor : id de Proveedor    (0 si no aplica) -> lista ?proveedor=
  - estado    : estado operativo / derivado          -> lista ?estado=
  - origen    : MANUAL | FACTURA | SYNC              -> dashboard ?origen=
  - texto     : busqueda libre                        -> lista ?q=
  - respuesta : frase de confirmacion para el chat
"""
from __future__ import annotations

import json

from ...infrastructure import catalogo as cat
from ...infrastructure import openai_client as ai

ESTADOS = ['', 'DISPONIBLE', 'ASIGNADA', 'VENCIDA', 'POR_VENCER', 'SUSPENDIDA', 'PENDIENTE_ACTIVACION', 'REVOCADA']
ORIGENES = ['', 'MANUAL', 'FACTURA', 'SYNC']
VISTAS = ['reportes', 'lista', 'ninguna']

# Reglas reutilizables (las usa tambien el prompt combinado de AsistenteChat).
REGLAS_FILTROS = """\
- tenant, empresa, tipo, proveedor: devolve el id EXACTO del catalogo cuyo nombre coincida (acepta errores de \
tipeo, mayusculas y coincidencias parciales). Si no se menciona o no hay coincidencia clara, devolve 0.
- estado: "DISPONIBLE" si dice disponible/libre/sin asignar; "ASIGNADA" si asignada/en uso/ocupada; \
"VENCIDA" si vencida/caducada/expirada; "POR_VENCER" si por vencer/proxima a vencer/vence pronto; \
"SUSPENDIDA", "PENDIENTE_ACTIVACION" o "REVOCADA" segun corresponda; "" si no aplica.
- origen: "FACTURA" si pide licencias generadas por factura/compra; "SYNC" si por sincronizacion/Microsoft 365/M365; \
"MANUAL" si registro manual; "" si no aplica.
- vista: "lista" si pide la lista/detalle/buscar una licencia o filtrar por estado/proveedor/texto; \
"reportes" si pide graficos/indicadores/KPIs/resumen/dashboard.
- texto: termino de busqueda libre (nombre de software, fabricante, codigo SKU o numero de factura) si lo menciona; si no, "".
- respuesta: una frase corta, amable, en espanol, confirmando que filtraste."""

SYSTEM_PROMPT = (
    'Sos el asistente de reportes de un sistema de gestion de licencias de software corporativo (multiempresa). '
    'Convertis la frase del usuario en filtros para el tablero. Respondes SOLO con los campos del esquema, sin texto extra.\n'
    'Reglas:\n' + REGLAS_FILTROS
)

# Esquema (solo filtros) para el endpoint dedicado /asistente/filtros/.
SCHEMA = {
    'type': 'object',
    'additionalProperties': False,
    'properties': {
        'vista': {'type': 'string', 'enum': ['reportes', 'lista', 'ninguna']},
        'tenant': {'type': 'integer'},
        'empresa': {'type': 'integer'},
        'tipo': {'type': 'integer'},
        'proveedor': {'type': 'integer'},
        'estado': {'type': 'string', 'enum': ESTADOS},
        'origen': {'type': 'string', 'enum': ORIGENES},
        'texto': {'type': 'string'},
        'respuesta': {'type': 'string'},
    },
    'required': ['vista', 'tenant', 'empresa', 'tipo', 'proveedor', 'estado', 'origen', 'texto', 'respuesta'],
}


# ---------------------------------------------------------------------------
# Helpers reutilizables (nivel de modulo)
# ---------------------------------------------------------------------------
def _int(valor) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return 0


def _inferir(consulta: str) -> dict:
    """Fallback por palabras clave para estado y origen."""
    q = consulta.lower()

    estado = ''
    if any(k in q for k in ('por vencer', 'proxima a vencer', 'próxima a vencer', 'vence pronto', 'a vencer')):
        estado = 'POR_VENCER'
    elif any(k in q for k in ('vencid', 'caducad', 'expirad')):
        estado = 'VENCIDA'
    elif any(k in q for k in ('disponible', 'libre', 'sin asignar', 'sin usar')):
        estado = 'DISPONIBLE'
    elif any(k in q for k in ('asignad', 'en uso', 'ocupad')):
        estado = 'ASIGNADA'
    elif 'suspendid' in q:
        estado = 'SUSPENDIDA'
    elif 'revocad' in q:
        estado = 'REVOCADA'
    elif any(k in q for k in ('pendiente de activacion', 'pendiente de activación', 'sin activar')):
        estado = 'PENDIENTE_ACTIVACION'

    origen = ''
    if any(k in q for k in ('factura', 'compra', 'compradas')):
        origen = 'FACTURA'
    elif any(k in q for k in ('sincroniz', 'm365', 'microsoft 365', 'office 365')):
        origen = 'SYNC'
    elif any(k in q for k in ('manual', 'cargada a mano', 'registro manual')):
        origen = 'MANUAL'

    return {'estado': estado, 'origen': origen}


def _inferir_vista(consulta: str, tiene_filtros: bool) -> str:
    q = consulta.lower()
    claves_lista = ['lista', 'listar', 'detalle', 'buscar', 'busca', 'mostrame', 'mostrar', 'cuales', 'cuáles']
    if any(k in q for k in claves_lista):
        return 'lista'
    claves_reportes = ['grafico', 'gráfico', 'indicador', 'kpi', 'resumen', 'dashboard', 'tablero', 'reporte', 'cuantas', 'cuántas', 'total']
    if any(k in q for k in claves_reportes):
        return 'reportes'
    return 'lista' if tiene_filtros else 'reportes'


def _respuesta_defecto(vista: str, tiene_filtros: bool) -> str:
    if tiene_filtros:
        return 'Listo, apliqué los filtros que entendí. Si querés, lo afino por empresa, tipo, proveedor o estado.'
    if vista == 'lista':
        return 'Te llevo a la lista de licencias. Decime estado, software o proveedor para filtrar más fino.'
    return 'Te muestro el dashboard general. Si querés, indicame empresa, tipo de licencia u origen.'


def _normalizar_respuesta(respuesta_modelo: str, vista: str, tiene_filtros: bool) -> str:
    if not respuesta_modelo:
        return _respuesta_defecto(vista, tiene_filtros)
    r = respuesta_modelo.lower()
    genericas = [
        'no se encontraron filtros', 'sin filtros', 'no encontre filtros', 'no encontré filtros',
        'no pude filtrar', 'no se pudo filtrar', 'no es clara',
    ]
    if any(g in r for g in genericas):
        return _respuesta_defecto(vista, tiene_filtros)
    return respuesta_modelo


def normalizar_filtros(parsed: dict, catalogo: dict, consulta: str) -> dict:
    """Valida la salida del modelo contra el catalogo y devuelve filtros usables."""
    ids_tenant = {t['id'] for t in catalogo['tenants']}
    ids_empresa = {e['id'] for e in catalogo['empresas']}
    ids_tipo = {t['id'] for t in catalogo['tipos']}
    ids_prov = {p['id'] for p in catalogo['proveedores']}

    tenant = _int(parsed.get('tenant'))
    empresa = _int(parsed.get('empresa'))
    tipo = _int(parsed.get('tipo'))
    proveedor = _int(parsed.get('proveedor'))
    estado = str(parsed.get('estado') or '')
    origen = str(parsed.get('origen') or '')
    vista = str(parsed.get('vista') or 'ninguna')
    texto = str(parsed.get('texto') or '').strip()

    inferidos = _inferir(consulta)
    if not estado:
        estado = inferidos['estado']
    if not origen:
        origen = inferidos['origen']

    tenant = tenant if tenant in ids_tenant else 0
    empresa = empresa if empresa in ids_empresa else 0
    tipo = tipo if tipo in ids_tipo else 0
    proveedor = proveedor if proveedor in ids_prov else 0
    estado = estado if estado in ESTADOS else ''
    origen = origen if origen in ORIGENES else ''
    vista = vista if vista in VISTAS else 'ninguna'

    tiene_filtros = bool(tenant or empresa or tipo or proveedor or estado or origen or texto)

    if vista == 'ninguna':
        vista = _inferir_vista(consulta, tiene_filtros)
    if (estado or proveedor or texto) and vista == 'reportes':
        vista = 'lista'

    respuesta = _normalizar_respuesta(str(parsed.get('respuesta') or '').strip(), vista, tiene_filtros)

    return {
        'vista': vista,
        'tenant': tenant,
        'empresa': empresa,
        'tipo': tipo,
        'proveedor': proveedor,
        'estado': estado,
        'origen': origen,
        'texto': texto,
        'respuesta': respuesta,
    }


def filtros_vacios() -> dict:
    """Conjunto de filtros neutro (sin nada aplicado)."""
    return {
        'vista': 'ninguna', 'tenant': 0, 'empresa': 0, 'tipo': 0,
        'proveedor': 0, 'estado': '', 'origen': '', 'texto': '',
    }


class InterpretarConsulta:
    """Endpoint dedicado de filtros (se mantiene; el widget usa AsistenteChat)."""

    def execute(self, consulta: str) -> dict:
        consulta = (consulta or '').strip()
        if not consulta:
            return self._fallback('Escribi o deci que reporte queres ver.')

        catalogo = cat.construir_catalogo()
        user = (
            'Catalogo (usa estos ids):\n'
            + json.dumps(catalogo, ensure_ascii=False)
            + '\n\nConsulta del usuario:\n'
            + consulta
        )

        try:
            texto_modelo = ai.chat(
                system=SYSTEM_PROMPT, user=user, schema=SCHEMA,
                schema_name='filtros_dashboard', temperature=0, max_tokens=400, timeout=20,
            )
        except ai.AsistenteNoConfigurado:
            return self._fallback('El asistente todavia no esta configurado (falta la clave OPENAI_API_KEY).')
        except ai.AsistenteError:
            return self._fallback('No pude consultar al asistente en este momento. Proba de nuevo.')

        try:
            parsed = json.loads(texto_modelo)
        except (json.JSONDecodeError, TypeError):
            parsed = None
        if not isinstance(parsed, dict):
            return self._fallback('No entendi bien la consulta. La podes reformular?')

        return {'ok': True, **normalizar_filtros(parsed, catalogo, consulta)}

    @staticmethod
    def _fallback(mensaje: str) -> dict:
        return {'ok': False, 'respuesta': mensaje, **filtros_vacios()}
