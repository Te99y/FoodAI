from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.forms import ModelForm
from django.contrib.auth.models import User
from .models import CustomUser, Meal

class RegisterForm(UserCreationForm):
    email = forms.EmailField()
    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2"]


class EditInfoForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ["height", "weight", "gender", "birth_date", "health_condition"]
        widgets = {
            'birth_date': forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD'}),
        }

class EditMealForm(ModelForm):
    class Meta:
        model = Meal
        fields = ["meal_image", "analysis", "date_time", "description"]
