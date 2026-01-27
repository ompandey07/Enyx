from .models import UserBalance , ExpenseBlock, ExpenseItem , UserIncome , UserGoal , UserKeep
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta, datetime
from decimal import Decimal, InvalidOperation
from decimal import Decimal, InvalidOperation
from bleach.css_sanitizer import CSSSanitizer
from django.contrib.auth import logout
from django.http import JsonResponse
from django.db.models import Sum
from django.db import models
import bleach

# ============================================
# Helper function
# ============================================
def is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


# ============================================
# Dashboard View
# ============================================
@login_required(login_url='/401/')
def dashboard_view(request):
    user = request.user
    profile = None

    if hasattr(user, 'profile'):
        profile = user.profile

    first_letter = user.first_name[0].upper() if user.first_name else user.email[0].upper()

    full_name = f"{user.first_name} {user.last_name}".strip()
    if not full_name:
        full_name = user.email.split('@')[0]

    # Get total available balance from UserBalance model
    total_balance = UserBalance.objects.filter(
        user=user, 
        status='active'
    ).aggregate(total=models.Sum('available_balance'))['total'] or Decimal('0.00')

    # Get total income
    total_income = UserIncome.objects.filter(
        user=user
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    # Get this month's income
    today = date.today()
    first_day_of_month = today.replace(day=1)
    monthly_income = UserIncome.objects.filter(
        user=user,
        created_at__date__gte=first_day_of_month,
        created_at__date__lte=today
    ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    # Get income breakdown by source for chart
    income_breakdown = UserIncome.objects.filter(
        user=user
    ).values('income_source').annotate(
        total=models.Sum('amount')
    ).order_by('-total')[:5]  # Top 5 sources

    income_labels = []
    income_values = []
    
    income_source_display = dict(UserIncome.INCOME_SOURCE_CHOICES)
    for item in income_breakdown:
        source = item['income_source']
        income_labels.append(income_source_display.get(source, source.capitalize()))
        income_values.append(float(item['total']))

    today_day_name = get_day_name(today)
    
    # Get current active expense block
    active_block = ExpenseBlock.objects.filter(
        user=user,
        status='active',
        start_date__lte=today,
        end_date__gte=today
    ).first()
    
    # Get today's expenses
    todays_expenses = Decimal('0.00')
    weekly_expenses_data = {
        'sunday': Decimal('0.00'),
        'monday': Decimal('0.00'),
        'tuesday': Decimal('0.00'),
        'wednesday': Decimal('0.00'),
        'thursday': Decimal('0.00'),
        'friday': Decimal('0.00'),
        'saturday': Decimal('0.00'),
    }
    
    total_weekly_expense = Decimal('0.00')
    
    if active_block:
        # Get today's expenses from active block
        todays_expenses = ExpenseItem.objects.filter(
            expense_block=active_block,
            expense_date=today
        ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
        
        # Get weekly expenses grouped by day
        weekly_items = ExpenseItem.objects.filter(
            expense_block=active_block
        ).values('expense_day').annotate(
            total=models.Sum('amount')
        )
        
        for item in weekly_items:
            day = item['expense_day']
            if day in weekly_expenses_data:
                weekly_expenses_data[day] = item['total']
        
        total_weekly_expense = active_block.total_expense
    
    # Prepare weekly expenses for template (ordered Sunday to Saturday)
    day_order = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
    day_labels = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    day_full_labels = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    weekly_amounts = []
    
    for i, day in enumerate(day_order):
        amount = weekly_expenses_data[day]
        weekly_amounts.append(float(amount))
    
    # Get balance breakdown by income method for chart
    balance_breakdown = UserBalance.objects.filter(
        user=user,
        status='active'
    ).values('income_method').annotate(
        total=models.Sum('available_balance')
    )
    
    balance_labels = []
    balance_values = []
    
    for item in balance_breakdown:
        method = item['income_method']
        balance_labels.append(method.capitalize())
        balance_values.append(float(item['total']))

    # ============================================
    # GOALS DATA
    # ============================================
    
    # Get all user goals
    all_goals = UserGoal.objects.filter(user=user).prefetch_related('balance_accounts')
    
    # Update status for overdue goals
    for goal in all_goals.filter(status__in=['new', 'running']):
        if goal.deadline < today:
            if goal.get_achievement_rate() >= 100:
                goal.status = 'completed'
            else:
                goal.status = 'failed'
            goal.save(update_fields=['status', 'updated_at'])
    
    # Refresh queryset after status updates
    all_goals = UserGoal.objects.filter(user=user).prefetch_related('balance_accounts')
    
    # Goals statistics
    total_goals = all_goals.count()
    active_goals = all_goals.filter(status__in=['new', 'running'])
    active_goals_count = active_goals.count()
    completed_goals_count = all_goals.filter(status='completed').count()
    failed_goals_count = all_goals.filter(status='failed').count()
    
    # Goals status distribution for chart
    goals_status_labels = []
    goals_status_values = []
    goals_status_colors = []
    
    status_data = [
        ('new', 'New', '#6366f1', all_goals.filter(status='new').count()),
        ('running', 'Running', '#f59e0b', all_goals.filter(status='running').count()),
        ('completed', 'Completed', '#10b981', completed_goals_count),
        ('failed', 'Failed', '#ef4444', failed_goals_count),
    ]
    
    for status_key, status_label, color, count in status_data:
        if count > 0:
            goals_status_labels.append(status_label)
            goals_status_values.append(count)
            goals_status_colors.append(color)
    
    # Active goals progress data for chart
    goals_progress_labels = []
    goals_progress_values = []
    goals_target_values = []
    goals_current_values = []
    
    # Get top 5 active goals for progress chart
    top_active_goals = active_goals.order_by('-created_at')[:5]
    
    for goal in top_active_goals:
        # Truncate title if too long
        title = goal.title[:20] + '...' if len(goal.title) > 20 else goal.title
        goals_progress_labels.append(title)
        goals_progress_values.append(float(goal.get_achievement_rate()))
        goals_target_values.append(float(goal.target_amount))
        goals_current_values.append(float(goal.get_current_savings()))
    
    # Calculate total goals target and current savings
    total_goals_target = sum(float(g.target_amount) for g in active_goals)
    total_goals_savings = sum(float(g.get_current_savings()) for g in active_goals)
    
    # Overall goals achievement rate
    if total_goals_target > 0:
        overall_goals_rate = min(100, (total_goals_savings / total_goals_target) * 100)
    else:
        overall_goals_rate = 0
    
    # Get nearest deadline goal
    nearest_goal = active_goals.order_by('deadline').first()
    
    # Goals prediction summary
    on_track_count = sum(1 for g in active_goals if g.get_status_prediction() == 'on_track')
    at_risk_count = sum(1 for g in active_goals if g.get_status_prediction() == 'at_risk')
    behind_count = sum(1 for g in active_goals if g.get_status_prediction() == 'behind')

    has_goals = total_goals > 0
    has_active_goals = active_goals_count > 0

    context = {
        'user': user,
        'profile': profile,
        'first_letter': first_letter,
        'full_name': full_name,
        'available_balance': float(total_balance),
        'total_income': float(total_income),
        'monthly_income': float(monthly_income),
        'todays_expenses': float(todays_expenses),
        'total_weekly_expense': float(total_weekly_expense),
        'weekly_amounts': weekly_amounts,
        'day_labels': day_labels,
        'day_full_labels': day_full_labels,
        'today_day_name': today_day_name.capitalize(),
        'today_date': today,
        'current_month': today.strftime('%B %Y'),
        'balance_labels': balance_labels,
        'balance_values': balance_values,
        'income_labels': income_labels,
        'income_values': income_values,
        'has_balance': len(balance_labels) > 0,
        'has_income': len(income_labels) > 0,
        'has_expenses': total_weekly_expense > 0,
        
        # Goals data
        'total_goals': total_goals,
        'active_goals_count': active_goals_count,
        'completed_goals_count': completed_goals_count,
        'failed_goals_count': failed_goals_count,
        'has_goals': has_goals,
        'has_active_goals': has_active_goals,
        'goals_status_labels': goals_status_labels,
        'goals_status_values': goals_status_values,
        'goals_status_colors': goals_status_colors,
        'goals_progress_labels': goals_progress_labels,
        'goals_progress_values': goals_progress_values,
        'goals_target_values': goals_target_values,
        'goals_current_values': goals_current_values,
        'total_goals_target': total_goals_target,
        'total_goals_savings': total_goals_savings,
        'overall_goals_rate': round(overall_goals_rate, 1),
        'nearest_goal': nearest_goal,
        'on_track_count': on_track_count,
        'at_risk_count': at_risk_count,
        'behind_count': behind_count,
        'top_active_goals': top_active_goals,
    }

    return render(request, 'Main/dashboard.html', context)
#?======================================================================================================================
#!=========================================== END OF DASHBOARD VIEWS ===========================================
#?======================================================================================================================

# ============================================
# Balance View
# ============================================
@login_required(login_url='/401/')
def balance_view(request):
    user = request.user
    profile = None

    if hasattr(user, 'profile'):
        profile = user.profile

    first_letter = user.first_name[0].upper() if user.first_name else user.email[0].upper()

    full_name = f"{user.first_name} {user.last_name}".strip()
    if not full_name:
        full_name = user.email.split('@')[0]

    # Get all balances for the user
    balances = UserBalance.objects.filter(user=user)

    context = {
        'user': user,
        'profile': profile,
        'first_letter': first_letter,
        'full_name': full_name,
        'balances': balances,
        'income_sources': UserBalance.INCOME_SOURCE_CHOICES,
        'income_methods': UserBalance.INCOME_METHOD_CHOICES,
        'status_choices': UserBalance.STATUS_CHOICES,
    }

    return render(request, 'Balance/balance.html', context)


# ============================================
# Add Balance View
# ============================================
@login_required(login_url='/401/')
def add_balance(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method', 'type': 'error'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        income_source = request.POST.get('income_source', 'salary').strip()
        account_name = request.POST.get('account_name', '').strip()
        income_method = request.POST.get('income_method', 'banking').strip()
        account_number = request.POST.get('account_number', '').strip()
        available_balance = request.POST.get('available_balance', '0').strip()
        status = request.POST.get('status', 'active').strip()

        # Validation
        if not account_name:
            return JsonResponse({'success': False, 'message': 'Account name is required', 'type': 'error'})
        
        if len(account_name) < 2:
            return JsonResponse({'success': False, 'message': 'Account name must be at least 2 characters', 'type': 'error'})
        
        if len(account_name) > 100:
            return JsonResponse({'success': False, 'message': 'Account name must be less than 100 characters', 'type': 'error'})
        
        if not account_number:
            return JsonResponse({'success': False, 'message': 'Account/Mobile number is required', 'type': 'error'})
        
        if len(account_number) < 5:
            return JsonResponse({'success': False, 'message': 'Account/Mobile number must be at least 5 characters', 'type': 'error'})
        
        if len(account_number) > 50:
            return JsonResponse({'success': False, 'message': 'Account/Mobile number must be less than 50 characters', 'type': 'error'})

        # Validate income source
        valid_sources = [choice[0] for choice in UserBalance.INCOME_SOURCE_CHOICES]
        if income_source not in valid_sources:
            return JsonResponse({'success': False, 'message': 'Invalid income source selected', 'type': 'error'})

        # Validate income method
        valid_methods = [choice[0] for choice in UserBalance.INCOME_METHOD_CHOICES]
        if income_method not in valid_methods:
            return JsonResponse({'success': False, 'message': 'Invalid income method selected', 'type': 'error'})

        # Validate status
        valid_statuses = [choice[0] for choice in UserBalance.STATUS_CHOICES]
        if status not in valid_statuses:
            return JsonResponse({'success': False, 'message': 'Invalid status selected', 'type': 'error'})

        # Validate balance
        try:
            balance_decimal = Decimal(available_balance)
            if balance_decimal < 0:
                return JsonResponse({'success': False, 'message': 'Balance cannot be negative', 'type': 'error'})
        except (InvalidOperation, ValueError):
            return JsonResponse({'success': False, 'message': 'Invalid balance amount', 'type': 'error'})

        # Check for duplicate account
        if UserBalance.objects.filter(
            user=request.user,
            account_name__iexact=account_name,
            account_number=account_number
        ).exists():
            return JsonResponse({'success': False, 'message': 'An account with this name and number already exists', 'type': 'error'})

        # Create balance
        balance = UserBalance.objects.create(
            user=request.user,
            income_source=income_source,
            account_name=account_name,
            income_method=income_method,
            account_number=account_number,
            available_balance=balance_decimal,
            status=status
        )

        return JsonResponse({
            'success': True, 
            'message': 'Account added successfully', 
            'type': 'success',
            'balance': {
                'id': balance.id,
                'account_name': balance.account_name,
                'available_balance': str(balance.available_balance),
                'income_source': balance.get_income_source_display(),
                'income_method': balance.get_income_method_display(),
                'status': balance.status,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.', 'type': 'error'})


# ============================================
# Edit Balance View
# ============================================
@login_required(login_url='/401/')
def edit_balance(request, balance_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method', 'type': 'error'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        balance = get_object_or_404(UserBalance, id=balance_id, user=request.user)

        income_source = request.POST.get('income_source', 'salary').strip()
        account_name = request.POST.get('account_name', '').strip()
        income_method = request.POST.get('income_method', 'banking').strip()
        account_number = request.POST.get('account_number', '').strip()
        available_balance = request.POST.get('available_balance', '0').strip()
        status = request.POST.get('status', 'active').strip()

        # Validation
        if not account_name:
            return JsonResponse({'success': False, 'message': 'Account name is required', 'type': 'error'})
        
        if len(account_name) < 2:
            return JsonResponse({'success': False, 'message': 'Account name must be at least 2 characters', 'type': 'error'})
        
        if len(account_name) > 100:
            return JsonResponse({'success': False, 'message': 'Account name must be less than 100 characters', 'type': 'error'})
        
        if not account_number:
            return JsonResponse({'success': False, 'message': 'Account/Mobile number is required', 'type': 'error'})
        
        if len(account_number) < 5:
            return JsonResponse({'success': False, 'message': 'Account/Mobile number must be at least 5 characters', 'type': 'error'})
        
        if len(account_number) > 50:
            return JsonResponse({'success': False, 'message': 'Account/Mobile number must be less than 50 characters', 'type': 'error'})

        # Validate income source
        valid_sources = [choice[0] for choice in UserBalance.INCOME_SOURCE_CHOICES]
        if income_source not in valid_sources:
            return JsonResponse({'success': False, 'message': 'Invalid income source selected', 'type': 'error'})

        # Validate income method
        valid_methods = [choice[0] for choice in UserBalance.INCOME_METHOD_CHOICES]
        if income_method not in valid_methods:
            return JsonResponse({'success': False, 'message': 'Invalid income method selected', 'type': 'error'})

        # Validate status
        valid_statuses = [choice[0] for choice in UserBalance.STATUS_CHOICES]
        if status not in valid_statuses:
            return JsonResponse({'success': False, 'message': 'Invalid status selected', 'type': 'error'})

        # Validate balance
        try:
            balance_decimal = Decimal(available_balance)
            if balance_decimal < 0:
                return JsonResponse({'success': False, 'message': 'Balance cannot be negative', 'type': 'error'})
        except (InvalidOperation, ValueError):
            return JsonResponse({'success': False, 'message': 'Invalid balance amount', 'type': 'error'})

        # Check for duplicate account (excluding current)
        if UserBalance.objects.filter(
            user=request.user,
            account_name__iexact=account_name,
            account_number=account_number
        ).exclude(id=balance_id).exists():
            return JsonResponse({'success': False, 'message': 'An account with this name and number already exists', 'type': 'error'})

        # Update balance
        balance.income_source = income_source
        balance.account_name = account_name
        balance.income_method = income_method
        balance.account_number = account_number
        balance.available_balance = balance_decimal
        balance.status = status
        balance.save()

        return JsonResponse({
            'success': True, 
            'message': 'Account updated successfully', 
            'type': 'success',
            'balance': {
                'id': balance.id,
                'account_name': balance.account_name,
                'available_balance': str(balance.available_balance),
                'income_source': balance.get_income_source_display(),
                'income_method': balance.get_income_method_display(),
                'status': balance.status,
            }
        })

    except UserBalance.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Account not found', 'type': 'error'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.', 'type': 'error'})


# ============================================
# Delete Balance View
# ============================================
@login_required(login_url='/401/')
def delete_balance(request, balance_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method', 'type': 'error'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        balance = get_object_or_404(UserBalance, id=balance_id, user=request.user)
        account_name = balance.account_name
        balance.delete()

        return JsonResponse({
            'success': True, 
            'message': f'Account "{account_name}" deleted successfully', 
            'type': 'success'
        })

    except UserBalance.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Account not found', 'type': 'error'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.', 'type': 'error'})


# ============================================
# Get Balance Details (for edit form)
# ============================================
@login_required(login_url='/401/')
def get_balance(request, balance_id):
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        balance = get_object_or_404(UserBalance, id=balance_id, user=request.user)

        return JsonResponse({
            'success': True,
            'balance': {
                'id': balance.id,
                'income_source': balance.income_source,
                'account_name': balance.account_name,
                'income_method': balance.income_method,
                'account_number': balance.account_number,
                'available_balance': str(balance.available_balance),
                'status': balance.status,
            }
        })

    except UserBalance.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Account not found', 'type': 'error'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred', 'type': 'error'})
    
#?======================================================================================================================
#!=========================================== END OF BALANCE VIEWS ===========================================
#?======================================================================================================================

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


def get_day_name(date_obj):
    """Get day name from date"""
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return days[date_obj.weekday()]


def get_today_day_name():
    """Get today's day name"""
    return get_day_name(date.today())


# ============================================
# Expenses List View
# ============================================
@login_required(login_url='/401/')
def expenses_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    first_letter = user.first_name[0].upper() if user.first_name else user.email[0].upper()
    full_name = f"{user.first_name} {user.last_name}".strip() or user.email.split('@')[0]

    # Get all expense blocks for this user
    expense_blocks = ExpenseBlock.objects.filter(user=user)
    
    # Check and close expired blocks
    for block in expense_blocks.filter(status='active'):
        block.check_and_close()
    
    # Refresh queryset after closing
    expense_blocks = ExpenseBlock.objects.filter(user=user)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(expense_blocks, 10)
    
    try:
        expense_blocks_page = paginator.page(page)
    except PageNotAnInteger:
        expense_blocks_page = paginator.page(1)
    except EmptyPage:
        expense_blocks_page = paginator.page(paginator.num_pages)
    
    # Calculate stats
    total_expenses = expense_blocks.aggregate(total=Sum('total_expense'))['total'] or 0
    active_blocks_count = expense_blocks.filter(status='active').count()
    closed_blocks_count = expense_blocks.filter(status='closed').count()

    context = {
        'user': user,
        'profile': profile,
        'first_letter': first_letter,
        'full_name': full_name,
        'expense_blocks': expense_blocks_page,
        'total_expenses': total_expenses,
        'active_blocks_count': active_blocks_count,
        'closed_blocks_count': closed_blocks_count,
        'expense_type_choices': ExpenseBlock.EXPENSE_TYPE_CHOICES,
        'day_choices': ExpenseBlock.DAY_CHOICES,
    }

    return render(request, 'Expenses/expenses.html', context)


# ============================================
# Create Expense Block
# ============================================
@login_required(login_url='/401/')
def create_expense_block(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    try:
        user = request.user
        title = request.POST.get('title', '').strip()
        expense_type = request.POST.get('expense_type', 'weekly').strip()
        starting_day = request.POST.get('starting_day', 'sunday').strip()
        
        # Validate expense_type
        valid_types = [choice[0] for choice in ExpenseBlock.EXPENSE_TYPE_CHOICES]
        if expense_type not in valid_types:
            return JsonResponse({'success': False, 'message': 'Invalid expense type'})
        
        # Validate starting_day
        valid_days = [choice[0] for choice in ExpenseBlock.DAY_CHOICES]
        if starting_day not in valid_days:
            return JsonResponse({'success': False, 'message': 'Invalid starting day'})
        
        today = date.today()
        
        # Check if there's already an active block for this user
        existing_active = ExpenseBlock.objects.filter(
            user=user,
            status='active',
            start_date__lte=today,
            end_date__gte=today
        ).first()
        
        if existing_active:
            return JsonResponse({
                'success': False, 
                'message': 'You already have an active expense block',
                'redirect': f'/main/expenses/{existing_active.id}/'
            })
        
        # Calculate end date
        end_date = ExpenseBlock.calculate_end_date(today, expense_type, starting_day)
        
        # Create new expense block
        block = ExpenseBlock.objects.create(
            user=user,
            title=title if title else None,
            expense_type=expense_type,
            starting_day=starting_day,
            start_date=today,
            end_date=end_date
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Expense block created successfully',
            'redirect': f'/main/expenses/{block.id}/'
        })
    
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})


# ============================================
# Expense Block Detail View
# ============================================
@login_required(login_url='/401/')
def expense_detail_view(request, block_id):
    user = request.user
    profile = getattr(user, 'profile', None)

    first_letter = user.first_name[0].upper() if user.first_name else user.email[0].upper()
    full_name = f"{user.first_name} {user.last_name}".strip() or user.email.split('@')[0]

    # Get the expense block
    expense_block = get_object_or_404(ExpenseBlock, id=block_id, user=user)
    
    # Check if block should be closed
    expense_block.check_and_close()
    
    # Get today's info
    today = date.today()
    today_day_name = get_day_name(today)
    
    # Check if today is within block date range
    is_today_in_block = expense_block.start_date <= today <= expense_block.end_date
    
    # Get expenses grouped by day
    expenses_by_day = expense_block.get_expenses_by_day()
    
    # Get today's expenses
    today_expenses = expense_block.items.filter(expense_date=today)
    has_today_expenses = today_expenses.exists()
    
    # All expense items with pagination
    all_expenses = expense_block.items.all()
    page = request.GET.get('page', 1)
    paginator = Paginator(all_expenses, 15)
    
    try:
        expense_items = paginator.page(page)
    except PageNotAnInteger:
        expense_items = paginator.page(1)
    except EmptyPage:
        expense_items = paginator.page(paginator.num_pages)
    
    # Get user's active balance accounts
    user_balances = UserBalance.objects.filter(user=user, status='active')
    has_balance = user_balances.exists()
    
    context = {
        'user': user,
        'profile': profile,
        'first_letter': first_letter,
        'full_name': full_name,
        'expense_block': expense_block,
        'expense_items': expense_items,
        'expenses_by_day': expenses_by_day,
        'today_day_name': today_day_name,
        'today_date': today,
        'is_today_in_block': is_today_in_block,
        'has_today_expenses': has_today_expenses,
        'today_expenses': today_expenses,
        'payment_methods': ExpenseItem.PAYMENT_METHOD_CHOICES,
        'day_choices': ExpenseItem.DAY_CHOICES,
        'user_balances': user_balances,
        'has_balance': has_balance,
    }

    return render(request, 'Expenses/expense_detail.html', context)


# ============================================
# Add Expense Item
# ============================================
@login_required(login_url='/401/')
def add_expense_item(request, block_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    try:
        expense_block = get_object_or_404(ExpenseBlock, id=block_id, user=request.user)
        
        # Check if block is closed
        if expense_block.status == 'closed':
            return JsonResponse({'success': False, 'message': 'This expense block is closed.'})
        
        expense_name = request.POST.get('expense_name', '').strip()
        amount = request.POST.get('amount', '0').strip()
        balance_id = request.POST.get('balance_id', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Get today's date and day
        today = date.today()
        today_day_name = get_day_name(today)
        
        # Check if today is within block date range
        if not (expense_block.start_date <= today <= expense_block.end_date):
            return JsonResponse({'success': False, 'message': 'Cannot add expenses outside block date range'})
        
        # Validation
        if not expense_name:
            return JsonResponse({'success': False, 'message': 'Expense name is required'})
        
        if len(expense_name) < 2:
            return JsonResponse({'success': False, 'message': 'Expense name must be at least 2 characters'})
        
        if len(expense_name) > 100:
            return JsonResponse({'success': False, 'message': 'Expense name must be less than 100 characters'})
        
        # Validate amount
        try:
            amount_decimal = Decimal(amount)
            if amount_decimal <= 0:
                return JsonResponse({'success': False, 'message': 'Amount must be greater than 0'})
        except (InvalidOperation, ValueError):
            return JsonResponse({'success': False, 'message': 'Invalid amount'})
        
        # Validate balance_id
        if not balance_id:
            return JsonResponse({'success': False, 'message': 'Please select an account'})
        
        # Get the selected balance account
        try:
            user_balance = UserBalance.objects.get(
                id=balance_id,
                user=request.user,
                status='active'
            )
        except UserBalance.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'message': 'Selected account not found or inactive.',
                'redirect_balance': True
            })
        
        if user_balance.available_balance < amount_decimal:
            return JsonResponse({
                'success': False, 
                'message': f'Insufficient balance in {user_balance.account_name}. Available: Rs. {user_balance.available_balance}'
            })
        
        # Deduct from balance
        user_balance.available_balance -= amount_decimal
        user_balance.save(update_fields=['available_balance', 'updated_at'])
        
        # Create expense item
        expense_item = ExpenseItem.objects.create(
            expense_block=expense_block,
            user_balance=user_balance,
            expense_name=expense_name,
            amount=amount_decimal,
            payment_method=user_balance.income_method,
            expense_day=today_day_name,
            expense_date=today,
            notes=notes if notes else None
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Expense added successfully',
            'expense': {
                'id': expense_item.id,
                'expense_name': expense_item.expense_name,
                'amount': str(expense_item.amount),
                'account_name': user_balance.account_name,
                'balance_id': user_balance.id,
                'payment_method': expense_item.get_payment_method_display(),
                'payment_method_value': expense_item.payment_method,
                'expense_day': expense_item.expense_day.capitalize(),
                'expense_date': expense_item.expense_date.strftime('%b %d, %Y'),
                'notes': expense_item.notes or '',
                'created_at': expense_item.created_at.strftime('%I:%M %p'),
            },
            'block_total': str(expense_block.total_expense),
            'item_count': expense_block.item_count
        })
    
    except ExpenseBlock.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Expense block not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})

