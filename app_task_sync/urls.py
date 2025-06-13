from django.urls import path
from . import views

urlpatterns = [
    path('empleados/', views.empleados_list, name='empleados_list'),
    path('prestadores/', views.prestadores_list, name='prestadores_list'),
    path("empleados/conduccion/",views.empleados_conduccion_list,name="empleados_conduccion_list"),
    path('contratos_list/', views.contratos_list, name='contratos_list'),
    path('estados/', views.estados_basicos_list, name='estados_basicos_list'),
    path('salarios/', views.salarios_list, name='salarios_list'),
    path('estudios/', views.estudios_list, name='estudios_list'),
    path('actualizar_empleado/', views.actualizar_empleado, name='actualizar_empleado'),
    
]
