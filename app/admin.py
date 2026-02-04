from django.contrib import admin
# from .models import 
# Register your models here.
from register.models import CustomUser, Meal
admin.site.register(CustomUser)
admin.site.register(Meal)
