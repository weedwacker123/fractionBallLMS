"""
Context processors for injecting global template variables

These make data available to all templates without explicitly passing in views
"""
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def menu_context(request):
    """
    Inject dynamic menu items into all templates

    Usage in templates:
        {% for item in header_menu %}
            <a href="{{ item.url }}">{{ item.label }}</a>
            {% if item.children %}
                {% for child in item.children %}
                    <a href="{{ child.url }}">{{ child.label }}</a>
                {% endfor %}
            {% endif %}
        {% endfor %}
    """
    path = getattr(request, "path", "") or ""
    # CMS routes do not use the public header/footer menu.
    if path.startswith('/cms/'):
        return {
            'header_menu': [],
            'footer_menu': [],
        }

    from content.menu_service import get_menus

    try:
        menus = get_menus()
        return {
            'header_menu': menus.get('header', []),
            'footer_menu': menus.get('footer', []),
        }
    except Exception as e:
        logger.error(f"Error loading menus: {e}")
        return {
            'header_menu': [],
            'footer_menu': [],
        }


def site_config_context(request):
    """
    Inject site configuration into all templates

    Usage in templates:
        {{ site_name }}
        {{ site_logo_url }}
    """
    # For now, return static values. Can be extended to fetch from Firestore
    return {
        'site_name': 'Fraction Ball',
        'site_tagline': 'Math Through Movement',
    }
