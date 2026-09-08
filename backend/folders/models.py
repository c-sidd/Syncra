from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
class Folder(models.Model):
    name=models.CharField(max_length=255)
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='folders')
    parent=models.ForeignKey('self',on_delete=models.CASCADE,null=True,blank=True,related_name='subfolders')
    created_at=models.DateTimeField(auto_now_add=True)
    deleted_at=models.DateTimeField(null=True,blank=True)
    def __str__(self): return self.name
    class Meta:
        constraints=[models.UniqueConstraint(fields=['user','parent','name'],name='unique_folder_name_per_parent')]
        indexes=[models.Index(fields=['user','parent']),models.Index(fields=['user','deleted_at'])]