# ============================================
# Update Expense Item
# ============================================
@login_required(login_url='/401/')
def update_expense_item(request, item_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    try:
        expense_item = get_object_or_404(
            ExpenseItem, 
            id=item_id, 
            expense_block__user=request.user
        )
        
        # Check if block is closed
        if expense_item.expense_block.status == 'closed':
            return JsonResponse({'success': False, 'message': 'This expense block is closed.'})
        
        expense_name = request.POST.get('expense_name', '').strip()
        amount = request.POST.get('amount', '0').strip()
        balance_id = request.POST.get('balance_id', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Store old values for balance adjustment
        old_amount = expense_item.amount
        old_balance = expense_item.user_balance
        
        # Validation
        if not expense_name:
            return JsonResponse({'success': False, 'message': 'Expense name is required'})
        
        if len(expense_name) < 2:
            return JsonResponse({'success': False, 'message': 'Expense name must be at least 2 characters'})
        
        if len(expense_name) > 100:
            return JsonResponse({'success': False, 'message': 'Expense name must be less than 100 characters'})
        
        # Validate amount
        try:
            amount_decimal = Decimal(amount)
            if amount_decimal <= 0:
                return JsonResponse({'success': False, 'message': 'Amount must be greater than 0'})
        except (InvalidOperation, ValueError):
            return JsonResponse({'success': False, 'message': 'Invalid amount'})
        
        # Validate balance_id
        if not balance_id:
            return JsonResponse({'success': False, 'message': 'Please select an account'})
        
        # Get the new selected balance account
        try:
            new_balance = UserBalance.objects.get(
                id=balance_id,
                user=request.user,
                status='active'
            )
        except UserBalance.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'message': 'Selected account not found or inactive.',
                'redirect_balance': True
            })
        
        # Handle balance adjustments
        # Refund old amount to old balance account
        if old_balance and old_balance.status == 'active':
            old_balance.available_balance += old_amount
            old_balance.save(update_fields=['available_balance', 'updated_at'])
        
        # Check if new balance has sufficient funds
        if new_balance.available_balance < amount_decimal:
            # Rollback refund
            if old_balance and old_balance.status == 'active':
                old_balance.available_balance -= old_amount
                old_balance.save(update_fields=['available_balance', 'updated_at'])
            return JsonResponse({
                'success': False, 
                'message': f'Insufficient balance in {new_balance.account_name}. Available: Rs. {new_balance.available_balance}'
            })
        
        # Deduct new amount from new balance
        new_balance.available_balance -= amount_decimal
        new_balance.save(update_fields=['available_balance', 'updated_at'])
        
        # Update expense item
        expense_item.expense_name = expense_name
        expense_item.amount = amount_decimal
        expense_item.user_balance = new_balance
        expense_item.payment_method = new_balance.income_method
        expense_item.notes = notes if notes else None
        expense_item.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Expense updated successfully',
            'expense': {
                'id': expense_item.id,
                'expense_name': expense_item.expense_name,
                'amount': str(expense_item.amount),
                'account_name': new_balance.account_name,
                'balance_id': new_balance.id,
                'payment_method': expense_item.get_payment_method_display(),
                'payment_method_value': expense_item.payment_method,
                'expense_day': expense_item.expense_day.capitalize(),
                'expense_date': expense_item.expense_date.strftime('%b %d, %Y'),
                'notes': expense_item.notes or '',
            },
            'block_total': str(expense_item.expense_block.total_expense),
            'item_count': expense_item.expense_block.item_count
        })
    
    except ExpenseItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Expense item not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})
