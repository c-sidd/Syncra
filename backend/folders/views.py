from botocore.exceptions import BotoCoreError, ClientError
from django.core.paginator import Paginator
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


PAGE_SIZE = 50


class CompactFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ('id', 'name', 'size', 'uploaded_at', 'folder', 'storage_class')
        read_only_fields = ('id', 'name', 'size', 'uploaded_at', 'folder', 'storage_class')


def _paginate(queryset, page):
    paginator = Paginator(queryset, PAGE_SIZE)
    current_page = paginator.get_page(page)
    return current_page, paginator


class FolderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        folders_page, folders_paginator = _paginate(
            Folder.objects.filter(user=request.user, parent__isnull=True).order_by('name', 'id'),
            request.query_params.get('folders_page', 1),
        )
        files_page, files_paginator = _paginate(
            File.objects.filter(user=request.user, folder__isnull=True).order_by('-uploaded_at', 'id'),
            request.query_params.get('files_page', 1),
        )
        total_storage = File.objects.filter(user=request.user).aggregate(total=Sum('size'))['total'] or 0

        return Response({
            'current_folder': None,
            'subfolders': FolderSerializer(folders_page.object_list, many=True).data,
            'files': CompactFileSerializer(files_page.object_list, many=True).data,
            'total_storage_used': total_storage,
            'pagination': {
                'folders_page': folders_page.number,
                'folders_pages': folders_paginator.num_pages,
                'folders_has_next': folders_page.has_next(),
                'files_page': files_page.number,
                'files_pages': files_paginator.num_pages,
                'files_has_next': files_page.has_next(),
                'page_size': PAGE_SIZE,
            },
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
        subfolders_page, subfolders_paginator = _paginate(
            Folder.objects.filter(user=request.user, parent=current_folder).order_by('name', 'id'),
            request.query_params.get('folders_page', 1),
        )
        files_page, files_paginator = _paginate(
            File.objects.filter(user=request.user, folder=current_folder).order_by('-uploaded_at', 'id'),
            request.query_params.get('files_page', 1),
        )
        total_storage = File.objects.filter(user=request.user).aggregate(total=Sum('size'))['total'] or 0

        return Response({
            'current_folder': FolderSerializer(current_folder).data,
            'subfolders': FolderSerializer(subfolders_page.object_list, many=True).data,
            'files': CompactFileSerializer(files_page.object_list, many=True).data,
            'total_storage_used': total_storage,
            'pagination': {
                'folders_page': subfolders_page.number,
                'folders_pages': subfolders_paginator.num_pages,
                'folders_has_next': subfolders_page.has_next(),
                'files_page': files_page.number,
                'files_pages': files_paginator.num_pages,
                'files_has_next': files_page.has_next(),
                'page_size': PAGE_SIZE,
            },
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        folder = get_object_or_404(Folder, pk=pk, user=request.user)
        client, connection = get_s3_client(request.user)

        if not client or not connection:
            return Response({'detail': 'S3 storage is not configured.'}, status=status.HTTP_400_BAD_REQUEST)

        def delete_folder_contents(current):
            for file_record in File.objects.filter(folder=current, user=request.user):
                try:
                    client.delete_object(Bucket=connection.bucket_name, Key=file_record.object_key)
                except (ClientError, BotoCoreError) as exc:
                    raise StorageDeletionError from exc
                file_record.delete()

            for child in Folder.objects.filter(parent=current, user=request.user):
                delete_folder_contents(child)
                child.delete()

        try:
            delete_folder_contents(folder)
            folder.delete()
        except StorageDeletionError:
            return Response({'detail': 'S3 deletion failed. Folder metadata was preserved for the remaining objects.'}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(status=status.HTTP_204_NO_CONTENT)


class StorageDeletionError(Exception):
    """Internal exception used to avoid exposing provider error details."""
