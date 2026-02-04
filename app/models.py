from django.db import models
from unicodedata import name 
from django.contrib.auth.models import User
import app

# Create your models here.

class User(models.Model):
    id = models.AutoField(primary_key = True)
    user_age = models.IntegerField()
    user_name = models.CharField(max_length = 50)

class Movie(models.Model):
    id = models.AutoField(primary_key = True)
    movie_name = models.CharField(max_length = 50)


