from django.shortcuts import render
from django.http import HttpResponse




def dashboard_view(request):
    return HttpResponse("Dashboard Page")
