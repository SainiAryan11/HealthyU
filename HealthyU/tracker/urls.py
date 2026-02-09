from django.urls import path
from . import views

urlpatterns = [
    # Home
    path("", views.home, name="home"),

    # Authentication
    path("signup/", views.signup, name="signup"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # Profile
    path("profile/", views.profile, name="profile"),

    # Streak / Leaderboard
    path("streak/", views.streak, name="streak"),

    # Exercise Plan
    path("create-plan/", views.create_plan, name="create_plan"),
    path("save-plan/", views.save_plan, name="save_plan"),

    # Exercise Flow
    path("session-report/", views.session_report, name="session_report"),

    # Session Completion (points + streak)
    path("complete-session/", views.complete_session, name="complete_session"),

    # View Your Plan
    path("view-plan/", views.view_plan, name="view_plan"),
    
    # Delete Existing Plan
    path("delete-plan/", views.delete_plan, name="delete_plan"),

    path("today-session/", views.today_session, name="today_session"),

    path("submit-session/", views.submit_session, name="submit_session"),

]
