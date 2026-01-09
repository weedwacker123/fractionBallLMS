"""
Site Configuration Service for fetching dynamic config from Firestore CMS

This service provides cached access to site configuration values like
file size limits, allowed types, and other settings.
"""
import logging
from typing import Any, Dict, List, Optional
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Cache TTL in seconds (30 seconds for quick CMS updates)
CONFIG_CACHE_TTL = getattr(settings, 'CONFIG_CACHE_TTL', 30)

# Fallback configuration values
FALLBACK_CONFIG = {
    'max_video_size': 500 * 1024 * 1024,  # 500MB
    'max_resource_size': 50 * 1024 * 1024,  # 50MB
    'max_image_size': 2 * 1024 * 1024,  # 2MB
    'allowed_video_types': [
        'video/mp4', 'video/mpeg', 'video/quicktime',
        'video/x-msvideo', 'video/webm'
    ],
    'allowed_resource_types': [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain',
        'image/jpeg', 'image/png', 'image/gif'
    ],
    'pagination_page_size': 20,
    'pagination_max_page_size': 100,
}


def _get_firestore_client():
    """Get Firestore client"""
    from content.firestore_service import get_firestore_client
    return get_firestore_client()


def _fetch_all_config_from_firestore() -> Dict[str, Any]:
    """
    Fetch all site configuration from Firestore siteConfig collection

    Returns:
        Dict of config key-value pairs
    """
    try:
        db = _get_firestore_client()
        docs = db.collection('siteConfig').stream()

        config = {}
        for doc in docs:
            data = doc.to_dict()
            key = data.get('key') or doc.id
            value = data.get('value')
            config[key] = value

        logger.info(f"Fetched {len(config)} config items from Firestore")
        return config

    except Exception as e:
        logger.error(f"Error fetching site config: {e}")
        return {}


def get_config(key: str, default: Any = None) -> Any:
    """
    Get a single configuration value

    Args:
        key: Config key name
        default: Default value if not found

    Returns:
        Config value or default
    """
    all_config = get_all_config()
    return all_config.get(key, FALLBACK_CONFIG.get(key, default))


def get_all_config() -> Dict[str, Any]:
    """
    Get all configuration values from cache or Firestore

    Returns:
        Dict of all config key-value pairs
    """
    cache_key = 'site:config'

    # Try cache first
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    # Fetch from Firestore
    config = _fetch_all_config_from_firestore()

    # Merge with fallbacks (Firestore values take precedence)
    merged_config = {**FALLBACK_CONFIG, **config}

    # Cache and return
    cache.set(cache_key, merged_config, CONFIG_CACHE_TTL)
    return merged_config


# Convenience functions for common config values

def get_max_video_size() -> int:
    """Get maximum video file size in bytes"""
    return get_config('max_video_size', FALLBACK_CONFIG['max_video_size'])


def get_max_resource_size() -> int:
    """Get maximum resource file size in bytes"""
    return get_config('max_resource_size', FALLBACK_CONFIG['max_resource_size'])


def get_max_image_size() -> int:
    """Get maximum image file size in bytes"""
    return get_config('max_image_size', FALLBACK_CONFIG['max_image_size'])


def get_allowed_video_types() -> List[str]:
    """Get list of allowed video MIME types"""
    return get_config('allowed_video_types', FALLBACK_CONFIG['allowed_video_types'])


def get_allowed_resource_types() -> List[str]:
    """Get list of allowed resource MIME types"""
    return get_config('allowed_resource_types', FALLBACK_CONFIG['allowed_resource_types'])


def get_pagination_page_size() -> int:
    """Get default pagination page size"""
    return get_config('pagination_page_size', FALLBACK_CONFIG['pagination_page_size'])


def get_pagination_max_page_size() -> int:
    """Get maximum pagination page size"""
    return get_config('pagination_max_page_size', FALLBACK_CONFIG['pagination_max_page_size'])


def refresh_config_cache():
    """
    Force refresh configuration cache
    Call this when config has changed in CMS
    """
    cache.delete('site:config')
    get_all_config()  # Repopulate
    logger.info("Site config cache refreshed")
