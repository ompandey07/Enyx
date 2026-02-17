from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets
from .models import PortfolioBlogs
from .serializers import PortfolioBlogsSerializer
import json


class PortfolioBlogsViewSet(viewsets.ModelViewSet):
    queryset = PortfolioBlogs.objects.all()
    serializer_class = PortfolioBlogsSerializer
    lookup_field = "blog_slug"


@login_required(login_url='/401/')
def blogs_manage_view(request):
    """Main blog management page"""
    blogs = PortfolioBlogs.objects.all()
    
    # Pagination - 10 blogs per page
    paginator = Paginator(blogs, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'blogs': page_obj,
        'page_obj': page_obj,
        'full_name': request.user.get_full_name() or request.user.username,
        'first_letter': request.user.username[0].upper() if request.user.username else 'U',
    }
    
    if hasattr(request.user, 'profile'):
        context['profile'] = request.user.profile
    
    return render(request, 'Blog/manage_blogs.html', context)


@login_required(login_url='/401/')
@require_http_methods(["POST"])
def blog_add_view(request):
    """Add new blog via AJAX"""
    try:
        # Handle both JSON and FormData
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        blog = PortfolioBlogs.objects.create(
            blog_heading=data.get('blog_heading'),
            blog_discription=data.get('blog_discription'),
            blog_source=data.get('blog_source', ''),
        )
        
        # Handle image upload
        if 'blog_image' in request.FILES:
            blog.blog_image = request.FILES['blog_image']
            blog.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Blog created successfully!',
            'blog': {
                'id': blog.id,
                'blog_slug': blog.blog_slug,
                'blog_heading': blog.blog_heading,
                'blog_discription': blog.blog_discription,
                'blog_source': blog.blog_source,
                'blog_image': blog.blog_image.url if blog.blog_image else None,
                'blog_created_at': blog.blog_created_at.strftime('%Y-%m-%d %H:%M'),
            }
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='/401/')
@require_http_methods(["GET"])
def blog_get_view(request, blog_slug):
    """Get single blog data via AJAX"""
    try:
        blog = PortfolioBlogs.objects.get(blog_slug=blog_slug)
        return JsonResponse({
            'success': True,
            'blog': {
                'id': blog.id,
                'blog_slug': blog.blog_slug,
                'blog_heading': blog.blog_heading,
                'blog_discription': blog.blog_discription,
                'blog_source': blog.blog_source,
                'blog_image': blog.blog_image.url if blog.blog_image else None,
            }
        })
    except PortfolioBlogs.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Blog not found'
        }, status=404)


@login_required(login_url='/401/')
@require_http_methods(["POST"])
def blog_edit_view(request, blog_slug):
    """Edit blog via AJAX"""
    try:
        blog = PortfolioBlogs.objects.get(blog_slug=blog_slug)
        
        # Handle both JSON and FormData
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
        
        blog.blog_heading = data.get('blog_heading', blog.blog_heading)
        blog.blog_discription = data.get('blog_discription', blog.blog_discription)
        blog.blog_source = data.get('blog_source', blog.blog_source)
        
        # Handle image upload
        if 'blog_image' in request.FILES:
            # Delete old image if exists
            if blog.blog_image:
                blog.blog_image.delete(save=False)
            blog.blog_image = request.FILES['blog_image']
        
        blog.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Blog updated successfully!',
            'blog': {
                'id': blog.id,
                'blog_slug': blog.blog_slug,
                'blog_heading': blog.blog_heading,
                'blog_discription': blog.blog_discription,
                'blog_source': blog.blog_source,
                'blog_image': blog.blog_image.url if blog.blog_image else None,
            }
        })
    except PortfolioBlogs.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Blog not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=400)


@login_required(login_url='/401/')
@require_http_methods(["POST"])
def blog_delete_view(request, blog_slug):
    """Delete blog via AJAX"""
    try:
        blog = PortfolioBlogs.objects.get(blog_slug=blog_slug)
        blog_heading = blog.blog_heading
        
        # Delete image file if exists
        if blog.blog_image:
            blog.blog_image.delete(save=False)
        
        blog.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Blog "{blog_heading}" deleted successfully!'
        })
    except PortfolioBlogs.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Blog not found'
        }, status=404)