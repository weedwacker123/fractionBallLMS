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
        ADMIN = 'ADMIN', 'Site Administrator'
        CONTENT_MANAGER = 'CONTENT_MANAGER', 'Content Manager'
        REGISTERED_USER = 'REGISTERED_USER', 'Registered User'

    # Legacy role mapping for migrating from 4-tier to 3-tier role system
    LEGACY_ROLE_MAP = {
        'SCHOOL_ADMIN': 'REGISTERED_USER',
        'TEACHER': 'REGISTERED_USER',
    }

    # Firebase integration
    firebase_uid = models.CharField(max_length=128, unique=True, help_text="Firebase User ID")

    # Role and organization
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.REGISTERED_USER,
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

    def save(self, *args, **kwargs):
        # Normalize legacy roles before saving
        if self.role in self.LEGACY_ROLE_MAP:
            self.role = self.LEGACY_ROLE_MAP[self.role]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"

    def get_full_name(self):
        """Return the user's full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    @property
    def is_admin(self):
        """Check if user is a site administrator"""
        return self.role == self.Role.ADMIN

    @property
    def is_content_manager(self):
        """Check if user is a content manager (can create/edit content without approval)"""
        return self.role == self.Role.CONTENT_MANAGER

    @property
    def is_registered_user(self):
        """Check if user is a registered user (basic access)"""
        return self.role == self.Role.REGISTERED_USER

    @property
    def can_manage_content(self):
        """Check if user can create/edit/delete content (Admin or Content Manager)"""
        return self.role in [self.Role.ADMIN, self.Role.CONTENT_MANAGER]

    @property
    def has_cms_access(self):
        """Check if user has access to CMS/Admin interface"""
        return self.role in [self.Role.ADMIN, self.Role.CONTENT_MANAGER]

    @property
    def can_moderate_community(self):
        """Check if user can moderate community posts (Admin or Content Manager)"""
        return self.role in [self.Role.ADMIN, self.Role.CONTENT_MANAGER]