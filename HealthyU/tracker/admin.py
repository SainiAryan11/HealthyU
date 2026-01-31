from django.contrib import admin

# Register your models here.

from .models import PhysicalHealth
admin.site.register(PhysicalHealth)

from .models import Exercise
admin.site.register(Exercise)

from .models import UserProfile
admin.site.register(UserProfile)