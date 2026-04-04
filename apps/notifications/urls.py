"""
Notifications App URL Configuration
"""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notifications_view, name='notifications'),
    path('holiday-reminder/', views.create_holiday_reminder, name='holiday-reminder'),
]
