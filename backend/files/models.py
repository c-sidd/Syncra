from django.db import models
from django.contrib.auth.models import User
from folders.models import Folder


class File(models.Model):
    name = models.CharField(max_length=255)
    object_key = models.CharField(max_length=1024)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True, related_name='files')
    size = models.BigIntegerField(null=True, blank=True)
    storage_class = models.CharField(max_length=50, default='STANDARD')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
