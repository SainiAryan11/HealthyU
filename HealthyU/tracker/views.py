import json
from datetime import timedelta  # ✅ add this

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.serializers.json import DjangoJSONEncoder

from .models import UserProfile, ExercisePlan, PlanItem, SessionRecord

def _count_status(items, status):
    return sum(1 for x in items if x.get("status") == status)

def _safe_list(report, key):
    val = report.get(key, [])
    return val if isinstance(val, list) else []

def _validate_skip_limit(report):
    physical = _safe_list(report, "physical")
    yoga = _safe_list(report, "yoga")

    total_skippable = len(physical) + len(yoga)
    if total_skippable == 0:
        return True, None

    skipped = _count_status(physical, "skipped") + _count_status(yoga, "skipped")
    max_skips = int(total_skippable * 0.25)  # floor like JS

    if skipped > max_skips:
        return False, f"Skip limit exceeded. Allowed {max_skips}, got {skipped}."
    return True, None

def _compute_progress_points(plan, report):
    # active categories based on plan content (NOT based on client)
    physical_count = plan.items.filter(category="Physical Exercise").count()
    yoga_count = plan.items.filter(category="Yoga").count()
    med_count = plan.items.filter(category__iexact="Meditation").count()

    active = []
    if physical_count > 0:
        active.append("physical")
    if yoga_count > 0:
        active.append("yoga")
    if med_count > 0:
        active.append("meditation")

    if not active:
        return 0, 0

    weight = 100 / len(active)

    physical = _safe_list(report, "physical")
    yoga = _safe_list(report, "yoga")

    # ✅ meditation summary object from JS
    meditation = report.get("meditation") or {}
    if not isinstance(meditation, dict):
        meditation = {}

    def ratio_done(lst):
        if not lst:
            return 0.0
        done = _count_status(lst, "completed")
        return done / len(lst)

    prog = 0.0

    # ✅ Physical: completed ratio
    if "physical" in active:
        prog += ratio_done(physical) * weight

    # ✅ Yoga: completed ratio
    if "yoga" in active:
        prog += ratio_done(yoga) * weight

    # ✅ Meditation: time ratio (spent/planned)
    if "meditation" in active:
        planned = meditation.get("planned_minutes", 0) or 0
        spent = meditation.get("spent_minutes", 0) or 0

        try:
            planned = float(planned)
            spent = float(spent)
        except Exception:
            planned = 0.0
            spent = 0.0

        med_ratio = 0.0
        if planned > 0:
            med_ratio = min(max(spent / planned, 0.0), 1.0)

        prog += med_ratio * weight

    # ✅ IMPORTANT: DON’T round too aggressively
    # Use floor to avoid showing 50 but saving as 49 after rounding noise
    progress = int(prog + 1e-9)  # floor-like
    progress = max(0, min(progress, 100))

    points = progress  # your rule

    return progress, points


# ---------------- HOME ----------------
from django.utils import timezone
from .models import ExercisePlan, SessionRecord, UserProfile

def home(request):
    context = {}

    if request.user.is_authenticated:
        today = timezone.localdate()

        plan = ExercisePlan.objects.filter(user=request.user).first()
        session_done_today = SessionRecord.objects.filter(user=request.user, date=today).exists()

        context.update({
            "plan": plan,
            "session_done_today": session_done_today,
        })

    return render(request, "tracker/home/home.html", context)


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
from django.utils import timezone
from .models import ExercisePlan, SessionRecord, UserProfile

@login_required(login_url="login")
def profile(request):
    profile_obj = UserProfile.objects.get(user=request.user)
    today = timezone.localdate()

    plan = ExercisePlan.objects.filter(user=request.user).first()

    # ✅ TRUE source of truth
    session_done_today = SessionRecord.objects.filter(user=request.user, date=today).exists()

    # (optional) sync profile flags to DB truth
    if session_done_today:
        profile_obj.session_saved_today = True
        if not profile_obj.last_activity or profile_obj.last_activity.date() != today:
            profile_obj.last_activity = timezone.now()
        profile_obj.save(update_fields=["session_saved_today", "last_activity"])

    return render(request, "tracker/profile/profile.html", {
        "plan": plan,
        "session_done_today": session_done_today,
    })


# ---------------- STREAK / LEADERBOARD ----------------
from django.db.models import F
from .models import UserProfile

def streak(request):
    top_users = (
        UserProfile.objects
        .select_related("user")
        .filter(user__is_superuser=False)
        .order_by("-streak", "-points")[:5]   # ✅ primary streak, secondary points
    )

    return render(request, "tracker/home/streak.html", {
        "top_users": top_users
    })



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
    today = timezone.localdate()

    last_act_date = profile.last_activity.date() if profile.last_activity else None

    # ✅ Block if session already saved today
    if profile.session_saved_today and last_act_date == today:
        return redirect("session_report")

    # ✅ Also block if SessionRecord exists today (stronger)
    if SessionRecord.objects.filter(user=request.user, date=today).exists():
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

import datetime
from django.http import Http404
from django.utils import timezone
from django.contrib.auth.decorators import login_required

@login_required(login_url="login")
def session_report(request, day=None):

    if day:
        try:
            date_obj = datetime.datetime.strptime(day, "%Y-%m-%d").date()
        except ValueError:
            return redirect("show_progress")
    else:
        date_obj = timezone.localdate()

    record = SessionRecord.objects.filter(
        user=request.user,
        date=date_obj
    ).first()

    return render(request, "tracker/session/session_report.html", {
        "record": record,
        "viewed_date": date_obj
    })



