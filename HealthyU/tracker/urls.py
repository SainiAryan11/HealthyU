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
    path("session-report/<str:day>/", views.session_report, name="session_report_by_day"),

    # View Your Plan
    path("view-plan/", views.view_plan, name="view_plan"),
    
    # Delete Existing Plan
    path("delete-plan/", views.delete_plan, name="delete_plan"),

    path("today-session/", views.today_session, name="today_session"),

    path("submit-session/", views.submit_session, name="submit_session"),

    path("progress/", views.show_progress, name="show_progress"),
    path("progress/data/", views.progress_data, name="progress_data"),
    # Challenges
    path("challenges/", views.challenges, name="challenges"),
    path("challenges/accept/<int:challenge_id>/", views.accept_challenge, name="accept_challenge"),

    # Yoga
    path("yoga/<str:yoga_type>/", views.yoga_detail, name="yoga_detail"),

    # Meditation
    path("meditation/<str:meditation_type>/", views.meditation_detail, name="meditation_detail"),

    # Workout Plans
    path("workout-plans/", views.workout_plans, name="workout_plans"),

    # Workout Details
    path("workout/<str:workout_type>/", views.workout_detail, name="workout_detail"),

    path("challenges/", views.challenges, name="challenges"),
    path("challenges/<int:challenge_id>/", views.challenge_session, name="challenge_session"),
    path("challenges/<int:challenge_id>/complete/", views.complete_challenge, name="complete_challenge"),

    path("points/", views.points, name="points"),
]
