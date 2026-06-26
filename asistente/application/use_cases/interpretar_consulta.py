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
import unicodedata

from ...infrastructure import catalogo as cat
from ...infrastructure import openai_client as ai

ESTADOS = ['', 'DISPONIBLE', 'ASIGNADA', 'VENCIDA', 'POR_VENCER', 'SUSPENDIDA', 'PENDIENTE_ACTIVACION', 'REVOCADA']
ORIGENES = ['', 'MANUAL', 'FACTURA', 'SYNC']
VISTAS = ['reportes', 'lista', 'ninguna']
ACCIONES = ['filtrar', 'exportar', 'limpiar']
FORMATOS = ['', 'PDF', 'EXCEL', 'CSV']

# Etiquetas legibles para construir la confirmacion autoritativa de filtros.
ESTADO_LABELS = {
    'DISPONIBLE': 'Disponible', 'ASIGNADA': 'Asignada', 'VENCIDA': 'Vencida',
    'POR_VENCER': 'Por vencer', 'SUSPENDIDA': 'Suspendida',
    'PENDIENTE_ACTIVACION': 'Pendiente de activación', 'REVOCADA': 'Revocada',
}
ORIGEN_LABELS = {'MANUAL': 'Manual', 'FACTURA': 'Factura', 'SYNC': 'Sincronización'}

