from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.http import JsonResponse
from datetime import datetime, timedelta
from decimal import Decimal


@login_required(login_url='/401/')
def dashboard_view(request):
    user = request.user
    profile = None
    
    # Get user profile if exists
    if hasattr(user, 'profile'):
        profile = user.profile
    
    # Get first letter of first name for avatar fallback
    first_letter = user.first_name[0].upper() if user.first_name else user.email[0].upper()
    
    # Get full name
    full_name = f"{user.first_name} {user.last_name}".strip()
    if not full_name:
        full_name = user.email.split('@')[0]
    
    # Sample data - replace with actual model queries
    available_balance = 2000
    todays_expenses = 150
    
    # Weekly expenses (Sunday to Saturday)
    weekly_expenses = [
        {'day': 'Sunday', 'short': 'Sun', 'amount': 120},
        {'day': 'Monday', 'short': 'Mon', 'amount': 85},
        {'day': 'Tuesday', 'short': 'Tue', 'amount': 200},
        {'day': 'Wednesday', 'short': 'Wed', 'amount': 45},
        {'day': 'Thursday', 'short': 'Thu', 'amount': 150},
        {'day': 'Friday', 'short': 'Fri', 'amount': 300},
        {'day': 'Saturday', 'short': 'Sat', 'amount': 75},
    ]
    
    # Calculate max for progress bars
    max_expense = max(exp['amount'] for exp in weekly_expenses) if weekly_expenses else 1
    for exp in weekly_expenses:
        exp['percentage'] = (exp['amount'] / max_expense) * 100
    
    context = {
        'user': user,
        'profile': profile,
        'first_letter': first_letter,
        'full_name': full_name,
        'available_balance': available_balance,
        'todays_expenses': todays_expenses,
        'weekly_expenses': weekly_expenses,
    }
    
    return render(request, 'Main/dashboard.html', context)