# ---------------- SAVE SESSION (POINTS + STREAK) ----------------
from datetime import timedelta
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import json

@login_required(login_url="login")
@require_POST
def submit_session(request):
    data = json.loads(request.body or "{}")
    report = data.get("report") or {}

    profile = UserProfile.objects.get(user=request.user)
    today = timezone.localdate()
    now = timezone.now()

    # ✅ must have a plan
    plan = ExercisePlan.objects.prefetch_related("items").filter(user=request.user).first()
    if not plan:
        return JsonResponse({"status": "error", "message": "No plan found."}, status=400)

    # ✅ One save per day (server truth)
    if SessionRecord.objects.filter(user=request.user, date=today).exists():
        return JsonResponse({
            "status": "error",
            "message": "Session already saved today. Come back tomorrow!",
            "reason": "already_saved"
        }, status=400)

    # ✅ Skip rule validation (Physical+Yoga only)
    ok, msg = _validate_skip_limit(report)
    if not ok:
        return JsonResponse({"status": "error", "message": msg, "reason": "skip_limit"}, status=400)

    # ✅ Compute progress + points on server
    progress, points = _compute_progress_points(plan, report)

    # ✅ Save allowed only if progress >= 50%
    if progress < 50:
        return JsonResponse({
            "status": "error",
            "message": "Session not saved. Progress must be at least 50% to save.",
            "reason": "progress_too_low",
            "progress": progress
        }, status=400)

    # ✅ STREAK: always use last_session_date (convert to date if needed)
    last_session_date = profile.last_session_date
    if hasattr(last_session_date, "date"):   # handles datetime accidentally stored
        last_session_date = last_session_date.date()

    yesterday = today - timedelta(days=1)

    if last_session_date == yesterday:
        profile.streak = (profile.streak or 0) + 1
    else:
        profile.streak = 1

    # ✅ POINTS
    profile.points = (profile.points or 0) + int(points or 0)

    # ✅ Update profile daily status
    profile.last_activity = now
    profile.last_session_date = today
    profile.last_session_report = report
    profile.session_saved_today = True
    profile.session_completed_today = (progress == 100)
    profile.save()

    # ✅ Store record for report + analytics
    SessionRecord.objects.create(
        user=request.user,
        date=today,
        report=report,
        points_earned=int(points or 0)
    )

    return JsonResponse({
        "status": "ok",
        "message": "Session saved successfully!",
        "progress": progress,
        "points_added": int(points or 0),
        "new_streak": profile.streak,
        "total_points": profile.points
    })

from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import timedelta

from .models import SessionRecord, ExercisePlan

@login_required(login_url="login")
def show_progress(request):
    plan = ExercisePlan.objects.filter(user=request.user).first()
    today = timezone.localdate()
    start = today - timedelta(days=30)

    records = (
        SessionRecord.objects
        .filter(user=request.user, date__gte=start, date__lte=today)
        .order_by("-date")
    )

    return render(request, "tracker/progress/show_progress.html", {
        "plan": plan,
        "records": records,
    })

