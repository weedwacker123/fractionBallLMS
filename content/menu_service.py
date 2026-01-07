"""
Menu Service for fetching dynamic menus from Firestore CMS

This service provides cached access to menu items for header/footer navigation
"""
import logging
from typing import List, Dict, Any, Optional
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Cache TTL in seconds (10 minutes for menus)
MENU_CACHE_TTL = getattr(settings, 'MENU_CACHE_TTL', 600)


def _get_firestore_client():
    """Get Firestore client - reuse from firestore_service"""
    from content.firestore_service import get_firestore_client
    return get_firestore_client()


def _fetch_menu_items_from_firestore(location: str) -> List[Dict[str, Any]]:
    """
    Fetch menu items from Firestore by location

    Args:
        location: 'header' or 'footer'

    Returns:
        List of menu items with nested children
    """
    try:
        db = _get_firestore_client()

        # Fetch all active menu items for this location
        docs = db.collection('menuItems').where('location', '==', location).where('active', '==', True).order_by('displayOrder').stream()

        items = []
        items_by_id = {}

        for doc in docs:
            data = doc.to_dict()
            item = {
                'id': doc.id,
                'label': data.get('label', ''),
                'url': data.get('url', ''),
                'type': data.get('type', 'page'),
                'openInNewTab': data.get('openInNewTab', False),
                'icon': data.get('icon'),
                'displayOrder': data.get('displayOrder', 0),
                'parentId': data.get('parentId'),
                'children': []
            }
            items.append(item)
            items_by_id[doc.id] = item

        # Build nested structure
        root_items = []
        for item in items:
            parent_ref = item.get('parentId')
            if parent_ref:
                # Get parent ID from reference
                parent_id = parent_ref.id if hasattr(parent_ref, 'id') else str(parent_ref)
                if parent_id in items_by_id:
                    items_by_id[parent_id]['children'].append(item)
            else:
                root_items.append(item)

        # Sort children by display order
        for item in root_items:
            item['children'].sort(key=lambda x: x.get('displayOrder', 0))

        logger.info(f"Fetched {len(root_items)} menu items for '{location}'")
        return root_items

    except Exception as e:
        logger.error(f"Error fetching menu items for '{location}': {e}")
        return []


def get_header_menu() -> List[Dict[str, Any]]:
    """
    Get header menu items from cache or Firestore

    Returns:
        List of menu items with nested children
    """
    cache_key = 'menu:header'

    # Try cache first
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Fetch from Firestore
    menu_items = _fetch_menu_items_from_firestore('header')

    # Use fallback if empty
    if not menu_items:
        logger.warning("Using fallback header menu - Firestore unavailable or empty")
        menu_items = _get_fallback_header_menu()

    # Cache and return
    cache.set(cache_key, menu_items, MENU_CACHE_TTL)
    return menu_items


def get_footer_menu() -> List[Dict[str, Any]]:
    """
    Get footer menu items from cache or Firestore

    Returns:
        List of menu items with nested children
    """
    cache_key = 'menu:footer'

    # Try cache first
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Fetch from Firestore
    menu_items = _fetch_menu_items_from_firestore('footer')

    # Use fallback if empty
    if not menu_items:
        logger.warning("Using fallback footer menu - Firestore unavailable or empty")
        menu_items = _get_fallback_footer_menu()

    # Cache and return
    cache.set(cache_key, menu_items, MENU_CACHE_TTL)
    return menu_items


def _get_fallback_header_menu() -> List[Dict[str, Any]]:
    """Fallback header menu if Firestore unavailable"""
    return [
        {'label': 'Home', 'url': '/', 'type': 'page', 'openInNewTab': False, 'children': []},
        {'label': 'Community', 'url': '/community/', 'type': 'page', 'openInNewTab': False, 'children': []},
        {'label': 'FAQ', 'url': '/faq/', 'type': 'page', 'openInNewTab': False, 'children': []},
    ]


def _get_fallback_footer_menu() -> List[Dict[str, Any]]:
    """Fallback footer menu if Firestore unavailable"""
    return [
        {'label': 'About', 'url': '/page/about/', 'type': 'page', 'openInNewTab': False, 'children': []},
        {'label': 'Contact', 'url': '/page/contact/', 'type': 'page', 'openInNewTab': False, 'children': []},
        {'label': 'Privacy Policy', 'url': '/page/privacy/', 'type': 'page', 'openInNewTab': False, 'children': []},
    ]


def refresh_menu_cache():
    """
    Force refresh all menu caches
    Call this when menus have changed in CMS
    """
    cache.delete('menu:header')
    cache.delete('menu:footer')

    # Pre-populate caches
    get_header_menu()
    get_footer_menu()

    logger.info("Menu caches refreshed")
