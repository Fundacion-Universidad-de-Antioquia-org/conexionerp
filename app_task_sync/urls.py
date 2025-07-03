from django.urls import path,re_path
from . import views
from drf_yasg import openapi


urlpatterns = [
    path('empleados/', views.empleados_list, name='empleados_list'),
    path('prestadores/', views.prestadores_list, name='prestadores_list'),
    path("empleados/conduccion/",views.empleados_conduccion_list,name="empleados_conduccion_list"),
    path("empleados/conduccion_codigo/",views.empleado_conduccion_por_codigo,name="empleado_conduccion_por_codigo"),

    path('contratos_list/', views.contratos_list, name='contratos_list'),
    path('hijos_employee/', views.empleados_y_sus_hijos_activos, name='empleados_y_sus_hijos_activos'),
    
    path('estados/', views.estados_basicos_list, name='estados_basicos_list'),
    path('salarios/', views.salarios_list, name='salarios_list'),
    path('estudios/', views.estudios_list, name='estudios_list'),
    path('actualizar_empleado/', views.actualizar_empleado, name='actualizar_empleado'),
]