@login_required(login_url="login")
def progress_data(request):
    """
    Returns JSON for Plotly charts:
    - daily (last 30 days)
    - weekly (last 12 weeks)
    - monthly (last 12 months)
    """
    today = timezone.localdate()

    # Pull last ~365 days for easy aggregation
    start = today - timedelta(days=365)
    qs = (
        SessionRecord.objects
        .filter(user=request.user, date__gte=start, date__lte=today)
        .order_by("date")
        .values("date", "points_earned", "report")
    )

    # --- Helper: compute progress from stored report (server-truth-ish) ---
    def compute_progress_from_report(report):
        # If your backend stored "report" as dict already, great.
        # If it stored as string, try parse.
        if report is None:
            return 0

        if isinstance(report, str):
            import json
            try:
                report = json.loads(report)
            except Exception:
                return 0

        physical = report.get("physical", []) if isinstance(report.get("physical", []), list) else []
        yoga = report.get("yoga", []) if isinstance(report.get("yoga", []), list) else []
        med = report.get("meditation", {}) if isinstance(report.get("meditation", {}), dict) else {}

        # active categories = those present in report
        active = []
        if len(physical) > 0: active.append("physical")
        if len(yoga) > 0: active.append("yoga")
        # meditation present only if planned in session
        if med and med.get("status") != "not_planned":
            active.append("meditation")

        if not active:
            return 0

        weight = 100 / len(active)

        def ratio_done(lst):
            if not lst:
                return 0.0
            done = sum(1 for x in lst if x.get("status") == "completed")
            return done / len(lst)

        prog = 0.0
        if "physical" in active:
            prog += ratio_done(physical) * weight
        if "yoga" in active:
            prog += ratio_done(yoga) * weight
        if "meditation" in active:
            prog += (1.0 if med.get("status") == "completed" else 0.0) * weight

        return max(0, min(int(round(prog)), 100))

    # --- Build daily series (last 30 days, include 0s) ---
    daily_map = {row["date"]: (compute_progress_from_report(row["report"]), int(row["points_earned"] or 0)) for row in qs}

    daily_labels = []
    daily_progress = []
    daily_points = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        p, pts = daily_map.get(d, (0, 0))
        daily_labels.append(d.isoformat())
        daily_progress.append(p)
        daily_points.append(min(pts, 100))

    # --- Weekly aggregation (last 12 weeks) ---
    # Week starts on Monday
    def week_start(date_obj):
        return date_obj - timedelta(days=date_obj.weekday())

    weekly_bucket = {}
    for row in qs:
        d = row["date"]
        ws = week_start(d)
        prog = compute_progress_from_report(row["report"])
        pts = int(row["points_earned"] or 0)
        if ws not in weekly_bucket:
            weekly_bucket[ws] = {"sum_prog": 0, "sum_pts": 0, "count": 0}
        weekly_bucket[ws]["sum_prog"] += prog
        weekly_bucket[ws]["sum_pts"] += min(pts, 100)
        weekly_bucket[ws]["count"] += 1

    # last 12 week starts
    current_ws = week_start(today)
    weekly_labels = []
    weekly_avg_progress = []
    weekly_total_points = []
    for i in range(11, -1, -1):
        ws = current_ws - timedelta(weeks=i)
        b = weekly_bucket.get(ws)
        weekly_labels.append(ws.isoformat())
        if b and b["count"] > 0:
            weekly_avg_progress.append(int(round(b["sum_prog"] / b["count"])))
            weekly_total_points.append(int(b["sum_pts"]))
        else:
            weekly_avg_progress.append(0)
            weekly_total_points.append(0)

    # --- Monthly aggregation (last 12 months) ---
    def month_key(date_obj):
        return (date_obj.year, date_obj.month)

    monthly_bucket = {}
    for row in qs:
        d = row["date"]
        mk = month_key(d)
        prog = compute_progress_from_report(row["report"])
        pts = int(row["points_earned"] or 0)
        if mk not in monthly_bucket:
            monthly_bucket[mk] = {"sum_prog": 0, "sum_pts": 0, "count": 0}
        monthly_bucket[mk]["sum_prog"] += prog
        monthly_bucket[mk]["sum_pts"] += min(pts, 100)
        monthly_bucket[mk]["count"] += 1

    # Build last 12 months keys
    monthly_labels = []
    monthly_avg_progress = []
    monthly_total_points = []

    y, m = today.year, today.month
    keys = []
    for _ in range(12):
        keys.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    keys.reverse()

    for (yy, mm) in keys:
        label = f"{yy:04d}-{mm:02d}"
        monthly_labels.append(label)
        b = monthly_bucket.get((yy, mm))
        if b and b["count"] > 0:
            monthly_avg_progress.append(int(round(b["sum_prog"] / b["count"])))
            monthly_total_points.append(int(b["sum_pts"]))
        else:
            monthly_avg_progress.append(0)
            monthly_total_points.append(0)

    return JsonResponse({
        "daily": {
            "labels": daily_labels,
            "progress": daily_progress,
            "points": daily_points
        },
        "weekly": {
            "labels": weekly_labels,
            "avg_progress": weekly_avg_progress,
            "total_points": weekly_total_points
        },
        "monthly": {
            "labels": monthly_labels,
            "avg_progress": monthly_avg_progress,
            "total_points": monthly_total_points
        }
    })

# ---------------- CHALLENGES ----------------
import random
from datetime import date

# Daily challenges pool
CHALLENGE_POOL = [
    {"icon_class": "challenge-icon-run", "title": "Morning Runner", "description": "Complete a 20-minute run or jog", "points": 25, "xp": 10, "category": "cardio"},
    {"icon_class": "challenge-icon-strength", "title": "Push-up Master", "description": "Do 50 push-ups (can be broken into sets)", "points": 20, "xp": 8, "category": "strength"},
    {"icon_class": "challenge-icon-meditation", "title": "Zen Master", "description": "Complete 15 minutes of meditation", "points": 15, "xp": 12, "category": "mindfulness"},
    {"icon_class": "challenge-icon-weights", "title": "Strength Builder", "description": "Complete a full strength training session", "points": 30, "xp": 15, "category": "strength"},
    {"icon_class": "challenge-icon-flexibility", "title": "Flexibility Focus", "description": "Do 20 minutes of stretching or yoga", "points": 18, "xp": 10, "category": "flexibility"},
    {"icon_class": "challenge-icon-cardio", "title": "Cardio King", "description": "30 minutes of any cardio activity", "points": 25, "xp": 12, "category": "cardio"},
    {"icon_class": "challenge-icon-legs", "title": "Leg Day Legend", "description": "Complete 100 squats throughout the day", "points": 22, "xp": 10, "category": "strength"},
    {"icon_class": "challenge-icon-core", "title": "Core Crusher", "description": "5-minute plank challenge (total time)", "points": 20, "xp": 15, "category": "strength"},
    {"icon_class": "challenge-icon-water", "title": "Water Warrior", "description": "Drink 8 glasses of water today", "points": 10, "xp": 5, "category": "wellness"},
    {"icon_class": "challenge-icon-sleep", "title": "Sleep Champion", "description": "Get 8 hours of quality sleep", "points": 15, "xp": 8, "category": "wellness"},
    {"icon_class": "challenge-icon-nutrition", "title": "Healthy Eater", "description": "Eat 5 servings of fruits/vegetables", "points": 12, "xp": 6, "category": "wellness"},
    {"icon_class": "challenge-icon-steps", "title": "Step Master", "description": "Walk 10,000 steps today", "points": 20, "xp": 10, "category": "cardio"},
    {"icon_class": "challenge-icon-consistency", "title": "Consistency King", "description": "Complete your daily workout plan", "points": 30, "xp": 15, "category": "general"},
    {"icon_class": "challenge-icon-mindbody", "title": "Mind & Body", "description": "Do both yoga and meditation today", "points": 35, "xp": 18, "category": "mindfulness"},
    {"icon_class": "challenge-icon-hiit", "title": "HIIT Hero", "description": "Complete a 20-minute HIIT workout", "points": 28, "xp": 14, "category": "cardio"},
    {"icon_class": "challenge-icon-burpees", "title": "Burpee Beast", "description": "Complete 30 burpees throughout the day", "points": 25, "xp": 12, "category": "strength"},
    {"icon_class": "challenge-icon-yoga", "title": "Yoga Warrior", "description": "Complete a 30-minute yoga session", "points": 22, "xp": 11, "category": "flexibility"},
    {"icon_class": "challenge-icon-endurance", "title": "Endurance Master", "description": "45 minutes of continuous cardio", "points": 35, "xp": 16, "category": "cardio"},
]

