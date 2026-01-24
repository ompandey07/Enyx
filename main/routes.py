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
]