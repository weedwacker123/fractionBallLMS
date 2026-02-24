"""
Centralized RBAC policy and authorization helpers.

All endpoint authorization should flow through this module so behavior and
debugging remain consistent as roles evolve.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple


# Action -> required permission keys.
# Keep this list focused on capabilities, not endpoints.
ACTION_POLICIES: Dict[str, Tuple[str, ...]] = {
    "cms.access": ("cms.access",),
    "reports.view": ("reports.view",),
    "users.manage": ("users.manage",),
    "schools.manage": ("schools.manage",),
    "content.manage": ("content.manage",),
    "content.approve": ("content.approve",),
    "bulk.upload": ("bulk.upload",),
    "community.create": ("community.create",),
    "community.moderate": ("community.moderate",),
    "dashboard.view": ("dashboard.view",),
    "notes.access": ("notes.access",),
    # Domain capability actions
    "activity.view": ("library.videos",),
    "library.videos.view": ("library.videos",),
    "library.resources.view": ("library.resources",),
    "video.stream": ("library.videos",),
    "resource.download": ("library.resources",),
}


@dataclass(frozen=True)
class RBACDecision:
    allowed: bool
    action: str
    required_permissions: Tuple[str, ...]
    missing_permissions: Tuple[str, ...]
    reason: str


def _required_permissions(action: str) -> Tuple[str, ...]:
    # If an action is not explicitly mapped, treat it as a permission key.
    return ACTION_POLICIES.get(action, (action,))


def _missing_permissions(user: Any, required: Sequence[str]) -> Tuple[str, ...]:
    missing = []
    for permission_key in required:
        if not user.has_perm_key(permission_key):
            missing.append(permission_key)
    return tuple(missing)


def _school_matches(user: Any, obj: Any) -> bool:
    if hasattr(obj, "school_id"):
        return getattr(obj, "school_id", None) == getattr(user, "school_id", None)
    if hasattr(obj, "school"):
        return getattr(obj, "school_id", None) == getattr(user, "school_id", None)
    return True


def _is_owner(user: Any, obj: Any) -> bool:
    if hasattr(obj, "owner_id"):
        return obj.owner_id == user.id
    if hasattr(obj, "author_id"):
        return obj.author_id == user.id
    return False


def _is_published(obj: Any) -> bool:
    return getattr(obj, "status", None) == "PUBLISHED"


def _scope_allowed(user: Any, action: str, obj: Optional[Any]) -> bool:
    # Route-level checks (obj is None) have no object scope constraints.
    if obj is None:
        return True

    # School scoping for core content surfaces.
    if action in {"activity.view", "library.videos.view", "library.resources.view", "video.stream", "resource.download"}:
        if user.has_perm_key("content.manage") or user.has_perm_key("schools.manage"):
            return True
        if not _school_matches(user, obj):
            return False
        return _is_owner(user, obj) or _is_published(obj)

    return True


def decide(user: Any, action: str, obj: Optional[Any] = None) -> RBACDecision:
    if not user or not getattr(user, "is_authenticated", False):
        return RBACDecision(
            allowed=False,
            action=action,
            required_permissions=(),
            missing_permissions=(),
            reason="unauthenticated",
        )

    required = _required_permissions(action)
    missing = _missing_permissions(user, required)
    if missing:
        return RBACDecision(
            allowed=False,
            action=action,
            required_permissions=required,
            missing_permissions=missing,
            reason="missing_permission",
        )

    if not _scope_allowed(user, action, obj):
        return RBACDecision(
            allowed=False,
            action=action,
            required_permissions=required,
            missing_permissions=(),
            reason="scope_denied",
        )

    return RBACDecision(
        allowed=True,
        action=action,
        required_permissions=required,
        missing_permissions=(),
        reason="allowed",
    )


def can(user: Any, action: str, obj: Optional[Any] = None) -> bool:
    return decide(user, action=action, obj=obj).allowed
