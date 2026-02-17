from django.contrib import admin
from .models import PortfolioBlogs


@admin.register(PortfolioBlogs)
class PortfolioBlogsAdmin(admin.ModelAdmin):
    list_display = (
        "blog_heading",
        "blog_slug",
        "blog_created_at",
        "blog_created_by",
    )
    prepopulated_fields = {"blog_slug": ("blog_heading",)}
    search_fields = ("blog_heading",)
