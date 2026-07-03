from django.urls import path
from .views import RegisterView, LoginView

urlpatterns = [
    # Map POST /api/auth/register/ to RegisterView
    path('register/', RegisterView.as_view(), name='register'),
    # Map POST /api/auth/login/ to LoginView
    path('login/', LoginView.as_view(), name='login'),
]
