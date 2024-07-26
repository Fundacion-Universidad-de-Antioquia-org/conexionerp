from django import forms
from .models import CtrlCapacitaciones

class CtrlCapacitacionesForm(forms.ModelForm):
  class Meta:
    model = CtrlCapacitaciones
    fields = '__all__'
    widgets = {
      'fecha': forms.DateInput(attrs={'type': 'date'}),
      'hora_inicial': forms.TimeInput(attrs={'type': 'time'}),
      'hora_final': forms.TimeInput(attrs={'type': 'time'}),
    }
    
class RegistrationForm(forms.Form):
  topic = forms.CharField(max_length= 250, label = 'Tema')
  DEPARMENTS_OPTIONS = [
    ('area_1', 'Área 1'),
    ('area_2', 'Área 2'),
    ('area_3', 'Área 3')
  ]
  department = forms.ChoiceField(choices=DEPARMENTS_OPTIONS, label= 'Departamento')
  moderator = forms.CharField(max_length=100,label='Moderador(a)')
  date = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}), label='fecha')
  start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), label='Hora inicial')
  end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), label='Hora final')