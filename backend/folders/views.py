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
            File.objects.filter(user=request.user, folder__isnull=True, deleted_at__isnull=True).order_by('-uploaded_at', 'id'),
            request.query_params.get('files_page', 1),
        )
        total_storage = File.objects.filter(user=request.user, deleted_at__isnull=True).aggregate(total=Sum('size'))['total'] or 0

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


class FolderTreeView(APIView):
    """Small, ownership-scoped folder list for move pickers."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        folders = Folder.objects.filter(user=request.user).order_by('name', 'id')
        return Response(FolderSerializer(folders, many=True).data)


class FolderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        current_folder = get_object_or_404(Folder, pk=pk, user=request.user)
        subfolders_page, subfolders_paginator = _paginate(
            Folder.objects.filter(user=request.user, parent=current_folder).order_by('name', 'id'),
            request.query_params.get('folders_page', 1),
        )
        files_page, files_paginator = _paginate(
            File.objects.filter(user=request.user, folder=current_folder, deleted_at__isnull=True).order_by('-uploaded_at', 'id'),
            request.query_params.get('files_page', 1),
        )
        total_storage = File.objects.filter(user=request.user, deleted_at__isnull=True).aggregate(total=Sum('size'))['total'] or 0

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

    def patch(self, request, pk):
        folder = get_object_or_404(Folder, pk=pk, user=request.user)
        serializer = FolderSerializer(folder, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        folder = get_object_or_404(Folder, pk=pk, user=request.user)
        client, connection = get_s3_client(request.user)
        if not client or not connection:
            return Response({'detail': 'S3 storage is not configured.'}, status=status.HTTP_400_BAD_REQUEST)

        stack = [folder]
        folders = []
        files = []
        while stack:
            current = stack.pop()
            folders.append(current)
            stack.extend(Folder.objects.filter(parent=current, user=request.user))
            files.extend(File.objects.filter(folder=current, user=request.user))

        try:
            keys = [{'Key': item.object_key} for item in files]
            for offset in range(0, len(keys), 1000):
                batch = keys[offset:offset + 1000]
                if not batch:
                    continue
                response = client.delete_objects(
                    Bucket=connection.bucket_name,
                    Delete={'Objects': batch, 'Quiet': True},
                )
                if response.get('Errors'):
                    raise StorageDeletionError
        except (ClientError, BotoCoreError, StorageDeletionError):
            return Response({'detail': 'S3 deletion failed. Folder metadata was not removed.'}, status=status.HTTP_502_BAD_GATEWAY)

        from django.db import transaction
        with transaction.atomic():
            File.objects.filter(pk__in=[item.pk for item in files]).delete()
            Folder.objects.filter(pk__in=[item.pk for item in folders]).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class StorageDeletionError(Exception):
    """Internal exception used to avoid exposing provider error details."""
