from rest_framework import serializers
from .models import File
from folders.models import Folder

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('id', 'name', 'file', 'size', 'uploaded_at', 'folder')
        # Block name, size and uploaded_at from manual client modifications
        read_only_fields = ('name', 'size', 'uploaded_at')

    # Dynamically limit the folder selection to folders owned by the active user
    def __init__(self, *args, **kwargs):
        super(FileSerializer, self).__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user:
            # Overwrite the queryset to ensure user cannot upload files to another user's folder
            self.fields['folder'].queryset = Folder.objects.filter(user=request.user)
