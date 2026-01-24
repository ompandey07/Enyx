from django.db import models
from django.contrib.auth.models import User
import os

def user_profile_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'user_{instance.user.id}_profile.{ext}'
    return os.path.join('Users', 'ProfileImages', filename)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to=user_profile_path, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email}'s Profile"

class LoginAttempt(models.Model):
    email = models.EmailField()
    ip_address = models.GenericIPAddressField()
    attempt_time = models.DateTimeField(auto_now_add=True)
    was_successful = models.BooleanField(default=False)

    class Meta:
        ordering = ['-attempt_time']

    def __str__(self):
        return f"{self.email} - {'Success' if self.was_successful else 'Failed'} - {self.attempt_time}"