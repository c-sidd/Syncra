from django.urls import path
from .views import RegisterView, LoginView, AWSConnectionView, AWSLifecycleView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('aws/', AWSConnectionView.as_view(), name='aws-connection'),
    path('aws/lifecycle/', AWSLifecycleView.as_view(), name='aws-lifecycle'),
]
