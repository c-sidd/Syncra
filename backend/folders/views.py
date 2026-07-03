from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Folder
from .serializers import FolderSerializer
from files.models import File
from rest_framework import serializers

# Compact File Serializer for displaying nested file lists inside folders
class CompactFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('id', 'name', 'file', 'size', 'uploaded_at')


# Handles listing ROOT directories and creating folders
class FolderListCreateView(APIView):
    # Enforce Token Authentication. Anonymous users will receive 401 Unauthorized.
    permission_classes = [IsAuthenticated]

    # GET /api/folders/ - List all root folders and files (where parent/folder is NULL)
    def get(self, request):
        # Fetch root folders owned by this user
        folders = Folder.objects.filter(user=request.user, parent__isnull=True)
        # Fetch root files owned by this user
        files = File.objects.filter(user=request.user, folder__isnull=True)
        
        # Serialize database row sets into JSON lists
        folder_serializer = FolderSerializer(folders, many=True)
        file_serializer = CompactFileSerializer(files, many=True)
        
        return Response({
            "current_folder": None,
            "subfolders": folder_serializer.data,
            "files": file_serializer.data
        }, status=status.HTTP_200_OK)

    # POST /api/folders/ - Create a folder
    def post(self, request):
        # Pass the request in the context dictionary so the serializer can restrict parent queryset validations
        serializer = FolderSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # Save the record, attaching the authenticated user as the owner
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        # If input data is malformed (e.g. name blank or parent not owned by user), return validation list
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Handles listing contents of specific nested subdirectories
class FolderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    # GET /api/folders/<id>/ - List contents of a specific folder
    def get(self, request, pk):
        # Fetch folder metadata. Enforces ownership: returns 404 if folder is owned by another user (Prevents IDOR)
        current_folder = get_object_or_404(Folder, pk=pk, user=request.user)
        
        # Fetch subfolders and nested files contained in this folder
        subfolders = Folder.objects.filter(user=request.user, parent=current_folder)
        files = File.objects.filter(user=request.user, folder=current_folder)
        
        folder_serializer = FolderSerializer(subfolders, many=True)
        file_serializer = CompactFileSerializer(files, many=True)
        
        return Response({
            "current_folder": FolderSerializer(current_folder).data,
            "subfolders": folder_serializer.data,
            "files": file_serializer.data
        }, status=status.HTTP_200_OK)