# Reglas reutilizables (las usa tambien el prompt combinado de AsistenteChat).
REGLAS_FILTROS = """\
- tenant, empresa, tipo, proveedor: devolve el id EXACTO del catalogo cuyo nombre coincida (acepta errores de \
tipeo, mayusculas y coincidencias parciales). Si no se menciona o no hay coincidencia clara, devolve 0.
- estado: "DISPONIBLE" si dice disponible/libre/sin asignar; "ASIGNADA" si asignada/en uso/ocupada; \
"VENCIDA" si vencida/caducada/expirada; "POR_VENCER" si por vencer/proxima a vencer/vence pronto/vence en los proximos 30 dias; \
"SUSPENDIDA" si suspendida/pausada/inhabilitada temporalmente; "PENDIENTE_ACTIVACION" si pendiente de activacion/sin activar/falta activar; \
"REVOCADA" si revocada/cancelada/anulada; "" si no aplica.
- origen: "FACTURA" si pide licencias generadas por factura/compra; "SYNC" si por sincronizacion/Microsoft 365/M365; \
"MANUAL" si registro manual; "" si no aplica.
- vista: "lista" si pide la lista/detalle/buscar una licencia o filtrar por estado/proveedor/texto; \
"reportes" si pide graficos/indicadores/KPIs/resumen/dashboard.
- texto: termino de busqueda libre (nombre de software, fabricante, codigo SKU o numero de factura) si lo menciona; si no, "".
- accion: "exportar" si pide crear/generar/descargar un reporte; si no, "filtrar".
- accion: "limpiar" si pide limpiar/quitar/restablecer filtros.
- formato: "PDF", "EXCEL" o "CSV" si pide exportar; "" si no aplica.
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
        'accion': {'type': 'string', 'enum': ACCIONES},
        'formato': {'type': 'string', 'enum': FORMATOS},
        'respuesta': {'type': 'string'},
    },
    'required': ['vista', 'tenant', 'empresa', 'tipo', 'proveedor', 'estado', 'origen', 'texto', 'accion', 'formato', 'respuesta'],
}


# ---------------------------------------------------------------------------
# Helpers reutilizables (nivel de modulo)
# ---------------------------------------------------------------------------
def _int(valor) -> int:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return 0


def _normalizar_texto(valor: str) -> str:
    text = unicodedata.normalize('NFKD', str(valor or ''))
    text = ''.join(ch for ch in text if not unicodedata.combining(ch))
    return ' '.join(text.lower().split())


def _score_nombre(nombre: str, consulta_normalizada: str) -> int:
    nombre_norm = _normalizar_texto(nombre)
    if not nombre_norm:
        return 0
    if nombre_norm in consulta_normalizada:
        return 100 + len(nombre_norm)
    consulta_tokens = set(consulta_normalizada.split())
    tokens = [token for token in nombre_norm.split() if len(token) > 2]
    return sum(1 for token in tokens if token in consulta_tokens)


def _buscar_id_catalogo(items: list[dict], consulta: str) -> int:
    consulta_norm = _normalizar_texto(consulta)
    mejor_id = 0
    mejor_score = 0
    empate = False
    for item in items:
        score = _score_nombre(item.get('nombre', ''), consulta_norm)
        if score > mejor_score:
            mejor_id = item.get('id') or 0
            mejor_score = score
            empate = False
        elif score and score == mejor_score:
            empate = True
    return 0 if empate and mejor_score < 100 else int(mejor_id or 0)


def _inferir_accion_formato(consulta: str) -> tuple[str, str]:
    q = _normalizar_texto(consulta)
    if any(k in q for k in ('limpiar filtros', 'quitar filtros', 'sacar filtros', 'restablecer filtros')):
        return 'limpiar', ''
    exportar = any(k in q for k in (
        'export', 'descarg', 'generar reporte', 'genera reporte',
        'crear reporte', 'crea reporte', 'reporte en', 'reporte pdf',
        'reporte excel', 'reporte csv',
    ))
    formato = ''
    if 'pdf' in q:
        formato = 'PDF'
    elif 'excel' in q or 'xlsx' in q:
        formato = 'EXCEL'
    elif 'csv' in q:
        formato = 'CSV'
    if exportar:
        return 'exportar', formato or 'PDF'
    return 'filtrar', ''


def interpretar_local(consulta: str, catalogo: dict) -> dict:
    """Parser deterministico para reconocer pedidos comunes aunque la IA falle."""
    inferidos = _inferir(consulta)
    accion, formato = _inferir_accion_formato(consulta)
    empresa = _buscar_id_catalogo(catalogo.get('empresas', []), consulta)
    tenant = _buscar_id_catalogo(catalogo.get('tenants', []), consulta)
    if empresa and not tenant:
        for item in catalogo.get('empresas', []):
            if item.get('id') == empresa:
                tenant = int(item.get('tenant') or 0)
                break
    tiene_filtros = bool(empresa or tenant or inferidos['estado'] or inferidos['origen'])
    return {
        'vista': _inferir_vista(consulta, tiene_filtros),
        'tenant': tenant,
        'empresa': empresa,
        'tipo': _buscar_id_catalogo(catalogo.get('tipos', []), consulta),
        'proveedor': _buscar_id_catalogo(catalogo.get('proveedores', []), consulta),
        'estado': inferidos['estado'],
        'origen': inferidos['origen'],
        'texto': '',
        'accion': accion,
        'formato': formato,
        'respuesta': '',
    }


def _inferir(consulta: str) -> dict:
    """Fallback por palabras clave para estado y origen."""
    q = _normalizar_texto(consulta)

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
    q = _normalizar_texto(consulta)
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
    accion = str(parsed.get('accion') or 'filtrar')
    formato = str(parsed.get('formato') or '').upper()

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
    accion = accion if accion in ACCIONES else 'filtrar'
    formato = formato if formato in FORMATOS else ''

    if empresa and not tenant:
        for item in catalogo['empresas']:
            if item['id'] == empresa:
                tenant = int(item.get('tenant') or 0)
                break

    tiene_filtros_basicos = bool(tenant or empresa or tipo or proveedor or estado or origen or texto)
    if vista == 'ninguna':
        vista = _inferir_vista(consulta, tiene_filtros_basicos)
    if accion == 'exportar':
        vista = 'reportes'
        formato = formato or 'PDF'

    # "Quitar / limpiar filtros / ver todo": solo si NO se pidio un filtro concreto.
    if accion == 'filtrar' and not tiene_filtros_basicos:
        _q = _normalizar_texto(consulta)
        if any(k in _q for k in (
            'limpiar filtro', 'limpia filtro', 'limpiar los filtro', 'quitar filtro', 'quita filtro',
            'quita los filtro', 'quitale los filtro', 'sacar filtro', 'saca filtro', 'saca los filtro',
            'borrar filtro', 'borra los filtro', 'sin filtro', 'reiniciar filtro', 'resetear filtro',
            'restablecer filtro', 'reiniciar el tablero', 'ver todo', 'ver todas las licencia',
            'mostrar todo', 'mostrame todo', 'mostrar todas las licencia', 'todo el inventario',
            'todas las licencia', 'sin ningun filtro', 'quitar todos', 'limpiar todo',
        )):
            accion = 'limpiar'
            vista = 'reportes'

    # Confirmacion AUTORITATIVA: se arma desde los ids YA validados contra el
    # catalogo (nombres reales), no desde la frase libre del modelo. Asi el texto
    # nunca afirma un filtro que no se va a aplicar.
    def _nombre(lista, _id):
        for x in lista:
            if x['id'] == _id:
                return x['nombre']
        return None

    filtros_aplicados = []
    if tenant:
        n = _nombre(catalogo['tenants'], tenant)
        if n:
            filtros_aplicados.append('Tenant: ' + n)
    if empresa:
        n = _nombre(catalogo['empresas'], empresa)
        if n:
            filtros_aplicados.append('Empresa: ' + n)
    if tipo:
        n = _nombre(catalogo['tipos'], tipo)
        if n:
            filtros_aplicados.append('Tipo: ' + n)
    if proveedor:
        n = _nombre(catalogo['proveedores'], proveedor)
        if n:
            filtros_aplicados.append('Proveedor: ' + n)
    if estado:
        filtros_aplicados.append('Estado: ' + ESTADO_LABELS.get(estado, estado))
    if origen:
        filtros_aplicados.append('Origen: ' + ORIGEN_LABELS.get(origen, origen))

    aplicar = bool(filtros_aplicados) or accion in ('exportar', 'limpiar')
    if accion == 'limpiar':
        respuesta = 'Listo, quité los filtros: te muestro todo el inventario en el dashboard.'
    elif accion == 'exportar':
        detalle = ', '.join(filtros_aplicados) if filtros_aplicados else 'el inventario general'
        respuesta = f'Genero el reporte {formato or "PDF"} para {detalle}.'
    elif filtros_aplicados:
        destino = 'la lista' if vista == 'lista' else 'el dashboard'
        adjetivo = 'filtrada' if vista == 'lista' else 'filtrado'
        respuesta = 'Te muestro ' + destino + ' ' + adjetivo + ' por ' + ', '.join(filtros_aplicados) + '.'
    else:
        # No se resolvio ningun filtro: usamos la ACLARACION contextual que escribio el
        # modelo (reconoce lo pedido y aclara que SI puede filtrar), salvo que afirme
        # falsamente un exito; en ese caso, aclaracion generica.
        modelo_resp = str(parsed.get('respuesta') or '').strip()
        _falso_exito = any(
            s in modelo_resp.lower()
            for s in ('te muestro el dashboard', 'filtrado por', 'abri el dashboard', 'abrí el dashboard',
                      'aplique el filtro', 'apliqué el filtro', 'abierto el dashboard',
                      'he filtrado', 'filtrado las', 'ya filtre', 'ya filtré')
        )
        if modelo_resp and not _falso_exito:
            respuesta = modelo_resp
        else:
            respuesta = (
                '¿Sobre qué querés el reporte? El dashboard se filtra por empresa, estado '
                '(disponible, asignada, vencida, por vencer, suspendida, pendiente o revocada), '
                'tipo de licencia, origen (manual, factura o sincronización), proveedor o tenant. '
                'Por ejemplo: "licencias vencidas" o "disponibles de Microsoft".'
            )

    return {
        'vista': vista,
        'tenant': tenant,
        'empresa': empresa,
        'tipo': tipo,
        'proveedor': proveedor,
        'estado': estado,
        'origen': origen,
        'texto': texto,
        'accion': accion,
        'formato': formato,
        'aplicar': aplicar,
        'filtros_aplicados': filtros_aplicados,
        'respuesta': respuesta,
    }


def filtros_vacios() -> dict:
    """Conjunto de filtros neutro (sin nada aplicado)."""
    return {
        'vista': 'ninguna', 'tenant': 0, 'empresa': 0, 'tipo': 0,
        'proveedor': 0, 'estado': '', 'origen': '', 'texto': '',
        'accion': 'filtrar', 'formato': '',
        'aplicar': False, 'filtros_aplicados': [],
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
            return {'ok': True, **normalizar_filtros(interpretar_local(consulta, catalogo), catalogo, consulta)}
        except ai.AsistenteError:
            return {'ok': True, **normalizar_filtros(interpretar_local(consulta, catalogo), catalogo, consulta)}

        try:
            parsed = json.loads(texto_modelo)
        except (json.JSONDecodeError, TypeError):
            parsed = None
        if not isinstance(parsed, dict):
            return {'ok': True, **normalizar_filtros(interpretar_local(consulta, catalogo), catalogo, consulta)}

        return {'ok': True, **normalizar_filtros(parsed, catalogo, consulta)}

    @staticmethod
    def _fallback(mensaje: str) -> dict:
        return {'ok': False, 'respuesta': mensaje, **filtros_vacios()}
