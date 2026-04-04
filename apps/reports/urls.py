"""
Reports App URL Configuration
"""
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_view, name='reports'),
    path('export/excel/', views.export_excel, name='export-excel'),
    path('export/pdf/', views.export_pdf, name='export-pdf'),
]
