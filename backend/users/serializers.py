from rest_framework import serializers
from django.contrib.auth.models import User

# UserSerializer is used to return clean user records to the client
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email')

# RegisterSerializer validates registration parameters and creates hashed users in PostgreSQL
class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password')
        # Enforce that password is write-only; it will never be returned in outgoing API JSON responses
        extra_kwargs = {'password': {'write_only': True}}

    # Override ModelSerializer's default save/create action
    def create(self, validated_data):
        # We must use create_user to trigger Django's default PBKDF2 password hashing mechanism
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        return user
