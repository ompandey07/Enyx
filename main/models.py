from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta, date
from django.utils import timezone
from calendar import monthrange
from decimal import Decimal


class UserBalance(models.Model):
    INCOME_SOURCE_CHOICES = [
        ('salary', 'Salary'),
        ('pocket_money', 'Pocket Money'),
        ('normal_budget', 'Normal Budget'),
        ('others', 'Others'),
    ]
    
    INCOME_METHOD_CHOICES = [
        ('banking', 'Banking'),
        ('esewa', 'Esewa'),
        ('khalti', 'Khalti'),
        ('others', 'Others'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('suspended', 'Suspended'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='balances')
    income_source = models.CharField(max_length=20, choices=INCOME_SOURCE_CHOICES, default='salary')
    account_name = models.CharField(max_length=100)
    income_method = models.CharField(max_length=20, choices=INCOME_METHOD_CHOICES, default='banking')
    account_number = models.CharField(max_length=50)
    available_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.account_name} - {self.user.email}"


class ExpenseBlock(models.Model):
    """
    Weekly/Monthly expense block
    Nepal week: Sunday (start) to Saturday (end)
    """
    EXPENSE_TYPE_CHOICES = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ]
    
    DAY_CHOICES = [
        ('sunday', 'Sunday'),
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('closed', 'Closed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='expense_blocks')
    title = models.CharField(max_length=100, blank=True, null=True)
    expense_type = models.CharField(max_length=20, choices=EXPENSE_TYPE_CHOICES, default='weekly')
    starting_day = models.CharField(max_length=20, choices=DAY_CHOICES, default='sunday')
    start_date = models.DateField()
    end_date = models.DateField()
    total_expense = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date', '-created_at']

    def __str__(self):
        return f"{self.title or 'Expense Block'} ({self.start_date} - {self.end_date})"
    
    def save(self, *args, **kwargs):
        # Auto generate title if not provided
        if not self.title:
            if self.expense_type == 'weekly':
                self.title = f"Week of {self.start_date.strftime('%b %d, %Y')}"
            else:
                self.title = f"Month of {self.start_date.strftime('%B %Y')}"
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def get_day_name(date_obj):
        """Get day name from date (Nepal format: Sunday=0)"""
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        return days[date_obj.weekday()]
    
    @staticmethod
    def calculate_end_date(start_date, expense_type, starting_day):
        """Calculate end date based on expense type"""
        if expense_type == 'weekly':
            # For weekly, end is always Saturday 11:59 PM
            # In Python: Monday=0, Sunday=6
            # We need to find next Saturday from start_date
            days_until_saturday = (5 - start_date.weekday()) % 7
            if days_until_saturday == 0 and start_date.weekday() != 5:
                days_until_saturday = 7
            return start_date + timedelta(days=days_until_saturday)
        else:
            # For monthly, end is last day of the month
            _, last_day = monthrange(start_date.year, start_date.month)
            return date(start_date.year, start_date.month, last_day)
    
    def update_total(self):
        """Update total expense from all items"""
        total = self.items.aggregate(total=models.Sum('amount'))['total'] or 0
        self.total_expense = total
        self.save(update_fields=['total_expense', 'updated_at'])
    
    def check_and_close(self):
        """Check if block should be closed based on current time"""
        now = timezone.now()
        
        # Create end datetime (end_date 11:59 PM)
        if now.date() > self.end_date or (now.date() == self.end_date and now.hour >= 23 and now.minute >= 59):
            if self.status == 'active':
                self.status = 'closed'
                self.save(update_fields=['status', 'updated_at'])
                return True
        return False
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    @property
    def days_remaining(self):
        if self.status == 'closed':
            return 0
        remaining = (self.end_date - date.today()).days
        return max(0, remaining)
    
    @property
    def item_count(self):
        return self.items.count()
    
    def get_expenses_by_day(self):
        """Get expenses grouped by day"""
        from collections import OrderedDict
        
        day_order = ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        grouped = OrderedDict()
        
        for day in day_order:
            grouped[day] = {
                'display': day.capitalize(),
                'items': [],
                'total': 0
            }
        
        for item in self.items.all():
            if item.expense_day in grouped:
                grouped[item.expense_day]['items'].append(item)
                grouped[item.expense_day]['total'] += item.amount
        
        return grouped


class ExpenseItem(models.Model):
    """
    Individual expense item within an expense block
    """
    DAY_CHOICES = [
        ('sunday', 'Sunday'),
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('banking', 'Banking'),
        ('esewa', 'Esewa'),
        ('khalti', 'Khalti'),
        ('others', 'Others'),
    ]
    
    expense_block = models.ForeignKey(ExpenseBlock, on_delete=models.CASCADE, related_name='items')
    user_balance = models.ForeignKey(UserBalance, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenses')
    expense_name = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='others')
    expense_day = models.CharField(max_length=20, choices=DAY_CHOICES)
    expense_date = models.DateField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']

    def __str__(self):
        return f"{self.expense_name} - Rs. {self.amount}"
    
    @property
    def account_name(self):
        """Get account name from user_balance"""
        if self.user_balance:
            return self.user_balance.account_name
        return "N/A"
    
    def save(self, *args, **kwargs):
        if not self.expense_date:
            self.expense_date = date.today()
        
        if not self.expense_day:
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            self.expense_day = days[self.expense_date.weekday()]
        
        # Auto-set payment_method from user_balance
        if self.user_balance:
            self.payment_method = self.user_balance.income_method
        
        super().save(*args, **kwargs)
        self.expense_block.update_total()
    
    def delete(self, *args, **kwargs):
        block = self.expense_block
        super().delete(*args, **kwargs)
        block.update_total()



class UserIncome(models.Model):
    INCOME_SOURCE_CHOICES = [
        ('salary', 'Salary'),
        ('budget', 'Budget'),
        ('loan', 'Loan'),
        ('share_amount', 'Share Amount'),
        ('bonus', 'Bonus'),
        ('investment', 'Investment Returns'),
        ('freelance', 'Freelance'),
        ('rental', 'Rental Income'),
        ('commission', 'Commission'),
        ('gift', 'Gift'),
        ('refund', 'Refund'),
        ('dividend', 'Dividend'),
        ('interest', 'Interest'),
        ('others', 'Others'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incomes')
    income_source = models.CharField(max_length=20, choices=INCOME_SOURCE_CHOICES, default='salary')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_account = models.ForeignKey(
        'UserBalance', 
        on_delete=models.CASCADE, 
        related_name='incomes'
    )
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_income_source_display()} - Rs. {self.amount} - {self.user.email}"
    

class UserGoal(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='goals')
    title = models.CharField(max_length=200)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    balance_accounts = models.ManyToManyField(UserBalance, related_name='goals', blank=True)
    start_date = models.DateField()
    deadline = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - Rs. {self.target_amount}"
    
    def save(self, *args, **kwargs):
        if not self.start_date:
            self.start_date = date.today()
        super().save(*args, **kwargs)
    
    @property
    def days_remaining(self):
        if self.status in ['completed', 'failed']:
            return 0
        remaining = (self.deadline - date.today()).days
        return max(0, remaining)
    
    @property
    def total_days(self):
        return (self.deadline - self.start_date).days
    
    @property
    def days_elapsed(self):
        elapsed = (date.today() - self.start_date).days
        return max(0, min(elapsed, self.total_days))
    
    @property
    def progress_percentage(self):
        if self.total_days <= 0:
            return 100
        return min(100, round((self.days_elapsed / self.total_days) * 100, 1))
    
    @property
    def is_overdue(self):
        return date.today() > self.deadline and self.status not in ['completed', 'failed']
    
    def get_total_income(self):
        """Get total income within goal period from selected accounts"""
        from django.db.models import Sum
        total = UserIncome.objects.filter(
            user=self.user,
            balance_account__in=self.balance_accounts.all(),
            created_at__date__gte=self.start_date,
            created_at__date__lte=self.deadline
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return total
    
    def get_total_expense(self):
        """Get total expenses within goal period from selected accounts"""
        from django.db.models import Sum
        total = ExpenseItem.objects.filter(
            expense_block__user=self.user,
            user_balance__in=self.balance_accounts.all(),
            expense_date__gte=self.start_date,
            expense_date__lte=self.deadline
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        return total
    
    def get_current_savings(self):
        """Calculate current savings (income - expense)"""
        return self.get_total_income() - self.get_total_expense()
    
    def get_achievement_rate(self):
        """Calculate achievement rate based on current savings vs target"""
        if self.target_amount <= 0:
            return 0
        current = self.get_current_savings()
        rate = (current / self.target_amount) * 100
        return min(100, max(0, round(rate, 1)))
    
    def get_daily_required(self):
        """Calculate daily amount required to reach goal"""
        if self.days_remaining <= 0:
            return Decimal('0.00')
        remaining_amount = self.target_amount - self.get_current_savings()
        if remaining_amount <= 0:
            return Decimal('0.00')
        return round(remaining_amount / self.days_remaining, 2)
    
    def get_status_prediction(self):
        """Predict goal status based on current progress"""
        achievement_rate = self.get_achievement_rate()
        progress = self.progress_percentage
        
        if achievement_rate >= 100:
            return 'on_track'  # Will complete
        elif progress > 0:
            # Calculate if current rate will achieve goal
            daily_savings = self.get_current_savings() / max(1, self.days_elapsed)
            projected_savings = daily_savings * self.total_days
            if projected_savings >= self.target_amount:
                return 'on_track'
            elif projected_savings >= self.target_amount * Decimal('0.7'):
                return 'at_risk'
            else:
                return 'behind'
        return 'new'


class UserKeep(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='keeps')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.email}"
    
    def get_created_at_local(self):
        from django.utils import timezone
        import pytz
        kathmandu_tz = pytz.timezone('Asia/Kathmandu')
        return self.created_at.astimezone(kathmandu_tz)
    
    def get_updated_at_local(self):
        from django.utils import timezone
        import pytz
        kathmandu_tz = pytz.timezone('Asia/Kathmandu')
        return self.updated_at.astimezone(kathmandu_tz)
    

class DatabaseBackup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='backups')
    filename = models.CharField(max_length=255)
    file_path = models.FileField(upload_to='backups/')
    file_size = models.BigIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.filename} - {self.user.email}"
    
    def get_created_at_local(self):
        import pytz
        kathmandu_tz = pytz.timezone('Asia/Kathmandu')
        return self.created_at.astimezone(kathmandu_tz)
    
    def get_file_size_display(self):
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"