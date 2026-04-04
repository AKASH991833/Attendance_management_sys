"""
Super Admin URL Configuration
"""
from django.urls import path
from . import views

app_name = 'super_admin'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.admin_profile, name='admin_profile'),

    # Teacher Management
    path('teachers/', views.teacher_list, name='teacher_list'),
    path('teachers/create/', views.teacher_create, name='teacher_create'),
    path('teachers/<int:pk>/', views.teacher_detail, name='teacher_detail'),
    path('teachers/<int:pk>/edit/', views.teacher_edit, name='teacher_edit'),
    path('teachers/<int:pk>/toggle-active/', views.teacher_toggle_active, name='teacher_toggle_active'),
    path('teachers/<int:pk>/delete/', views.teacher_delete, name='teacher_delete'),
    path('teachers/<int:pk>/students/', views.teacher_students, name='teacher_students'),
    path('teachers/<int:pk>/timetable/', views.teacher_timetable, name='teacher_timetable'),
    
    # Teacher Attendance (Admin marks)
    path('teacher-attendance/', views.mark_teacher_attendance, name='mark_teacher_attendance'),
    
    # System-wide views
    path('students/', views.all_students, name='all_students'),
    path('batches/', views.all_batches, name='all_batches'),
    path('batches/<int:pk>/', views.batch_detail, name='batch_detail'),
    path('export-excel/', views.export_all_data_excel, name='export_excel'),

    # System Logs
    path('logs/', views.system_logs, name='system_logs'),
]
