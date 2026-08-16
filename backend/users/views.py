import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token

from .serializers import RegisterSerializer, UserSerializer
from .models import AWSConnection
from .crypto import encrypt_value, decrypt_value


class RegisterView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'user': UserSerializer(user).data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        user = authenticate(username=request.data.get('username'), password=request.data.get('password'))
        if user is not None:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key, 'user': UserSerializer(user).data})
        return Response({'non_field_errors': ['Unable to log in with provided credentials.']}, status=status.HTTP_400_BAD_REQUEST)


def get_s3_client(user):
    connection = AWSConnection.objects.filter(user=user).first()
    if not connection:
        return None, None
    client = boto3.client('s3', aws_access_key_id=connection.access_key_id, aws_secret_access_key=decrypt_value(connection.secret_access_key), region_name=connection.region)
    return client, connection


class AWSConnectionView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        connection = AWSConnection.objects.filter(user=request.user).first()
        if not connection:
            return Response({'connected': False})
        return Response({'connected': True, 'id': connection.id, 'name': connection.name, 'access_key_id': connection.access_key_id, 'region': connection.region, 'bucket_name': connection.bucket_name, 'created_at': connection.created_at, 'updated_at': connection.updated_at})

    def post(self, request):
        access_key_id = request.data.get('access_key_id', '').strip()
        secret_access_key = request.data.get('secret_access_key', '').strip()
        region = request.data.get('region', 'us-east-1').strip()
        bucket_name = request.data.get('bucket_name', '').strip()
        name = request.data.get('name', 'My S3 Storage').strip() or 'My S3 Storage'
        existing = AWSConnection.objects.filter(user=request.user).first()
        if existing and not secret_access_key:
            secret_access_key = decrypt_value(existing.secret_access_key)
        if not all([access_key_id, secret_access_key, region, bucket_name]):
            return Response({'detail': 'Access key, secret key, region and bucket are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            s3 = boto3.client('s3', aws_access_key_id=access_key_id, aws_secret_access_key=secret_access_key, region_name=region)
            s3.head_bucket(Bucket=bucket_name)
        except (ClientError, BotoCoreError, NoCredentialsError) as exc:
            return Response({'detail': f'AWS connection failed: {exc}'}, status=status.HTTP_400_BAD_REQUEST)
        connection, _ = AWSConnection.objects.update_or_create(user=request.user, defaults={'name': name, 'access_key_id': access_key_id, 'secret_access_key': encrypt_value(secret_access_key), 'region': region, 'bucket_name': bucket_name})
        return Response({'connected': True, 'id': connection.id, 'name': connection.name, 'region': connection.region, 'bucket_name': connection.bucket_name}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        deleted, _ = AWSConnection.objects.filter(user=request.user).delete()
        return Response({'deleted': bool(deleted)})


class AWSLifecycleView(APIView):
    permission_classes = [IsAuthenticated]
    allowed_classes = {'INTELLIGENT_TIERING', 'STANDARD_IA', 'GLACIER_IR', 'GLACIER', 'DEEP_ARCHIVE'}

    def post(self, request):
        client, connection = get_s3_client(request.user)
        if not connection:
            return Response({'detail': 'Connect your S3 storage first.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            days = int(request.data.get('days', 90))
        except (TypeError, ValueError):
            return Response({'detail': 'days must be an integer.'}, status=status.HTTP_400_BAD_REQUEST)
        storage_class = str(request.data.get('storage_class', 'GLACIER')).upper()
        if days < 1 or storage_class not in self.allowed_classes:
            return Response({'detail': 'Choose valid days and storage class.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            client.put_bucket_lifecycle_configuration(Bucket=connection.bucket_name, LifecycleConfiguration={'Rules': [{'ID': f'syncra-user-{request.user.id}', 'Status': 'Enabled', 'Filter': {'Prefix': f'{request.user.id}/'}, 'Transitions': [{'Days': days, 'StorageClass': storage_class}]}]})
        except (ClientError, BotoCoreError) as exc:
            return Response({'detail': f'Could not save lifecycle rule: {exc}'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'enabled': True, 'days': days, 'storage_class': storage_class})

    def delete(self, request):
        client, connection = get_s3_client(request.user)
        if not connection:
            return Response({'detail': 'Connect your S3 storage first.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            client.put_bucket_lifecycle_configuration(Bucket=connection.bucket_name, LifecycleConfiguration={'Rules': []})
        except (ClientError, BotoCoreError) as exc:
            return Response({'detail': f'Could not remove lifecycle rules: {exc}'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'enabled': False})
