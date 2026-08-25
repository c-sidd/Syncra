from django.urls import path
from .views import (
    FileUploadView,
    FilePresignUploadView,
    FileCompleteUploadView,
    FileMultipartInitiateView,
    FileMultipartCompleteView,
    FileDownloadView,
    FileDetailView,
)

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('upload/presign/', FilePresignUploadView.as_view(), name='file-upload-presign'),
    path('upload/complete/', FileCompleteUploadView.as_view(), name='file-upload-complete'),
    path('upload/multipart/initiate/', FileMultipartInitiateView.as_view(), name='file-upload-multipart-initiate'),
    path('upload/multipart/complete/', FileMultipartCompleteView.as_view(), name='file-upload-multipart-complete'),
    path('<int:pk>/download/', FileDownloadView.as_view(), name='file-download'),
    path('<int:pk>/', FileDetailView.as_view(), name='file-detail'),
]
