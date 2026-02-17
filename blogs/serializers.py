from rest_framework import serializers
from .models import PortfolioBlogs


class PortfolioBlogsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioBlogs
        fields = "__all__"
        read_only_fields = (
            "blog_slug",
            "blog_created_at",
            "blog_updated_at",
            "blog_created_by",
        )
