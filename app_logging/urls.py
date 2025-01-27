from django.urls import path
from app_logging.views import registrar_log,update_log_date

urlpatterns = [
    path('registrar/', registrar_log, name='registrar_log'),
    path('consultar/', update_log_date, name='update_log_date'),

    # Definir las rutas aquí, por ejemplo:
    # path('upload/', views.upload_file, name='upload_file'),
]