# ============================================
# Get Expense Item Details (for edit form)
# ============================================
@login_required(login_url='/401/')
def get_expense_item(request, item_id):
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    try:
        expense_item = get_object_or_404(
            ExpenseItem, 
            id=item_id, 
            expense_block__user=request.user
        )
        
        return JsonResponse({
            'success': True,
            'expense': {
                'id': expense_item.id,
                'expense_name': expense_item.expense_name,
                'amount': str(expense_item.amount),
                'balance_id': expense_item.user_balance.id if expense_item.user_balance else '',
                'account_name': expense_item.user_balance.account_name if expense_item.user_balance else '',
                'payment_method': expense_item.payment_method,
                'expense_day': expense_item.expense_day,
                'expense_day_display': expense_item.expense_day.capitalize(),
                'expense_date': expense_item.expense_date.strftime('%Y-%m-%d'),
                'expense_date_display': expense_item.expense_date.strftime('%b %d, %Y'),
                'notes': expense_item.notes or '',
            }
        })
    
    except ExpenseItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Expense item not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred'})
# ============================================
# Update Expense Block Title Only
# ============================================
@login_required(login_url='/401/')
def update_expense_block(request, block_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    try:
        expense_block = get_object_or_404(ExpenseBlock, id=block_id, user=request.user)
        
        title = request.POST.get('title', '').strip()
        
        if title:
            if len(title) > 100:
                return JsonResponse({'success': False, 'message': 'Title must be less than 100 characters'})
            expense_block.title = title
            expense_block.save(update_fields=['title', 'updated_at'])
        
        return JsonResponse({
            'success': True,
            'message': 'Block title updated successfully',
            'title': expense_block.title
        })
    
    except ExpenseBlock.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Expense block not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred.'})
#?======================================================================================================================
#!=========================================== END OF EXPENSE VIEWS ===========================================
#?====================================================================================================================== 


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


# ============================================
# Income View
# ============================================
@login_required(login_url='/401/')
def income_view(request):
    user = request.user
    profile = None

    if hasattr(user, 'profile'):
        profile = user.profile

    first_letter = user.first_name[0].upper() if user.first_name else user.email[0].upper()

    full_name = f"{user.first_name} {user.last_name}".strip()
    if not full_name:
        full_name = user.email.split('@')[0]

    # Get all incomes for the user
    incomes_list = UserIncome.objects.filter(user=user).select_related('balance_account')
    
    # Pagination - 50 items per page
    paginator = Paginator(incomes_list, 50)
    page = request.GET.get('page', 1)
    
    try:
        incomes = paginator.page(page)
    except PageNotAnInteger:
        incomes = paginator.page(1)
    except EmptyPage:
        incomes = paginator.page(paginator.num_pages)

    # Get user's active balance accounts for the dropdown
    balance_accounts = UserBalance.objects.filter(user=user, status='active')

    context = {
        'user': user,
        'profile': profile,
        'first_letter': first_letter,
        'full_name': full_name,
        'incomes': incomes,
        'total_incomes': incomes_list.count(),
        'balance_accounts': balance_accounts,
        'income_sources': UserIncome.INCOME_SOURCE_CHOICES,
    }

    return render(request, 'Income/income.html', context)


# ============================================
# Add Income View
# ============================================
@login_required(login_url='/401/')
def add_income(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method', 'type': 'error'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        income_source = request.POST.get('income_source', 'salary').strip()
        amount = request.POST.get('amount', '0').strip()
        balance_account_id = request.POST.get('balance_account', '').strip()
        description = request.POST.get('description', '').strip()

        # Validation
        if not amount:
            return JsonResponse({'success': False, 'message': 'Amount is required', 'type': 'error'})
        
        # Validate amount
        try:
            amount_decimal = Decimal(amount)
            if amount_decimal <= 0:
                return JsonResponse({'success': False, 'message': 'Amount must be greater than zero', 'type': 'error'})
        except (InvalidOperation, ValueError):
            return JsonResponse({'success': False, 'message': 'Invalid amount', 'type': 'error'})

        # Validate income source
        valid_sources = [choice[0] for choice in UserIncome.INCOME_SOURCE_CHOICES]
        if income_source not in valid_sources:
            return JsonResponse({'success': False, 'message': 'Invalid income source selected', 'type': 'error'})

        # Validate balance account
        if not balance_account_id:
            return JsonResponse({'success': False, 'message': 'Please select an account', 'type': 'error'})
        
        try:
            balance_account = UserBalance.objects.get(id=balance_account_id, user=request.user, status='active')
        except UserBalance.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Selected account not found or inactive', 'type': 'error'})

        # Create income
        income = UserIncome.objects.create(
            user=request.user,
            income_source=income_source,
            amount=amount_decimal,
            balance_account=balance_account,
            description=description
        )

        # Update balance account
        balance_account.available_balance += amount_decimal
        balance_account.save()

        return JsonResponse({
            'success': True, 
            'message': 'Income added successfully', 
            'type': 'success',
            'income': {
                'id': income.id,
                'income_source': income.get_income_source_display(),
                'amount': str(income.amount),
                'account_name': balance_account.account_name,
                'description': income.description or '-',
                'created_at': income.created_at.strftime('%b %d, %Y %I:%M %p'),
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.', 'type': 'error'})


# ============================================
# Edit Income View
# ============================================
@login_required(login_url='/401/')
def edit_income(request, income_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method', 'type': 'error'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        income = get_object_or_404(UserIncome, id=income_id, user=request.user)
        old_amount = income.amount
        old_balance_account = income.balance_account

        income_source = request.POST.get('income_source', 'salary').strip()
        amount = request.POST.get('amount', '0').strip()
        balance_account_id = request.POST.get('balance_account', '').strip()
        description = request.POST.get('description', '').strip()

        # Validation
        if not amount:
            return JsonResponse({'success': False, 'message': 'Amount is required', 'type': 'error'})
        
        # Validate amount
        try:
            amount_decimal = Decimal(amount)
            if amount_decimal <= 0:
                return JsonResponse({'success': False, 'message': 'Amount must be greater than zero', 'type': 'error'})
        except (InvalidOperation, ValueError):
            return JsonResponse({'success': False, 'message': 'Invalid amount', 'type': 'error'})

        # Validate income source
        valid_sources = [choice[0] for choice in UserIncome.INCOME_SOURCE_CHOICES]
        if income_source not in valid_sources:
            return JsonResponse({'success': False, 'message': 'Invalid income source selected', 'type': 'error'})

        # Validate balance account
        if not balance_account_id:
            return JsonResponse({'success': False, 'message': 'Please select an account', 'type': 'error'})
        
        try:
            new_balance_account = UserBalance.objects.get(id=balance_account_id, user=request.user, status='active')
        except UserBalance.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Selected account not found or inactive', 'type': 'error'})

        # Adjust balance accounts
        # First, subtract old amount from old account
        old_balance_account.available_balance -= old_amount
        old_balance_account.save()

        # Then, add new amount to new account
        new_balance_account.available_balance += amount_decimal
        new_balance_account.save()

        # Update income
        income.income_source = income_source
        income.amount = amount_decimal
        income.balance_account = new_balance_account
        income.description = description
        income.save()

        return JsonResponse({
            'success': True, 
            'message': 'Income updated successfully', 
            'type': 'success',
            'income': {
                'id': income.id,
                'income_source': income.get_income_source_display(),
                'amount': str(income.amount),
                'account_name': new_balance_account.account_name,
                'description': income.description or '-',
            }
        })

    except UserIncome.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Income not found', 'type': 'error'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.', 'type': 'error'})


# ============================================
# Delete Income View
# ============================================
@login_required(login_url='/401/')
def delete_income(request, income_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method', 'type': 'error'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        income = get_object_or_404(UserIncome, id=income_id, user=request.user)
        
        # Subtract amount from balance account
        balance_account = income.balance_account
        balance_account.available_balance -= income.amount
        balance_account.save()
        
        income.delete()

        return JsonResponse({
            'success': True, 
            'message': 'Income deleted successfully', 
            'type': 'success'
        })

    except UserIncome.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Income not found', 'type': 'error'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.', 'type': 'error'})


# ============================================
# Get Income Details (for edit form)
# ============================================
@login_required(login_url='/401/')
def get_income(request, income_id):
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        income = get_object_or_404(UserIncome, id=income_id, user=request.user)

        return JsonResponse({
            'success': True,
            'income': {
                'id': income.id,
                'income_source': income.income_source,
                'amount': str(income.amount),
                'balance_account': income.balance_account.id,
                'description': income.description or '',
            }
        })

    except UserIncome.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Income not found', 'type': 'error'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred', 'type': 'error'})

#?======================================================================================================================
#!=========================================== END OF INCOME VIEWS ===========================================
#?======================================================================================================================


# ============================================
# Goals View
# ============================================
@login_required(login_url='/401/')
def goals_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    first_letter = user.first_name[0].upper() if user.first_name else user.email[0].upper()
    full_name = f"{user.first_name} {user.last_name}".strip() or user.email.split('@')[0]

    # Get all goals for the user with pagination
    goals_list = UserGoal.objects.filter(user=user).prefetch_related('balance_accounts')
    
    # Update status for overdue goals
    today = date.today()
    for goal in goals_list.filter(status__in=['new', 'running']):
        if goal.deadline < today:
            if goal.get_achievement_rate() >= 100:
                goal.status = 'completed'
            else:
                goal.status = 'failed'
            goal.save(update_fields=['status', 'updated_at'])
    
    # Refresh queryset
    goals_list = UserGoal.objects.filter(user=user).prefetch_related('balance_accounts')
    
    # Pagination - 10 items per page
    paginator = Paginator(goals_list, 10)
    page = request.GET.get('page', 1)
    
    try:
        goals = paginator.page(page)
    except PageNotAnInteger:
        goals = paginator.page(1)
    except EmptyPage:
        goals = paginator.page(paginator.num_pages)

    # Get user's active balance accounts for the form
    balance_accounts = UserBalance.objects.filter(user=user, status='active')

    # Stats
    total_goals = goals_list.count()
    active_goals = goals_list.filter(status__in=['new', 'running']).count()
    completed_goals = goals_list.filter(status='completed').count()
    failed_goals = goals_list.filter(status='failed').count()

    context = {
        'user': user,
        'profile': profile,
        'first_letter': first_letter,
        'full_name': full_name,
        'goals': goals,
        'total_goals': total_goals,
        'active_goals': active_goals,
        'completed_goals': completed_goals,
        'failed_goals': failed_goals,
        'balance_accounts': balance_accounts,
        'status_choices': UserGoal.STATUS_CHOICES,
        'today_date': today.strftime('%Y-%m-%d'),
    }

    return render(request, 'Goals/goals.html', context)


# ============================================
# Create Goal
# ============================================
@login_required(login_url='/401/')
def create_goal(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method', 'type': 'error'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        title = request.POST.get('title', '').strip()
        target_amount = request.POST.get('target_amount', '0').strip()
        deadline = request.POST.get('deadline', '').strip()
        status = request.POST.get('status', 'new').strip()
        account_ids = request.POST.getlist('balance_accounts')

        # Validation
        if not title:
            return JsonResponse({'success': False, 'message': 'Goal title is required', 'type': 'error'})
        
        if len(title) < 3:
            return JsonResponse({'success': False, 'message': 'Goal title must be at least 3 characters', 'type': 'error'})
        
        if len(title) > 200:
            return JsonResponse({'success': False, 'message': 'Goal title must be less than 200 characters', 'type': 'error'})
        
        # Validate amount
        try:
            amount_decimal = Decimal(target_amount)
            if amount_decimal <= 0:
                return JsonResponse({'success': False, 'message': 'Target amount must be greater than zero', 'type': 'error'})
        except (InvalidOperation, ValueError):
            return JsonResponse({'success': False, 'message': 'Invalid target amount', 'type': 'error'})

        # Validate deadline
        if not deadline:
            return JsonResponse({'success': False, 'message': 'Deadline is required', 'type': 'error'})
        
        try:
            deadline_date = datetime.strptime(deadline, '%Y-%m-%d').date()
            if deadline_date <= date.today():
                return JsonResponse({'success': False, 'message': 'Deadline must be in the future', 'type': 'error'})
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Invalid deadline date format', 'type': 'error'})

        # Validate status
        valid_statuses = [choice[0] for choice in UserGoal.STATUS_CHOICES]
        if status not in valid_statuses:
            return JsonResponse({'success': False, 'message': 'Invalid status selected', 'type': 'error'})

        # Validate accounts
        if not account_ids:
            return JsonResponse({'success': False, 'message': 'Please select at least one account', 'type': 'error'})

        # Verify accounts belong to user
        accounts = UserBalance.objects.filter(id__in=account_ids, user=request.user, status='active')
        if accounts.count() != len(account_ids):
            return JsonResponse({'success': False, 'message': 'One or more selected accounts are invalid', 'type': 'error'})

        # Create goal
        goal = UserGoal.objects.create(
            user=request.user,
            title=title,
            target_amount=amount_decimal,
            start_date=date.today(),
            deadline=deadline_date,
            status=status
        )
        
        # Add accounts
        goal.balance_accounts.set(accounts)

        return JsonResponse({
            'success': True, 
            'message': 'Goal created successfully', 
            'type': 'success',
            'goal': {
                'id': goal.id,
                'title': goal.title,
                'target_amount': str(goal.target_amount),
                'start_date': goal.start_date.strftime('%b %d, %Y'),
                'deadline': goal.deadline.strftime('%b %d, %Y'),
                'status': goal.status,
                'status_display': goal.get_status_display(),
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.', 'type': 'error'})


# ============================================
# Update Goal (Title and Status only)
# ============================================
@login_required(login_url='/401/')
def update_goal(request, goal_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method', 'type': 'error'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        goal = get_object_or_404(UserGoal, id=goal_id, user=request.user)

        title = request.POST.get('title', '').strip()
        status = request.POST.get('status', '').strip()

        # Validation
        if title:
            if len(title) < 3:
                return JsonResponse({'success': False, 'message': 'Goal title must be at least 3 characters', 'type': 'error'})
            
            if len(title) > 200:
                return JsonResponse({'success': False, 'message': 'Goal title must be less than 200 characters', 'type': 'error'})
            
            goal.title = title

        if status:
            valid_statuses = [choice[0] for choice in UserGoal.STATUS_CHOICES]
            if status not in valid_statuses:
                return JsonResponse({'success': False, 'message': 'Invalid status selected', 'type': 'error'})
            goal.status = status

        goal.save()

        return JsonResponse({
            'success': True, 
            'message': 'Goal updated successfully', 
            'type': 'success',
            'goal': {
                'id': goal.id,
                'title': goal.title,
                'status': goal.status,
                'status_display': goal.get_status_display(),
            }
        })

    except UserGoal.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Goal not found', 'type': 'error'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.', 'type': 'error'})


# ============================================
# Get Goal Details (for edit form)
# ============================================
@login_required(login_url='/401/')
def get_goal(request, goal_id):
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        goal = get_object_or_404(UserGoal, id=goal_id, user=request.user)

        return JsonResponse({
            'success': True,
            'goal': {
                'id': goal.id,
                'title': goal.title,
                'target_amount': str(goal.target_amount),
                'start_date': goal.start_date.strftime('%Y-%m-%d'),
                'deadline': goal.deadline.strftime('%Y-%m-%d'),
                'status': goal.status,
                'account_ids': list(goal.balance_accounts.values_list('id', flat=True)),
            }
        })

    except UserGoal.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Goal not found', 'type': 'error'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred', 'type': 'error'})


# ============================================
# Goal Detail View (Progress Page)
# ============================================
@login_required(login_url='/401/')
def goal_detail_view(request, goal_id):
    user = request.user
    profile = getattr(user, 'profile', None)

    first_letter = user.first_name[0].upper() if user.first_name else user.email[0].upper()
    full_name = f"{user.first_name} {user.last_name}".strip() or user.email.split('@')[0]

    # Get the goal
    goal = get_object_or_404(UserGoal, id=goal_id, user=user)
    
    # Update status if needed
    today = date.today()
    if goal.status in ['new', 'running'] and goal.deadline < today:
        if goal.get_achievement_rate() >= 100:
            goal.status = 'completed'
        else:
            goal.status = 'failed'
        goal.save(update_fields=['status', 'updated_at'])
    
    # Get income and expense data for the goal period
    total_income = goal.get_total_income()
    total_expense = goal.get_total_expense()
    current_savings = goal.get_current_savings()
    achievement_rate = goal.get_achievement_rate()
    daily_required = goal.get_daily_required()
    status_prediction = goal.get_status_prediction()
    
    # Calculate rates
    target = goal.target_amount
    if target > 0:
        success_rate = min(100, float(current_savings / target * 100)) if current_savings > 0 else 0
        remaining_rate = max(0, 100 - success_rate)
    else:
        success_rate = 0
        remaining_rate = 100
    
    # Get daily data for charts (last 7 days or goal period, whichever is shorter)
    chart_start = max(goal.start_date, today - timedelta(days=6))
    chart_end = min(goal.deadline, today)
    
    daily_income_data = []
    daily_expense_data = []
    daily_labels = []
    daily_savings_data = []
    
    current_date = chart_start
    while current_date <= chart_end:
        daily_labels.append(current_date.strftime('%b %d'))
        
        # Get daily income
        day_income = UserIncome.objects.filter(
            user=user,
            balance_account__in=goal.balance_accounts.all(),
            created_at__date=current_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        daily_income_data.append(float(day_income))
        
        # Get daily expense
        day_expense = ExpenseItem.objects.filter(
            expense_block__user=user,
            user_balance__in=goal.balance_accounts.all(),
            expense_date=current_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        daily_expense_data.append(float(day_expense))
        
        # Daily savings
        daily_savings_data.append(float(day_income - day_expense))
        
        current_date += timedelta(days=1)
    
    # Cumulative data for progress chart
    cumulative_savings = []
    running_total = Decimal('0.00')
    current_date = goal.start_date
    cumulative_labels = []
    target_line = []
    
    total_days = goal.total_days if goal.total_days > 0 else 1
    daily_target = target / total_days
    
    while current_date <= min(goal.deadline, today):
        cumulative_labels.append(current_date.strftime('%b %d'))
        
        day_income = UserIncome.objects.filter(
            user=user,
            balance_account__in=goal.balance_accounts.all(),
            created_at__date=current_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        day_expense = ExpenseItem.objects.filter(
            expense_block__user=user,
            user_balance__in=goal.balance_accounts.all(),
            expense_date=current_date
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        
        running_total += (day_income - day_expense)
        cumulative_savings.append(float(running_total))
        
        days_from_start = (current_date - goal.start_date).days + 1
        target_line.append(float(daily_target * days_from_start))
        
        current_date += timedelta(days=1)
    
    # Selected accounts info
    selected_accounts = goal.balance_accounts.all()
    accounts_total_balance = selected_accounts.aggregate(total=Sum('available_balance'))['total'] or Decimal('0.00')

    context = {
        'user': user,
        'profile': profile,
        'first_letter': first_letter,
        'full_name': full_name,
        'goal': goal,
        'total_income': float(total_income),
        'total_expense': float(total_expense),
        'current_savings': float(current_savings),
        'achievement_rate': achievement_rate,
        'daily_required': float(daily_required),
        'status_prediction': status_prediction,
        'success_rate': round(success_rate, 1),
        'remaining_rate': round(remaining_rate, 1),
        'target_amount': float(target),
        'days_remaining': goal.days_remaining,
        'days_elapsed': goal.days_elapsed,
        'total_days': goal.total_days,
        'progress_percentage': goal.progress_percentage,
        'is_overdue': goal.is_overdue,
        'today_date': today,
        'selected_accounts': selected_accounts,
        'accounts_total_balance': float(accounts_total_balance),
        # Chart data
        'daily_labels': daily_labels,
        'daily_income_data': daily_income_data,
        'daily_expense_data': daily_expense_data,
        'daily_savings_data': daily_savings_data,
        'cumulative_labels': cumulative_labels,
        'cumulative_savings': cumulative_savings,
        'target_line': target_line,
    }

    return render(request, 'Goals/goal_detail.html', context)

# ?======================================================================================================================
#!=========================================== END OF GOALS VIEWS ===========================================
# ?======================================================================================================================


# ============================================
# Report View
# ============================================
@login_required(login_url='/401/')
def report_view(request):
    user = request.user
    profile = getattr(user, 'profile', None)

    first_letter = user.first_name[0].upper() if user.first_name else user.email[0].upper()
    full_name = f"{user.first_name} {user.last_name}".strip() or user.email.split('@')[0]

    # Get all expense blocks for the user
    expense_blocks = ExpenseBlock.objects.filter(user=user).prefetch_related('items')
    
    # Check and close expired blocks
    for block in expense_blocks.filter(status='active'):
        block.check_and_close()
    
    # Refresh queryset
    expense_blocks = ExpenseBlock.objects.filter(user=user).prefetch_related('items')
    
    # Prepare blocks data for JSON
    import json
    blocks_tree = []
    all_expenses_list = []
    
    for block in expense_blocks:
        days_list = []
        current_date = block.start_date
        while current_date <= block.end_date:
            day_name = get_day_name(current_date)
            day_expenses = block.items.filter(expense_date=current_date)
            day_total = day_expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            days_list.append({
                'name': day_name,
                'display': day_name.capitalize(),
                'date': current_date.strftime('%Y-%m-%d'),
                'date_display': current_date.strftime('%b %d, %Y'),
                'expense_count': day_expenses.count(),
                'total': float(day_total),
            })
            current_date += timedelta(days=1)
        
        blocks_tree.append({
            'id': block.id,
            'title': block.title,
            'expense_type': block.expense_type,
            'expense_type_display': block.get_expense_type_display(),
            'status': block.status,
            'status_display': block.get_status_display(),
            'start_date': block.start_date.strftime('%b %d'),
            'end_date': block.end_date.strftime('%b %d, %Y'),
            'total_expense': float(block.total_expense),
            'item_count': block.item_count,
            'days': days_list,
        })
    
    # Get all expense items for JSON
    all_items = ExpenseItem.objects.filter(expense_block__user=user).select_related('expense_block', 'user_balance')
    
    for item in all_items:
        all_expenses_list.append({
            'id': item.id,
            'block_id': item.expense_block.id,
            'block_title': item.expense_block.title,
            'expense_name': item.expense_name,
            'amount': float(item.amount),
            'account_name': item.account_name,
            'payment_method': item.get_payment_method_display(),
            'expense_day': item.expense_day,
            'expense_day_display': item.expense_day.capitalize(),
            'expense_date': item.expense_date.strftime('%Y-%m-%d'),
            'expense_date_display': item.expense_date.strftime('%b %d, %Y'),
            'notes': item.notes or '',
            'created_at': item.created_at.strftime('%I:%M %p'),
        })
    
    # Stats
    total_expenses = expense_blocks.aggregate(total=Sum('total_expense'))['total'] or Decimal('0.00')
    total_items = ExpenseItem.objects.filter(expense_block__user=user).count()
    active_blocks = expense_blocks.filter(status='active').count()
    closed_blocks = expense_blocks.filter(status='closed').count()
    
    # Weekly vs Monthly counts
    weekly_blocks = expense_blocks.filter(expense_type='weekly').count()
    monthly_blocks = expense_blocks.filter(expense_type='monthly').count()

    context = {
        'user': user,
        'profile': profile,
        'first_letter': first_letter,
        'full_name': full_name,
        'total_expenses': total_expenses,
        'total_items': total_items,
        'active_blocks': active_blocks,
        'closed_blocks': closed_blocks,
        'weekly_blocks': weekly_blocks,
        'monthly_blocks': monthly_blocks,
        'blocks_tree_json': json.dumps(blocks_tree),
        'all_expenses_json': json.dumps(all_expenses_list),
    }

    return render(request, 'Report/report.html', context)


# ============================================
# Get Day Expenses (AJAX)
# ============================================
@login_required(login_url='/401/')
def get_day_expenses(request, block_id, day):
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request'})
    
    try:
        block = get_object_or_404(ExpenseBlock, id=block_id, user=request.user)
        
        # Parse date from day parameter (format: YYYY-MM-DD)
        try:
            expense_date = datetime.strptime(day, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Invalid date format'})
        
        # Get expenses for that day
        expenses = block.items.filter(expense_date=expense_date).order_by('-created_at')
        
        expenses_data = []
        for expense in expenses:
            expenses_data.append({
                'id': expense.id,
                'expense_name': expense.expense_name,
                'amount': str(expense.amount),
                'account_name': expense.account_name,
                'payment_method': expense.get_payment_method_display(),
                'notes': expense.notes or '',
                'created_at': expense.created_at.strftime('%I:%M %p'),
            })
        
        day_total = expenses.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        day_name = get_day_name(expense_date)
        
        return JsonResponse({
            'success': True,
            'block_title': block.title,
            'block_id': block.id,
            'day_name': day_name.capitalize(),
            'day_date': expense_date.strftime('%B %d, %Y'),
            'day_total': str(day_total),
            'expense_count': len(expenses_data),
            'expenses': expenses_data,
        })
    
    except ExpenseBlock.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Expense block not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})

#?======================================================================================================================
#!=========================================== END OF REPORT VIEWS ===========================================
#?====================================================================================================================== 



# ?======================================================================================================================
# Allowed tags and attributes for bleach
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 's', 'ul', 'ol', 'li', 'blockquote',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'pre', 'code', 'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr', 'span', 'div', 'sub', 'sup'
]

ALLOWED_ATTRIBUTES = {
    '*': ['class', 'style'],
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'width', 'height'],
    'td': ['colspan', 'rowspan'],
    'th': ['colspan', 'rowspan'],
}

css_sanitizer = CSSSanitizer(allowed_css_properties=[
    'color', 'background-color', 'font-size', 'font-weight', 'font-style',
    'text-align', 'text-decoration', 'margin', 'padding', 'border',
    'width', 'height', 'list-style-type'
])

def is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def sanitize_html(html_content):
    if not html_content:
        return ''
    return bleach.clean(
        html_content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        css_sanitizer=css_sanitizer,
        strip=True
    )

# ============================================
# Keep List View
# ============================================
@login_required(login_url='/401/')
def keep_view(request):
    user = request.user
    profile = None

    if hasattr(user, 'profile'):
        profile = user.profile

    first_letter = user.first_name[0].upper() if user.first_name else user.email[0].upper()

    full_name = f"{user.first_name} {user.last_name}".strip()
    if not full_name:
        full_name = user.email.split('@')[0]

    # Get all keeps for the user
    keeps_list = UserKeep.objects.filter(user=user)
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(keeps_list, 10)  # 10 items per page
    
    try:
        keeps = paginator.page(page)
    except PageNotAnInteger:
        keeps = paginator.page(1)
    except EmptyPage:
        keeps = paginator.page(paginator.num_pages)

    context = {
        'user': user,
        'profile': profile,
        'first_letter': first_letter,
        'full_name': full_name,
        'keeps': keeps,
        'paginator': paginator,
    }

    return render(request, 'Keep/keep.html', context)


# ============================================
# Add Keep View
# ============================================
@login_required(login_url='/401/')
def add_keep(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method', 'type': 'error'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()

        # Validation
        if not title:
            return JsonResponse({'success': False, 'message': 'Title is required', 'type': 'error'})
        
        if len(title) < 2:
            return JsonResponse({'success': False, 'message': 'Title must be at least 2 characters', 'type': 'error'})
        
        if len(title) > 200:
            return JsonResponse({'success': False, 'message': 'Title must be less than 200 characters', 'type': 'error'})

        # Sanitize description
        sanitized_description = sanitize_html(description)

        # Create keep
        keep = UserKeep.objects.create(
            user=request.user,
            title=title,
            description=sanitized_description
        )

        return JsonResponse({
            'success': True, 
            'message': 'Note added successfully', 
            'type': 'success',
            'keep': {
                'id': keep.id,
                'title': keep.title,
                'description': keep.description,
                'created_at': keep.get_created_at_local().strftime('%b %d, %Y %I:%M %p'),
                'updated_at': keep.get_updated_at_local().strftime('%b %d, %Y %I:%M %p'),
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.', 'type': 'error'})


# ============================================
# Edit Keep View
# ============================================
@login_required(login_url='/401/')
def edit_keep(request, keep_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method', 'type': 'error'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        keep = get_object_or_404(UserKeep, id=keep_id, user=request.user)

        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()

        # Validation
        if not title:
            return JsonResponse({'success': False, 'message': 'Title is required', 'type': 'error'})
        
        if len(title) < 2:
            return JsonResponse({'success': False, 'message': 'Title must be at least 2 characters', 'type': 'error'})
        
        if len(title) > 200:
            return JsonResponse({'success': False, 'message': 'Title must be less than 200 characters', 'type': 'error'})

        # Sanitize description
        sanitized_description = sanitize_html(description)

        # Update keep
        keep.title = title
        keep.description = sanitized_description
        keep.save()

        return JsonResponse({
            'success': True, 
            'message': 'Note updated successfully', 
            'type': 'success',
            'keep': {
                'id': keep.id,
                'title': keep.title,
                'description': keep.description,
                'created_at': keep.get_created_at_local().strftime('%b %d, %Y %I:%M %p'),
                'updated_at': keep.get_updated_at_local().strftime('%b %d, %Y %I:%M %p'),
            }
        })

    except UserKeep.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Note not found', 'type': 'error'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.', 'type': 'error'})


# ============================================
# Delete Keep View
# ============================================
@login_required(login_url='/401/')
def delete_keep(request, keep_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method', 'type': 'error'})
    
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        keep = get_object_or_404(UserKeep, id=keep_id, user=request.user)
        title = keep.title
        keep.delete()

        return JsonResponse({
            'success': True, 
            'message': f'Note "{title}" deleted successfully', 
            'type': 'success'
        })

    except UserKeep.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Note not found', 'type': 'error'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred. Please try again.', 'type': 'error'})


# ============================================
# Get Keep Details
# ============================================
@login_required(login_url='/401/')
def get_keep(request, keep_id):
    if not is_ajax(request):
        return JsonResponse({'success': False, 'message': 'Invalid request', 'type': 'error'})
    
    try:
        keep = get_object_or_404(UserKeep, id=keep_id, user=request.user)

        return JsonResponse({
            'success': True,
            'keep': {
                'id': keep.id,
                'title': keep.title,
                'description': keep.description,
                'created_at': keep.get_created_at_local().strftime('%b %d, %Y %I:%M %p'),
                'updated_at': keep.get_updated_at_local().strftime('%b %d, %Y %I:%M %p'),
            }
        })

    except UserKeep.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Note not found', 'type': 'error'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': 'An error occurred', 'type': 'error'})