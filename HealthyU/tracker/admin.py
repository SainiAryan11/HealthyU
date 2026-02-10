from django.contrib import admin
from .models import UserProfile, SessionRecord

# Register your models here.

from .models import PhysicalHealth
admin.site.register(PhysicalHealth)

from .models import Exercise
admin.site.register(Exercise)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'streak', 'last_activity', 'last_session_date')


@admin.register(SessionRecord)
class SessionRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'points_earned', 'created_at')
    list_filter = ('date', 'user')
    search_fields = ('user__username',)


from .models import ExercisePlan, PlanItem

admin.site.register(ExercisePlan)
admin.site.register(PlanItem)
