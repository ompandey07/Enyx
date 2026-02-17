from django.db import models
from django.utils.text import slugify


class PortfolioBlogs(models.Model):
    blog_heading = models.CharField(max_length=255)
    blog_slug = models.SlugField(max_length=255, unique=True, blank=True)

    blog_image = models.ImageField(
        upload_to="blog_images/",
        null=True,
        blank=True
    )

    blog_created_at = models.DateTimeField(auto_now_add=True)
    blog_updated_at = models.DateTimeField(auto_now=True)

    blog_discription = models.TextField()
    blog_source = models.URLField()

    blog_created_by = models.CharField(
        max_length=100,
        default="Om Pandey",
        editable=False
    )

    class Meta:
        ordering = ["-blog_created_at"]

    def save(self, *args, **kwargs):
        if not self.blog_slug:
            self.blog_slug = slugify(self.blog_heading)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.blog_heading
