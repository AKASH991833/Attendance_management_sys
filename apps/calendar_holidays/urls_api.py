"""
Calendar & Holidays App API URL Configuration
"""
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('holidays/', views.holidays_list_api, name='holidays-list'),
    path('holiday/add/', views.holiday_add_api, name='holiday-add'),
    path('holiday/<int:holiday_id>/delete/', views.holiday_delete_api, name='holiday-delete'),
]
