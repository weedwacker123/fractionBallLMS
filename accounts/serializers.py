"""
Serializers for User and School models
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import School

User = get_user_model()


class SchoolSerializer(serializers.ModelSerializer):
    """Serializer for School model"""
    
    class Meta:
        model = School
        fields = [
            'id',
            'name',
            'domain',
            'address',
            'phone',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    school_name = serializers.CharField(source='school.name', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'firebase_uid',
            'role',
            'school',
            'school_name',
            'phone',
            'is_active',
            'is_staff',
            'created_at',
            'updated_at',
            'last_login'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'last_login', 'full_name', 'school_name']
        extra_kwargs = {
            'password': {'write_only': True},
            'firebase_uid': {'required': False}
        }


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users"""
    
    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'firebase_uid',
            'role',
            'school',
            'phone',
            'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False}
        }
    
    def create(self, validated_data):
        """Create user with properly hashed password"""
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        
        if password:
            user.set_password(password)
        else:
            # Set unusable password for Firebase-only accounts
            user.set_unusable_password()
        
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating existing users"""
    
    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'email',
            'role',
            'school',
            'phone',
            'is_active'
        ]































