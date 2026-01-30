from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('streak/', views.streak, name='streak'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
]
