"""URLs del modulo facturacion. Sin namespace."""

from django.urls import path

from . import views


urlpatterns = [
    # === COTIZACIONES (antes Propuestas) ===
    path('cotizaciones/',                            views.lista_propuestas,    name='lista_cotizaciones'),
    path('cotizaciones/crear/',                      views.crear_propuesta,     name='crear_cotizacion'),
    path('cotizaciones/<int:pk>/editar/',            views.editar_propuesta,    name='editar_cotizacion'),
    path('cotizaciones/<int:pk>/aprobar/',           views.aprobar_propuesta,   name='aprobar_cotizacion'),
    path('cotizaciones/<int:pk>/rechazar/',          views.rechazar_propuesta,  name='rechazar_cotizacion'),
    path('cotizaciones/<int:pk>/eliminar/',          views.eliminar_propuesta,  name='eliminar_cotizacion'),

    # === FACTURAS ===
    path('facturas/',                                views.lista_facturas,      name='lista_facturas'),
    path('facturas/seleccionar-cotizacion/',         views.seleccionar_cotizacion, name='seleccionar_cotizacion'),
    path('facturas/emitir/<int:propuesta_id>/',      views.emitir_factura_desde_propuesta, name='emitir_factura_desde_cotizacion'),
    path('facturas/<int:pk>/editar/',                views.editar_factura,      name='editar_factura'),
    path('facturas/<int:pk>/anular/',                views.anular_factura,      name='anular_factura'),
    path('facturas/<int:pk>/eliminar/',              views.eliminar_factura,    name='eliminar_factura'),


    # === Detalle (solo lectura) ===
    path('cotizaciones/<int:pk>/detalle/',           views.detalle_cotizacion,  name='detalle_cotizacion'),
    path('facturas/<int:pk>/detalle/',               views.detalle_factura,     name='detalle_factura'),

    # === PDF ===
    path('cotizaciones/<int:pk>/pdf/',               views.pdf_cotizacion,      name='pdf_cotizacion'),
    path('facturas/<int:pk>/pdf/',                   views.pdf_factura,         name='pdf_factura'),
    path('cotizaciones/<int:pk>/contrato-pdf/',      views.pdf_contrato,        name='pdf_contrato'),
    # === AJAX ===
    path('ajax/precio-licencia/',                    views.precio_licencia,     name='precio_licencia'),

    # === ALIASES (back-compat con templates/links viejos) ===
    path('propuestas/',                              views.lista_propuestas,    name='lista_propuestas'),
    path('propuestas/crear/',                        views.crear_propuesta,     name='crear_propuesta'),
    path('propuestas/<int:pk>/editar/',              views.editar_propuesta,    name='editar_propuesta'),
    path('propuestas/<int:pk>/aprobar/',             views.aprobar_propuesta,   name='aprobar_propuesta'),
    path('propuestas/<int:pk>/rechazar/',            views.rechazar_propuesta,  name='rechazar_propuesta'),
    path('propuestas/<int:pk>/eliminar/',            views.eliminar_propuesta,  name='eliminar_propuesta'),
    path('facturas/crear/',                          views.seleccionar_cotizacion, name='crear_factura'),
]