def get_daily_challenges():
    """Get 5 random challenges for today based on date seed"""
    today = date.today()
    seed = int(today.strftime("%Y%m%d"))
    random.seed(seed)
    
    challenges = random.sample(CHALLENGE_POOL, 5)
    for i, challenge in enumerate(challenges):
        challenge['id'] = i + 1
        challenge['completed'] = False  # You can check against user's completed challenges
    
    return challenges

@login_required(login_url="login")
def challenges(request):
    daily_challenges = get_daily_challenges()
    
    context = {
        'daily_challenges': daily_challenges,
        'today_date': date.today().strftime("%B %d, %Y"),
        'completed_today': 0,  # Calculate from user's data
        'total_completed': 0,  # Calculate from user's data
        'points_earned': 0,  # Calculate from user's data
    }
    
    return render(request, "tracker/challenges/challenges.html", context)

@login_required(login_url="login")
def accept_challenge(request, challenge_id):
    # Logic to accept and track challenge
    # Redirect to appropriate page or show modal
    return redirect("challenges")


# ---------------- YOGA DETAILS ----------------
YOGA_DATA = {
    'surya-namaskar': {
        'name': 'Surya Namaskar (Sun Salutation)',
        'duration': 15,
        'difficulty': 'Beginner',
        'calories': 150,
        'image_url': 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=1200&h=600&fit=crop',
        'description': 'Surya Namaskar, or Sun Salutation, is a sequence of 12 powerful yoga poses. It provides a good cardiovascular workout, stretches every part of the body, and when performed at a fast pace, can give you a great workout.',
        'benefits': [
            'Improves blood circulation throughout the body',
            'Strengthens muscles and joints',
            'Improves digestive system functioning',
            'Helps in weight loss and glowing skin',
            'Improves flexibility and posture',
            'Reduces stress and anxiety'
        ],
        'steps': [
            {
                'title': 'Pranamasana (Prayer Pose)',
                'description': 'Stand at the edge of your mat, keep your feet together and balance your weight equally on both feet. Expand your chest and relax your shoulders. As you breathe in, lift both arms up from the sides, and as you exhale, bring your palms together in front of your chest in prayer position.',
                'image': 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500&h=400&fit=crop',
                'image_credit': 'Photo by Kalen Emsley on Unsplash'
            },
            {
                'title': 'Hastauttanasana (Raised Arms Pose)',
                'description': 'Breathing in, lift the arms up and back, keeping the biceps close to the ears. The effort is to stretch the whole body up from the heels to the tips of the fingers. Push the pelvis forward and look up.',
                'image': 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=500&h=400&fit=crop',
                'image_credit': 'Photo by Jared Rice on Unsplash'
            },
            {
                'title': 'Hastapadasana (Standing Forward Bend)',
                'description': 'Breathing out, bend forward from the waist keeping the spine erect. Bring the hands down to the floor beside the feet. If needed, you may bend the knees to bring the palms down to the floor.',
                'image': 'https://images.unsplash.com/photo-1599901860904-17e6ed7083a0?w=500&h=400&fit=crop',
                'image_credit': 'Photo by Dane Wetton on Unsplash'
            },
            {
                'title': 'Ashwa Sanchalanasana (Equestrian Pose)',
                'description': 'Breathing in, push your right leg back as far as possible. Bring the right knee to the floor and look up. The left foot should be exactly in between the palms.',
                'image': 'https://images.unsplash.com/photo-1588286840104-8957b019727f?w=500&h=400&fit=crop',
                'image_credit': 'Photo by Oksana Taran on Unsplash'
            },
            {
                'title': 'Dandasana (Stick Pose)',
                'description': 'As you breathe in, take the left leg back and bring the whole body in a straight line. Keep your arms perpendicular to the floor.',
                'image': 'https://images.unsplash.com/photo-1603988363607-e1e4a66962c6?w=500&h=400&fit=crop',
                'image_credit': 'Photo by Ginny Rose Stewart on Unsplash'
            },
        ],
        'tips': [
            'Practice on an empty stomach, preferably in the morning',
            'Breathe deeply and synchronize your breath with movements',
            'Start slowly and gradually increase the pace',
            'Listen to your body and don\'t push beyond your limits',
            'Maintain proper form rather than speed',
            'Stay hydrated before and after practice'
        ]
    },
    'hatha-yoga': {
        'name': 'Hatha Yoga',
        'duration': 30,
        'difficulty': 'Beginner',
        'calories': 180,
        'image_url': 'https://images.unsplash.com/photo-1545389336-cf090694435e?w=1200&h=600&fit=crop',
        'description': 'Hatha Yoga is a gentle introduction to the most basic yoga postures. It focuses on breathing techniques and meditation, making it perfect for beginners and those seeking stress relief.',
        'benefits': [
            'Reduces stress and promotes relaxation',
            'Improves flexibility and balance',
            'Strengthens core muscles',
            'Enhances mental clarity and focus',
            'Improves breathing and lung capacity',
            'Promotes better sleep quality'
        ],
        'steps': [
            {
                'title': 'Mountain Pose (Tadasana)',
                'description': 'Stand with feet together, arms at sides. Distribute weight evenly through feet. Engage thighs, lift chest, and reach crown of head toward ceiling. Hold for 5-10 breaths.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Child\'s Pose (Balasana)',
                'description': 'Kneel on floor, sit back on heels. Fold forward, extending arms in front. Rest forehead on mat. Breathe deeply and hold for 1-3 minutes.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Cat-Cow Pose (Marjaryasana-Bitilasana)',
                'description': 'Start on hands and knees. Inhale, arch back (cow). Exhale, round spine (cat). Flow between poses for 10 breaths.',
                'image': None,
                'image_credit': ''
            },
        ],
        'tips': [
            'Move slowly and mindfully between poses',
            'Focus on your breath throughout the practice',
            'Use props like blocks or straps if needed',
            'Don\'t compare yourself to others',
            'Practice regularly for best results'
        ]
    },
    'power-yoga': {
        'name': 'Power Yoga',
        'duration': 45,
        'difficulty': 'Advanced',
        'calories': 400,
        'image_url': 'https://images.unsplash.com/photo-1552196563-55cd4e45efb3?w=1200&h=600&fit=crop',
        'description': 'Power Yoga is a vigorous, fitness-based approach to vinyasa-style yoga. It incorporates the athleticism of Ashtanga, including lots of vinyasas (series of poses done in sequence).',
        'benefits': [
            'Builds strength and stamina',
            'Increases flexibility and balance',
            'Burns calories and aids weight loss',
            'Improves cardiovascular health',
            'Enhances mental focus and discipline',
            'Tones muscles throughout the body'
        ],
        'steps': [
            {
                'title': 'Warm-up Flow',
                'description': 'Begin with 5 rounds of Sun Salutation A to warm up the body and prepare for more intense poses.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Warrior Sequence',
                'description': 'Flow through Warrior I, II, and III poses, holding each for 5 breaths. Focus on strength and stability.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Balance Poses',
                'description': 'Practice Tree Pose, Eagle Pose, and Half Moon Pose to challenge your balance and core strength.',
                'image': None,
                'image_credit': ''
            },
        ],
        'tips': [
            'Build up gradually - don\'t rush into advanced poses',
            'Stay hydrated throughout your practice',
            'Use a non-slip yoga mat for safety',
            'Listen to your body and take breaks when needed',
            'Combine with proper nutrition for best results'
        ]
    },
    'yin-yoga': {
        'name': 'Yin Yoga',
        'duration': 60,
        'difficulty': 'Intermediate',
        'calories': 120,
        'image_url': 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=1200&h=600&fit=crop',
        'description': 'Yin Yoga is a slow-paced style where poses are held for longer periods. It targets the deep connective tissues and is meditative in nature.',
        'benefits': [
            'Increases circulation in joints',
            'Improves flexibility in deep tissues',
            'Calms and balances mind and body',
            'Reduces stress and anxiety',
            'Enhances meditation practice',
            'Promotes deep relaxation'
        ],
        'steps': [
            {
                'title': 'Butterfly Pose',
                'description': 'Sit with soles of feet together, knees falling to sides. Fold forward gently. Hold for 3-5 minutes, breathing deeply.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Dragon Pose',
                'description': 'Low lunge position with back knee down. Sink hips forward and down. Hold for 3-5 minutes each side.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Sleeping Swan',
                'description': 'Pigeon pose variation. Fold forward over front leg. Hold for 3-5 minutes each side for deep hip opening.',
                'image': None,
                'image_credit': ''
            },
        ],
        'tips': [
            'Hold poses for 3-5 minutes to target deep tissues',
            'Use props generously for support and comfort',
            'Breathe naturally and deeply',
            'Come out of poses slowly and mindfully',
            'Practice in a quiet, calm environment'
        ]
    }
}

