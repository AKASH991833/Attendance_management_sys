"""
Accounts App API URL Configuration
"""
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('stats/', views.dashboard_stats_api, name='dashboard-stats'),
]
