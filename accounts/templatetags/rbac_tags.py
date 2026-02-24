from django import template

register = template.Library()


@register.filter
def has_perm_key(user, permission_key):
    """
    Template filter to check dynamic permissions.
    Usage: {% if user|has_perm_key:'cms.access' %}
    """
    if not user or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
        return False
    return user.has_perm_key(permission_key)
