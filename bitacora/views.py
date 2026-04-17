from django.shortcuts import render
from .models import Bitacora
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator

@login_required
def lista_bitacora(request):
    if not request.user.has_perm('bitacora.view_bitacora'):
        raise PermissionDenied

    registros = Bitacora.objects.all()

    if not request.user.is_superuser:
        registros = registros.filter(usuario=request.user)

    usuario = request.GET.get('usuario')
    accion = request.GET.get('accion')
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')

    if usuario:
        registros = registros.filter(usuario__username=usuario)

    if accion:
        registros = registros.filter(accion=accion)

    if fecha_inicio:
        registros = registros.filter(fecha__date__gte=fecha_inicio)

    if fecha_fin:
        registros = registros.filter(fecha__date__lte=fecha_fin)

    registros = registros.order_by('-fecha')

    paginator = Paginator(registros, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    usuarios = Bitacora.objects.values_list('usuario__username', flat=True).distinct()
    query_params = request.GET.copy()
    query_params.pop('page', None)

    context = {
        'registros': page_obj,
        'page_obj': page_obj,
        'usuarios': usuarios,
        'filtros': request.GET,
        'query_string': query_params.urlencode(),
    }

    return render(request, 'bitacora/lista_bitacora.html', context)
