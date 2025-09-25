from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission class for system administrators only
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_admin
        )


class IsSchoolAdmin(permissions.BasePermission):
    """
    Permission class for school administrators
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_admin or request.user.is_school_admin)
        )


class IsTeacher(permissions.BasePermission):
    """
    Permission class for teachers (includes school admins and system admins)
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role in ['TEACHER', 'SCHOOL_ADMIN', 'ADMIN']
        )


class IsSchoolMember(permissions.BasePermission):
    """
    Permission class for users within the same school
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'school')
        )
    
    def has_object_permission(self, request, view, obj):
        # System admins can access everything
        if request.user.is_admin:
            return True
            
        # Check if object has school attribute and user belongs to same school
        if hasattr(obj, 'school'):
            return obj.school == request.user.school
            
        # Check if object is a school and user belongs to it
        if hasattr(obj, 'name') and hasattr(obj, 'domain'):  # Likely a School object
            return obj == request.user.school
            
        return False


class CanManageSchool(permissions.BasePermission):
    """
    Permission class for managing school-specific resources
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_admin or request.user.is_school_admin)
        )
    
    def has_object_permission(self, request, view, obj):
        # System admins can manage any school
        if request.user.is_admin:
            return True
            
        # School admins can only manage their own school
        if request.user.is_school_admin:
            if hasattr(obj, 'school'):
                return obj.school == request.user.school
            elif hasattr(obj, 'name') and hasattr(obj, 'domain'):  # School object
                return obj == request.user.school
                
        return False


class IsOwnerOrSchoolAdmin(permissions.BasePermission):
    """
    Permission class for resource owners or school administrators
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated
        )
    
    def has_object_permission(self, request, view, obj):
        # System admins can access everything
        if request.user.is_admin:
            return True
            
        # School admins can access resources in their school
        if request.user.is_school_admin and hasattr(obj, 'school'):
            return obj.school == request.user.school
            
        # Users can access their own resources
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
            
        return False
