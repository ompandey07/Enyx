from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta, date
from django.utils import timezone
from calendar import monthrange


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
    
    def save(self, *args, **kwargs):
        # Auto-set expense_day and expense_date if not provided
        if not self.expense_date:
            self.expense_date = date.today()
        
        if not self.expense_day:
            # Get day name from expense_date
            days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            self.expense_day = days[self.expense_date.weekday()]
        
        super().save(*args, **kwargs)
        # Update block total after saving
        self.expense_block.update_total()
    
    def delete(self, *args, **kwargs):
        block = self.expense_block
        super().delete(*args, **kwargs)
        # Update block total after deletion
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