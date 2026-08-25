import re

from rest_framework import serializers

from .models import Folder


SAFE_NAME_RE = re.compile(r'^[^/\\\x00-\x1f\x7f]+$')


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ('id', 'name', 'parent', 'created_at')
        read_only_fields = ('created_at',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request and request.user:
            self.fields['parent'].queryset = Folder.objects.filter(user=request.user)

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError('Folder name cannot be empty.')
        if len(value) > 255:
            raise serializers.ValidationError('Folder name cannot exceed 255 characters.')
        if not SAFE_NAME_RE.fullmatch(value):
            raise serializers.ValidationError(
                'Folder name contains invalid path or control characters.'
            )
        return value

    def validate(self, attrs):
        parent = attrs.get('parent')
        instance = self.instance

        if parent and instance:
            if parent.pk == instance.pk:
                raise serializers.ValidationError(
                    {'parent': 'A folder cannot be its own parent.'}
                )

            ancestor = parent
            while ancestor is not None:
                if ancestor.pk == instance.pk:
                    raise serializers.ValidationError(
                        {'parent': 'A folder cannot be moved inside its own descendants.'}
                    )
                ancestor = ancestor.parent

        return attrs
