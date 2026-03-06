from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('home/', views.home_view, name='home'),
    path('services/', views.services_view, name='services'),
    path('nearby_hosp/', views.nearby_hospitals_view, name='nearby_hospitals'),
    path('contact/', views.contact_view, name='contact'),
    path('chat/', views.chat_view, name='chat'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/nearby-hospitals/', views.nearby_hospitals_api, name='nearby_hospitals_api'),
]