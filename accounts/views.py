from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.http import JsonResponse
from .models import UserProfile, LoginAttempt
from datetime import timedelta
import re

# ============================================
# Email Validation Helper Functions
# ============================================

ALLOWED_DOMAINS = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']
ALLOWED_COUNTRY_DOMAINS = ['.com.np']

BLOCKED_PREFIXES = [
    'test', 'tes', 'admin', 'administrator', 'root', 'user', 'demo',
    'sample', 'example', 'temp', 'tmp', 'fake', 'dummy', 'null',
    'undefined', 'anonymous', 'guest', 'support', 'info', 'contact',
    'noreply', 'no-reply', 'mailer', 'postmaster', 'webmaster'
]

def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def is_valid_email_domain(email):
    """Check if email domain is allowed"""
    if '@' not in email:
        return False, "Invalid email format"
    
    domain = email.split('@')[1].lower()
    
    if domain in ALLOWED_DOMAINS:
        return True, ""
    
    for country_domain in ALLOWED_COUNTRY_DOMAINS:
        if domain.endswith(country_domain):
            return True, ""
    
    supported = ', '.join([f'@{d}' for d in ALLOWED_DOMAINS] + [f'@*{d}' for d in ALLOWED_COUNTRY_DOMAINS])
    return False, f"We currently support only: {supported}"

def is_blocked_email_prefix(email):
    """Check if email prefix is blocked"""
    if '@' not in email:
        return True, "Invalid email format"
    
    prefix = email.split('@')[0].lower()
    
    for blocked in BLOCKED_PREFIXES:
        if prefix == blocked or prefix.startswith(blocked):
            return True, f"Email addresses starting with '{blocked}' are not allowed"
    
    return False, ""

def is_numeric_only_prefix(email):
    """Check if email prefix contains only numbers"""
    if '@' not in email:
        return True, "Invalid email format"
    
    prefix = email.split('@')[0]
    
    if prefix.isdigit():
        return True, "Email addresses with only numbers are not allowed"
    
    if re.match(r'^\d{4,}', prefix):
        return True, "Email addresses starting with long number sequences are not allowed"
    
    return False, ""

def is_valid_email_format(email):
    """Comprehensive email format validation"""
    email_regex = r'^[a-zA-Z][a-zA-Z0-9._-]*[a-zA-Z0-9]@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if len(email) < 6:
        return False, "Email is too short"
    
    if not re.match(email_regex, email):
        return False, "Invalid email format. Email must start with a letter and contain valid characters"
    
    return True, ""

def validate_email_complete(email):
    """Complete email validation"""
    email = email.lower().strip()
    
    valid, msg = is_valid_email_format(email)
    if not valid:
        return False, msg
    
    valid, msg = is_valid_email_domain(email)
    if not valid:
        return False, msg
    
    blocked, msg = is_blocked_email_prefix(email)
    if blocked:
        return False, msg
    
    numeric, msg = is_numeric_only_prefix(email)
    if numeric:
        return False, msg
    
    return True, ""

