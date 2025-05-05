from django.urls import path, include
from .views import odoo_data_endpoint

urlpatterns = [
    path('odoo-data/', odoo_data_endpoint, name='odoo_data'),
]
