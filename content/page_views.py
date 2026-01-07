"""
Page views for rendering custom CMS pages

Supports HTML passthrough from CMS pages collection
"""
import logging
from django.shortcuts import render
from django.http import Http404
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

# Cache TTL for pages (15 minutes)
PAGE_CACHE_TTL = getattr(settings, 'PAGE_CACHE_TTL', 900)


def _get_firestore_client():
    """Get Firestore client"""
    from content.firestore_service import get_firestore_client
    return get_firestore_client()


def _fetch_page_from_firestore(slug: str) -> dict:
    """
    Fetch a page by slug from Firestore

    Args:
        slug: URL-friendly page identifier

    Returns:
        Page data dict or None
    """
    try:
        db = _get_firestore_client()

        # Query for page by slug
        docs = db.collection('pages').where('slug', '==', slug).where('status', '==', 'published').limit(1).stream()

        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            return data

        return None

    except Exception as e:
        logger.error(f"Error fetching page '{slug}': {e}")
        return None


def _sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML content for safe rendering

    Allows basic HTML tags but strips potentially dangerous elements
    """
    try:
        import bleach

        # Allowed tags for page content
        allowed_tags = [
            'p', 'br', 'hr',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'strong', 'b', 'em', 'i', 'u', 's', 'strike',
            'a', 'img',
            'ul', 'ol', 'li',
            'table', 'thead', 'tbody', 'tr', 'th', 'td',
            'div', 'span', 'section', 'article', 'header', 'footer', 'nav',
            'blockquote', 'pre', 'code',
            'iframe',  # For embedded videos
        ]

        # Allowed attributes
        allowed_attrs = {
            '*': ['class', 'id', 'style'],
            'a': ['href', 'title', 'target', 'rel'],
            'img': ['src', 'alt', 'title', 'width', 'height', 'loading'],
            'iframe': ['src', 'width', 'height', 'frameborder', 'allowfullscreen', 'allow'],
            'table': ['border', 'cellpadding', 'cellspacing'],
            'th': ['colspan', 'rowspan'],
            'td': ['colspan', 'rowspan'],
        }

        return bleach.clean(
            html_content,
            tags=allowed_tags,
            attributes=allowed_attrs,
            strip=True
        )

    except ImportError:
        # If bleach is not installed, return content as-is (not recommended for production)
        logger.warning("bleach not installed - HTML not sanitized")
        return html_content


def custom_page(request, slug):
    """
    Render a custom page from CMS

    URL: /page/<slug>/

    Args:
        request: HTTP request
        slug: Page slug from URL

    Returns:
        Rendered page template
    """
    # Try cache first
    cache_key = f'page:{slug}'
    page = cache.get(cache_key)

    if page is None:
        # Fetch from Firestore
        page = _fetch_page_from_firestore(slug)

        if page:
            # Cache the page
            cache.set(cache_key, page, PAGE_CACHE_TTL)

    if not page:
        raise Http404("Page not found")

    # Sanitize HTML content
    content = page.get('content', '')
    sanitized_content = _sanitize_html(content)

    context = {
        'page': page,
        'page_title': page.get('title', 'Page'),
        'page_content': sanitized_content,
        'meta_title': page.get('metaTitle') or page.get('title'),
        'meta_description': page.get('metaDescription', ''),
    }

    return render(request, 'custom_page.html', context)


def refresh_page_cache(slug: str = None):
    """
    Refresh page cache

    Args:
        slug: Specific page slug to refresh, or None to clear all
    """
    if slug:
        cache.delete(f'page:{slug}')
        logger.info(f"Page cache cleared for: {slug}")
    else:
        # Can't easily clear all page caches without knowing all slugs
        # Would need to iterate through pages collection
        logger.info("Page cache refresh requested (specific slug not provided)")
