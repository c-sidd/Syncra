import uuid

from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import FileSerializer
from .models import File
from folders.models import Folder
from users.views import get_s3_client


class FilePresignUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get('name', '')
        try:
            safe_name = FileSerializer.validate_upload_name(name)
        except Exception as exc:
            message = exc.detail if hasattr(exc, 'detail') else str(exc)
            return Response({'name': [message]}, status=status.HTTP_400_BAD_REQUEST)

        try:
            size = int(request.data.get('size'))
        except (TypeError, ValueError):
            return Response({'size': ['A valid file size is required.']}, status=status.HTTP_400_BAD_REQUEST)
        if size < 0:
            return Response({'size': ['File size cannot be negative.']}, status=status.HTTP_400_BAD_REQUEST)
        if size > settings.MAX_UPLOAD_SIZE_BYTES:
            return Response({'size': ['File exceeds the maximum upload size.']}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        folder_id = request.data.get('folder')
        folder = None
        if folder_id not in (None, '', 'null'):
            folder = get_object_or_404(Folder, pk=folder_id, user=request.user)

        try:
            client, connection = get_s3_client(request.user)
        except (BotoCoreError, ClientError):
            return Response({'detail': 'Unable to connect to S3 storage.'}, status=status.HTTP_502_BAD_GATEWAY)
        if not connection:
            return Response({'detail': 'Connect your AWS S3 bucket before uploading.'}, status=status.HTTP_400_BAD_REQUEST)

        prefix = f'{request.user.id}/' + (f'{folder.id}/' if folder else '')
        object_key = f'{prefix}{uuid.uuid4().hex}-{safe_name}'
        content_type = request.data.get('content_type') or 'application/octet-stream'
        try:
            url = client.generate_presigned_url('put_object', Params={'Bucket': connection.bucket_name, 'Key': object_key, 'ContentType': content_type}, ExpiresIn=900, HttpMethod='PUT')
        except (ClientError, BotoCoreError):
            return Response({'detail': 'Unable to create upload link.'}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({'upload_url': url, 'object_key': object_key, 'expires_in': 900, 'name': safe_name, 'size': size, 'content_type': content_type, 'folder': folder.id if folder else None})


class FileCompleteUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        object_key = str(request.data.get('object_key', ''))
        if not object_key.startswith(f'{request.user.id}/'):
            return Response({'object_key': ['Invalid object key.']}, status=status.HTTP_400_BAD_REQUEST)
        name = request.data.get('name', '')
        try:
            safe_name = FileSerializer.validate_upload_name(name)
        except Exception as exc:
            message = exc.detail if hasattr(exc, 'detail') else str(exc)
            return Response({'name': [message]}, status=status.HTTP_400_BAD_REQUEST)
        try:
            client, connection = get_s3_client(request.user)
        except (BotoCoreError, ClientError):
            return Response({'detail': 'Unable to connect to S3 storage.'}, status=status.HTTP_502_BAD_GATEWAY)
        if not connection:
            return Response({'detail': 'S3 storage is not configured.'}, status=status.HTTP_400_BAD_REQUEST)
        folder_id = request.data.get('folder')
        folder = None
        if folder_id not in (None, '', 'null'):
            folder = get_object_or_404(Folder, pk=folder_id, user=request.user)
            if not object_key.startswith(f'{request.user.id}/{folder.id}/'):
                return Response({'detail': 'Object key does not belong to the selected folder.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            head = client.head_object(Bucket=connection.bucket_name, Key=object_key)
        except (ClientError, BotoCoreError):
            return Response({'detail': 'Uploaded object could not be verified in S3.'}, status=status.HTTP_502_BAD_GATEWAY)
        size = int(head.get('ContentLength', 0))
        if size > settings.MAX_UPLOAD_SIZE_BYTES:
            try:
                client.delete_object(Bucket=connection.bucket_name, Key=object_key)
            except (ClientError, BotoCoreError):
                pass
            return Response({'detail': 'Uploaded object exceeds the maximum size.'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        try:
            with transaction.atomic():
                record = File.objects.create(user=request.user, folder=folder, name=safe_name, size=size, object_key=object_key, storage_class=head.get('StorageClass', 'STANDARD'))
        except Exception:
            try:
                client.delete_object(Bucket=connection.bucket_name, Key=object_key)
            except (ClientError, BotoCoreError):
                pass
            return Response({'detail': 'File metadata could not be saved. The upload was rolled back.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(FileSerializer(record, context={'request': request}).data, status=status.HTTP_201_CREATED)


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        try:
            client, connection = get_s3_client(request.user)
        except (BotoCoreError, ClientError):
            return Response({'detail': 'Unable to connect to S3 storage.'}, status=status.HTTP_502_BAD_GATEWAY)
        if not connection:
            return Response({'detail': 'Connect an AWS S3 bucket in Account settings before uploading.'}, status=status.HTTP_400_BAD_REQUEST)
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'file': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
        try:
            safe_name = FileSerializer.validate_upload_name(file_obj.name)
        except Exception as exc:
            message = exc.detail if hasattr(exc, 'detail') else str(exc)
            return Response({'file': [message]}, status=status.HTTP_400_BAD_REQUEST)
        if file_obj.size > settings.MAX_UPLOAD_SIZE_BYTES:
            return Response({'file': ['File is too large.']}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        serializer = FileSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        folder = serializer.validated_data.get('folder')
        prefix = f'{request.user.id}/' + (f'{folder.id}/' if folder else '')
        object_key = f'{prefix}{uuid.uuid4().hex}-{safe_name}'
        try:
            client.upload_fileobj(file_obj, connection.bucket_name, object_key, ExtraArgs={'ContentType': file_obj.content_type or 'application/octet-stream', 'StorageClass': 'STANDARD'})
        except (ClientError, BotoCoreError):
            return Response({'detail': 'S3 upload failed.'}, status=status.HTTP_502_BAD_GATEWAY)
        try:
            with transaction.atomic():
                record = serializer.save(user=request.user, name=safe_name, size=file_obj.size, object_key=object_key, storage_class='STANDARD')
        except Exception:
            try:
                client.delete_object(Bucket=connection.bucket_name, Key=object_key)
            except (ClientError, BotoCoreError):
                pass
            return Response({'detail': 'File metadata could not be saved. The upload was rolled back.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(FileSerializer(record, context={'request': request}).data, status=status.HTTP_201_CREATED)


class FileDownloadView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        record = get_object_or_404(File, pk=pk, user=request.user)
        try:
            client, connection = get_s3_client(request.user)
        except (BotoCoreError, ClientError):
            return Response({'detail': 'Unable to connect to S3 storage.'}, status=status.HTTP_502_BAD_GATEWAY)
        if not connection:
            return Response({'detail': 'Connect your S3 storage first.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            url = client.generate_presigned_url('get_object', Params={'Bucket': connection.bucket_name, 'Key': record.object_key}, ExpiresIn=300)
        except (ClientError, BotoCoreError):
            return Response({'detail': 'Unable to create download link.'}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({'url': url, 'expires_in': 300})


class FileDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, pk):
        record = get_object_or_404(File, pk=pk, user=request.user)
        try:
            client, connection = get_s3_client(request.user)
        except (BotoCoreError, ClientError):
            return Response({'detail': 'Unable to connect to S3 storage.'}, status=status.HTTP_502_BAD_GATEWAY)
        if not connection:
            return Response({'detail': 'S3 storage is not configured.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            client.delete_object(Bucket=connection.bucket_name, Key=record.object_key)
        except (ClientError, BotoCoreError):
            return Response({'detail': 'S3 delete failed. File metadata was preserved.'}, status=status.HTTP_502_BAD_GATEWAY)
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
