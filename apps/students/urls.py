"""
Students App URL Configuration
"""
from django.urls import path
from . import views

app_name = 'students'

urlpatterns = [
    # Batch URLs
    path('batches/', views.batch_list_view, name='batch-list'),
    path('batches/add/', views.batch_add_view, name='batch-add'),
    path('batches/<int:batch_id>/edit/', views.batch_edit_view, name='batch-edit'),
    path('batches/<int:batch_id>/delete/', views.batch_delete_view, name='batch-delete'),
    
    # Student URLs
    path('', views.student_list_view, name='student-list'),
    path('add/', views.student_add_view, name='student-add'),
    path('<int:student_id>/edit/', views.student_edit_view, name='student-edit'),
    path('<int:student_id>/delete/', views.student_delete_view, name='student-delete'),
    path('<int:student_id>/', views.student_detail_view, name='student-detail'),
]
