from django.urls import path, re_path
from . import views
from app_learning.services.odoo_conection import fetch_departametos_from_odoo

urlpatterns = [
    path('home/', views.home, name='home'),
    path('create/', views.create_capacitacion, name='create_capacitacion'),
    #path('list/', views.list_capacitaciones, name='capacitaciones_list'),
    path('register/', views.registration_view, name='registration_form'),
    # path('success/<str:employee_name>/', views.success_view, name='success_without_url'),
    re_path(r'^success/(?P<employee_name>[^/]+)/(?P<url_reunion>.*)?/$', views.success_view, name='success'),
    path('fetch_departametos_from_odoo/', fetch_departametos_from_odoo, name='fetch_departametos_from_odoo'),
    path('details/<int:id>/', views.details_view, name='details_view'),
    path('capacitaciones/', views.list_capacitaciones, name='list_capacitaciones'),
    path('edit/<int:id>/', views.edit_capacitacion, name='edit_capacitacion'),
    path('view_assistants/<int:id>/', views.view_assistants, name='view_assistants'),
]