def validate_password(password, confirm_password=None):
    """Validate password strength"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    if confirm_password and password != confirm_password:
        return False, "Passwords do not match"
    
    return True, ""

# ============================================
# Rate Limiting Functions
# ============================================

def get_lockout_duration(failed_attempts):
    """Calculate lockout duration based on failed attempts"""
    if failed_attempts < 5:
        return 0
    
    lockout_multiplier = (failed_attempts - 1) // 5
    return lockout_multiplier * 5

def check_rate_limit(email, ip_address):
    """Check if user is rate limited"""
    now = timezone.now()
    
    one_hour_ago = now - timedelta(hours=1)
    failed_attempts = LoginAttempt.objects.filter(
        email=email.lower(),
        was_successful=False,
        attempt_time__gte=one_hour_ago
    ).count()
    
    if failed_attempts < 5:
        return True, "", failed_attempts
    
    last_attempt = LoginAttempt.objects.filter(
        email=email.lower(),
        was_successful=False
    ).first()
    
    if not last_attempt:
        return True, "", 0
    
    lockout_minutes = get_lockout_duration(failed_attempts)
    lockout_end = last_attempt.attempt_time + timedelta(minutes=lockout_minutes)
    
    if now < lockout_end:
        remaining = lockout_end - now
        remaining_minutes = int(remaining.total_seconds() // 60) + 1
        return False, f"Too many failed attempts. Please try again in {remaining_minutes} minute(s)", failed_attempts
    
    return True, "", failed_attempts

def record_login_attempt(email, ip_address, was_successful):
    """Record a login attempt"""
    LoginAttempt.objects.create(
        email=email.lower(),
        ip_address=ip_address,
        was_successful=was_successful
    )
    
    if was_successful:
        LoginAttempt.objects.filter(
            email=email.lower(),
            was_successful=False
        ).delete()

# ============================================
# Helper to check if request is AJAX
# ============================================

def is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

# ============================================
# Views
# ============================================

def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        if is_ajax(request):
            return JsonResponse({'success': True, 'redirect': '/dashboard/'})
        return redirect('dashboard_view')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me') == 'on'
        
        ip_address = get_client_ip(request)
        
        # Validate inputs
        if not email or not password:
            if is_ajax(request):
                return JsonResponse({'success': False, 'message': 'Please fill in all fields', 'type': 'error'})
            return render(request, 'Auth/login.html', {'toast_message': 'Please fill in all fields', 'toast_type': 'error'})
        
        # Check rate limiting
        allowed, message, failed_count = check_rate_limit(email, ip_address)
        if not allowed:
            if is_ajax(request):
                return JsonResponse({'success': False, 'message': message, 'type': 'error'})
            return render(request, 'Auth/login.html', {'toast_message': message, 'toast_type': 'error'})
        
        # Try to get user by email
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username
        except User.DoesNotExist:
            record_login_attempt(email, ip_address, False)
            remaining = 5 - (failed_count + 1)
            if remaining > 0:
                msg = f'Invalid email or password. {remaining} attempts remaining'
            else:
                msg = 'Too many failed attempts. Please try again in 5 minutes'
            
            if is_ajax(request):
                return JsonResponse({'success': False, 'message': msg, 'type': 'error'})
            return render(request, 'Auth/login.html', {'toast_message': msg, 'toast_type': 'error'})
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            record_login_attempt(email, ip_address, True)
            login(request, user)
            
            if not remember_me:
                request.session.set_expiry(0)
            else:
                request.session.set_expiry(60 * 60 * 24 * 30)
            
            if is_ajax(request):
                return JsonResponse({'success': True, 'redirect': '/dashboard/'})
            return redirect('dashboard_view')
        else:
            record_login_attempt(email, ip_address, False)
            remaining = 5 - ((failed_count + 1) % 5)
            if remaining == 0:
                remaining = 5
            
            if (failed_count + 1) >= 5 and (failed_count + 1) % 5 == 0:
                lockout_mins = get_lockout_duration(failed_count + 1)
                msg = f'Too many failed attempts. Please try again in {lockout_mins} minutes'
            else:
                msg = f'Invalid email or password. {remaining} attempts remaining before lockout'
            
            if is_ajax(request):
                return JsonResponse({'success': False, 'message': msg, 'type': 'error'})
            return render(request, 'Auth/login.html', {'toast_message': msg, 'toast_type': 'error'})
    
    return render(request, 'Auth/login.html', {'toast_message': None, 'toast_type': None})


def register_view(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        if is_ajax(request):
            return JsonResponse({'success': True, 'redirect': '/dashboard/'})
        return redirect('dashboard_view')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        profile_image = request.FILES.get('profile_image')
        
        # Validate required fields
        if not all([first_name, last_name, email, password, confirm_password]):
            if is_ajax(request):
                return JsonResponse({'success': False, 'message': 'Please fill in all required fields', 'type': 'error'})
            return render(request, 'Auth/register.html', {'toast_message': 'Please fill in all required fields', 'toast_type': 'error'})
        
        # Validate names
        if len(first_name) < 2:
            if is_ajax(request):
                return JsonResponse({'success': False, 'message': 'First name must be at least 2 characters', 'type': 'error'})
            return render(request, 'Auth/register.html', {'toast_message': 'First name must be at least 2 characters', 'toast_type': 'error'})
        
        if len(last_name) < 2:
            if is_ajax(request):
                return JsonResponse({'success': False, 'message': 'Last name must be at least 2 characters', 'type': 'error'})
            return render(request, 'Auth/register.html', {'toast_message': 'Last name must be at least 2 characters', 'toast_type': 'error'})
        
        if not first_name.replace(' ', '').isalpha():
            if is_ajax(request):
                return JsonResponse({'success': False, 'message': 'First name should only contain letters', 'type': 'error'})
            return render(request, 'Auth/register.html', {'toast_message': 'First name should only contain letters', 'toast_type': 'error'})
        
        if not last_name.replace(' ', '').isalpha():
            if is_ajax(request):
                return JsonResponse({'success': False, 'message': 'Last name should only contain letters', 'type': 'error'})
            return render(request, 'Auth/register.html', {'toast_message': 'Last name should only contain letters', 'toast_type': 'error'})
        
        # Validate email
        valid, msg = validate_email_complete(email)
        if not valid:
            if is_ajax(request):
                return JsonResponse({'success': False, 'message': msg, 'type': 'error'})
            return render(request, 'Auth/register.html', {'toast_message': msg, 'toast_type': 'error'})
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            if is_ajax(request):
                return JsonResponse({'success': False, 'message': 'An account with this email already exists', 'type': 'error'})
            return render(request, 'Auth/register.html', {'toast_message': 'An account with this email already exists', 'toast_type': 'error'})
        
        # Validate password
        valid, msg = validate_password(password, confirm_password)
        if not valid:
            if is_ajax(request):
                return JsonResponse({'success': False, 'message': msg, 'type': 'error'})
            return render(request, 'Auth/register.html', {'toast_message': msg, 'toast_type': 'error'})
        
        # Validate profile image if provided
        if profile_image:
            allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
            if profile_image.content_type not in allowed_types:
                if is_ajax(request):
                    return JsonResponse({'success': False, 'message': 'Profile image must be JPEG, PNG, GIF, or WebP', 'type': 'error'})
                return render(request, 'Auth/register.html', {'toast_message': 'Profile image must be JPEG, PNG, GIF, or WebP', 'toast_type': 'error'})
            
            max_size = 5 * 1024 * 1024
            if profile_image.size > max_size:
                if is_ajax(request):
                    return JsonResponse({'success': False, 'message': 'Profile image must be less than 5MB', 'type': 'error'})
                return render(request, 'Auth/register.html', {'toast_message': 'Profile image must be less than 5MB', 'toast_type': 'error'})
        
        try:
            # Create username from email
            username = email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            # Create profile
            profile = UserProfile.objects.create(user=user)
            
            # Save profile image if provided
            if profile_image:
                profile.profile_image = profile_image
                profile.save()
            
            # Log the user in
            login(request, user)
            
            if is_ajax(request):
                return JsonResponse({'success': True, 'redirect': '/dashboard/'})
            return redirect('dashboard_view')
            
        except Exception as e:
            if is_ajax(request):
                return JsonResponse({'success': False, 'message': 'An error occurred. Please try again', 'type': 'error'})
            return render(request, 'Auth/register.html', {'toast_message': 'An error occurred. Please try again', 'toast_type': 'error'})
    
    return render(request, 'Auth/register.html', {'toast_message': None, 'toast_type': None})


def logout_view(request):
    """Handle user logout"""
    logout(request)
    return redirect('accounts:login')