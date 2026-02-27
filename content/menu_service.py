"""
Menu Service for fetching dynamic menus from Firestore CMS

This service provides cached access to menu items for header/footer navigation
"""
import logging
from typing import List, Dict, Any
from django.core.cache import cache
from django.conf import settings
from content.firestore_service import FIRESTORE_QUERY_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)

# Cache TTL in seconds (5 minutes default - menus change infrequently)
MENU_CACHE_TTL = getattr(settings, 'MENU_CACHE_TTL', 300)


def _get_firestore_client():
    """Get Firestore client - reuse from firestore_service"""
    from content.firestore_service import get_firestore_client
    return get_firestore_client()


def _normalize_url(url: str) -> str:
    """
    Normalize internal URLs from CMS:
    - Ensure leading slash and trailing slash on internal paths
    """
    if not url:
        return '/'
    # Don't touch external URLs
    if url.startswith('http://') or url.startswith('https://'):
        return url
    # Ensure leading slash
    if not url.startswith('/'):
        url = '/' + url
    # Ensure trailing slash (Django APPEND_SLASH expects it)
    if url != '/' and not url.endswith('/'):
        url = url + '/'
    return url


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
        from google.cloud.firestore_v1.base_query import FieldFilter
        # Query without order_by to avoid composite index requirement; sort in Python
        docs = db.collection('menuItems').where(
            filter=FieldFilter('location', '==', location)
        ).where(
            filter=FieldFilter('active', '==', True)
        ).stream(timeout=FIRESTORE_QUERY_TIMEOUT_SECONDS)

        items = []
        items_by_id = {}

        for doc in docs:
            data = doc.to_dict()
            item = {
                'id': doc.id,
                'label': data.get('label', ''),
                'url': _normalize_url(data.get('url', '')),
                'type': data.get('type', 'page'),
                'openInNewTab': data.get('openInNewTab', False),
                'icon': data.get('icon'),
                'displayOrder': data.get('displayOrder', 0),
                'parentId': data.get('parentId'),
                'children': []
            }
            items.append(item)
            items_by_id[doc.id] = item

        # Sort items by displayOrder (done in Python to avoid composite index)
        items.sort(key=lambda x: x.get('displayOrder', 0))

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


def _fetch_all_menus_from_firestore() -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch all active menu items once and split into header/footer trees.
    """
    try:
        db = _get_firestore_client()
        from google.cloud.firestore_v1.base_query import FieldFilter
        docs = db.collection('menuItems').where(
            filter=FieldFilter('active', '==', True)
        ).stream(timeout=FIRESTORE_QUERY_TIMEOUT_SECONDS)

        buckets: Dict[str, List[Dict[str, Any]]] = {
            'header': [],
            'footer': [],
        }
        item_maps: Dict[str, Dict[str, Dict[str, Any]]] = {
            'header': {},
            'footer': {},
        }

        for doc in docs:
            data = doc.to_dict()
            location = data.get('location')
            if location not in buckets:
                continue

            item = {
                'id': doc.id,
                'label': data.get('label', ''),
                'url': _normalize_url(data.get('url', '')),
                'type': data.get('type', 'page'),
                'openInNewTab': data.get('openInNewTab', False),
                'icon': data.get('icon'),
                'displayOrder': data.get('displayOrder', 0),
                'parentId': data.get('parentId'),
                'children': [],
            }
            buckets[location].append(item)
            item_maps[location][doc.id] = item

        result: Dict[str, List[Dict[str, Any]]] = {}
        for location in ('header', 'footer'):
            items = buckets[location]
            items.sort(key=lambda x: x.get('displayOrder', 0))
            root_items = []
            id_map = item_maps[location]

            for item in items:
                parent_ref = item.get('parentId')
                if parent_ref:
                    parent_id = parent_ref.id if hasattr(parent_ref, 'id') else str(parent_ref)
                    if parent_id in id_map:
                        id_map[parent_id]['children'].append(item)
                else:
                    root_items.append(item)

            for item in root_items:
                item['children'].sort(key=lambda x: x.get('displayOrder', 0))
            result[location] = root_items

        logger.info(
            "Fetched %s header menu items and %s footer menu items",
            len(result['header']),
            len(result['footer']),
        )
        return result
    except Exception as e:
        logger.error(f"Error fetching full menus: {e}")
        return {
            'header': [],
            'footer': [],
        }


def get_menus() -> Dict[str, List[Dict[str, Any]]]:
    """
    Get both header and footer menus using one cache entry/read path.
    """
    cache_key = 'menu:all'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    menus = _fetch_all_menus_from_firestore()
    if not menus.get('header'):
        logger.warning("Using fallback header menu - Firestore unavailable or empty")
        menus['header'] = _get_fallback_header_menu()
    if not menus.get('footer'):
        menus['footer'] = _get_fallback_footer_menu()

    cache.set(cache_key, menus, MENU_CACHE_TTL)
    return menus


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

    # Prefer shared menu cache to avoid duplicate Firestore reads per request
    menus = get_menus()
    menu_items = menus.get('header', [])

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

    # Prefer shared menu cache to avoid duplicate Firestore reads per request
    menus = get_menus()
    menu_items = menus.get('footer', [])

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
    return []


def refresh_menu_cache():
    """
    Force refresh all menu caches
    Call this when menus have changed in CMS
    """
    cache.delete('menu:header')
    cache.delete('menu:footer')
    cache.delete('menu:all')

    # Pre-populate caches
    get_menus()
    get_header_menu()
    get_footer_menu()

    logger.info("Menu caches refreshed")
