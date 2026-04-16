from django.shortcuts import render
from .models import Bitacora
from django.contrib.auth.decorators import login_required

@login_required
def lista_bitacora(request):
    registros = Bitacora.objects.all().order_by('-fecha')

    context = {
        'registros': registros
    }

    return render(request, 'bitacora/lista_bitacora.html', context)