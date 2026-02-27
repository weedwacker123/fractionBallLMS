from rest_framework import permissions
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import render
from django.http import JsonResponse
from functools import wraps
from accounts import rbac


def _wants_json_response(request):
    """Return True if the client expects JSON instead of HTML."""
    accept = request.headers.get("Accept", "")
    return (
        request.path.startswith('/api/')
        or request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        or 'application/json' in accept
    )


def _permission_denied_response(request, action: str, reason: str):
    """Return either JSON 403 or a friendly HTML permission page."""
    if _wants_json_response(request):
        return JsonResponse(
            {
                "success": False,
                "message": f"Access denied ({reason}) for {action}",
            },
            status=403,
        )
    return render(
        request,
        'no_permission.html',
        {
            'required_action': action,
            'deny_reason': reason,
        },
        status=403,
    )


def require_permission(permission_key: str):
    """
    Factory that returns a DRF permission class for a given permission key.
    Usage: permission_classes = [require_permission('cms_edit')]
    """
    class DynamicPermission(permissions.BasePermission):
        def has_permission(self, request, view):
            return rbac.can(request.user, permission_key)
    DynamicPermission.__name__ = f'HasPerm_{permission_key}'
    DynamicPermission.__qualname__ = f'HasPerm_{permission_key}'
    return DynamicPermission


def require_permission_view(permission_key: str):
    """Decorator for Django views to enforce RBAC permission keys."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path(),
                    login_url='/accounts/login/',
                )
            decision = rbac.decide(request.user, permission_key)
            if decision.allowed:
                return view_func(request, *args, **kwargs)
            return _permission_denied_response(
                request,
                action=permission_key,
                reason=decision.reason,
            )
        return _wrapped
    return decorator


def require_action(action: str):
    """DRF permission class factory based on centralized RBAC actions."""
    class DynamicActionPermission(permissions.BasePermission):
        def has_permission(self, request, view):
            return rbac.can(request.user, action)
    DynamicActionPermission.__name__ = f'HasAction_{action.replace(".", "_")}'
    DynamicActionPermission.__qualname__ = DynamicActionPermission.__name__
    return DynamicActionPermission


def require_action_view(action: str):
    """Django view decorator based on centralized RBAC actions."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(
                    request.get_full_path(),
                    login_url='/accounts/login/',
                )
            decision = rbac.decide(request.user, action)
            if decision.allowed:
                return view_func(request, *args, **kwargs)
            return _permission_denied_response(
                request,
                action=action,
                reason=decision.reason,
            )
        return _wrapped
    return decorator


class IsAdmin(permissions.BasePermission):
    """Permission class for system administrators only"""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsContentManager(permissions.BasePermission):
    """Permission class for content managers (can manage content without approval)"""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            (request.user.is_admin or request.user.has_perm_key('cms_edit'))
        )


class CanManageContent(permissions.BasePermission):
    """Permission class for users who can create/edit/delete content"""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.has_perm_key('cms_edit')
        )


class HasCMSAccess(permissions.BasePermission):
    """Permission class for users with CMS/Admin interface access"""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.has_perm_key('cms_view')
        )


class IsRegisteredUser(permissions.BasePermission):
    """Permission class for any authenticated registered user."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated
        )


class CanModerateCommunity(permissions.BasePermission):
    """Permission class for community moderation."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.has_perm_key('community_moderate')
        )


class IsOwner(permissions.BasePermission):
    """Permission class for resource owners."""

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        if hasattr(obj, 'author'):
            return obj.author == request.user
        return False
