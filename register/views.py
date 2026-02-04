from django.shortcuts import render, redirect
from .forms import RegisterForm, EditInfoForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
# Create your views here.
def register(response):
    if response.method == "POST":
        form = RegisterForm(response.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            if user is not None:
                # Log in the user
                login(response, user)
            return redirect("/edit")
    else:
        form = RegisterForm()
    return render(response, "register/register.html", {"form":form})


def edit(response):
    if response.method == "POST":
        form = EditInfoForm(response.POST, instance = response.user)
        if form.is_valid():
            form.save()
            return redirect("/profile")
    else:
        form = EditInfoForm(instance=response.user)
    return render(response, "edit/edit.html", {"form":form})