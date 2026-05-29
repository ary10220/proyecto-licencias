"""
Servicio de generacion de PDFs.

Usa xhtml2pdf. Si no esta instalado, devuelve HTML del template
para que el browser lo renderice/imprima con Ctrl+P.

Detecta automaticamente si existe el logo en facturacion/static/facturacion/img/logo.png
y lo pasa al template via context.
"""

from __future__ import annotations

import logging
import os
from io import BytesIO

from django.conf import settings
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


def _pisa_disponible():
    try:
        from xhtml2pdf import pisa  # noqa: F401
        return True
    except ImportError:
        return False


def _logo_url():
    """
    Busca el logo en este orden:
      1. facturacion/static/facturacion/img/logo.png
      2. facturacion/static/facturacion/img/logo.jpg
      3. facturacion/static/facturacion/img/logo.svg
    Retorna ruta absoluta (file://) para que xhtml2pdf lo encuentre,
    o None si no existe.
    """
    for ext in ('png', 'jpg', 'jpeg', 'svg'):
        candidate = finders.find(f'facturacion/img/logo.{ext}')
        if candidate and os.path.exists(candidate):
            return 'file://' + os.path.abspath(candidate).replace('\\', '/')
    return None


def _context_with_logo(context: dict) -> dict:
    """Agrega `logo_url` al context si existe el archivo."""
    logo = _logo_url()
    if logo:
        context = {**context, 'logo_url': logo}
    return context


def _normalize_paper_size(paper_size: str | None) -> tuple[str, str]:
    value = (paper_size or 'letter').strip().lower()
    if value == 'a4':
        return 'A4', 'a4'
    return 'letter', 'letter'


def _context_for_render(context: dict, *, paper_size: str | None = None, preview_mode: bool = False) -> dict:
    css_paper_size, paper_class = _normalize_paper_size(paper_size)
    enriched = {
        **context,
        'paper_size': css_paper_size,
        'paper_class': paper_class,
        'preview_mode': preview_mode,
    }
    return _context_with_logo(enriched)


def render_to_pdf(template_name: str, context: dict, *, paper_size: str | None = None) -> bytes | None:
    if not _pisa_disponible():
        logger.warning("xhtml2pdf no esta instalado")
        return None
    try:
        from xhtml2pdf import pisa
        html = render_to_string(template_name, _context_for_render(context, paper_size=paper_size))
        result = BytesIO()
        # link_callback para que xhtml2pdf resuelva file:// e imagenes
        def link_callback(uri, rel):
            if uri.startswith('file://'):
                return uri[len('file://'):]
            return uri
        pdf_status = pisa.CreatePDF(html, dest=result, encoding='utf-8', link_callback=link_callback)
        if pdf_status.err:
            logger.error("xhtml2pdf error: %s", pdf_status.err)
            return None
        return result.getvalue()
    except Exception as exc:
        logger.exception("Error generando PDF: %s", exc)
        return None


def _html_preview_response(template_name: str, context: dict, *, paper_size: str | None = None) -> HttpResponse:
    html = render_to_string(template_name, _context_for_render(
        context,
        paper_size=paper_size,
        preview_mode=True,
    ))
    response = HttpResponse(html, content_type='text/html; charset=utf-8')
    response['X-Frame-Options'] = 'SAMEORIGIN'
    response['Cache-Control'] = 'no-store'
    return response


def _pdf_response(
    template_name: str,
    context: dict,
    filename: str,
    download: bool = False,
    preview: bool = False,
    paper_size: str | None = None,
) -> HttpResponse:
    if preview:
        return _html_preview_response(template_name, context, paper_size=paper_size)

    pdf_bytes = render_to_pdf(template_name, context, paper_size=paper_size)

    if pdf_bytes is None:
        # Fallback HTML (cuando xhtml2pdf no esta instalado)
        html = render_to_string(template_name, _context_for_render(context, paper_size=paper_size))
        response = HttpResponse(html, content_type='text/html; charset=utf-8')
        if download:
            response['Content-Disposition'] = f'attachment; filename="{filename.rsplit(".", 1)[0]}.html"'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        return response

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    disposition = 'attachment' if download else 'inline'
    response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    return response


def cotizacion_pdf_response(propuesta, download: bool = False, preview: bool = False, paper_size: str | None = None) -> HttpResponse:
    filename = f"cotizacion_{propuesta.numero or propuesta.pk}.pdf"
    return _pdf_response(
        'facturacion/pdf/cotizacion.html',
        {
            'propuesta': propuesta,
            'doc_titulo': 'COTIZACION',
            'numero': propuesta.numero,
            'fecha': propuesta.fecha,
        },
        filename, download, preview, paper_size,
    )


def factura_pdf_response(factura, download: bool = False, preview: bool = False, paper_size: str | None = None) -> HttpResponse:
    filename = f"factura_{factura.numero or factura.pk}.pdf"
    return _pdf_response(
        'facturacion/pdf/factura.html',
        {
            'factura': factura,
            'doc_titulo': 'FACTURA',
            'numero': factura.numero,
            'fecha': factura.fecha,
        },
        filename, download, preview, paper_size,
    )


def contrato_pdf_response(propuesta, download: bool = False, preview: bool = False, paper_size: str | None = None) -> HttpResponse:
    filename = f"contrato_{propuesta.numero or propuesta.pk}.pdf"
    return _pdf_response(
        'facturacion/pdf/contrato.html',
        {
            'propuesta': propuesta,
            'doc_titulo': 'CONTRATO',
            'numero': propuesta.numero,
            'fecha': propuesta.fecha,
        },
        filename, download, preview, paper_size,
    )
