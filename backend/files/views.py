from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import FileSerializer
from .models import File

class FileUploadView(APIView):
    # Restrict endpoint to authenticated users
    permission_classes = [IsAuthenticated]
    
    # Configure parsers to decode binary multipart form segments
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        # Instantiate the serializer, passing the request context to filter target folders
        serializer = FileSerializer(data=request.data, context={'request': request})
        
        if serializer.is_valid():
            # Retrieve the file stream object from request's parsed binary segments
            file_obj = request.FILES.get('file')
            if not file_obj:
                return Response({"file": ["This field is required."]}, status=status.HTTP_400_BAD_REQUEST)
                
            # Extract file metadata properties
            file_size = file_obj.size
            file_name = file_obj.name
            
            # Save the file record, mapping it to request.user and attaching metadata parameters
            serializer.save(
                user=request.user,
                name=file_name,
                size=file_size
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        # Return field validation errors
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Fetch file record. Enforces user ownership! (Prevents IDOR)
        file_record = get_object_or_404(File, pk=pk, user=request.user)
        # file_record.file.url returns the presigned URL computed by django-storages
        s3_url = file_record.file.url
        # Redirect browser directly to download bytes from S3
        return HttpResponseRedirect(s3_url)

class FileDetailView(APIView):
    # Enforce token security checks
    permission_classes = [IsAuthenticated]

    # DELETE /api/files/<id>/
    def delete(self, request, pk):
        # 1. Fetch file record. Enforces user ownership! (Prevents IDOR)
        file_record = get_object_or_404(File, pk=pk, user=request.user)
        
        # 2. Delete the actual file object from the S3 Bucket
        # Calling delete(save=False) triggers django-storages S3 engine
        # to send a DeleteObject request to the S3 bucket API
        file_record.file.delete(save=False)
        
        # 3. Delete the metadata row from PostgreSQL
        file_record.delete()
        
        # 4. Return HTTP 204 No Content
        return Response(status=status.HTTP_204_NO_CONTENT)
