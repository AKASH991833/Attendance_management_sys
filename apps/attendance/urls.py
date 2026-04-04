"""
Attendance App URL Configuration
"""
from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'attendance'

urlpatterns = [
    # Default redirect to mark attendance
    path('', lambda request: redirect('attendance:mark')),
    
    # Monthly Attendance (DEFAULT)
    path('mark/', views.mark_attendance_view, name='mark'),

    # History and Student Detail
    path('history/', views.attendance_history_view, name='history'),
    path('student/<int:student_id>/', views.student_attendance_detail_view, name='student-detail'),
]
