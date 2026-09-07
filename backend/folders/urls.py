from django.urls import path
from .views import FolderListCreateView, FolderDetailView, FolderTreeView

urlpatterns = [
    # Map GET/POST /api/folders/ to the root list-create handler
    path('', FolderListCreateView.as_view(), name='folder-list-create'),
    path('tree/', FolderTreeView.as_view(), name='folder-tree'),
    # Map GET /api/folders/<id>/ to the detail subdirectory contents list handler
    path('<int:pk>/', FolderDetailView.as_view(), name='folder-detail'),
]
