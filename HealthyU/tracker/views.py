import json
import datetime

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.serializers.json import DjangoJSONEncoder

from .models import UserProfile, ExercisePlan, PlanItem, SessionRecord


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
    try:
        plan = ExercisePlan.objects.prefetch_related("items").get(user=request.user)
    except ExercisePlan.DoesNotExist:
        plan = None

    profile_obj = UserProfile.objects.get(user=request.user)
    today = timezone.now().date()
    session_done_today = (profile_obj.last_session_date == today)

    return render(request, "tracker/profile/profile.html", {
        "plan": plan,
        "session_done_today": session_done_today
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
    # ✅ Block starting session if already completed today
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
    med_items = plan.items.filter(category__iexact="Meditation").order_by("id")

    # ✅ Flags for dynamic progress / phase logic
    has_physical = physical_items.exists()
    has_yoga = yoga_items.exists()
    has_meditation = med_items.exists()

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

    # ✅ Meditation: Build array of meditations (not just one)
    meditation_data = []
    if med_items.exists():
        meditation_steps = [
            "Sit comfortably with a straight back",
            "Close your eyes and relax your shoulders",
            "Breathe slowly in and out through the nose",
            "Bring attention back when the mind wanders",
            "Finish gently and open your eyes slowly"
        ]
        meditation_data = build_list(
            med_items,
            "{name} helps calm your mind. Sit comfortably and focus on your breath.",
            meditation_steps
        )

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
@require_POST
@login_required(login_url="login")
def submit_session(request):
    data = json.loads(request.body)
    earned_points = int(data.get("points", 0))
    earned_points = min(earned_points, 100)  # ✅ cap

    profile = UserProfile.objects.get(user=request.user)
    today = timezone.now().date()

    # ✅ Check if session already completed today
    is_restart = profile.last_session_date == today
    
    # If restart, subtract previously earned points
    if is_restart:
        old_session = SessionRecord.objects.filter(user=request.user, date=today).first()
        if old_session:
            profile.points -= old_session.points_earned

    # ---- STREAK LOGIC (24-hour rule) ----
    # Only increment streak if this is NOT a restart (first completion today)
    if not is_restart:
        last_act = profile.last_activity
        now = timezone.now()
        if last_act:
            # If last_activity is a date (old rows), convert to aware datetime at midnight
            if isinstance(last_act, datetime.datetime):
                last_dt = last_act
            else:
                # last_act is likely a date; combine with midnight in current timezone
                last_dt = timezone.make_aware(datetime.datetime.combine(last_act, datetime.time.min))

            delta = now - last_dt
            if delta <= datetime.timedelta(hours=24):
                profile.streak += 1
            else:
                profile.streak = 1
        else:
            # First ever activity
            profile.streak = 1

    # ---- POINTS ----
    profile.points += earned_points
    profile.last_activity = timezone.now()
    profile.last_session_date = today
    profile.session_completed_today = True  # ✅ Mark session as completed today
    profile.save()

    # ---- SAVE SESSION RECORD ----
    SessionRecord.objects.update_or_create(
        user=request.user,
        date=today,
        defaults={
            "report": data.get("report", {}),
            "points_earned": earned_points
        }
    )

    return JsonResponse({
        "status": "ok",
        "points_added": earned_points,
        "streak": profile.streak,
        "is_restart": is_restart
    })

@login_required(login_url="login")
def complete_session(request):
    profile = UserProfile.objects.get(user=request.user)
    today = timezone.now().date()
    # Use 24-hour rule for streaks
    last_act = profile.last_activity
    now = timezone.now()
    if last_act:
        if isinstance(last_act, datetime.datetime):
            last_dt = last_act
        else:
            last_dt = timezone.make_aware(datetime.datetime.combine(last_act, datetime.time.min))

        delta = now - last_dt
        if delta <= datetime.timedelta(hours=24):
            profile.streak += 1
        else:
            profile.streak = 1
    else:
        profile.streak = 1

    profile.points += 10
    profile.last_activity = timezone.now()
    profile.last_session_date = today
    profile.session_completed_today = True
    profile.save()

    return redirect("profile")


# ---- NEW: DELETE SESSION ----
@require_POST
@login_required(login_url="login")
def delete_session(request):
    profile = UserProfile.objects.get(user=request.user)
    today = timezone.now().date()

    # ✅ Get the session record and subtract points
    session_record = SessionRecord.objects.filter(user=request.user, date=today).first()
    if session_record:
        profile.points -= session_record.points_earned
        session_record.delete()

    # ✅ Reduce streak by 1
    if profile.streak > 0:
        profile.streak -= 1

    # ✅ Reset session date and completed_today flag to allow restart
    profile.last_session_date = None
    profile.session_completed_today = False
    profile.save()

    return JsonResponse({"status": "ok", "message": "Session deleted successfully"})