def yoga_detail(request, yoga_type):
    if yoga_type not in YOGA_DATA:
        return redirect('home')
    
    yoga = YOGA_DATA[yoga_type]
    return render(request, "tracker/yoga/yoga_detail.html", {"yoga": yoga})


# ---------------- MEDITATION DETAILS ----------------
MEDITATION_DATA = {
    'mindfulness': {
        'name': 'Mindfulness Meditation',
        'duration': 20,
        'difficulty': 'Beginner',
        'focus': 'Present Moment',
        'image_url': 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=1200&h=600&fit=crop',
        'description': 'Mindfulness meditation involves paying attention to the present moment without judgment. It helps you become more aware of your thoughts, feelings, and sensations.',
        'benefits': [
            'Reduces stress and anxiety',
            'Improves focus and concentration',
            'Enhances emotional regulation',
            'Promotes better sleep',
            'Increases self-awareness',
            'Boosts overall well-being'
        ],
        'steps': [
            {
                'title': 'Find a Comfortable Position',
                'description': 'Sit in a comfortable position with your back straight. You can sit on a chair, cushion, or floor. Rest your hands on your lap or knees.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Focus on Your Breath',
                'description': 'Close your eyes and bring your attention to your breath. Notice the sensation of air entering and leaving your nostrils. Don\'t try to control your breathing.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Observe Your Thoughts',
                'description': 'When thoughts arise, simply acknowledge them without judgment. Imagine them as clouds passing by. Gently return your focus to your breath.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Body Scan',
                'description': 'Slowly scan your body from head to toe, noticing any sensations, tension, or relaxation. Don\'t try to change anything, just observe.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Conclude Mindfully',
                'description': 'After 15-20 minutes, slowly bring your awareness back to your surroundings. Open your eyes gently and take a moment before standing.',
                'image': None,
                'image_credit': ''
            },
        ],
        'tips': [
            'Start with just 5-10 minutes and gradually increase',
            'Practice at the same time each day for consistency',
            'Be patient with yourself - it takes practice',
            'Use guided meditations if you\'re a beginner',
            'Create a dedicated meditation space',
            'Don\'t judge your meditation as good or bad'
        ]
    },
    'breathing': {
        'name': 'Breathing Exercise (Pranayama)',
        'duration': 10,
        'difficulty': 'Beginner',
        'focus': 'Breath Control',
        'image_url': 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=1200&h=600&fit=crop',
        'description': 'Pranayama breathing exercises help control the breath to influence the flow of prana (life energy) in the body. These techniques calm the mind and energize the body.',
        'benefits': [
            'Reduces stress and calms the nervous system',
            'Improves lung capacity and oxygen intake',
            'Enhances mental clarity and focus',
            'Balances emotions and mood',
            'Lowers blood pressure',
            'Improves sleep quality'
        ],
        'steps': [
            {
                'title': '4-7-8 Breathing Technique',
                'description': 'Inhale through your nose for 4 counts, hold your breath for 7 counts, exhale through your mouth for 8 counts. Repeat 4-8 times.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Alternate Nostril Breathing',
                'description': 'Close right nostril, inhale through left. Close left nostril, exhale through right. Inhale through right, close it, exhale through left. Repeat for 5-10 minutes.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Box Breathing',
                'description': 'Inhale for 4 counts, hold for 4 counts, exhale for 4 counts, hold for 4 counts. Visualize tracing a box. Repeat for 5-10 minutes.',
                'image': None,
                'image_credit': ''
            },
        ],
        'tips': [
            'Practice on an empty stomach',
            'Sit in a comfortable, upright position',
            'Breathe through your nose unless instructed otherwise',
            'Don\'t force the breath - keep it natural',
            'Stop if you feel dizzy or uncomfortable',
            'Practice regularly for best results'
        ]
    },
    'body-scan': {
        'name': 'Body Scan Meditation',
        'duration': 25,
        'difficulty': 'Beginner',
        'focus': 'Body Awareness',
        'image_url': 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=1200&h=600&fit=crop',
        'description': 'Body scan meditation involves systematically focusing attention on different parts of the body, promoting relaxation and body awareness.',
        'benefits': [
            'Releases physical tension',
            'Improves body awareness',
            'Promotes deep relaxation',
            'Helps with pain management',
            'Reduces insomnia',
            'Connects mind and body'
        ],
        'steps': [
            {
                'title': 'Lie Down Comfortably',
                'description': 'Lie on your back with arms at your sides, palms facing up. Close your eyes and take a few deep breaths to settle in.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Start with Your Toes',
                'description': 'Bring attention to your toes. Notice any sensations - warmth, coolness, tingling, or nothing at all. Breathe into this area for 30 seconds.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Move Up Gradually',
                'description': 'Slowly move your attention up through feet, ankles, calves, knees, thighs. Spend 30-60 seconds on each body part.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Continue Through Torso and Arms',
                'description': 'Scan through hips, abdomen, chest, back, shoulders, arms, hands, and fingers. Notice sensations without trying to change them.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Finish with Head and Face',
                'description': 'Move attention to neck, jaw, face, and top of head. Take a few full-body breaths before slowly opening your eyes.',
                'image': None,
                'image_credit': ''
            },
        ],
        'tips': [
            'Practice lying down or in a reclined position',
            'Use a guided recording when starting out',
            'Don\'t worry if you fall asleep - it\'s normal',
            'Notice sensations without judging them',
            'Practice before bed for better sleep',
            'Be patient - it gets easier with practice'
        ]
    },
    'guided': {
        'name': 'Guided Meditation',
        'duration': 15,
        'difficulty': 'Beginner',
        'focus': 'Visualization',
        'image_url': 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?w=1200&h=600&fit=crop',
        'description': 'Guided meditation uses visualization and imagery led by a teacher or recording. It\'s perfect for beginners and helps achieve specific goals like relaxation or confidence.',
        'benefits': [
            'Easy for beginners to follow',
            'Reduces stress and anxiety quickly',
            'Improves visualization skills',
            'Enhances creativity',
            'Promotes positive thinking',
            'Helps achieve specific goals'
        ],
        'steps': [
            {
                'title': 'Choose Your Focus',
                'description': 'Select a guided meditation based on your goal - relaxation, sleep, confidence, healing, etc. Find a quiet space and get comfortable.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Follow the Voice',
                'description': 'Listen to the guide\'s voice and follow their instructions. They will lead you through breathing, relaxation, and visualization.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Engage Your Imagination',
                'description': 'Actively visualize the scenes and scenarios described. Use all your senses - see, hear, feel, smell, and taste in your imagination.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Stay Present',
                'description': 'If your mind wanders, gently bring it back to the guide\'s voice. Don\'t judge yourself - wandering is normal.',
                'image': None,
                'image_credit': ''
            },
            {
                'title': 'Transition Slowly',
                'description': 'When the meditation ends, take your time returning to normal awareness. Stretch gently and open your eyes slowly.',
                'image': None,
                'image_credit': ''
            },
        ],
        'tips': [
            'Use headphones for better immersion',
            'Try different guides to find your favorite',
            'Practice at the same time daily',
            'Start with shorter sessions (5-10 minutes)',
            'Create a comfortable meditation space',
            'Be open to the experience without expectations'
        ]
    }
}

