"""
Communications App API URL Configuration
"""
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('send/', views.send_broadcast_api, name='send'),
    path('templates/', views.get_broadcast_templates_api, name='templates'),
]
