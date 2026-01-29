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