def meditation_detail(request, meditation_type):
    if meditation_type not in MEDITATION_DATA:
        return redirect('home')
    
    meditation = MEDITATION_DATA[meditation_type]
    return render(request, "tracker/meditation/meditation_detail.html", {"meditation": meditation})


# ---------------- WORKOUT PLANS ----------------
def workout_plans(request):
    return render(request, "tracker/plans/workout_plans.html")

# ---------------- POINTS PAGE ----------------
@login_required(login_url="login")
def points(request):
    profile = UserProfile.objects.get(user=request.user)
    return render(request, "tracker/points/points.html", {"profile": profile})


# ---------------- WORKOUT DETAILS ----------------
WORKOUT_DATA = {
    'burpees': {
        'name': 'Burpees',
        'duration': 15,
        'difficulty': 'High',
        'calories': 150,
        'image_url': 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=1200&h=600&fit=crop',
        'description': 'Burpees are a full-body exercise that combines a squat, plank, and jump. This high-intensity movement works multiple muscle groups simultaneously and is excellent for building strength and cardiovascular endurance.',
        'benefits': [
            'Burns calories quickly and efficiently',
            'Strengthens entire body including legs, core, chest, and arms',
            'Improves cardiovascular fitness',
            'Requires no equipment',
            'Can be done anywhere',
            'Boosts metabolism for hours after workout'
        ],
        'steps': [
            {'title': 'Starting Position', 'description': 'Stand with feet shoulder-width apart, arms at your sides.'},
            {'title': 'Squat Down', 'description': 'Lower into a squat position and place your hands on the floor in front of you.'},
            {'title': 'Jump Back', 'description': 'Jump your feet back to land in a plank position with arms extended.'},
            {'title': 'Push-up (Optional)', 'description': 'Perform a push-up, keeping your body in a straight line.'},
            {'title': 'Jump Forward', 'description': 'Jump your feet back to the squat position.'},
            {'title': 'Explosive Jump', 'description': 'Jump up explosively with arms reaching overhead.'},
            {'title': 'Repeat', 'description': 'Land softly and immediately begin the next repetition.'}
        ],
        'tips': [
            'Keep your core engaged throughout the movement',
            'Land softly to protect your joints',
            'Maintain proper form even when tired',
            'Start with modified versions if needed',
            'Breathe consistently - exhale on exertion'
        ]
    },
    'lunges': {
        'name': 'Lunges',
        'duration': 10,
        'difficulty': 'Medium',
        'calories': 80,
        'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200&h=600&fit=crop',
        'description': 'Lunges are a fundamental lower body exercise that targets the quadriceps, hamstrings, and glutes. They also improve balance, coordination, and core stability.',
        'benefits': [
            'Strengthens legs and glutes',
            'Improves balance and stability',
            'Enhances hip flexibility',
            'Corrects muscle imbalances',
            'Functional movement for daily activities',
            'Can be done with or without weights'
        ],
        'steps': [
            {'title': 'Starting Position', 'description': 'Stand tall with feet hip-width apart, hands on hips or at sides.'},
            {'title': 'Step Forward', 'description': 'Take a large step forward with your right foot.'},
            {'title': 'Lower Down', 'description': 'Bend both knees to 90 degrees, lowering your back knee toward the floor.'},
            {'title': 'Check Alignment', 'description': 'Front knee should be directly above ankle, not past toes.'},
            {'title': 'Push Back', 'description': 'Push through your front heel to return to starting position.'},
            {'title': 'Alternate Legs', 'description': 'Repeat with the left leg. Continue alternating.'}
        ],
        'tips': [
            'Keep your torso upright throughout the movement',
            'Don\'t let your front knee go past your toes',
            'Engage your core for better balance',
            'Take a big enough step to maintain proper form',
            'Look straight ahead, not down'
        ]
    },
    'mountain-climbers': {
        'name': 'Mountain Climbers',
        'duration': 10,
        'difficulty': 'High',
        'calories': 120,
        'image_url': 'https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=1200&h=600&fit=crop',
        'description': 'Mountain climbers are a dynamic exercise that combines cardio and strength training. This movement engages your core, shoulders, and legs while elevating your heart rate.',
        'benefits': [
            'Excellent cardiovascular workout',
            'Strengthens core muscles',
            'Improves agility and coordination',
            'Burns calories rapidly',
            'Enhances shoulder stability',
            'Increases hip flexibility'
        ],
        'steps': [
            {'title': 'Plank Position', 'description': 'Start in a high plank position with hands under shoulders.'},
            {'title': 'Engage Core', 'description': 'Keep your body in a straight line from head to heels.'},
            {'title': 'Drive Knee', 'description': 'Bring your right knee toward your chest.'},
            {'title': 'Quick Switch', 'description': 'Quickly switch legs, bringing left knee forward as right leg goes back.'},
            {'title': 'Maintain Pace', 'description': 'Continue alternating legs in a running motion.'},
            {'title': 'Keep Form', 'description': 'Maintain plank position throughout the exercise.'}
        ],
        'tips': [
            'Keep hips level - don\'t let them pike up',
            'Maintain a steady breathing rhythm',
            'Start slow and build up speed',
            'Keep shoulders directly over wrists',
            'Engage your core to protect your back'
        ]
    },
    'squats': {
        'name': 'Squats',
        'duration': 10,
        'difficulty': 'Medium',
        'calories': 90,
        'image_url': 'https://images.unsplash.com/photo-1574680096145-d05b474e2155?w=1200&h=600&fit=crop',
        'description': 'Squats are one of the most effective lower body exercises. They target the quadriceps, hamstrings, glutes, and core while improving overall strength and mobility.',
        'benefits': [
            'Builds leg and glute strength',
            'Improves core stability',
            'Enhances mobility and flexibility',
            'Functional movement for daily life',
            'Increases bone density',
            'Boosts athletic performance'
        ],
        'steps': [
            {'title': 'Starting Position', 'description': 'Stand with feet shoulder-width apart, toes slightly pointed out.'},
            {'title': 'Engage Core', 'description': 'Tighten your core and keep chest up.'},
            {'title': 'Lower Down', 'description': 'Bend knees and hips, lowering as if sitting in a chair.'},
            {'title': 'Depth', 'description': 'Lower until thighs are parallel to floor or as low as comfortable.'},
            {'title': 'Drive Up', 'description': 'Push through heels to return to starting position.'},
            {'title': 'Repeat', 'description': 'Maintain form throughout all repetitions.'}
        ],
        'tips': [
            'Keep your weight in your heels',
            'Don\'t let knees cave inward',
            'Keep chest up and back straight',
            'Go as deep as your mobility allows',
            'Breathe in going down, out coming up'
        ]
    },
    'push-ups': {
        'name': 'Push-ups',
        'duration': 10,
        'difficulty': 'Medium',
        'calories': 70,
        'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200&h=600&fit=crop',
        'description': 'Push-ups are a classic upper body exercise that builds strength in the chest, shoulders, triceps, and core. They require no equipment and can be modified for any fitness level.',
        'benefits': [
            'Strengthens chest, shoulders, and triceps',
            'Builds core stability',
            'Improves posture',
            'Increases functional strength',
            'Can be done anywhere',
            'Multiple variations available'
        ],
        'steps': [
            {'title': 'Starting Position', 'description': 'Start in a high plank with hands slightly wider than shoulders.'},
            {'title': 'Body Alignment', 'description': 'Keep body in a straight line from head to heels.'},
            {'title': 'Lower Down', 'description': 'Bend elbows to lower chest toward the floor.'},
            {'title': 'Bottom Position', 'description': 'Lower until chest nearly touches the floor.'},
            {'title': 'Push Up', 'description': 'Press through palms to return to starting position.'},
            {'title': 'Repeat', 'description': 'Maintain proper form throughout all reps.'}
        ],
        'tips': [
            'Keep elbows at 45-degree angle from body',
            'Don\'t let hips sag or pike up',
            'Engage your core throughout',
            'Look slightly ahead, not straight down',
            'Modify on knees if needed'
        ]
    },
    'plank': {
        'name': 'Plank',
        'duration': 5,
        'difficulty': 'Medium',
        'calories': 50,
        'image_url': 'https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1200&h=600&fit=crop',
        'description': 'The plank is an isometric core exercise that builds strength and endurance in the abs, back, and stabilizer muscles. It\'s one of the best exercises for developing core stability.',
        'benefits': [
            'Strengthens entire core',
            'Improves posture',
            'Reduces back pain',
            'Enhances balance and stability',
            'Increases flexibility',
            'Boosts metabolism'
        ],
        'steps': [
            {'title': 'Starting Position', 'description': 'Begin in a forearm plank position with elbows under shoulders.'},
            {'title': 'Body Alignment', 'description': 'Form a straight line from head to heels.'},
            {'title': 'Engage Core', 'description': 'Tighten your abs and squeeze your glutes.'},
            {'title': 'Hold Position', 'description': 'Maintain the position without letting hips sag or rise.'},
            {'title': 'Breathe', 'description': 'Breathe steadily throughout the hold.'},
            {'title': 'Release', 'description': 'Lower to the floor when time is complete.'}
        ],
        'tips': [
            'Don\'t hold your breath - breathe normally',
            'Keep neck neutral - don\'t look up',
            'Squeeze glutes to protect lower back',
            'Start with shorter holds and build up',
            'Focus on quality over duration'
        ]
    }
}

def workout_detail(request, workout_type):
    if workout_type not in WORKOUT_DATA:
        return redirect('home')
    
    workout = WORKOUT_DATA[workout_type]
    return render(request, "tracker/workouts/workout_detail.html", {"workout": workout})

import datetime
from django.http import Http404

@login_required(login_url="login")
def progress_day_detail(request, day):
    # day comes like "2026-02-14"
    try:
        d = datetime.date.fromisoformat(day)
    except ValueError:
        raise Http404("Invalid date")

    record = SessionRecord.objects.filter(user=request.user, date=d).first()
    if not record:
        raise Http404("No session for this date")

    return render(request, "tracker/progress/day_detail.html", {"record": record})
