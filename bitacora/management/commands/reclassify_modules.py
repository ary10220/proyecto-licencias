from __future__ import annotations

from django.core.management.base import BaseCommand
from bitacora.domain.services import MODULOS
from bitacora.models import Bitacora


class Command(BaseCommand):
    help = (
        "Reclasifica módulos antiguos en Bitácora (por ejemplo, eventos de cargos/áreas "
        "que quedaron como 'Configuración') para mantener coherencia en reportes."
    )

    def handle(self, *args, **options):
        config_label = MODULOS.get("CONFIG", "Configuración")
        org_label = MODULOS.get("ORG", "Organización")

        # Heurística: antes guardábamos cargos/áreas bajo CONFIG. Lo movemos a ORG.
        patterns = [
            "cargo ",
            "cargo:",
            "cargos ",
            "área de usuario",
            "area de usuario",
            "área ",
            "area ",
        ]

        # Evitamos `update()` masivo/transactions grandes porque en Windows+OneDrive
        # SQLite puede dar "disk I/O error" por locks durante commits grandes.
        total_updated = 0
        seen_ids: set[int] = set()
        qs_base = Bitacora.objects.filter(modulo=config_label).only("id", "descripcion", "modulo")

        for pat in patterns:
            for b in qs_base.filter(descripcion__icontains=pat).iterator(chunk_size=200):
                if b.id in seen_ids:
                    continue
                seen_ids.add(b.id)
                b.modulo = org_label
                b.save(update_fields=["modulo"])
                total_updated += 1

        self.stdout.write(self.style.SUCCESS(f"Registros actualizados: {total_updated}"))
