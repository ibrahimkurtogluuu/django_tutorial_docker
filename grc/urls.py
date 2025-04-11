from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='grc/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='grc/logout.html'), name='logout'),
    path('standards/', views.standards, name='standards'),
    path('form/standards/', views.form_standards, name='form_standards'),
    path('customers/', views.customers, name='customers'),
    path('form/', views.form_submission, name='form_submission'),
    path('form/', views.form_submission, name='form_submission'),
    path('reports/', views.reports, name='reports'),
    path('reports/create/', views.create_report, name='create_report'),
    path('reports/view/', views.view_report, name='view_report'),
]

    # path('reports/', views.reports, name='reports'),
    # path('create_report/<str:session_id>/', views.create_report, name='create_report'),
    # path('view_report/<str:session_id>/', views.view_report, name='view_report'),
    # path('form_submission/', views.form_submission, name='form_submission'),