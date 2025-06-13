from django.urls import path,re_path
from . import views
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="API Task Sync",
      default_version='v1',
      description="Documentación Swagger de la API de integración Odoo para app_task_sync",
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('empleados/', views.empleados_list, name='empleados_list'),
    path('prestadores/', views.prestadores_list, name='prestadores_list'),
    path("empleados/conduccion/",views.empleados_conduccion_list,name="empleados_conduccion_list"),
    path('contratos_list/', views.contratos_list, name='contratos_list'),
    path('estados/', views.estados_basicos_list, name='estados_basicos_list'),
    path('salarios/', views.salarios_list, name='salarios_list'),
    path('estudios/', views.estudios_list, name='estudios_list'),
    path('actualizar_empleado/', views.actualizar_empleado, name='actualizar_empleado'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
