/* ============================================
   ELITE WEALTH CAPITA - MAIN JS
   General site functionality
   ============================================ */
(function () {
    'use strict';

    // Use centralized config from config.js
    // Get API configuration from DOM or config
    const API_BASE = '';
    const API_URL = API_BASE + '/api';

    // Mobile Menu Toggle
    function initMobileMenu() {
        const toggle = document.querySelector('.navbar-toggle') || document.querySelector('.mobile-menu-toggle');
        const menu = document.querySelector('.navbar-menu') || document.querySelector('.nav-menu');

        if (toggle && menu) {
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                menu.classList.toggle('active');
                toggle.classList.toggle('active');
                const expanded = menu.classList.contains('active');
                toggle.setAttribute('aria-expanded', expanded);
            });

            document.addEventListener('click', (e) => {
                if (!toggle.contains(e.target) && !menu.contains(e.target)) {
                    menu.classList.remove('active');
                    toggle.classList.remove('active');
                    toggle.setAttribute('aria-expanded', 'false');
                }
            });

            menu.querySelectorAll('a').forEach(link => {
                link.addEventListener('click', () => {
                    menu.classList.remove('active');
                    toggle.classList.remove('active');
                    toggle.setAttribute('aria-expanded', 'false');
                });
            });
        }
    }

    // Smooth Scroll
    function initSmoothScroll() {
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }

    // Crypto Ticker — Fetch from Django API
    async function initCryptoTicker() {
        const tickerTrack = document.querySelector('.ticker-track');
        if (!tickerTrack) return;

        try {
            const response = await fetch('/investments/api/ticker/');
            const result = await response.json();
            
            if (!result.success || !result.tickers) {
                console.warn('Crypto ticker API returned no data');
                return;
            }
            
            let tickerHTML = '';
            result.tickers.forEach(crypto => {
                const changeFixed = parseFloat(crypto.change_24h || 0).toFixed(2);
                const changeClass = crypto.change_24h >= 0 ? 'positive' : 'negative';
                const changeSymbol = crypto.change_24h >= 0 ? '+' : '';
                const priceFormatted = parseFloat(crypto.price).toLocaleString(undefined, { 
                    minimumFractionDigits: 2, 
                    maximumFractionDigits: crypto.price < 0.01 ? 8 : 2 
                });
                tickerHTML += `
                    <div class="ticker-item">
                        <span class="crypto-symbol">${crypto.symbol}</span>
                        <span class="crypto-price">$${priceFormatted}</span>
                        <span class="crypto-change ${changeClass}">${changeSymbol}${changeFixed}%</span>
                    </div>
                `;
            });

            tickerTrack.innerHTML = tickerHTML + tickerHTML;
        } catch (error) {
            console.error('Failed to load crypto ticker:', error);
        }
    }

    // Toast Notifications
    function showToast(message, type = 'info') {
        const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
        const backgrounds = { 
            success: 'linear-gradient(135deg, #10b981, #059669)', 
            error: 'linear-gradient(135deg, #ef4444, #dc2626)', 
            warning: 'linear-gradient(135deg, #f59e0b, #d97706)', 
            info: 'linear-gradient(135deg, #3b82f6, #2563eb)' 
        };
        
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${icons[type] || icons.info}</span>
            <span class="toast-message">${message}</span>
        `;
        toast.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 12px;
            display: flex;
            align-items: center;
            gap: 10px;
            color: white;
            font-weight: 500;
            z-index: 200;
            transform: translateX(120%);
            transition: transform 0.3s ease;
            background: ${backgrounds[type] || backgrounds.info};
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        `;

        document.body.appendChild(toast);
        setTimeout(() => toast.style.transform = 'translateX(0)', 10);
        setTimeout(() => {
            toast.style.transform = 'translateX(120%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Format Currency
    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
    }

    // Format Date
    function formatDate(dateString) {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric'
        });
    }

    // Scroll Animations
    function initScrollAnimations() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                }
            });
        }, { threshold: 0.1 });
        document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));
    }

    // Navbar Scroll Effect
    function initNavbarScroll() {
        const navbar = document.querySelector('.navbar');
        if (!navbar) return;
        let scrollTimeout;
        window.addEventListener('scroll', () => {
            if (scrollTimeout) return;
            scrollTimeout = setTimeout(() => {
                scrollTimeout = null;
                if (window.scrollY > 50) {
                    navbar.classList.add('scrolled');
                } else {
                    navbar.classList.remove('scrolled');
                }
            }, 100);
        }, { passive: true });
    }

    // Initialize on DOM Load
    document.addEventListener('DOMContentLoaded', () => {
        initMobileMenu();
        initSmoothScroll();
        initCryptoTicker();
        initScrollAnimations();
        initNavbarScroll();
        const tickerInterval = setInterval(initCryptoTicker, 60000);

        // Add cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (tickerInterval) clearInterval(tickerInterval);
        });
    });

    // Export functions globally
    window.showToast = showToast;
    window.formatCurrency = formatCurrency;
    window.formatDate = formatDate;
    window.logout = function() {
        window.location.href = '/accounts/logout/';
    };
})();
