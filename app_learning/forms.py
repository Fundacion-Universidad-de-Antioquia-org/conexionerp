# from cProfile import label
# from tkinter import Widget
from django import forms
import hashlib # para el hash de la contraseña
from .models import CtrlCapacitaciones
from app_learning.services.odoo_conection import fetch_departametos_from_odoo

class CtrlCapacitacionesForm(forms.ModelForm):
    area_encargada = forms.ChoiceField(choices=[], label=('Proceso encargado'))
    modalidad = forms.ChoiceField(
        choices=[('', 'Elija una modalidad')] + CtrlCapacitaciones.MODALIDAD,
        required=True,
        label='Modalidad'
    )
    
    tipo = forms.ChoiceField(
        choices=[('', 'Elija el tipo de evento')] + CtrlCapacitaciones.TIPO,
        required= True,
        label='Tipo de evento'
    )
    
    privacidad = forms.ChoiceField(
        choices=[('', 'Nivel de privacidad')] + CtrlCapacitaciones.PRIVACIDAD,
        required=True,
        label= 'Privacidad'
    )

    verificacion_identidad = forms.ChoiceField(
        choices=CtrlCapacitaciones.VERIFICACION_IDENTIDAD,
        label='Verificacion de identidad (se pedira la contraseña de la intranet a todos los asistentes)',
        required = True,
    )
    

    class Meta:
        model = CtrlCapacitaciones
        fields = ['fecha', 
                  'responsable', 
                  'hora_inicial', 
                  'hora_final', 
                  'tema',
                  'moderador', 
                  'total_invitados',
                  'area_encargada', 
                  'modalidad', 
                  'url_reunion', 
                  'ubicacion',
                  'tipo',
                  'privacidad', 
                  'objetivo',
                  'temas', 
                  'estado']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicial': forms.TimeInput(attrs={'type': 'time'}),
            'hora_final': forms.TimeInput(attrs={'type': 'time'}),
            'tema': forms.TextInput(attrs={'placeholder': 'Nombre del evento'}),
            'moderador': forms.TextInput(attrs={'placeholder': 'Nombre del Moderador'}),
            'responsable': forms.TextInput(attrs={'placeholder': 'Nombre del Responsable'}),
            'objetivo': forms.Textarea(attrs={
                'rows': 4,
                'cols': 40,
                'placeholder': 'Escriba un objetivo de máximo 255 caracteres',
                'maxlength': 255
            }),
            'url_reunion': forms.TextInput(attrs={'placeholder': 'Ingrese la URL de la reunión'}),
            'ubicacion': forms.TextInput(attrs={'placeholder': 'Ingrese la ubicación'}),
            'total_invitados': forms.NumberInput(attrs={'min':1, 'placeholder': 'Cantidad de invitados'}),
            'temas': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Escriba los temas de la capacitación',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        areas = fetch_departametos_from_odoo()
        areas_choices = [(area_encargada, area_encargada) for area_encargada in areas]
        self.fields['area_encargada'].choices = areas_choices
        
        #Estado 'ACTIVA' al crear capacitación:
        if not self.instance.pk:
            self.fields['estado'].initial = 'ACTIVA'
            self.fields['estado'].widget.attrs['disabled'] = 'disabled'
        else: #si se está editando
            self.fields['estado'].widget.attrs.pop('disabled', None)

        # Obtener modalidad actual desde datos del formulario o instancia existente
        modalidad = self.data.get('modalidad') or (self.instance.modalidad if self.instance else '')

        # Cambiar el widget según la modalidad seleccionada
        if modalidad == 'VIRTUAL':
            self.fields['url_reunion'].widget = forms.TextInput(attrs={'placeholder': 'Ingrese la URL del evento'})
            self.fields['url_reunion'].required = True
        elif modalidad == 'PRESENCIAL':
            self.fields['ubicacion'].widget = forms.TextInput(attrs={'placeholder': 'Ingrese la ubicación'})
            self.fields['ubicacion'].required = True
        elif modalidad == 'MIXTA':
            self.fields['url_reunion'].widget = forms.TextInput(attrs={'placeholder': 'Ingrese la URL del evento'})
            self.fields['ubicacion'].widget = forms.TextInput(attrs={'placeholder': 'Ingrese la ubicación'})
            self.fields['url_reunion'].required = True
            self.fields['ubicacion'].required = True
        
class RegistrationForm(forms.Form):
  topic = forms.CharField(max_length= 250, label = 'Tema', widget=forms.TextInput(attrs={'readonly':'readonly'}))
  department = forms.CharField(max_length=250, label= 'Departamento', widget= forms.TextInput(attrs={'readonly':'readonly'}))
  moderator = forms.CharField(max_length=100,label='Moderador(a)', widget = forms.TextInput(attrs={'readonly':'readonly'}))
  date = forms.DateField(widget=forms.DateInput(attrs={'type':'date', 'readonly': 'readonly'}), label='fecha', input_formats=['%Y-%m-%d'])
  start_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'readonly': 'readonly'}), label='Hora inicial')
  end_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time', 'readonly': 'readonly'}), label='Hora final')
  mode = forms.CharField(max_length=10, label='Modalidad', required=True)
  tipo = forms.CharField(max_length=15, label='Tipo de evento', required=False)
  privacidad = forms.CharField(max_length=20, label= 'Privacidad', required=False)
  location = forms.CharField(max_length=255, label='Ubicación', required=False)  # Solo requerido para ciertas modalidades
  url_reunion = forms.CharField(max_length=255, label='URL del evento', required=False)  # Solo requerido para ciertas modalidades
  in_charge = forms.CharField(max_length=60, label='Responsable', widget=forms.TextInput(attrs={'readonly':'readonly'}))
  
  password_id = forms.CharField (
  max_length = 50,
  label="Contrase de Intranet",
  required=False, # Cambiamos a false para manejar el requerimiento con JavaScript
  widget=forms.PasswordInput(attrs={
            'placeholder': 'Ingrese su contraseña de intranet'
        }))

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
        cleaned_data[field] = cleaned_data[field]

    # cifrar la contraseña a MD5
    if 'password_id' in cleaned_data:
        password_original = cleaned_data['password_id']
        # Guardamos la contraseña cifrada en un nuevo campo
        cleaned_data['hashed_password'] = hashlib.md5(password_original.encode('utf-8')).hexdigest()
    return cleaned_data

""" lo que hace este fragmento de codigo es verificar si existe el campo password_id, si existe,
obtiene el valor del campo, lo cifra en MD5 y lo guarda en un nuevo campo llamado hashed_password"""
