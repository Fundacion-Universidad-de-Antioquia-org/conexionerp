from django.urls import path
from app_logging.views import registrar_log

urlpatterns = [
    path('registrar/', registrar_log, name='registrar_log'),
    # Definir las rutas aquí, por ejemplo:
    # path('upload/', views.upload_file, name='upload_file'),
]
