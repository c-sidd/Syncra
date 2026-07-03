from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .serializers import RegisterSerializer, UserSerializer

# RegisterView manages user registrations and returns a secure token key
class RegisterView(APIView):
    # Registration is public; it requires no credentials to access
    permission_classes = []

    def post(self, request):
        # Bind incoming JSON data to the serializer
        serializer = RegisterSerializer(data=request.data)
        
        # Run validations (username uniqueness, email patterns, password constraints)
        if serializer.is_valid():
            # Save user row to PostgreSQL (calls create_user internally)
            user = serializer.save()
            # Retrieve or generate a new 40-character Auth Token for this user
            token, created = Token.objects.get_or_create(user=user)
            
            # Return token and user info with 210 Created status code
            return Response({
                "token": token.key,
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
            
        # If inputs are invalid, return key-value validation errors with 400 Bad Request
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# LoginView authenticates credentials and returns the user's active token
class LoginView(APIView):
    # Login is public
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Authenticate checks the username exists and validates the password hash
        user = authenticate(username=username, password=password)
        
        if user is not None:
            # Fetch the existing token, or create one if missing
            token, created = Token.objects.get_or_create(user=user)
            
            # Return token key and user info
            return Response({
                "token": token.key,
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
            
        # If credentials do not match, return field-level error with 400 Bad Request
        return Response({
            "non_field_errors": ["Unable to log in with provided credentials."]
        }, status=status.HTTP_400_BAD_REQUEST)
