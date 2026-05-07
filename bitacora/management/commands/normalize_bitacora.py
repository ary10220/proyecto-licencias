from __future__ import annotations

from django.core.management.base import BaseCommand

from bitacora.domain.services import limpiar_descripcion, resolver_modulo
from bitacora.models import Bitacora


class Command(BaseCommand):
    help = "Normaliza modulos y descripciones historicas de la bitacora."

    def handle(self, *args, **options):
        actualizados = 0

        for evento in Bitacora.objects.only("id", "accion", "modulo", "descripcion").iterator(chunk_size=200):
            modulo_resuelto = resolver_modulo(evento.modulo, evento.descripcion, evento.accion)
            descripcion_limpia = limpiar_descripcion(evento.descripcion)

            cambios = []
            if modulo_resuelto and evento.modulo != modulo_resuelto:
                evento.modulo = modulo_resuelto
                cambios.append("modulo")
            if descripcion_limpia != (evento.descripcion or ""):
                evento.descripcion = descripcion_limpia
                cambios.append("descripcion")

            if cambios:
                evento.save(update_fields=cambios)
                actualizados += 1

        self.stdout.write(self.style.SUCCESS(f"Registros normalizados: {actualizados}"))
