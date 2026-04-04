"""
Calendar & Holidays App URL Configuration
"""
from django.urls import path
from . import views

app_name = 'calendar_holidays'

urlpatterns = [
    path('', views.calendar_view, name='calendar'),
]
