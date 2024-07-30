from django import forms
from .models import CtrlCapacitaciones
from app_learning.services.odoo_conection import fetch_departametos_from_odoo

class CtrlCapacitacionesForm(forms.ModelForm):
  area_encargada =forms.ChoiceField(choices=[], label=('Departamentos'))
  class Meta:
    model = CtrlCapacitaciones
    fields = '__all__'
    widgets = {
      'fecha': forms.DateInput(attrs={'type': 'date'}),
      'hora_inicial': forms.TimeInput(attrs={'type': 'time'}),
      'hora_final': forms.TimeInput(attrs={'type': 'time'}),
    }
    
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    areas = fetch_departametos_from_odoo()
    # print('departamentos',areas)
    areas_choices = [(area_encargada, area_encargada)for area_encargada in areas]
    self .fields['area_encargada'].choices = areas_choices  
        
class RegistrationForm(forms.Form):
  topic = forms.CharField(max_length= 250, label = 'Tema', widget=forms.TextInput(attrs={'readonly':'readonly'}))
  department = forms.CharField(max_length=250, label= 'Departamento', widget= forms.TextInput(attrs={'readonly':'readonly'}))
  moderator = forms.CharField(max_length=100,label='Moderador(a)', widget = forms.TextInput(attrs={'readonly':'readonly'}))
  date = forms.DateField(widget=forms.DateInput(attrs={'type':'date', 'readonly': 'readonly'}), label='fecha')
  start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'readonly': 'readonly'}), label='Hora inicial')
  end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'readonly': 'readonly'}), label='Hora final')
  document_id = forms.CharField(max_length=20, label='Documento de Identidad', required=True)