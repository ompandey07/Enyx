from django.shortcuts import render




def unauthorized_view(request):
    """
    Renders a custom 401 Unauthorized error page.
    """
    return render(request, 'Errors/401.html')