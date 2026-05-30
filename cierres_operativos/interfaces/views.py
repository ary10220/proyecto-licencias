from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib import messages

# Importaciones absolutas limpias:
from cierres_operativos.interfaces.forms.cierres_forms import GenerarNotaAlquilerForm
from cierres_operativos.application.use_cases.generar_nota_alquiler import GenerarNotaAlquilerCasoUso
from cierres_operativos.models import PropuestaComercial

class GenerarNotaAlquilerView(View):
    template_name = 'cierres_operativos/generar_nota.html'

    def get(self, request, propuesta_id):
        # Aseguramos que la propuesta exista y esté pendiente
        propuesta = get_object_or_404(PropuestaComercial, pk=propuesta_id, estado='PENDIENTE')
        form = GenerarNotaAlquilerForm()
        
        return render(request, self.template_name, {
            'form': form,
            'propuesta': propuesta
        })

    def post(self, request, propuesta_id):
        propuesta = get_object_or_404(PropuestaComercial, pk=propuesta_id, estado='PENDIENTE')
        form = GenerarNotaAlquilerForm(request.POST)

        # Validación única y limpia estándar de Django
        if form.is_valid():
            # Extraemos los datos limpios del formulario
            nro_nota = form.cleaned_data['nro_nota']
            fecha_vencimiento = form.cleaned_data['fecha_vencimiento_pago']
            empleados_ids = [emp.id for emp in form.cleaned_data['empleados_notificar']]

            # Instanciamos y ejecutamos nuestro Caso de Uso (Clean Architecture)
            caso_uso = GenerarNotaAlquilerCasoUso()
            try:
                caso_uso.ejecutar(
                    propuesta_id=propuesta.id,
                    nro_nota=nro_nota,
                    fecha_vencimiento_pago=fecha_vencimiento,
                    empleados_a_notificar_ids=empleados_ids
                )
                messages.success(request, f"¡Cierre Operativo Exitoso! Nota {nro_nota} generada y alertas registradas.")
                
                # RECOMENDACIÓN: Si aún no tienes la vista de destino, puedes redirigir 
                # temporalmente a una ruta existente o al admin para probar el flujo.
                return redirect('admin:index') 
                
            except Exception as e:
                messages.error(request, f"Error al ejecutar el cierre operativo: {str(e)}")
        
        return render(request, self.template_name, {
            'form': form,
            'propuesta': propuesta
        })