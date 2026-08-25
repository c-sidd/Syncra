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
        self.email = 'testuser@example.com'
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email=self.email,
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_user_registration(self):
        client = APIClient()
        response = client.post(
            '/api/auth/register/',
            {
                'username': 'newstudent',
                'email': 'newstudent@example.com',
                'password': 'securepassword999',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], 'newstudent')

    def test_user_login(self):
        client = APIClient()
        response = client.post(
            '/api/auth/login/',
            {'username': self.username, 'password': self.password},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_folder_creation_and_listing(self):
        response = self.client.post(
            '/api/folders/', {'name': 'Test Folder', 'parent': None}, format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.get('/api/folders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['subfolders']), 1)
        self.assertEqual(response.data['subfolders'][0]['name'], 'Test Folder')

    @patch('files.views.get_s3_client')
    def test_file_upload_download_and_delete(self, get_s3_client):
        folder = Folder.objects.create(name='Upload Folder', user=self.user)
        mock_client = MagicMock()
        connection = MagicMock(bucket_name='test-bucket')
        get_s3_client.return_value = (mock_client, connection)

        mock_file = SimpleUploadedFile(
            name='notes.txt',
            content=b'Learning Full Stack Development is amazing!',
            content_type='text/plain',
        )
        response = self.client.post(
            '/api/files/upload/',
            {'file': mock_file, 'folder': folder.id},
            format='multipart',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        file_id = response.data['id']
        self.assertEqual(response.data['name'], 'notes.txt')
        self.assertEqual(response.data['size'], 43)
        mock_client.upload_fileobj.assert_called_once()

        mock_client.generate_presigned_url.return_value = 'https://example.test/signed-file'
        response = self.client.get(f'/api/files/{file_id}/download/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['expires_in'], 300)
        self.assertEqual(response.data['url'], 'https://example.test/signed-file')

        response = self.client.delete(f'/api/files/{file_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_client.delete_object.assert_called_once()
        self.assertFalse(File.objects.filter(id=file_id).exists())

    @patch('files.views.get_s3_client')
    def test_upload_rejected_when_file_is_too_large(self, get_s3_client):
        connection = MagicMock(bucket_name='test-bucket')
        get_s3_client.return_value = (MagicMock(), connection)
        with self.settings(MAX_UPLOAD_SIZE_BYTES=4):
            response = self.client.post(
                '/api/files/upload/',
                {'file': SimpleUploadedFile('large.txt', b'12345', content_type='text/plain')},
                format='multipart',
            )
        self.assertEqual(response.status_code, status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        self.assertIn('file', response.data)
        get_s3_client.return_value[0].upload_fileobj.assert_not_called()

    def test_unauthenticated_api_rejection(self):
        response = APIClient().get('/api/folders/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
