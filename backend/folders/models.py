from django.db import models
from django.contrib.auth.models import User

# The Folder model represents directories in our cloud storage
class Folder(models.Model):
    # Store the display name of the folder (e.g. "Work Documents")
    name = models.CharField(max_length=255)
    
    # Link this folder to a specific User.
    # If the user is deleted, all their folders are cascaded (deleted) too.
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='folders')
    
    # Self-referencing relationship (Adjacency List Pattern) to support nested folders.
    # Points to another record in the same 'Folder' table.
    # null=True & blank=True allows a folder to exist in the Root directory.
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subfolders'
    )
    
    # Automatically capture when this folder record was inserted
    created_at = models.DateTimeField(auto_now_add=True)

    # String representation for admin panels and logging
    def __str__(self):
        return self.name
