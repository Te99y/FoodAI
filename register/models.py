from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import os

class CustomUser(AbstractUser):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('', 'Prefer not to say'),  # Empty string for users who prefer not to reveal their gender
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    health_condition = models.CharField(max_length=100, null=True, blank=True)

def upload_path_original(instance, filename):
    username = instance.user.username
    upload_time = instance.upload_time()
    _, extension = os.path.splitext(filename)    
    return f'app/meal_data/meal_images/{username}/{upload_time}{extension}'

def upload_path_segmented(instance, filename):
    username = instance.user.username
    upload_time = instance.upload_time()
    _, extension = os.path.splitext(filename)    
    return f'app/meal_data/segmented_images/{username}/{upload_time}{extension}'

class Meal(models.Model):
    def upload_time(self):
        return timezone.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    meal_image = models.ImageField(upload_to=upload_path_original, null=True)
    segment_image = models.ImageField(upload_to=upload_path_segmented, null=True, blank=True)
    analysis = models.JSONField(null=True, blank=True)
    date_time = models.DateTimeField(default=(timezone.now))
    description = models.CharField(max_length=100, blank=True)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

