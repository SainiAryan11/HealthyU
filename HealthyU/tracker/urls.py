from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('streak/', views.streak, name='streak'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup, name='signup'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('start-exercise/', views.start_exercise, name='start_exercise'),
    path('exercise-session/', views.exercise_session, name='exercise_session'),
    path('yoga-session/', views.yoga_session, name='yoga_session'),
    path('session-report/', views.session_report, name='session_report'),
    path('complete-session/', views.complete_session, name='complete_session'),

]
