import uuid

from botocore.exceptions import BotoCoreError, ClientError
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser

from .serializers import FileSerializer
from .models import File
from users.views import get_s3_client


class FileUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        client, connection = get_s3_client(request.user)
        if not connection:
            return Response(
                {'detail': 'Connect an AWS S3 bucket in Account settings before uploading.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'file': ['This field is required.']}, status=status.HTTP_400_BAD_REQUEST)

        max_size = settings.MAX_UPLOAD_SIZE_BYTES
        if file_obj.size > max_size:
            return Response(
                {
                    'file': [
                        f'File is too large. Maximum allowed size is {max_size // (1024 * 1024)} MB.'
                    ]
                },
                status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            )

        serializer = FileSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        folder = serializer.validated_data.get('folder')
        prefix = f'{request.user.id}/'
        if folder:
            prefix += f'{folder.id}/'
        object_key = f'{prefix}{uuid.uuid4().hex}-{file_obj.name}'

        try:
            client.upload_fileobj(
                file_obj,
                connection.bucket_name,
                object_key,
                ExtraArgs={
                    'ContentType': file_obj.content_type or 'application/octet-stream',
                    'StorageClass': 'STANDARD',
                },
            )
        except (ClientError, BotoCoreError) as exc:
            return Response({'detail': 'S3 upload failed.'}, status=status.HTTP_502_BAD_GATEWAY)

        try:
            record = serializer.save(
                user=request.user,
                name=file_obj.name,
                size=file_obj.size,
                object_key=object_key,
                storage_class='STANDARD',
            )
        except Exception:
            # Keep the database and bucket consistent when metadata creation fails.
            try:
                client.delete_object(Bucket=connection.bucket_name, Key=object_key)
            except (ClientError, BotoCoreError):
                pass
            raise

        return Response(
            FileSerializer(record, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class FileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        record = get_object_or_404(File, pk=pk, user=request.user)
        client, connection = get_s3_client(request.user)
        if not connection:
            return Response({'detail': 'Connect your S3 storage first.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            url = client.generate_presigned_url(
                'get_object',
                Params={'Bucket': connection.bucket_name, 'Key': record.object_key},
                ExpiresIn=300,
            )
        except (ClientError, BotoCoreError) as exc:
            return Response(
                {'detail': 'Unable to create download link.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({'url': url, 'expires_in': 300})


class FileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, pk):
        record = get_object_or_404(File, pk=pk, user=request.user)
        client, connection = get_s3_client(request.user)
        if connection:
            try:
                client.delete_object(Bucket=connection.bucket_name, Key=record.object_key)
            except (ClientError, BotoCoreError):
                return Response({'detail': 'S3 delete failed.'}, status=status.HTTP_502_BAD_GATEWAY)
        record.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
