from django.contrib import admin
from .models import UserProfile

# Register your models here.

from .models import PhysicalHealth
admin.site.register(PhysicalHealth)

from .models import Exercise
admin.site.register(Exercise)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'streak', 'last_activity')


from .models import ExercisePlan, PlanItem

admin.site.register(ExercisePlan)
admin.site.register(PlanItem)
