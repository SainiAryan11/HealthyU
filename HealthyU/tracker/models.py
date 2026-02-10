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
    last_activity = models.DateField(null=True, blank=True)
    last_session_date = models.DateField(null=True, blank=True)
    last_session_report = models.JSONField(null=True, blank=True)
    session_saved_today = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

from django.db import models
from django.contrib.auth.models import User

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

