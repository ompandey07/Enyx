from django.urls import path
from . import views

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
]