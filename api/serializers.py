from rest_framework import serializers
from accounts.models import User, School


class SchoolSerializer(serializers.ModelSerializer):
    """Serializer for School model"""
    
    user_count = serializers.SerializerMethodField()
    
    class Meta:
        model = School
        fields = [
            'id', 'name', 'domain', 'address', 'phone', 
            'user_count', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'user_count']
    
    def get_user_count(self, obj):
        """Get count of active users in this school"""
        return obj.user_set.filter(is_active=True).count()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""
    
    school_name = serializers.CharField(source='school.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'school', 'school_name', 'phone',
            'is_active', 'created_at', 'updated_at', 'last_login'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_login', 'full_name', 'role_display', 'school_name']
    
    def validate_email(self, value):
        """Validate email uniqueness"""
        if User.objects.filter(email=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new users (admin only)"""
    
    password = serializers.CharField(write_only=True, required=False)
    firebase_uid = serializers.CharField(required=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name', 
            'role', 'school', 'phone', 'firebase_uid', 'password'
        ]
    
    def create(self, validated_data):
        """Create user with proper password handling"""
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user
    
    def validate_firebase_uid(self, value):
        """Validate Firebase UID uniqueness"""
        if User.objects.filter(firebase_uid=value).exists():
            raise serializers.ValidationError("A user with this Firebase UID already exists.")
        return value


class MeSerializer(serializers.ModelSerializer):
    """Serializer for current user profile"""
    
    school_name = serializers.CharField(source='school.name', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'school', 'school_name', 'phone',
            'permissions', 'is_active', 'created_at', 'last_login'
        ]
        read_only_fields = [
            'id', 'username', 'role', 'school', 'created_at', 'last_login',
            'full_name', 'role_display', 'school_name', 'permissions'
        ]
    
    def get_permissions(self, obj):
        """Get user permissions for frontend"""
        return {
            'is_admin': obj.is_admin,
            'is_school_admin': obj.is_school_admin,
            'is_teacher': obj.is_teacher,
            'can_manage_users': obj.is_admin or obj.is_school_admin,
            'can_manage_content': True,  # All authenticated users can manage content
            'can_approve_content': obj.is_admin or obj.is_school_admin,
        }
