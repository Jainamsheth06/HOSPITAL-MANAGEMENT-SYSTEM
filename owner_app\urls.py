from django.urls import path
from . import views

urlpatterns = [
    path('', views.owner_dashboard, name='owner_root'),
    path('login/', views.owner_login, name='owner_login'),
    path('logout/', views.owner_logout, name='owner_logout'),
    path('dashboard/', views.owner_dashboard, name='owner_dashboard'),
    path('receptionist/<int:user_id>/delete/', views.delete_receptionist, name='delete_receptionist'),
]

