"""
Role/Permission Service for dynamic RBAC

Fetches role definitions from Firestore roles collection,
caches them in Django's cache framework, and provides
permission-checking utilities.

Architecture mirrors content/firestore_service.py:
- Firestore is source of truth (CMS writes, LMS reads)
- Django cache with TTL for performance
- Hardcoded fallbacks for resilience
"""
import logging
from typing import Dict, Set
from django.core.cache import cache

logger = logging.getLogger(__name__)

ROLE_CACHE_TTL = 300  # 5 minutes
ROLE_CACHE_KEY = 'rbac:roles'

# Canonical list of all permission keys the LMS recognizes.
# MUST stay in sync with permissionKeys in CMS src/collections/roles.ts
PERMISSION_KEYS = [
    'community.create',
    'community.moderate',
    'content.manage',
    'content.approve',
    'cms.access',
    'reports.view',
    'library.videos',
    'library.resources',
    'dashboard.view',
    'users.manage',
    'schools.manage',
    'bulk.upload',
    'notes.access',
]

# Fallback role definitions — exact match of current hardcoded behavior.
# Used when Firestore is unavailable.
FALLBACK_ROLES: Dict[str, dict] = {
    'ADMIN': {
        'key': 'ADMIN',
        'name': 'Site Administrator',
        'permissions': {k: True for k in PERMISSION_KEYS},
    },
    'CONTENT_MANAGER': {
        'key': 'CONTENT_MANAGER',
        'name': 'Content Manager',
        'permissions': {
            'community.create': True,
            'community.moderate': True,
            'content.manage': True,
            'content.approve': True,
            'cms.access': True,
            'reports.view': True,
            'library.videos': True,
            'library.resources': True,
            'dashboard.view': True,
            'bulk.upload': True,
            'notes.access': True,
            'users.manage': False,
            'schools.manage': False,
        },
    },
    'REGISTERED_USER': {
        'key': 'REGISTERED_USER',
        'name': 'Registered User',
        'permissions': {
            'community.create': True,
            'community.moderate': False,
            'content.manage': False,
            'content.approve': False,
            'cms.access': False,
            'reports.view': False,
            'library.videos': True,
            'library.resources': True,
            'dashboard.view': True,
            'bulk.upload': True,
            'notes.access': True,
            'users.manage': False,
            'schools.manage': False,
        },
    },
}


def _fetch_roles_from_firestore() -> Dict[str, dict]:
    """Fetch all role definitions from Firestore roles collection."""
    try:
        from content.firestore_service import get_all_documents
        docs = get_all_documents('roles')
        roles = {}
        for doc in docs:
            key = doc.get('key')
            if key:
                roles[key] = {
                    'key': key,
                    'name': doc.get('name', key),
                    'permissions': doc.get('permissions', {}),
                }
        return roles
    except Exception as e:
        logger.error(f"Error fetching roles from Firestore: {e}")
        return {}


def get_all_roles() -> Dict[str, dict]:
    """
    Get all role definitions, with caching and fallback.
    Returns dict keyed by role key.
    """
    cached = cache.get(ROLE_CACHE_KEY)
    if cached is not None:
        return cached

    roles = _fetch_roles_from_firestore()

    if not roles:
        logger.warning("Using fallback role definitions")
        roles = FALLBACK_ROLES

    cache.set(ROLE_CACHE_KEY, roles, ROLE_CACHE_TTL)
    return roles


def get_role_permissions(role_key: str) -> Dict[str, bool]:
    """
    Get the permissions map for a specific role key.
    Returns dict of permission_key -> bool.
    """
    roles = get_all_roles()
    role = roles.get(role_key)
    if role:
        return role.get('permissions', {})
    logger.warning(f"Unknown role key '{role_key}', returning empty permissions")
    return {}


def has_permission(role_key: str, permission_key: str) -> bool:
    """Check if a role has a specific permission."""
    perms = get_role_permissions(role_key)
    return perms.get(permission_key, False)


def get_role_names() -> Dict[str, str]:
    """Get mapping of role key -> display name for all roles."""
    roles = get_all_roles()
    return {key: role['name'] for key, role in roles.items()}


def refresh_roles_cache():
    """Force refresh the roles cache."""
    cache.delete(ROLE_CACHE_KEY)
    get_all_roles()
    logger.info("Roles cache refreshed")
