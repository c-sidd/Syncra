import re

from rest_framework import serializers

from .models import File
from folders.models import Folder


SAFE_FILE_NAME_RE = re.compile(r'^[^/\\\x00-\x1f\x7f]+$')


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

    @staticmethod
    def validate_upload_name(name):
        name = name.strip()
        if not name:
            raise serializers.ValidationError('File name cannot be empty.')
        if len(name) > 255:
            raise serializers.ValidationError('File name cannot exceed 255 characters.')
        if not SAFE_FILE_NAME_RE.fullmatch(name):
            raise serializers.ValidationError(
                'File name contains invalid path or control characters.'
            )
        if name in {'.', '..'}:
            raise serializers.ValidationError('Invalid file name.')
        return name

    def validate(self, attrs):
        request = self.context.get('request')
        folder = attrs.get('folder')
        if request and folder and folder.user_id != request.user.id:
            raise serializers.ValidationError({'folder': 'Invalid folder.'})
        return attrs
