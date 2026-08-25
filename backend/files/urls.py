from django.urls import path
from .views import FileUploadView, FilePresignUploadView, FileCompleteUploadView, FileDownloadView, FileDetailView

urlpatterns = [
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    path('upload/presign/', FilePresignUploadView.as_view(), name='file-upload-presign'),
    path('upload/complete/', FileCompleteUploadView.as_view(), name='file-upload-complete'),
    path('<int:pk>/download/', FileDownloadView.as_view(), name='file-download'),
    path('<int:pk>/', FileDetailView.as_view(), name='file-detail'),
]
