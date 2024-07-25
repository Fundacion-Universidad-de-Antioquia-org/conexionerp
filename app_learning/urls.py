from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_capacitacion, name='create_capacitacion'),
    path('list/', views.list_capacitaciones, name='capacitaciones_list'),
]