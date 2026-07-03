from rest_framework import serializers
from .models import Folder

class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ('id', 'name', 'parent', 'created_at')
        # Ensure clients cannot spoof or modify the created_at timestamp
        read_only_fields = ('created_at',)

    # Restrict the parent directory dropdown selection list to only folders the active user owns
    def __init__(self, *args, **kwargs):
        super(FolderSerializer, self).__init__(*args, **kwargs)
        # Pull the HTTP request object passed inside the view context
        request = self.context.get('request')
        if request and request.user:
            # Overwrite the parent field's validation queryset.
            # DRF will reject any parent folder ID that does not belong to the user with a 400 Validation Error.
            self.fields['parent'].queryset = Folder.objects.filter(user=request.user)
