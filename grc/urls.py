from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('standards/', views.standards, name='standards'),
    path('customers/', views.customers, name='customers'),
    path('reports/', views.reports, name='reports'),
]
