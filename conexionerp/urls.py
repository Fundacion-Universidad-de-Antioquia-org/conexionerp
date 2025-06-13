
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    settings.AUTH.urlpattern,
    path('', TemplateView.as_view(template_name="vista.html"), name='home'),
    #migracion
    path('admin/', admin.site.urls),
    path('sync/', include('app_sync.urls')),
    path('files/', include('app_file_management.urls')),
    path('tasks/', include('app_task_sync.urls')),
    path('pdf/', include('app_pdf_management.urls')),
    path('logs/', include('app_logging.urls')),
    path('learn/', include('app_learning.urls')),
    path('employee/', include('app_comprobantes.urls')),
    
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
