from django.urls import path
from . import views , database_backup

urlpatterns = [

    #!================== DASHBOARD ========================== 
    path('dashboard/', views.dashboard_view, name='dashboard_view'),


    #!================= BALANCE MANAGEMENT ==========================
    path('balance/', views.balance_view, name='balance_view'),
    path('balance/add/', views.add_balance, name='add_balance'),
    path('balance/edit/<int:balance_id>/', views.edit_balance, name='edit_balance'),
    path('balance/delete/<int:balance_id>/', views.delete_balance, name='delete_balance'),
    path('balance/get/<int:balance_id>/', views.get_balance, name='get_balance'),


    # !================= EXPENSE MANAGEMENT ==========================
    path('expenses/', views.expenses_view, name='expenses_view'),
    path('expenses/create/', views.create_expense_block, name='create_expense_block'),
    path('expenses/<int:block_id>/', views.expense_detail_view, name='expense_detail_view'),
    path('expenses/<int:block_id>/update/', views.update_expense_block, name='update_expense_block'),
    path('expenses/<int:block_id>/add/', views.add_expense_item, name='add_expense_item'),
    path('expenses/item/<int:item_id>/update/', views.update_expense_item, name='update_expense_item'),
    path('expenses/item/<int:item_id>/get/', views.get_expense_item, name='get_expense_item'),


    # !================= INCOME MANAGEMENT ==========================
    path('income/', views.income_view, name='income_view'),
    path('income/add/', views.add_income, name='add_income'),
    path('income/edit/<int:income_id>/', views.edit_income, name='edit_income'),
    path('income/delete/<int:income_id>/', views.delete_income, name='delete_income'),
    path('income/get/<int:income_id>/', views.get_income, name='get_income'),


    # !================= GOALS MANAGEMENT ==========================
    path('goals/', views.goals_view, name='goals_view'),
    path('goals/create/', views.create_goal, name='create_goal'),
    path('goals/<int:goal_id>/update/', views.update_goal, name='update_goal'),
    path('goals/<int:goal_id>/get/', views.get_goal, name='get_goal'),
    path('goals/<int:goal_id>/', views.goal_detail_view, name='goal_detail_view'),


    # !================= REPORTS ========================== 
    path('report/', views.report_view, name='report_view'),
    path('report/expenses/<int:block_id>/<str:day>/', views.get_day_expenses, name='get_day_expenses'),


    #!================= KEEP MANAGEMENT ==========================
    path('keep/', views.keep_view, name='keep_view'),
    path('keep/add/', views.add_keep, name='add_keep'),
    path('keep/edit/<int:keep_id>/', views.edit_keep, name='edit_keep'),
    path('keep/delete/<int:keep_id>/', views.delete_keep, name='delete_keep'),
    path('keep/get/<int:keep_id>/', views.get_keep, name='get_keep'),


    #!================= BACKUP MANAGEMENT ==========================
    path('backup/', database_backup.backup_view, name='backup_view'),
    path('backup/create/', database_backup.create_backup, name='create_backup'),
    path('backup/download/<int:backup_id>/', database_backup.download_backup, name='download_backup'),
    path('backup/restore/', database_backup.restore_backup, name='restore_backup'),
    path('backup/delete/<int:backup_id>/', database_backup.delete_backup, name='delete_backup'),
    path('backup/get/<int:backup_id>/', database_backup.get_backup, name='get_backup'),
    path('backup/list/', database_backup.get_all_backups, name='get_all_backups'),
]