"""
Teacher Attendance URL Configuration
"""
from django.urls import path
from . import views

app_name = 'teacher_attendance'

urlpatterns = [
    path('mark/', views.mark_attendance, name='mark_attendance'),
    path('history/', views.attendance_history, name='attendance_history'),
    path('edit/<int:pk>/', views.edit_attendance, name='edit_attendance'),
    path('delete/<int:pk>/', views.delete_attendance, name='delete_attendance'),
]
