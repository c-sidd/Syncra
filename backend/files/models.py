import uuid
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from folders.models import Folder

class File(models.Model):
    name=models.CharField(max_length=255)
    object_key=models.CharField(max_length=1024)
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='files')
    folder=models.ForeignKey(Folder,on_delete=models.CASCADE,null=True,blank=True,related_name='files')
    size=models.BigIntegerField(null=True,blank=True)
    storage_class=models.CharField(max_length=50,default='STANDARD')
    uploaded_at=models.DateTimeField(auto_now_add=True)
    deleted_at=models.DateTimeField(null=True,blank=True)
    def __str__(self): return self.name
    class Meta:
        indexes=[models.Index(fields=['user','deleted_at']),models.Index(fields=['user','folder'])]

def upload_expiry(): return timezone.now()+timedelta(minutes=20)

class UploadSession(models.Model):
    class State(models.TextChoices): PENDING='PENDING','Pending'; COMPLETED='COMPLETED','Completed'; ABORTED='ABORTED','Aborted'
    user=models.ForeignKey(User,on_delete=models.CASCADE,related_name='upload_sessions')
    folder=models.ForeignKey(Folder,on_delete=models.CASCADE,null=True,blank=True,related_name='upload_sessions')
    object_key=models.CharField(max_length=1024,unique=True); name=models.CharField(max_length=255); size=models.BigIntegerField()
    content_type=models.CharField(max_length=255,default='application/octet-stream'); is_multipart=models.BooleanField(default=False)
    multipart_upload_id=models.CharField(max_length=255,blank=True); part_count=models.PositiveIntegerField(default=0)
    state=models.CharField(max_length=16,choices=State.choices,default=State.PENDING); expires_at=models.DateTimeField(default=upload_expiry); created_at=models.DateTimeField(auto_now_add=True)
    def is_active(self): return self.state==self.State.PENDING and self.expires_at>timezone.now()
    class Meta: indexes=[models.Index(fields=['state','expires_at']),models.Index(fields=['user','state'])]

class ShareLink(models.Model):
    token=models.UUIDField(default=uuid.uuid4,unique=True,editable=False)
    file=models.ForeignKey(File,on_delete=models.CASCADE,related_name='share_links')
    created_by=models.ForeignKey(User,on_delete=models.CASCADE)
    expires_at=models.DateTimeField(null=True,blank=True)
    is_active=models.BooleanField(default=True)
    created_at=models.DateTimeField(auto_now_add=True)
    def valid(self): return self.is_active and (self.expires_at is None or self.expires_at>timezone.now())
