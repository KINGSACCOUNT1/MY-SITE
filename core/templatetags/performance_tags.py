"""Template tags for performance optimizations."""
from django import template
from django.templatetags.static import static
import os

register = template.Library()


@register.inclusion_tag('components/optimized_image.html')
def optimized_image(src, alt="", css_class="", loading="lazy", width=None, height=None):
    """
    Render an optimized image with WebP fallback and lazy loading.
    
    Usage:
        {% load performance_tags %}
        {% optimized_image "images/hero.jpg" alt="Hero Image" css_class="img-fluid" %}
    """
    # Generate WebP path
    base_path = src.rsplit('.', 1)[0] if '.' in src else src
    ext = src.rsplit('.', 1)[1] if '.' in src else 'jpg'
    webp_path = f"{base_path}.webp"
    
    return {
        'webp_src': static(webp_path),
        'fallback_src': static(src),
        'alt': alt,
        'css_class': css_class,
        'loading': loading,
        'width': width,
        'height': height,
    }


@register.simple_tag
def minified_static(path):
    """
    Return minified version of static file if in production.
    
    Usage:
        {% load performance_tags %}
        <link rel="stylesheet" href="{% minified_static 'css/style.css' %}">
    """
    from django.conf import settings
    
    # In production, use minified versions
    if not settings.DEBUG:
        # Check if path is CSS or JS
        if path.endswith('.css'):
            min_path = path.replace('.css', '.min.css')
        elif path.endswith('.js'):
            min_path = path.replace('.js', '.min.js')
        else:
            return static(path)
        
        # Return minified path
        return static(min_path)
    
    # In development, use regular files
    return static(path)
