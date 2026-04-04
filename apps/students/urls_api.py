"""
Students App API URL Configuration
"""
from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    path('search/', views.student_search_api, name='student-search'),
]
