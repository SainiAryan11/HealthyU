from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

# Create your views here.

def home(request):
    return render(request, 'home.html')

def signup(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password']
        dob = request.POST['dob']  # stored later (ignore for now)

        # Create user (email as username)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        return redirect('login')

    return render(request, 'signup.html')


def login_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:
            login(request, user)
            return redirect('profile')

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('home')

from .models import Exercise

@login_required(login_url='login')
def profile(request):
    exercises = Exercise.objects.all()
    return render(request, 'profile.html', {'exercises': exercises})

def streak(request):
    return render(request, 'streak.html')
