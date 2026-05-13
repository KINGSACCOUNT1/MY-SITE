"""
Bot Protection Middleware for Elite Wealth Capital
Blocks malicious AI scanners and security checkers while allowing legitimate search engines
"""

from django.http import HttpResponseForbidden
from django.conf import settings
import re


class BotProtectionMiddleware:
    """
    Middleware to block malicious bots, AI scanners, and security checkers
    while allowing legitimate search engines like Google, Bing, etc.
    """
    
    # Malicious bots and AI scanners to block
    BLOCKED_USER_AGENTS = [
        # Security Scanners
        r'scamadviser',
        r'sitecheck',
        r'norton-safeweb',
        r'mcafee',
        r'wpscan',
        r'nikto',
        r'nessus',
        r'qualys',
        r'burp',
        r'nmap',
        r'masscan',
        r'sqlmap',
        r'metasploit',
        
        # AI Crawlers (OpenAI, Anthropic, etc.)
        r'gptbot',
        r'chatgpt-user',
        r'chatgpt',
        r'ccbot',
        r'anthropic-ai',
        r'claude-web',
        r'cohere-ai',
        r'omgilibot',
        
        # SEO/Scraping Bots (not Google/Bing)
        r'semrushbot',
        r'ahrefsbot',
        r'mj12bot',
        r'dotbot',
        r'blexbot',
        r'dataforseobot',
        r'petalbot',
        r'bytespider',
        r'screaming frog',
        
        # Social Media Bots
        r'facebookbot',
        r'facebookexternalhit',
        r'twitterbot',
        
        # Generic Scrapers
        r'curl',
        r'wget',
        r'python-requests',
        r'scrapy',
        r'phantomjs',
        r'headless',
    ]
    
    # Legitimate bots to ALLOW
    ALLOWED_USER_AGENTS = [
        r'googlebot',
        r'google-inspectiontool',
        r'bingbot',
        r'slurp',  # Yahoo
        r'duckduckbot',
        r'baiduspider',
        r'yandexbot',
        r'applebot',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # Compile regex patterns for performance
        self.blocked_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.BLOCKED_USER_AGENTS
        ]
        self.allowed_patterns = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.ALLOWED_USER_AGENTS
        ]
    
    def __call__(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # Skip bot protection for admin users
        if hasattr(request, 'user') and request.user.is_staff:
            return self.get_response(request)
        
        # Allow empty user agents (some browsers)
        if not user_agent:
            return self.get_response(request)
        
        # Check if it's a legitimate search engine first
        for pattern in self.allowed_patterns:
            if pattern.search(user_agent):
                # It's a legitimate bot, allow access
                return self.get_response(request)
        
        # Check if it's a malicious bot
        for pattern in self.blocked_patterns:
            if pattern.search(user_agent):
                # Block the malicious bot
                return HttpResponseForbidden(
                    "<h1>403 Forbidden</h1>"
                    "<p>Access denied. Automated scanning is not permitted.</p>"
                )
        
        # Default: allow normal traffic
        return self.get_response(request)


class IPBlockMiddleware:
    """
    Middleware to block known malicious IP ranges
    """
    
    # Known scanner IP ranges (can be expanded)
    BLOCKED_IPS = [
        # Add specific IPs if you identify scanner sources
        # Example: '192.168.1.100',
    ]
    
    BLOCKED_IP_RANGES = [
        # Add IP ranges if needed
        # Example: '192.168.1.',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        ip = self.get_client_ip(request)
        
        # Check if IP is blocked
        if ip in self.BLOCKED_IPS:
            return HttpResponseForbidden("<h1>403 Forbidden</h1>")
        
        # Check if IP is in blocked range
        for ip_range in self.BLOCKED_IP_RANGES:
            if ip.startswith(ip_range):
                return HttpResponseForbidden("<h1>403 Forbidden</h1>")
        
        return self.get_response(request)
    
    def get_client_ip(self, request):
        """Get the real client IP (handles proxies like Cloudflare)"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
