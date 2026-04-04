"""
Reports App API URL Configuration
"""
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('data/', views.report_data_api, name='report-data'),
]
