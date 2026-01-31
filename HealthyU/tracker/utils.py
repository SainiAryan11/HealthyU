from datetime import date

def update_streak_and_points(profile):
    today = date.today()

    if profile.last_activity == today:
        # already counted today
        return

    if profile.last_activity is None:
        profile.streak = 1
    else:
        delta = (today - profile.last_activity).days

        if delta == 1:
            profile.streak += 1
        else:
            profile.streak = 1

    profile.points += 10
    profile.last_activity = today
    profile.save()
