"""
Asistente de AYUDA global: responde en lenguaje natural "como funciona / donde
esta X" sobre el sistema de gestion de licencias. Usa la MISMA API (OpenAI via
urllib) que el asistente de reportes, pero con un prompt de onboarding y un
catalogo de modulos embebido (grounding) para no inventar funciones.

Devuelve texto plano. Mismo patron que el `AsistenteAyuda` del sistema CUP.
"""
from __future__ import annotations

from ...infrastructure import openai_client as ai

# Catalogo de modulos del sistema. Se usa como grounding tanto en el asistente
# de ayuda como en el asistente unificado (AsistenteChat).
GUIA_MODULOS = """\
MODULOS (menu lateral):
- Inicio: pantalla de entrada con accesos rapidos.
- Dashboard: reporteria ejecutiva del inventario. KPIs (total, asignadas, disponibles, vencidas, por vencer),
  graficos por estado, por origen y por tipo, alertas de stock bajo y licencias proximas a vencer.
  Se puede filtrar por tenant, empresa, tipo de licencia y origen.
- Licencias: inventario de licencias. Permite crear licencias (de a una o en masa), editarlas, asignarlas a un
  empleado y liberarlas. Incluye: asignacion masiva, el catalogo de software (tipos de licencia) y proveedores,
  la sincronizacion con Microsoft 365 (subiendo un Excel) y la exportacion del inventario a Excel.
  Estados de una licencia: DISPONIBLE, ASIGNADA, VENCIDA, POR VENCER, SUSPENDIDA, PENDIENTE DE ACTIVACION, REVOCADA.
- Empleados: alta, edicion, baja y reactivacion de empleados. Al dar de baja a un empleado se liberan
  automaticamente sus licencias asignadas.
- Gestion Global: administra la estructura organizacional: tenants (grupo corporativo), empresas, divisiones,
  areas y unidades.
- Facturacion: modulo comercial. Se crea una cotizacion (propuesta), se aprueba y se emite la factura; al emitir,
  el sistema genera automaticamente el stock de licencias en el inventario. Se pueden descargar PDF de cotizacion,
  factura y contrato.
- Bitacora: auditoria de todas las acciones del sistema (quien hizo que y cuando). Se puede filtrar.
- Usuarios: cuentas de usuario, roles (grupos de permisos), areas de usuario, cargos y el perfil propio.

REGLAS CLAVE:
- Una licencia se asigna a UN empleado a la vez; al liberarla vuelve al pool de disponibles.
- No se puede eliminar/deshabilitar una licencia que tiene una asignacion activa: primero hay que liberarla.
- Una licencia esta "por vencer" si vence dentro de los proximos 30 dias.
- Cada usuario ve solo los modulos que su rol (grupo) le permite.
- Cuando se crea un usuario nuevo, su contrasena inicial debe cambiarse en el primer ingreso.
"""

SYSTEM_PROMPT = (
    'Sos el asistente de ayuda del sistema de Gestion de Licencias de software (control de TI corporativo, multiempresa).\n'
    'Tu UNICO trabajo es explicar, en espanol claro y breve, COMO USAR el sistema.\n'
    'Cuando expliques como hacer una tarea, respondé con PASOS NUMERADOS y accionables (1., 2., 3. ...): el primer '
    'paso indica el modulo del menu lateral y el boton/accion por donde empezar, y los siguientes describen en '
    'orden que cargar o tocar hasta terminar. Usá los pasos que la tarea necesite (normalmente 3 a 6). No te '
    'limites a decir donde esta la funcion.\n'
    'Basate UNICAMENTE en las funciones, modulos, botones y estados de este catalogo: NO inventes pantallas ni '
    'pasos; si un dato no esta en el catalogo, decilo en vez de inventarlo.\n'
    'Si te preguntan algo ajeno al sistema o que no sabes, decilo con amabilidad y sugeri consultar al administrador.\n'
    'Si preguntan "donde esta X", indicá el item del menu lateral y, si aplica, los pasos para llegar.\n\n'
    + GUIA_MODULOS
)


class AsistenteAyuda:
    """Chatbot de onboarding disponible en todas las paginas."""

    def execute(self, consulta: str, rol: str = '') -> dict:
        consulta = (consulta or '').strip()
        if not consulta:
            return {
                'ok': False,
                'respuesta': 'Escribí tu pregunta. Por ejemplo: "¿cómo asigno una licencia a un empleado?".',
            }

        user = (f'Rol del usuario que pregunta: {rol}.\n\n' if rol else '') + 'Pregunta:\n' + consulta

        try:
            texto = ai.chat(
                system=SYSTEM_PROMPT,
                user=user,
                temperature=0.2,
                max_tokens=500,
                timeout=25,
            )
        except ai.AsistenteNoConfigurado:
            return {
                'ok': False,
                'respuesta': 'El asistente de ayuda todavía no está configurado (falta la clave OPENAI_API_KEY).',
            }
        except ai.AsistenteError:
            return {'ok': False, 'respuesta': 'No pude responder en este momento. Probá de nuevo.'}

        texto = (texto or '').strip()
        if not texto:
            return {'ok': False, 'respuesta': 'No entendí bien la pregunta. ¿La podés reformular?'}

        return {'ok': True, 'respuesta': texto}
