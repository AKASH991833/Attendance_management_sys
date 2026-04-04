"""
Notifications App API URL Configuration
"""
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('unread-count/', views.unread_count_api, name='unread-count'),
    path('<int:notification_id>/read/', views.mark_notification_read_api, name='mark-read'),
    path('mark-all-read/', views.mark_all_read_api, name='mark-all-read'),
    path('<int:notification_id>/delete/', views.delete_notification_api, name='delete'),
]
