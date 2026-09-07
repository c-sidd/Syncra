from django.urls import path
from .views import (
    FileUploadView,
    FilePresignUploadView,
    FileCompleteUploadView,
    FileMultipartInitiateView,
    FileMultipartCompleteView,
    FileMultipartAbortView,
    FileDownloadView,
    FileDetailView,
    TrashListView,
    FileRestoreView,
    FilePermanentDeleteView,
)

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('upload/presign/', FilePresignUploadView.as_view(), name='file-upload-presign'),
    path('upload/complete/', FileCompleteUploadView.as_view(), name='file-upload-complete'),
    path('upload/multipart/initiate/', FileMultipartInitiateView.as_view(), name='file-upload-multipart-initiate'),
    path('upload/multipart/complete/', FileMultipartCompleteView.as_view(), name='file-upload-multipart-complete'),
    path('upload/multipart/abort/', FileMultipartAbortView.as_view(), name='file-upload-multipart-abort'),
    path('<int:pk>/download/', FileDownloadView.as_view(), name='file-download'),
    path('trash/', TrashListView.as_view(), name='file-trash'),
    path('<int:pk>/restore/', FileRestoreView.as_view(), name='file-restore'),
    path('<int:pk>/permanent/', FilePermanentDeleteView.as_view(), name='file-permanent-delete'),
    path('<int:pk>/', FileDetailView.as_view(), name='file-detail'),
]
