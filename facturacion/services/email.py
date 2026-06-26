"""Envio de documentos comerciales por correo."""

from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.urls import reverse

from ..infrastructure.models import Factura
from .pdf import render_to_pdf

logger = logging.getLogger(__name__)


def _correo_empresa(factura: Factura) -> str:
    empresa = getattr(factura, 'empresa', None)
    return (getattr(empresa, 'email_facturacion', '') or '').strip()


def enviar_factura_pagada_por_email(factura: Factura, *, request=None) -> tuple[bool, str]:
    """Envia la factura PDF al correo de facturacion de la empresa."""
    factura = (
        Factura.objects
        .select_related('empresa', 'tenant', 'proveedor', 'propuesta')
        .prefetch_related('detalles__tipo_licencia')
        .get(pk=factura.pk)
    )
    destinatario = _correo_empresa(factura)
    if not destinatario:
        return False, "No se envio correo: la empresa no tiene correo de facturacion configurado."

    detalle_url = ""
    if request is not None:
        try:
            detalle_url = request.build_absolute_uri(reverse('detalle_factura', args=[factura.pk]))
        except Exception:
            detalle_url = ""

    subject = f"Factura {factura.numero} pagada"
    body = (
        f"Estimados,\n\n"
        f"Adjuntamos la factura {factura.numero} correspondiente a {factura.razon_social or factura.empresa.nombre}.\n"
        f"Total: Bs. {factura.total:.2f}\n"
        f"Estado: {factura.estado_pago_label}\n"
    )
    if detalle_url:
        body += f"\nPuede revisar el detalle en: {detalle_url}\n"
    body += "\nSaludos."

    pdf_bytes = render_to_pdf(
        'facturacion/pdf/factura.html',
        {
            'factura': factura,
            'doc_titulo': 'FACTURA',
            'numero': factura.numero,
            'fecha': factura.fecha,
        },
        paper_size='letter',
    )

    email = EmailMessage(subject, body, settings.DEFAULT_FROM_EMAIL, [destinatario])
    filename = f"factura_{factura.numero or factura.pk}.pdf"
    if pdf_bytes:
        email.attach(filename, pdf_bytes, 'application/pdf')
    else:
        html = render_to_string('facturacion/pdf/factura.html', {
            'factura': factura,
            'doc_titulo': 'FACTURA',
            'numero': factura.numero,
            'fecha': factura.fecha,
        })
        email.attach(filename.replace('.pdf', '.html'), html, 'text/html')

    try:
        email.send(fail_silently=False)
    except Exception as exc:
        logger.exception("No se pudo enviar factura %s por email: %s", factura.numero, exc)
        return False, "El pago se registro, pero no se pudo enviar la factura por correo. Revisa la configuracion SMTP."

    return True, f"Factura enviada al correo {destinatario}."
