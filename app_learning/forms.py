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