from django import forms
from .models import CtrlCapacitaciones
from app_learning.services.odoo_conection import fetch_departametos_from_odoo

class CtrlCapacitacionesForm(forms.ModelForm):
  area_encargada =forms.ChoiceField(choices=[], label=('Programa - Área'))
  class Meta:
    model = CtrlCapacitaciones
    fields = ['fecha', 'moderador','hora_inicial', 'hora_final','tema','area_encargada','objetivo','estado']
    widgets = {
      'fecha': forms.DateInput(attrs={'type': 'date'}),
      'hora_inicial': forms.TimeInput(attrs={'type': 'time'}),
      'hora_final': forms.TimeInput(attrs={'type': 'time'}),
      'tema': forms.TextInput(attrs={'placeholder': 'Nombre de la capacitación'}),
      'moderador': forms.TextInput(attrs={'placeholder':'Nombre del Moderador'}),
      'objetivo': forms.Textarea(attrs={
                'rows': 4, 
                'cols': 40, 
                'placeholder': 'Escriba un objetivo de máximo 160 caracteres',
                'maxlength': 161
            }),
    }
    
  def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    areas = fetch_departametos_from_odoo()
    #print('departamentos',areas)
    areas_choices = [(area_encargada, area_encargada)for area_encargada in areas]
    self .fields['area_encargada'].choices = areas_choices
        
class RegistrationForm(forms.Form):
  topic = forms.CharField(max_length= 250, label = 'Tema', widget=forms.TextInput(attrs={'readonly':'readonly'}))
  department = forms.CharField(max_length=250, label= 'Departamento', widget= forms.TextInput(attrs={'readonly':'readonly'}))
  moderator = forms.CharField(max_length=100,label='Moderador(a)', widget = forms.TextInput(attrs={'readonly':'readonly'}))
  date = forms.DateField(widget=forms.DateInput(attrs={'type':'date', 'readonly': 'readonly'}), label='fecha', input_formats=['%Y-%m-%d'])
  start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'readonly': 'readonly'}), label='Hora inicial')
  end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'readonly': 'readonly'}), label='Hora final')
  document_id = forms.CharField(
    max_length=20, 
    label='Documento de Identidad', 
    required=True, 
    widget=forms.TextInput(attrs={
            'placeholder': 'Ingrese su número de documento'
        }))
  def clean(self):
    cleaned_data = super().clean()
    # Convertir todos los campos a mayúsculas
    for field in cleaned_data:
      if isinstance(cleaned_data[field], str):
        cleaned_data[field] = cleaned_data[field].upper()
    return cleaned_data