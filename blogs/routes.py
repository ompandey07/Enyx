from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PortfolioBlogsViewSet,
    blogs_manage_view,
    blog_add_view,
    blog_get_view,
    blog_edit_view,
    blog_delete_view,
)

router = DefaultRouter()
router.register(r"blogs", PortfolioBlogsViewSet, basename="blogs")

urlpatterns = [
    # DRF API Routes
    path('', include(router.urls)),
    
    
    path('manage/', blogs_manage_view, name='manage_blogs'),
    path('add/', blog_add_view, name='add_blog'),
    path('get/<slug:blog_slug>/', blog_get_view, name='get_blog'),
    path('edit/<slug:blog_slug>/', blog_edit_view, name='edit_blog'),
    path('delete/<slug:blog_slug>/', blog_delete_view, name='delete_blog'),
]