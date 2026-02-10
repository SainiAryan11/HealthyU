import json
from datetime import timedelta

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.serializers.json import DjangoJSONEncoder

from .models import UserProfile, ExercisePlan, PlanItem


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
    plan = ExercisePlan.objects.prefetch_related("items").filter(user=request.user).first()

    profile_obj = UserProfile.objects.get(user=request.user)
    today = timezone.now().date()

    # ✅ Reset daily flag if it's a new day
    if profile_obj.last_activity != today and profile_obj.session_saved_today:
        profile_obj.session_saved_today = False
        profile_obj.save(update_fields=["session_saved_today"])

    # ✅ This controls whether button shows "Start" or "View Report"
    session_done_today = (profile_obj.session_saved_today and profile_obj.last_activity == today)

    return render(request, "tracker/profile/profile.html", {
        "plan": plan,
        "session_done_today": session_done_today,
        "profile_obj": profile_obj
    })


# ---------------- STREAK / LEADERBOARD ----------------
def streak(request):
    return render(request, "tracker/home/streak.html")


# ---------------- PLAN ----------------
@login_required(login_url="login")
def create_plan(request):
    # one plan only
    if ExercisePlan.objects.filter(user=request.user).exists():
        return redirect("view_plan")
    return render(request, "tracker/plan/create_plan.html")


@require_POST
@login_required(login_url="login")
def save_plan(request):
    # one plan only
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


# ---------------- SESSION PAGES ----------------
@login_required(login_url="login")
def today_session(request):
    # ✅ Block restarting session if already completed today
    profile = UserProfile.objects.get(user=request.user)
    today = timezone.now().date()

    if profile.last_session_date == today:
        return redirect("session_report")

    # ✅ Load user's plan
    try:
        plan = ExercisePlan.objects.prefetch_related("items").get(user=request.user)
    except ExercisePlan.DoesNotExist:
        return redirect("profile")

    physical_items = plan.items.filter(category="Physical Exercise").order_by("id")
    yoga_items = plan.items.filter(category="Yoga").order_by("id")
    med_item = plan.items.filter(category__iexact="Meditation").order_by("id").first()

    # ✅ Flags for dynamic progress / phase logic
    has_physical = physical_items.exists()
    has_yoga = yoga_items.exists()
    has_meditation = (med_item is not None)

    # ✅ If user selected nothing at all → go back
    if (not has_physical) and (not has_yoga) and (not has_meditation):
        return redirect("profile")

    def build_list(qs, default_desc, steps):
        arr = []
        for item in qs:
            arr.append({
                "name": item.name,
                "description": default_desc.format(name=item.name),
                "value": item.value,
                "unit": item.unit,
                "steps": steps
            })
        return arr

    physical_steps = [
        "Maintain correct posture",
        "Start slow and steady",
        "Focus on breathing",
        "Keep movements controlled",
        "Finish and rest briefly"
    ]
    yoga_steps = [
        "Stand/sit in a comfortable pose",
        "Breathe slowly and deeply",
        "Move gently with control",
        "Hold the posture steadily",
        "Release slowly and relax"
    ]

    physical_data = build_list(
        physical_items,
        "Perform {name} safely and with proper form.",
        physical_steps
    )

    yoga_data = build_list(
        yoga_items,
        "Relax your body and breathe steadily during {name}.",
        yoga_steps
    )

    # ✅ Meditation: ONLY if selected (no default)
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

    return render(request, "tracker/session/today_session.html", {
        "physical_json": json.dumps(physical_data, cls=DjangoJSONEncoder),
        "yoga_json": json.dumps(yoga_data, cls=DjangoJSONEncoder),
        "meditation_json": json.dumps(meditation_data, cls=DjangoJSONEncoder),
        "has_physical": has_physical,
        "has_yoga": has_yoga,
        "has_meditation": has_meditation,
    })

@login_required(login_url="login")
def session_report(request):
    return render(request, "tracker/session/session_report.html")


# ---------------- SAVE SESSION (POINTS + STREAK) ----------------
@login_required(login_url="login")
@require_POST
def submit_session(request):
    data = json.loads(request.body)

    report = data.get("report", {})
    progress = min(int(report.get("progress", 0)), 100)
    points = min(int(data.get("points", 0)), 100)

    profile = UserProfile.objects.get(user=request.user)
    today = timezone.now().date()

    # ✅ Cannot save if progress < 50%
    if progress < 50:
        return JsonResponse({
            "status": "error",
            "message": "Session not saved. Complete at least 50% to save.",
            "reason": "progress_too_low"
        }, status=400)

    # ✅ Only 1 save per day
    if profile.session_saved_today and profile.last_activity == today:
        return JsonResponse({
            "status": "error",
            "message": "Session already saved today. Come back tomorrow!",
            "reason": "already_saved"
        }, status=400)

    # ✅ Streak logic (only happens when session is saved)
    if profile.last_activity:
        if profile.last_activity == today - timedelta(days=1):
            profile.streak += 1
        elif profile.last_activity != today:
            profile.streak = 1
    else:
        profile.streak = 1

    # ✅ Points
    profile.points += points

    # ✅ Mark saved today (controls profile button)
    profile.last_activity = today
    profile.session_saved_today = True
    profile.save()

    return JsonResponse({
        "status": "ok",
        "message": "Session saved successfully!",
        "progress": progress,
        "points_added": points,
        "new_streak": profile.streak,
        "total_points": profile.points
    })

@login_required(login_url="login")
def complete_session(request):
    profile = UserProfile.objects.get(user=request.user)
    today = timezone.now().date()

    if profile.last_activity:
        if profile.last_activity == today:
            pass
        elif profile.last_activity == today - timedelta(days=1):
            profile.streak += 1
        else:
            profile.streak = 1
    else:
        profile.streak = 1

    profile.points += 10
    profile.last_activity = today
    profile.save()

    return redirect("profile")