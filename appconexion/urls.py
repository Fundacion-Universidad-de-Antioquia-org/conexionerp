from django.urls import path, include
from django.contrib import admin

from . import views

admin.autodiscover()



# /api/employees


urlpatterns = [
    path(route='sincronizar', view= views.sync_view, name='sincronizar'),
    path(route='prestadores', view= views.sync_view_presta, name='prestadores'),
    path(route='documento', view= views.sync_view_doc, name='documento'),
]
