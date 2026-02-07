from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from datetime import timedelta

from .models import UserProfile, ExercisePlan, PlanItem
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse


# ---------------- HOME ----------------
def home(request):
    return render(request, "tracker/home/home.html")


# ---------------- AUTH ----------------
def signup(request):
    if request.method == "POST":
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        email = request.POST["email"]
        password = request.POST["password"]
        dob = request.POST["dob"]  # ignore for now / store later

        # email as username
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        return redirect("login")

    return render(request, "tracker/auth/signup.html")


def login_view(request):
    error = None

    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            return redirect("profile")
        else:
            error = "Invalid email or password"

    return render(request, "tracker/auth/login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("home")


# ---------------- PROFILE ----------------
@login_required(login_url="login")
def profile(request):
    try:
        plan = ExercisePlan.objects.prefetch_related("items").get(user=request.user)
    except ExercisePlan.DoesNotExist:
        plan = None
    return render(request, "tracker/profile/profile.html", {"plan": plan})


# ---------------- STREAK / LEADERBOARD ----------------
def streak(request):
    return render(request, "tracker/home/streak.html")


# ---------------- PLAN ----------------
@login_required(login_url="login")
def create_plan(request):
    if ExercisePlan.objects.filter(user=request.user).exists():
        return redirect("view_plan")
    return render(request, "tracker/plan/create_plan.html")



@require_POST
@login_required(login_url="login")
def save_plan(request):
    if ExercisePlan.objects.filter(user=request.user).exists():
        return JsonResponse(
            {"status": "error", "message": "Plan already exists. You can only delete it."},
            status=400
        )

    data = json.loads(request.body)
    plan = ExercisePlan.objects.create(user=request.user)

    for item in data.get("items", []):
        PlanItem.objects.create(
            plan=plan,
            name=item["name"],
            category=item["category"],
            value=int(item["value"]),
            unit=item["unit"]
        )

    return JsonResponse({"status": "ok", "message": "Plan saved successfully!"})


# ---------------- SESSION PAGES (FRONTEND ONLY FOR NOW) ----------------

@login_required(login_url="login")
def session_report(request):
    return render(request, "tracker/session/session_report.html")


# ---------------- COMPLETE SESSION (STREAK + POINTS) ----------------
@login_required(login_url="login")
def complete_session(request):
    profile = UserProfile.objects.get(user=request.user)
    today = timezone.now().date()

    # ---- STREAK LOGIC ----
    if profile.last_activity:
        if profile.last_activity == today:
            pass
        elif profile.last_activity == today - timedelta(days=1):
            profile.streak += 1
        else:
            profile.streak = 1
    else:
        profile.streak = 1

    # ---- POINTS ----
    profile.points += 10
    profile.last_activity = today
    profile.save()

    return redirect("profile")

@login_required(login_url="login")
def view_plan(request):
    try:
        plan = ExercisePlan.objects.prefetch_related("items").get(user=request.user)
    except ExercisePlan.DoesNotExist:
        plan = None
    return render(request, "tracker/plan/view_plan.html", {"plan": plan})


@login_required(login_url="login")
@require_POST
def delete_plan(request):
    plan = ExercisePlan.objects.filter(user=request.user).first()
    if plan:
        plan.delete()
    return redirect("profile")

import json
from django.core.serializers.json import DjangoJSONEncoder

@login_required(login_url="login")
def today_session(request):
    try:
        plan = ExercisePlan.objects.prefetch_related("items").get(user=request.user)
    except ExercisePlan.DoesNotExist:
        return redirect("profile")

    physical_items = plan.items.filter(category="Physical Exercise").order_by("id")
    yoga_items = plan.items.filter(category="Yoga").order_by("id")
    
    med_item = plan.items.filter(category__iexact="Meditation").order_by("id").first()

    meditation_data = None
    if med_item:
        meditation_data = {
            "name": med_item.name,
            "description": f"{med_item.name} helps calm your mind. Sit comfortably and focus on your breath.",
            "value": med_item.value,   # minutes
            "unit": "min",
            "steps": [
                "Sit comfortably with a straight back",
                "Close your eyes and relax your shoulders",
                "Breathe slowly in and out through the nose",
                "Bring attention back when the mind wanders",
                "Finish gently and open your eyes slowly"
            ]
        }
    else:
        meditation_data = {
            "name": "Meditation",
            "description": "Sit comfortably and focus on your breath.",
            "value": 5,
            "unit": "min",
            "steps": [
                "Sit comfortably with a straight back",
                "Close your eyes and relax your shoulders",
                "Breathe slowly in and out through the nose",
                "Bring attention back when the mind wanders",
                "Finish gently and open your eyes slowly"
            ]
        }


    if not physical_items.exists() and not yoga_items.exists():
        return redirect("profile")

    def build_list(qs, default_desc):
        arr = []
        for item in qs:
            arr.append({
                "name": item.name,
                "description": default_desc.format(name=item.name),
                "value": item.value,
                "unit": item.unit,
                "steps": [
                    "Maintain correct posture",
                    "Start slow and steady",
                    "Focus on breathing",
                    "Keep movements controlled",
                    "Finish and rest briefly"
                ]
            })
        return arr

    physical_data = build_list(physical_items, "Perform {name} safely and with proper form.")
    yoga_data = build_list(yoga_items, "Relax your body and breathe steadily during {name}.")

    return render(request, "tracker/session/today_session.html", {
        "physical_json": json.dumps(physical_data, cls=DjangoJSONEncoder),
        "yoga_json": json.dumps(yoga_data, cls=DjangoJSONEncoder),
        "meditation_json": json.dumps(meditation_data, cls=DjangoJSONEncoder),
    })
