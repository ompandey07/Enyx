from django.urls import path
from . import views , error_view

urlpatterns = [

    # =========== Error Pages ===========
    path('401/', error_view.unauthorized_view, name='unauthorized_view'),
    

    # =========== Index Page ===========
    path('', views.index_page, name='index_page'),
]