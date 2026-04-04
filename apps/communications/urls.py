"""
Communications App URL Configuration
"""
from django.urls import path
from . import views

app_name = 'communications'

urlpatterns = [
    path('broadcast/', views.broadcast_view, name='broadcast'),
]
