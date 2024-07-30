from django.urls import path
from . import views
from app_learning.services.odoo_conection import fetch_departametos_from_odoo

urlpatterns = [
    path('create/', views.create_capacitacion, name='create_capacitacion'),
    path('list/', views.list_capacitaciones, name='capacitaciones_list'),
    path('register/', views.registration_view, name='registration_form'),
    path('success/', views.success_view, name='success'),
    path('fetch_departametos_from_odoo/', fetch_departametos_from_odoo, name='fetch_departametos_from_odoo'),
    path('details/', views.details_view, name='details_view'),
]