from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token

from folders.models import Folder
from .models import File


class SyncraAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.username = 'testuser'
        self.password = 'securepassword123'
        self.user = User.objects.create_user(username=self.username, password=self.password, email='testuser@example.com')
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_user_registration(self):
        response = APIClient().post('/api/auth/register/', {'username': 'newstudent', 'email': 'newstudent@example.com', 'password': 'securepassword999'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)

    def test_user_login(self):
        response = APIClient().post('/api/auth/login/', {'username': self.username, 'password': self.password}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_folder_creation_and_listing(self):
        response = self.client.post('/api/folders/', {'name': 'Test Folder', 'parent': None}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        response = self.client.get('/api/folders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['subfolders']), 1)

    @patch('files.views.get_s3_client')
    def test_presigned_upload_and_complete(self, get_s3_client):
        folder = Folder.objects.create(name='Upload Folder', user=self.user)
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = 'https://example.test/upload'
        mock_client.head_object.return_value = {'ContentLength': 5, 'StorageClass': 'STANDARD'}
        get_s3_client.return_value = (mock_client, MagicMock(bucket_name='test-bucket'))
        response = self.client.post('/api/files/upload/presign/', {'name': 'notes.txt', 'size': 5, 'content_type': 'text/plain', 'folder': folder.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        object_key = response.data['object_key']
        self.assertTrue(object_key.startswith(f'{self.user.id}/{folder.id}/'))
        response = self.client.post('/api/files/upload/complete/', {'object_key': object_key, 'name': 'notes.txt', 'folder': folder.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['size'], 5)
        self.assertTrue(File.objects.filter(object_key=object_key, user=self.user).exists())

    @patch('files.views.get_s3_client')
    def test_presign_rejects_oversized_file(self, get_s3_client):
        with self.settings(MAX_UPLOAD_SIZE_BYTES=4):
            response = self.client.post('/api/files/upload/presign/', {'name': 'large.txt', 'size': 5}, format='json')
        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        get_s3_client.assert_not_called()

    @patch('files.views.get_s3_client')
    def test_multipart_initiate_and_complete(self, get_s3_client):
        folder = Folder.objects.create(name='Large Files', user=self.user)
        mock_client = MagicMock()
        mock_client.create_multipart_upload.return_value = {'UploadId': 'upload-123'}
        mock_client.generate_presigned_url.side_effect = lambda operation, **kwargs: f'https://example.test/{operation}/{kwargs["Params"]["PartNumber"]}'
        mock_client.head_object.return_value = {'ContentLength': 9 * 1024 * 1024, 'StorageClass': 'STANDARD'}
        get_s3_client.return_value = (mock_client, MagicMock(bucket_name='test-bucket'))
        response = self.client.post('/api/files/upload/multipart/initiate/', {'name': 'large.bin', 'size': 9 * 1024 * 1024, 'folder': folder.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['parts']), 2)
        key = response.data['object_key']
        response = self.client.post('/api/files/upload/multipart/complete/', {'object_key': key, 'upload_id': 'upload-123', 'name': 'large.bin', 'folder': folder.id, 'parts': [{'PartNumber': 1, 'ETag': '"a"'}, {'PartNumber': 2, 'ETag': '"b"'}]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_client.complete_multipart_upload.assert_called_once()
        self.assertTrue(File.objects.filter(object_key=key, user=self.user).exists())

    @patch('files.views.get_s3_client')
    def test_multipart_rejects_invalid_parts(self, get_s3_client):
        response = self.client.post('/api/files/upload/multipart/complete/', {'object_key': f'{self.user.id}/x', 'upload_id': 'u', 'parts': [{'PartNumber': 1, 'ETag': 'x'}, {'PartNumber': 1, 'ETag': 'y'}]}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        get_s3_client.assert_not_called()

    @patch('files.views.get_s3_client')
    def test_file_upload_download_and_delete(self, get_s3_client):
        folder = Folder.objects.create(name='Upload Folder', user=self.user)
        mock_client = MagicMock()
        connection = MagicMock(bucket_name='test-bucket')
        get_s3_client.return_value = (mock_client, connection)
        mock_file = SimpleUploadedFile('notes.txt', b'Learning Full Stack Development is amazing!', content_type='text/plain')
        response = self.client.post('/api/files/upload/', {'file': mock_file, 'folder': folder.id}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        file_id = response.data['id']
        mock_client.upload_fileobj.assert_called_once()
        mock_client.generate_presigned_url.return_value = 'https://example.test/signed-file'
        response = self.client.get(f'/api/files/{file_id}/download/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.delete(f'/api/files/{file_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(File.objects.filter(id=file_id).exists())

    @patch('files.views.get_s3_client')
    def test_upload_rejected_when_file_is_too_large(self, get_s3_client):
        with self.settings(MAX_UPLOAD_SIZE_BYTES=4):
            response = self.client.post('/api/files/upload/', {'file': SimpleUploadedFile('large.txt', b'12345', content_type='text/plain')}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

    def test_unauthenticated_api_rejection(self):
        response = APIClient().get('/api/folders/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
