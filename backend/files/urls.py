from django.urls import path
from .views import FileUploadView, FileDownloadView, FileDetailView

urlpatterns = [
    # Map POST /api/files/upload/ to FileUploadView
    path('upload/', FileUploadView.as_view(), name='file-upload'),
    # Map GET /api/files/<id>/download/ to FileDownloadView
    path('<int:pk>/download/', FileDownloadView.as_view(), name='file-download'),
    # Map DELETE /api/files/<id>/ to FileDetailView
    path('<int:pk>/', FileDetailView.as_view(), name='file-detail'),
]
