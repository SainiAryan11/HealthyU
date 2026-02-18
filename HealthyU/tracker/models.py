from django.db import models
from django.contrib.auth.models import User

class PhysicalHealth(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    steps = models.IntegerField()
    calories = models.IntegerField()
    sleep_hours = models.FloatField()
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.user)
    

class Exercise(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name
    

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    points = models.IntegerField(default=0)
    streak = models.IntegerField(default=0)
    last_activity = models.DateTimeField(null=True, blank=True)
    last_session_date = models.DateField(null=True, blank=True)
    last_session_report = models.JSONField(null=True, blank=True)
    session_saved_today = models.BooleanField(default=False)
    session_completed_today = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class SessionRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="session_records")
    date = models.DateField()
    report = models.JSONField()
    points_earned = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']


class ExercisePlan(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} plan ({self.created_at.date()})"


class PlanItem(models.Model):
    CATEGORY_CHOICES = [
        ("Physical Exercise", "Physical Exercise"),
        ("Yoga", "Yoga"),
        ("Meditation", "Meditation"),
    ]

    plan = models.ForeignKey(ExercisePlan, on_delete=models.CASCADE, related_name="items")
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    value = models.IntegerField()  # frequency or minutes
    unit = models.CharField(max_length=10)  # "freq" or "min"

    def __str__(self):
        return f"{self.name} ({self.category})"
    

class DailyProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    progress = models.IntegerField(default=0)   # 0-100
    points = models.IntegerField(default=0)     # points earned that day

    class Meta:
        unique_together = ("user", "date")
        ordering = ["date"]

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.progress}%)"


from django.utils import timezone

class DailyExerciseChallenge(models.Model):
    """
    10 challenges per user, created from user's PlanItem (Physical Exercise).
    day_number: 1..10
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="exercise_challenges")
    plan_item = models.ForeignKey("PlanItem", on_delete=models.CASCADE)
    day_number = models.IntegerField()  # 1..10

    class Meta:
        unique_together = ("user", "day_number")
        ordering = ["day_number"]

    def __str__(self):
        return f"{self.user.username} Day {self.day_number}: {self.plan_item.name}"


class DailyExerciseChallengeLog(models.Model):
    """
    Stores completion/skip for each day challenge.
    """
    STATUS_CHOICES = [
        ("completed", "Completed"),
        ("skipped", "Skipped"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(DailyExerciseChallenge, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    date = models.DateField(default=timezone.localdate)

    class Meta:
        unique_together = ("user", "challenge")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user.username} - {self.challenge.day_number} - {self.status}"

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ChallengeMaster(models.Model):
    """
    Global 10 challenges. Not user-specific. Visible to everyone.
    """
    day_number = models.IntegerField(unique=True)  # 1..10
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    value = models.IntegerField(default=10)  # e.g. 10 reps or 5 mins
    unit = models.CharField(max_length=20, default="freq")  # "freq" or "min"

    steps = models.JSONField(default=list)  # list of step strings
    reward_points = models.IntegerField(default=50)

    class Meta:
        ordering = ["day_number"]

    def __str__(self):
        return f"Day {self.day_number} - {self.title}"


class UserChallengeLog(models.Model):
    """
    Only for logged-in users: completion tracking.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    challenge = models.ForeignKey(ChallengeMaster, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[("completed", "Completed")])
    date = models.DateField(default=timezone.localdate)

    class Meta:
        unique_together = ("user", "challenge")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user.username} - Day {self.challenge.day_number} - {self.status}"

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class PointsTransaction(models.Model):
    SOURCE_CHOICES = [
        ("session", "Session"),
        ("challenge", "Challenge"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="points_transactions")
    date = models.DateTimeField(default=timezone.now)

    points = models.IntegerField()  # +50 etc (can be negative later if you want)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES)

    note = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.user.username} {self.points} ({self.source})"
