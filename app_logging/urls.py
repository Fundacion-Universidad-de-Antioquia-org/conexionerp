from django.urls import path
from app_logging.views import registrar_log,consultar_logs

urlpatterns = [
    path('registrar/', registrar_log, name='registrar_log'),
    path('consultar/', consultar_logs, name='consultar_logs'),

    # Definir las rutas aquí, por ejemplo:
    # path('upload/', views.upload_file, name='upload_file'),
]
