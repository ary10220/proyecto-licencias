"""
Bitacora del Asistente de IA: registra las interacciones del usuario con el chatbot.

Se guarda la consulta (recortada por privacidad/tamano), si fue ayuda o filtros,
y si se aplico un filtro al tablero. NO se guarda la respuesta completa del modelo
(solo su longitud), para no almacenar texto innecesario.
"""
from ..domain.services import ACCIONES, MODULOS
from ..application.use_cases.log_event import log_event

_MAX = 200


def _recortar(texto):
    texto = " ".join(str(texto or "").split())
    return (texto[:_MAX].rstrip() + "…") if len(texto) > _MAX else texto


def log_asistente_consulta(request, consulta, intencion=None, respuesta=None, aplico_filtro=False):
    consulta = _recortar(consulta)
    tipo = "filtros" if intencion == "filtros" else "ayuda"
    partes = [f"Consulta al asistente IA ({tipo})"]
    if consulta:
        partes.append(f'"{consulta}"')
    if intencion == "filtros":
        partes.append("aplicó filtro al tablero" if aplico_filtro else "sin filtro aplicado")
    log_event(
        request=request,
        accion=ACCIONES["CONSULTAR"],
        modulo=MODULOS["ASISTENTE_IA"],
        descripcion=". ".join(partes) + ".",
    )
