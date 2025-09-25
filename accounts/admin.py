from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import School, User


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    """Admin configuration for School model"""
    
    list_display = ['name', 'domain', 'user_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'domain', 'address']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'domain', 'is_active')
        }),
        ('Contact Information', {
            'fields': ('address', 'phone'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_count(self, obj):
        """Display count of users in this school"""
        count = obj.user_set.count()
        return format_html('<strong>{}</strong>', count)
    user_count.short_description = 'Users'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch"""
        return super().get_queryset(request).prefetch_related('user_set')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for custom User model"""
    
    list_display = ['username', 'email', 'get_full_name', 'role', 'school', 'is_active', 'created_at']
    list_filter = ['role', 'school', 'is_active', 'is_staff', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'firebase_uid']
    readonly_fields = ['firebase_uid', 'created_at', 'updated_at', 'last_login', 'date_joined']
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Firebase Integration', {
            'fields': ('firebase_uid',),
            'classes': ('collapse',)
        }),
        ('Role & Organization', {
            'fields': ('role', 'school')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
        ('Role & Organization', {
            'fields': ('role', 'school')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'phone'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset and apply school-based filtering for school admins"""
        queryset = super().get_queryset(request).select_related('school')
        
        # School admins can only see users from their school
        if not request.user.is_superuser and hasattr(request.user, 'role'):
            if request.user.role == 'SCHOOL_ADMIN':
                queryset = queryset.filter(school=request.user.school)
        
        return queryset
    
    def get_form(self, request, obj=None, **kwargs):
        """Customize form based on user role"""
        form = super().get_form(request, obj, **kwargs)
        
        # School admins can only assign users to their school
        if not request.user.is_superuser and hasattr(request.user, 'role'):
            if request.user.role == 'SCHOOL_ADMIN':
                if 'school' in form.base_fields:
                    form.base_fields['school'].queryset = School.objects.filter(id=request.user.school.id)
                    form.base_fields['school'].initial = request.user.school
                    form.base_fields['school'].widget.attrs['readonly'] = True
        
        return form
    
    def save_model(self, request, obj, form, change):
        """Custom save logic"""
        # Set school for school admins
        if not change and hasattr(request.user, 'role') and request.user.role == 'SCHOOL_ADMIN':
            obj.school = request.user.school
        
        super().save_model(request, obj, form, change)