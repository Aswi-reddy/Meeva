from django.urls import path
from . import views
urlpatterns =[
    path('', views.landing_page, name='landing_page'),
    path('role-login/', views.role_login, name='role_login'),
]