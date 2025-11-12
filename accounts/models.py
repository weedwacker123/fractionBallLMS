from django.contrib.auth.models import AbstractUser
from django.db import models


class School(models.Model):
    """School/District model for organizing users"""
    name = models.CharField(max_length=200)
    domain = models.CharField(max_length=100, unique=True, help_text="Unique school identifier")
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'School'
        verbose_name_plural = 'Schools'

    def __str__(self):
        return self.name


class User(AbstractUser):
    """Custom user model with Firebase integration and role-based access"""
    
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'System Admin'
        SCHOOL_ADMIN = 'SCHOOL_ADMIN', 'School Admin'
        TEACHER = 'TEACHER', 'Teacher'
    
    # Firebase integration
    firebase_uid = models.CharField(max_length=128, unique=True, help_text="Firebase User ID")
    
    # Role and organization
    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.TEACHER,
        help_text="User role determines access permissions"
    )
    school = models.ForeignKey(
        School, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="School/District the user belongs to (optional for development)"
    )
    
    # Profile information
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_full_name(self):
        """Return the user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    @property
    def is_admin(self):
        """Check if user is a system admin"""
        return self.role == self.Role.ADMIN

    @property
    def is_school_admin(self):
        """Check if user is a school admin"""
        return self.role == self.Role.SCHOOL_ADMIN

    @property
    def is_teacher(self):
        """Check if user is a teacher"""
        return self.role == self.Role.TEACHER

    def can_manage_school(self, school):
        """Check if user can manage a specific school"""
        if self.is_admin:
            return True
        if self.is_school_admin and self.school == school:
            return True
        return False