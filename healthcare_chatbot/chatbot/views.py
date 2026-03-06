import json
import re
import math
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

from .models import UserProfile, ChatHistory
from .ml_engine import predict_disease, parse_symptoms_from_text
from .language_translations import get_translation

# ... (previous healthcare facilities database code stays the same)

HEALTHCARE_FACILITIES = [
    # ... (all hospital data from previous version)
]

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two coordinates in kilometers using Haversine formula"""
    R = 6371
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))
    distance = R * c
    
    return round(distance, 2)


def validate_email(email):
    """Validate email format"""
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return False, "Invalid email format."
    return True, ""


def validate_password(password):
    """Validate password strength"""
    errors = []
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain uppercase letter.")
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain lowercase letter.")
    if not re.search(r'[0-9]', password):
        errors.append("Password must contain number.")
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};:\'",.<>?/\\|`~]', password):
        errors.append("Password must contain special character.")
    
    return (False, errors) if errors else (True, [])


# ─────────────────────────────────────────────
#  AUTH VIEWS
# ─────────────────────────────────────────────

def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not first_name:
            messages.error(request, 'First name is required.')
            return render(request, 'chatbot/register.html')

        if not last_name:
            messages.error(request, 'Last name is required.')
            return render(request, 'chatbot/register.html')

        if not username or not re.match(r'^[a-zA-Z0-9_]{3,}$', username):
            messages.error(request, 'Username must be 3+ characters.')
            return render(request, 'chatbot/register.html')

        is_valid_email, email_error = validate_email(email)
        if not is_valid_email:
            messages.error(request, email_error)
            return render(request, 'chatbot/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'chatbot/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'chatbot/register.html')

        is_strong_password, password_errors = validate_password(password)
        if not is_strong_password:
            for error in password_errors:
                messages.error(request, error)
            return render(request, 'chatbot/register.html')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'chatbot/register.html')

        if mobile and not re.match(r'^[0-9]{10,}$', mobile):
            messages.error(request, 'Invalid mobile number.')
            return render(request, 'chatbot/register.html')

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            UserProfile.objects.create(user=user, mobile=mobile)
            login(request, user)
            messages.success(request, f'Welcome {first_name}!')
            return redirect('home')
        except Exception:
            messages.error(request, 'Registration error.')
            return render(request, 'chatbot/register.html')

    return render(request, 'chatbot/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Username and password required.')
            return render(request, 'chatbot/login.html')
        
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            return redirect('home')
        messages.error(request, 'Invalid credentials.')
    return render(request, 'chatbot/login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('login')


# ─────────────────────────────────────────────
#  MAIN PAGES
# ─────────────────────────────────────────────

@login_required
def home_view(request):
    return render(request, 'chatbot/home.html')


@login_required
def nearby_hospitals_view(request):
    return render(request, 'chatbot/nearby_hospitals.html')


@login_required
def services_view(request):
    return render(request, 'chatbot/services.html')


@login_required
def contact_view(request):
    return render(request, 'chatbot/contact.html')


@login_required
def chat_view(request):
    history = ChatHistory.objects.filter(user=request.user).order_by('timestamp')
    return render(request, 'chatbot/chat.html', {'history': history})


# ─────────────────────────────────────────────
#  API ENDPOINTS
# ─────────────────────────────────────────────

@login_required
@csrf_exempt
def nearby_hospitals_api(request):
    """API endpoint to fetch nearby hospitals and clinics"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        user_lat = float(data.get('latitude'))
        user_lng = float(data.get('longitude'))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid coordinates'}, status=400)

    facilities_with_distance = []
    for facility in HEALTHCARE_FACILITIES:
        distance = calculate_distance(user_lat, user_lng, facility['lat'], facility['lng'])
        facilities_with_distance.append({**facility, 'distance': distance})

    nearby_facilities = sorted(facilities_with_distance, key=lambda x: x['distance'])[:20]

    return JsonResponse({
        'user_location': {'latitude': user_lat, 'longitude': user_lng},
        'facilities': nearby_facilities,
        'count': len(nearby_facilities)
    })


@login_required
@csrf_exempt
def chat_api(request):
    """Chat API with language support"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        language = data.get('language', 'english').lower()
    except Exception:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if not user_message:
        return JsonResponse({'response': 'Please enter a message.'})

    response_text, disease_data = process_chat_message(user_message, request.user, language)

    ChatHistory.objects.create(
        user=request.user,
        message=user_message,
        response=response_text,
    )

    return JsonResponse({
        'response': response_text,
        'disease': disease_data,
    })


def process_chat_message(message: str, user, language='english'):
    """Process user message with language support"""
    msg_lower = message.lower()
    
    # Greeting
    greetings = ['hi', 'hello', 'hey', 'हेलो', 'नमस्ते', 'नमस्कार', 'हिंदी में', 'ಹಲೋ', 'నమస్కారం', 'வணக்கம்']
    if any(g in msg_lower for g in greetings):
        response = get_translation(language, 'greeting', name=user.first_name or user.username)
        return response, None

    # Help
    if 'help' in msg_lower or 'what can you do' in msg_lower:
        response = get_translation(language, 'help_response')
        return response, None

    # Appointment
    if 'appointment' in msg_lower or 'book' in msg_lower:
        response = get_translation(language, 'appointment_info')
        return response, None

    # Hospital
    if 'hospital' in msg_lower or 'clinic' in msg_lower:
        response = get_translation(language, 'hospital_info')
        return response, None

    # Thank you
    if 'thank' in msg_lower:
        response = get_translation(language, 'thank_you')
        return response, None

    # Symptom analysis
    symptoms = parse_symptoms_from_text(message)

    if not symptoms:
        response = get_translation(language, 'no_symptoms')
        return response, None

    result = predict_disease(symptoms)

    if not result:
        response = get_translation(language, 'no_match')
        return response, None

    # Build disease response in selected language
    severity_icon = get_translation(language, 'disease_severity_major') if result['severity'] == 'Major' else get_translation(language, 'disease_severity_minor')
    severity_text = get_translation(language, 'severity_text')
    precautions_text = get_translation(language, 'precautions_text')
    disclaimer = get_translation(language, 'disclaimer')
    based_on = get_translation(language, 'based_on', symptoms=", ".join(result['matched_symptoms']))
    
    prec_list = "\n".join(f"  • {p}" for p in result['precautions'])
    
    response = (
        f"{based_on}\n\n"
        f"**{result['name']}** {severity_icon}\n\n"
        f"{result['description']}\n\n"
        f"{severity_text} {result['severity']}\n\n"
        f"{precautions_text}\n{prec_list}\n\n"
        f"{disclaimer}"
    )

    return response, result