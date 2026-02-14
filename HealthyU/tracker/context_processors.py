# tracker/context_processors.py

from .models import UserProfile

def user_stats(request):
    if request.user.is_authenticated:
        try:
            profile = UserProfile.objects.get(user=request.user)
            return {
                "nav_points": profile.points,
                "nav_streak": profile.streak
            }
        except UserProfile.DoesNotExist:
            pass

    return {
        "nav_points": 0,
        "nav_streak": 0
    }
