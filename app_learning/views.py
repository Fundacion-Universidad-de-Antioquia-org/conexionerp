from django.shortcuts import render, redirect
from .forms import CtrlCapacitacionesForm
from .forms import RegistrationForm
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

def registration_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Procesa los datos en form.cleaned_data
            topic = form.cleaned_data['topic']
            department = form.cleaned_data['department']
            moderator =form.cleaned_data['moderator']
            date = form.cleaned_data ['date']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data ['end_time']
            # Puedes hacer algo con los datos aquí
            return redirect('success')
    else:
        form = RegistrationForm()

    return render(request, 'registration_form.html', {'form': form})

def success_view(request):
    return render(request, 'success.html')