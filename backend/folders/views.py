from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from .models import Folder
from .serializers import FolderSerializer
from files.models import File
from users.views import get_s3_client


class CompactFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('id', 'name', 'size', 'uploaded_at', 'folder', 'storage_class')
        read_only_fields = ('id', 'name', 'size', 'uploaded_at', 'folder', 'storage_class')


class FolderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        folders = Folder.objects.filter(user=request.user, parent__isnull=True)
        files = File.objects.filter(user=request.user, folder__isnull=True)
        folder_serializer = FolderSerializer(folders, many=True)
        file_serializer = CompactFileSerializer(files, many=True)
        total_storage = File.objects.filter(user=request.user).aggregate(total=Sum('size'))['total'] or 0

        return Response({
            'current_folder': None,
            'subfolders': folder_serializer.data,
            'files': file_serializer.data,
            'total_storage_used': total_storage,
        }, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = FolderSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FolderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        current_folder = get_object_or_404(Folder, pk=pk, user=request.user)
        subfolders = Folder.objects.filter(user=request.user, parent=current_folder)
        files = File.objects.filter(user=request.user, folder=current_folder)
        total_storage = File.objects.filter(user=request.user).aggregate(total=Sum('size'))['total'] or 0

        return Response({
            'current_folder': FolderSerializer(current_folder).data,
            'subfolders': FolderSerializer(subfolders, many=True).data,
            'files': CompactFileSerializer(files, many=True).data,
            'total_storage_used': total_storage,
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        folder = get_object_or_404(Folder, pk=pk, user=request.user)
        client, connection = get_s3_client(request.user)

        # Delete every object represented by this folder tree from S3 first.
        def delete_folder_contents(current):
            for file_record in File.objects.filter(folder=current, user=request.user):
                if client and connection:
                    try:
                        client.delete_object(Bucket=connection.bucket_name, Key=file_record.object_key)
                    except Exception as exc:
                        raise RuntimeError(f'Could not delete {file_record.name} from S3: {exc}')
                file_record.delete()

            for child in Folder.objects.filter(parent=current, user=request.user):
                delete_folder_contents(child)
                child.delete()

        try:
            delete_folder_contents(folder)
            folder.delete()
        except RuntimeError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(status=status.HTTP_204_NO_CONTENT)
