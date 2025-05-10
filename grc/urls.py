from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.CustomLoginView.as_view(template_name='grc/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='grc/logout.html'), name='logout'),
    path('standards/', views.standards, name='standards'),
    path('form/standards/', views.form_standards, name='form_standards'),
    path('customers/', views.customers, name='customers'),
    path('form/', views.form_submission, name='form_submission'),
    path('form/update/<int:user_id>/', views.update_user_form, name='update_user_form'),
    path('reports/', views.reports, name='reports'),
    path('reports/create/', views.create_report, name='create_report'),
    path('reports/create/<int:user_id>', views.user_create_report, name='user_create_report'),
    path('reports/view/', views.view_report, name='view_report'),
    path('reports/view/<int:user_id>', views.user_view_report, name='user_view_report'),
    path('users/', views.users, name='users'),
    path('form/update_test/<int:user_id>/', views.update_user_form_test, name='update_user_form_test'),
    path('chatbot/', views.chatbot, name='chatbot'),
    path('trigger_spider/<int:user_id>/', views.trigger_spider, name='trigger_spider'),
    path('analyze_web_content/<int:user_id>/', views.analyze_web_content, name='analyze_web_content'),
]
