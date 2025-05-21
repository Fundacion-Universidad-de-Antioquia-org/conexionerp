from django.urls import path, re_path
from . import views
from app_learning.services.odoo_conection import fetch_departametos_from_odoo

urlpatterns = [
    path('home/', views.home, name='home'),
    path('create/', views.create_capacitacion, name='create_capacitacion'),
    path('register/', views.registration_view, name='registration_view'),  # Sin ID en la URL
    path('register/<int:id>/', views.registration_view, name='registration_view'),  # Con ID en la URL
    re_path(r'^success/(?P<employee_name>[^/]+)/(?P<url_reunion>.*)?/$', views.success_view, name='success'),
    path('fetch_departametos_from_odoo/', fetch_departametos_from_odoo, name='fetch_departametos_from_odoo'),
    path('details/<int:id>/', views.details_view, name='details_view'),
    path('capacitaciones/', views.list_capacitaciones, name='list_capacitaciones'),
    path('edit/<int:id>/', views.edit_capacitacion, name='edit_capacitacion'),
    path('view_assistants/<int:id>/', views.view_assistants, name='view_assistants'),
    path('search_employees/', views.search_employees, name='search_employees'),
    path('capacitacion/imagen/eliminar/<int:image_id>/', views.delete_image, name='delete_image'),
    path('capacitacion/imagen/ver/<int:image_id>/', views.view_image, name='view_image'),
    path('get_employee_names/', views.get_employee_names, name='get_employee_names'),
    path('capacitacion/<int:id>/generar_pdf/', views.generar_pdf, name='generar_pdf'),
    path('verificacion-config/', views.verificacion_config, name='verificacion_config'),
]