from django.db import models
from django.contrib.auth.models import User


class AWSConnection(models.Model):
    """One private AWS S3 connection owned by a Syncra user."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='aws_connection')
    name = models.CharField(max_length=100, default='My S3 Storage')
    access_key_id = models.CharField(max_length=255)
    secret_access_key = models.TextField()
    region = models.CharField(max_length=100, default='us-east-1')
    bucket_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.user.username} - {self.bucket_name}'
