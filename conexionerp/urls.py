"""
URL configuration for conexionerp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', TemplateView.as_view(template_name="vista.html"), name='home'),
    #migracion
    path('admin/', admin.site.urls),
    path('sync/', include('app_sync.urls')),
    path('files/', include('app_file_management.urls')),
    path('tasks/', include('app_task_sync.urls')),
    path('pdf/', include('app_pdf_management.urls')),
    path('logs/', include('app_logging.urls')),
    path('learn/', include('app_learning.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
