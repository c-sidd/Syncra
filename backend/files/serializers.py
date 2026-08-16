from rest_framework import serializers
from .models import File
from folders.models import Folder


class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('id', 'name', 'size', 'uploaded_at', 'folder', 'storage_class')
        read_only_fields = ('name', 'size', 'uploaded_at', 'storage_class')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user:
            self.fields['folder'].queryset = Folder.objects.filter(user=request.user)
