from django.urls import path
from .views import RegisterView, LoginView, AWSConnectionView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('aws/', AWSConnectionView.as_view(), name='aws-connection'),
]
