import uuid

from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import FileSerializer
from .models import File, UploadSession
from folders.models import Folder
from users.views import get_s3_client


MULTIPART_PART_SIZE = 8 * 1024 * 1024
MULTIPART_MAX_PARTS = 10_000


def storage_client(request):
    try:
        result = get_s3_client(request.user)
        if not result or len(result) != 2:
            return None, None, Response({'detail': 'Unable to connect to S3 storage.'}, status=status.HTTP_502_BAD_GATEWAY)
        client, connection = result
    except (BotoCoreError, ClientError, TypeError, ValueError):
        return None, None, Response({'detail': 'Unable to connect to S3 storage.'}, status=status.HTTP_502_BAD_GATEWAY)
    if not connection:
        return None, None, Response({'detail': 'Connect your AWS S3 bucket before uploading files.'}, status=status.HTTP_400_BAD_REQUEST)
    return client, connection, None


def create_upload_session(*, user, folder, name, size, content_type, is_multipart, multipart_upload_id='', part_count=0):
    prefix = f'{user.id}/' + (f'{folder.id}/' if folder else '')
    object_key = f'{prefix}{uuid.uuid4().hex}-{name}'
    return UploadSession.objects.create(
        user=user, folder=folder, object_key=object_key, name=name, size=size,
        content_type=content_type, is_multipart=is_multipart,
        multipart_upload_id=multipart_upload_id, part_count=part_count,
    )


def pending_session_or_error(request, object_key, *, multipart=False, upload_id=''):
    try:
        session = UploadSession.objects.get(user=request.user, object_key=object_key)
    except UploadSession.DoesNotExist:
        return None, Response({'detail': 'Unknown upload session.'}, status=status.HTTP_400_BAD_REQUEST)
    if not session.is_active() or session.is_multipart != multipart or (multipart and session.multipart_upload_id != upload_id):
        return None, Response({'detail': 'Upload session is no longer active.'}, status=status.HTTP_400_BAD_REQUEST)
    return session, None


class FilePresignUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get('name', '')
        try:
            safe_name = FileSerializer.validate_upload_name(name)
            size = int(request.data.get('size'))
        except (TypeError, ValueError):
            return Response({'size': ['A valid file size is required.']}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({'name': [exc.detail if hasattr(exc, 'detail') else str(exc)]}, status=status.HTTP_400_BAD_REQUEST)
        if size < 0:
            return Response({'size': ['File size cannot be negative.']}, status=status.HTTP_400_BAD_REQUEST)
        if settings.STORAGE_QUOTA_BYTES > 0:
            from django.db.models import Sum
            used = File.objects.filter(user=request.user, deleted_at__isnull=True).aggregate(total=Sum('size'))['total'] or 0
            if used + size > settings.STORAGE_QUOTA_BYTES:
                return Response({'detail': 'Storage quota exceeded.'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        if size > settings.MAX_UPLOAD_SIZE_BYTES:
            return Response({'size': ['File exceeds the maximum upload size.']}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        folder_id = request.data.get('folder')
        folder = None if folder_id in (None, '', 'null') else get_object_or_404(Folder, pk=folder_id, user=request.user)
        client, connection, error = storage_client(request)
        if error:
            return error
        content_type = request.data.get('content_type') or 'application/octet-stream'
        session = create_upload_session(user=request.user, folder=folder, name=safe_name, size=size, content_type=content_type, is_multipart=False)
        try:
            url = client.generate_presigned_url('put_object', Params={'Bucket': connection.bucket_name, 'Key': session.object_key, 'ContentType': content_type}, ExpiresIn=900, HttpMethod='PUT')
        except (ClientError, BotoCoreError):
            session.delete()
            return Response({'detail': 'Unable to create upload link.'}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({'upload_url': url, 'object_key': session.object_key, 'expires_in': 900, 'name': safe_name, 'size': size, 'content_type': content_type, 'folder': folder.id if folder else None})


class FileCompleteUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        object_key = str(request.data.get('object_key', ''))
        name = request.data.get('name', '')
        try:
            safe_name = FileSerializer.validate_upload_name(name)
        except Exception as exc:
            return Response({'name': [exc.detail if hasattr(exc, 'detail') else str(exc)]}, status=status.HTTP_400_BAD_REQUEST)
        client, connection, error = storage_client(request)
        if error:
            return error
        session, error = pending_session_or_error(request, object_key)
        if error:
            return error
        if safe_name != session.name or request.data.get('folder') not in (None, '', 'null', session.folder_id):
            return Response({'detail': 'Upload details do not match the issued upload session.'}, status=status.HTTP_400_BAD_REQUEST)
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
                record = File.objects.create(user=request.user, folder=session.folder, name=safe_name, size=size, object_key=object_key, storage_class=head.get('StorageClass', 'STANDARD'))
                session.state = UploadSession.State.COMPLETED
                session.save(update_fields=['state'])
        except Exception:
            try:
                client.delete_object(Bucket=connection.bucket_name, Key=object_key)
            except (ClientError, BotoCoreError):
                pass
            return Response({'detail': 'File metadata could not be saved. The upload was rolled back.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(FileSerializer(record, context={'request': request}).data, status=status.HTTP_201_CREATED)


class FileMultipartInitiateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        name = request.data.get('name', '')
        try:
            safe_name = FileSerializer.validate_upload_name(name)
            size = int(request.data.get('size'))
        except (TypeError, ValueError):
            return Response({'size': ['A valid file size is required.']}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as exc:
            return Response({'name': [exc.detail if hasattr(exc, 'detail') else str(exc)]}, status=status.HTTP_400_BAD_REQUEST)
        if size <= MULTIPART_PART_SIZE or size > settings.MAX_UPLOAD_SIZE_BYTES:
            return Response({'size': ['Multipart upload requires a file larger than 8 MB and within the configured maximum.']}, status=status.HTTP_400_BAD_REQUEST)
        folder_id = request.data.get('folder')
        folder = None if folder_id in (None, '', 'null') else get_object_or_404(Folder, pk=folder_id, user=request.user)
        client, connection, error = storage_client(request)
        if error:
            return error
        content_type = request.data.get('content_type') or 'application/octet-stream'
        try:
            temporary_key = f"{request.user.id}/" + (f'{folder.id}/' if folder else '') + f'{uuid.uuid4().hex}-{safe_name}'
            result = client.create_multipart_upload(Bucket=connection.bucket_name, Key=temporary_key, ContentType=content_type, StorageClass='STANDARD')
        except (ClientError, BotoCoreError):
            return Response({'detail': 'Unable to start multipart upload.'}, status=status.HTTP_502_BAD_GATEWAY)
        part_count = (size + MULTIPART_PART_SIZE - 1) // MULTIPART_PART_SIZE
        urls = []
        try:
            for part_number in range(1, part_count + 1):
                urls.append({'part_number': part_number, 'url': client.generate_presigned_url('upload_part', Params={'Bucket': connection.bucket_name, 'Key': temporary_key, 'UploadId': result['UploadId'], 'PartNumber': part_number}, ExpiresIn=900, HttpMethod='PUT')})
        except (ClientError, BotoCoreError):
            try:
                client.abort_multipart_upload(Bucket=connection.bucket_name, Key=temporary_key, UploadId=result['UploadId'])
            except (ClientError, BotoCoreError):
                pass
            return Response({'detail': 'Unable to create multipart upload links.'}, status=status.HTTP_502_BAD_GATEWAY)
        session = UploadSession.objects.create(user=request.user, folder=folder, object_key=temporary_key, name=safe_name, size=size, content_type=content_type, is_multipart=True, multipart_upload_id=result['UploadId'], part_count=part_count)
        return Response({'upload_id': result['UploadId'], 'object_key': session.object_key, 'part_size': MULTIPART_PART_SIZE, 'parts': urls, 'name': safe_name, 'size': size, 'folder': folder.id if folder else None, 'expires_in': 900})


class FileMultipartCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        key = str(request.data.get('object_key', ''))
        upload_id = str(request.data.get('upload_id', ''))
        parts = request.data.get('parts')
        if not key or not upload_id or not isinstance(parts, list) or not parts:
            return Response({'detail': 'Invalid multipart upload completion request.'}, status=status.HTTP_400_BAD_REQUEST)
        normalized = []
        seen = set()
        try:
            for part in parts:
                number = int(part['PartNumber'])
                etag = str(part['ETag'])
                if number < 1 or number > MULTIPART_MAX_PARTS or number in seen or not etag:
                    raise ValueError
                seen.add(number)
                normalized.append({'PartNumber': number, 'ETag': etag})
            normalized.sort(key=lambda item: item['PartNumber'])
        except (KeyError, TypeError, ValueError):
            return Response({'parts': ['Parts must contain unique PartNumber and ETag values.']}, status=status.HTTP_400_BAD_REQUEST)
        client, connection, error = storage_client(request)
        if error:
            return error
        session, error = pending_session_or_error(request, key, multipart=True, upload_id=upload_id)
        if error:
            return error
        expected_parts = set(range(1, session.part_count + 1))
        if set(seen) != expected_parts:
            return Response({'parts': ['All expected multipart parts must be present exactly once.']}, status=status.HTTP_400_BAD_REQUEST)
        try:
            client.complete_multipart_upload(Bucket=connection.bucket_name, Key=key, UploadId=upload_id, MultipartUpload={'Parts': normalized})
            head = client.head_object(Bucket=connection.bucket_name, Key=key)
        except (ClientError, BotoCoreError):
            return Response({'detail': 'Unable to complete or verify multipart upload.'}, status=status.HTTP_502_BAD_GATEWAY)
        size = int(head.get('ContentLength', 0))
        if size > settings.MAX_UPLOAD_SIZE_BYTES:
            try:
                client.delete_object(Bucket=connection.bucket_name, Key=key)
            except (ClientError, BotoCoreError):
                pass
            return Response({'detail': 'Uploaded object exceeds the maximum size.'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        name = request.data.get('name', '')
        try:
            safe_name = FileSerializer.validate_upload_name(name)
        except Exception as exc:
            return Response({'name': [exc.detail if hasattr(exc, 'detail') else str(exc)]}, status=status.HTTP_400_BAD_REQUEST)
        if safe_name != session.name or request.data.get('folder') not in (None, '', 'null', session.folder_id):
            return Response({'detail': 'Upload details do not match the issued upload session.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                record = File.objects.create(user=request.user, folder=session.folder, name=safe_name, size=size, object_key=key, storage_class=head.get('StorageClass', 'STANDARD'))
                session.state = UploadSession.State.COMPLETED
                session.save(update_fields=['state'])
        except Exception:
            try:
                client.delete_object(Bucket=connection.bucket_name, Key=key)
            except (ClientError, BotoCoreError):
                pass
            return Response({'detail': 'File metadata could not be saved. The upload was rolled back.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(FileSerializer(record, context={'request': request}).data, status=status.HTTP_201_CREATED)


class FileMultipartAbortView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        key = str(request.data.get('object_key', ''))
        upload_id = str(request.data.get('upload_id', ''))
        session, error = pending_session_or_error(request, key, multipart=True, upload_id=upload_id)
        if error:
            return error
        client, connection, error = storage_client(request)
        if error:
            return error
        try:
            client.abort_multipart_upload(Bucket=connection.bucket_name, Key=key, UploadId=upload_id)
        except (ClientError, BotoCoreError):
            return Response({'detail': 'Unable to cancel multipart upload.'}, status=status.HTTP_502_BAD_GATEWAY)
        session.state = UploadSession.State.ABORTED
        session.save(update_fields=['state'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'file': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)
        try:
            safe_name = FileSerializer.validate_upload_name(file_obj.name)
        except Exception as exc:
            return Response({'file': [exc.detail if hasattr(exc, 'detail') else str(exc)]}, status=status.HTTP_400_BAD_REQUEST)
        if file_obj.size > settings.MAX_UPLOAD_SIZE_BYTES:
            return Response({'file': ['File is too large.']}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        serializer = FileSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        client, connection, error = storage_client(request)
        if error:
            return error
        folder = serializer.validated_data.get('folder')
        prefix = f'{request.user.id}/' + (f'{folder.id}/' if folder else '')
        key = f'{prefix}{uuid.uuid4().hex}-{safe_name}'
        try:
            client.upload_fileobj(file_obj, connection.bucket_name, key, ExtraArgs={'ContentType': file_obj.content_type or 'application/octet-stream', 'StorageClass': 'STANDARD'})
        except (ClientError, BotoCoreError):
            return Response({'detail': 'S3 upload failed.'}, status=status.HTTP_502_BAD_GATEWAY)
        try:
            with transaction.atomic():
                record = serializer.save(user=request.user, name=safe_name, size=file_obj.size, object_key=key, storage_class='STANDARD')
        except Exception:
            try:
                client.delete_object(Bucket=connection.bucket_name, Key=key)
            except (ClientError, BotoCoreError):
                pass
            return Response({'detail': 'File metadata could not be saved. The upload was rolled back.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(FileSerializer(record, context={'request': request}).data, status=status.HTTP_201_CREATED)


class FileDownloadView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, pk):
        record = get_object_or_404(File, pk=pk, user=request.user, deleted_at__isnull=True)
        client, connection, error = storage_client(request)
        if error:
            return error
        try:
            url = client.generate_presigned_url('get_object', Params={'Bucket': connection.bucket_name, 'Key': record.object_key}, ExpiresIn=300)
        except (ClientError, BotoCoreError):
            return Response({'detail': 'Unable to create download link.'}, status=status.HTTP_502_BAD_GATEWAY)
        return Response({'url': url, 'expires_in': 300})


class FileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        record = get_object_or_404(File, pk=pk, user=request.user, deleted_at__isnull=True)
        serializer = FileSerializer(record, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(FileSerializer(record, context={'request': request}).data)

    def delete(self, request, pk):
        record = get_object_or_404(File, pk=pk, user=request.user, deleted_at__isnull=True)
        record.deleted_at = timezone.now()
        record.save(update_fields=['deleted_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)


class TrashListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        records = File.objects.filter(user=request.user, deleted_at__isnull=False).order_by('-deleted_at')
        return Response(FileSerializer(records, many=True, context={'request': request}).data)


class FileRestoreView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        record = get_object_or_404(File, pk=pk, user=request.user, deleted_at__isnull=False)
        record.deleted_at = None
        record.save(update_fields=['deleted_at'])
        return Response(FileSerializer(record, context={'request': request}).data)


class FilePermanentDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        record = get_object_or_404(File, pk=pk, user=request.user, deleted_at__isnull=False)
        client, connection, error = storage_client(request)
        if error:
            return error
        try:
            client.delete_object(Bucket=connection.bucket_name, Key=record.object_key)
        except (ClientError, BotoCoreError):
            return Response({'detail': 'S3 delete failed. File metadata was preserved.'}, status=status.HTTP_502_BAD_GATEWAY)
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
