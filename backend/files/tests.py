from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from folders.models import Folder
from .models import File

# Override storage to InMemoryStorage during the test run to avoid calling live AWS S3
@override_settings(STORAGES={
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
})
class SyncraAPITests(TestCase):
    def setUp(self):
        # 1. Instantiate the test client
        self.client = APIClient()
        
        # 2. Create a test user record directly in the test database
        self.username = "testuser"
        self.password = "securepassword123"
        self.email = "testuser@example.com"
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email=self.email
        )
        
        # 3. Create the auth token for this user
        self.token = Token.objects.create(user=self.user)
        
        # 4. Configure the test client to include the Auth header in all subsequent requests
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_user_registration(self):
        # Clear credentials for public registration check
        client = APIClient()
        payload = {
            "username": "newstudent",
            "email": "newstudent@example.com",
            "password": "securepassword999"
        }
        response = client.post('/api/auth/register/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['username'], "newstudent")

    def test_user_login(self):
        client = APIClient()
        payload = {
            "username": self.username,
            "password": self.password
        }
        response = client.post('/api/auth/login/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_folder_creation_and_listing(self):
        # 1. Create a root folder via API
        payload = {"name": "Test Folder", "parent": None}
        response = self.client.post('/api/folders/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        folder_id = response.data['id']
        
        # 2. List root contents. Verify the new folder is displayed
        response = self.client.get('/api/folders/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['subfolders']), 1)
        self.assertEqual(response.data['subfolders'][0]['name'], "Test Folder")

    def test_file_upload_download_and_delete(self):
        # 1. Create a parent folder
        folder = Folder.objects.create(name="Upload Folder", user=self.user)
        
        # 2. Construct a mock binary file payload
        mock_file = SimpleUploadedFile(
            name="notes.txt",
            content=b"Learning Full Stack Development is amazing!",
            content_type="text/plain"
        )
        
        # 3. POST upload request
        payload = {
            "file": mock_file,
            "folder": folder.id
        }
        response = self.client.post('/api/files/upload/', payload, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        file_id = response.data['id']
        self.assertEqual(response.data['name'], "notes.txt")
        self.assertEqual(response.data['size'], 43)  # size in bytes of content string
        
        # 4. GET Download redirect check
        response = self.client.get(f'/api/files/{file_id}/download/')
        # Assert response is a 302 Found redirect
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)
        
        # 5. DELETE File check
        response = self.client.delete(f'/api/files/{file_id}/')
        # Assert deletion succeeded with 204 No Content
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        # Verify row is removed from PostgreSQL database
        self.assertFalse(File.objects.filter(id=file_id).exists())

    def test_unauthenticated_api_rejection(self):
        # Instantiate a client without token headers
        unauth_client = APIClient()
        response = unauth_client.get('/api/folders/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
