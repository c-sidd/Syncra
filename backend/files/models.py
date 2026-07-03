from django.db import models
from django.contrib.auth.models import User
from folders.models import Folder

# The File model tracks file metadata records in PostgreSQL
class File(models.Model):
    # The visual name displayed to the user (e.g. "profile_picture.jpg")
    name = models.CharField(max_length=255)
    
    # Core file adapter. Stores path references to the physical storage engine (S3)
    file = models.FileField(upload_to='uploads/')
    
    # The owner who uploaded this file.
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='files')
    
    # Optional folder link. If null, the file is stored in the user's root directory.
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='files'
    )
    
    # File size stored in bytes. BigInt allows files larger than 2.14GB.
    size = models.BigIntegerField(null=True, blank=True)
    
    # Timestamp set automatically on record creation
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
