"""
URL configuration for EduTrack Pro project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Main app URLs
    path('', include('apps.accounts.urls')),
    path('dashboard/', include('apps.accounts.urls_dashboard')),
    path('students/', include('apps.students.urls')),
    path('attendance/', include('apps.attendance.urls')),
    path('timetable/', include('apps.timetable.urls')),
    path('communications/', include('apps.communications.urls')),
    path('workspace/', include('apps.workspace.urls')),
    path('reports/', include('apps.reports.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('teacher-attendance/', include('apps.teacher_attendance.urls')),
    path('admin-panel/', include('apps.super_admin.urls')),
    
    # API endpoints
    path('api/attendance/', include('apps.attendance.urls_api')),
    path('api/dashboard/', include('apps.accounts.urls_api')),
    path('api/communications/', include('apps.communications.urls_api')),
    path('api/notifications/', include('apps.notifications.urls_api')),
    path('api/students/', include('apps.students.urls_api')),
    path('api/reports/', include('apps.reports.urls_api')),
    path('api/calendar/', include('apps.calendar_holidays.urls_api')),
    
    # PWA
    path('offline/', TemplateView.as_view(template_name='offline.html'), name='offline'),
    path('service-worker.js', TemplateView.as_view(template_name='service-worker.js', content_type='text/javascript'), name='service-worker'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error pages
handler404 = 'apps.accounts.views.custom_404'
handler500 = 'apps.accounts.views.custom_500'
