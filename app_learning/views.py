from django.shortcuts import render, redirect
from .forms import CtrlCapacitacionesForm
from .models import CtrlCapacitaciones

def create_capacitacion(request):
    if request.method == 'POST':
        form = CtrlCapacitacionesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('capacitaciones_list')
    else:
        form = CtrlCapacitacionesForm()
    return render(request, 'crear_capacitacion.html', {'form': form})

def list_capacitaciones(request):
    capacitaciones = CtrlCapacitaciones.objects.all()
    return render(request, 'list_capacitaciones.html', {'capacitaciones': capacitaciones})