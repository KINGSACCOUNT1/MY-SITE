from django import template
from django.utils.safestring import mark_safe
import bleach

register = template.Library()

ALLOWED_TAGS = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code', 'pre']
ALLOWED_ATTRIBUTES = {'a': ['href', 'title', 'target']}

@register.filter(name='bleach_clean')
def bleach_clean(value):
    """Sanitize HTML content, allowing only safe tags."""
    if value is None:
        return ''
    cleaned = bleach.clean(value, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)
    return mark_safe(cleaned)
