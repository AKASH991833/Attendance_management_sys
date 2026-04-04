"""
Timetable App URL Configuration
"""
from django.urls import path
from . import views

app_name = 'timetable'

urlpatterns = [
    path('', views.timetable_list_view, name='timetable-list'),
    path('manage/', views.timetable_manage_view, name='timetable-manage'),
    path('slot/add/', views.slot_add_view, name='slot-add'),
    path('slot/<int:slot_id>/edit/', views.slot_edit_view, name='slot-edit'),
    path('slot/<int:slot_id>/delete/', views.slot_delete_view, name='slot-delete'),
]
