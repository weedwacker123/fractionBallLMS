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


class IsContentManager(permissions.BasePermission):
    """
    Permission class for content managers (can manage content without approval)
    As per TRD: Content managers can create, edit, delete content and publish directly
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_admin or request.user.is_content_manager)
        )


class CanManageContent(permissions.BasePermission):
    """
    Permission class for users who can create/edit/delete content
    Includes: Admin, Content Manager
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.can_manage_content
        )


class HasCMSAccess(permissions.BasePermission):
    """
    Permission class for users with CMS/Admin interface access
    As per TRD: Only Admin and Content Manager have CMS access
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.has_cms_access
        )


class IsRegisteredUser(permissions.BasePermission):
    """
    Permission class for any authenticated registered user.
    All authenticated users have at least REGISTERED_USER level access.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated
        )


class CanModerateCommunity(permissions.BasePermission):
    """
    Permission class for community moderation (Admin or Content Manager).
    Moderators can delete/edit posts, lock threads, pin posts, and manage flags.
    """

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.can_moderate_community
        )


class IsOwner(permissions.BasePermission):
    """
    Permission class for resource owners.
    Allows users to manage their own resources.
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

        # Users can access their own resources
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'author'):
            return obj.author == request.user

        return False
