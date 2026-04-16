from django.shortcuts import render
from .models import Bitacora
from django.contrib.auth.decorators import login_required

@login_required
def lista_bitacora(request):

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

    usuarios = Bitacora.objects.values_list('usuario__username', flat=True).distinct()

    context = {
        'registros': registros,
        'usuarios': usuarios,
        'filtros': request.GET
    }

    return render(request, 'bitacora/lista_bitacora.html', context)