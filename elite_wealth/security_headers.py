"""
Custom middleware for adding security headers and cache control to all HTTP responses.
Implements Content-Security-Policy, Permissions-Policy, X-XSS-Protection, and Cache-Control headers.
Enhanced to protect against DOM-based XSS and optimize performance with proper caching.
"""
import re


class SecurityHeadersMiddleware:
    """
    Middleware to add security headers and cache control to all HTTP responses.
    Protects against XSS, clickjacking, DOM-based XSS, and unauthorized feature access.
    Optimizes performance with proper Cache-Control headers for static assets.
    """
    
    # Static asset patterns for caching
    STATIC_PATTERNS = [
        r'^/static/.*\.(css|js|png|jpg|jpeg|gif|webp|woff2?|ttf|eot|svg|ico|avif)$',
        r'^/static/images/',
        r'^/static/css/',
        r'^/static/js/',
        r'^/static/fonts/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.STATIC_PATTERNS]
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Set cache control headers for performance
        self._set_cache_headers(request, response)
        
        # Content-Security-Policy Header
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://www.googletagmanager.com https://cdnjs.cloudflare.com https://consent.cookiebot.com https://translate.google.com https://translate.googleapis.com https://www.google-analytics.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com data:; "
            "connect-src 'self' https://api.coingecko.com https://www.google-analytics.com; "
            "frame-src 'self'; "
            "worker-src blob: 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'; "
            "upgrade-insecure-requests"
        )
        
        # X-XSS-Protection Header
        response['X-XSS-Protection'] = '1; mode=block'
        
        # Permissions-Policy Header
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=(), payment=()'
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # HSTS for HTTPS connections
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response
    
    def _is_static_asset(self, path):
        """Check if path is a static asset that should be cached long-term."""
        return any(pattern.match(path) for pattern in self._compiled_patterns)
    
    def _set_cache_headers(self, request, response):
        """Set appropriate Cache-Control headers based on content type and path."""
        path = request.path
        content_type = response.get('Content-Type', '')
        
        # Static assets with content hash - cache for 1 year (immutable)
        if self._is_static_asset(path):
            response['Cache-Control'] = 'public, max-age=31536000, immutable'
            response['Vary'] = 'Accept-Encoding'
        
        # API/AJAX endpoints - no cache
        elif path.startswith('/api/') or path.startswith('/ajax/') or 'application/json' in content_type:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        # HTML pages - short cache with revalidation
        elif 'text/html' in content_type:
            response['Cache-Control'] = 'public, max-age=300, must-revalidate'
        
        # Default - 1 hour cache
        else:
            response['Cache-Control'] = 'public, max-age=3600'
