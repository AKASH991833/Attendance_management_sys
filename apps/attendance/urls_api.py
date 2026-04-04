"""
Attendance App API URL Configuration
"""
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('save/', views.save_attendance_api, name='save'),
    path('check/', views.check_attendance_api, name='check'),
    
    # Monthly Attendance APIs
    path('monthly/', views.monthly_attendance_fetch_api, name='monthly-fetch'),
    path('monthly/save/', views.monthly_attendance_save_api, name='monthly-save'),
    path('mark-day/', views.mark_day_attendance_api, name='mark-day'),
]
