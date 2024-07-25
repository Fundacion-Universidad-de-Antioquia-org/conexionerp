from django.urls import path, include
from django.contrib import admin
from . import views

admin.autodiscover()
# /api/employees


urlpatterns = [
    path(route='empleados/comunicaciones/', view= views.sync_empleados_comunicaciones, name='empleados_comunicaciones'),
    path(route='prestadores/comunicaciones/', view= views.sync_prestadores_comunicaciones, name='prestadores_comunicaciones'),
    path(route='documento', view= views.sync_view_doc, name='documento'), #prueba
]
