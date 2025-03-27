from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('standards/', views.standards, name='standards'),
    path('customers/', views.customers, name='customers'),
    path('reports/', views.reports, name='reports'),
    path('create_report/<str:session_id>/', views.create_report, name='create_report'),
    path('view_report/<str:session_id>/', views.view_report, name='view_report'),
]
