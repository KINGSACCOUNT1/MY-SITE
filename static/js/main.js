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
        // Support both old (.mobile-menu-toggle, .nav-menu) and new (.navbar-toggle, .navbar-menu) classes
        const toggle = document.querySelector('.navbar-toggle') || document.querySelector('.mobile-menu-toggle');
        const menu = document.querySelector('.navbar-menu') || document.querySelector('.nav-menu');

        if (toggle && menu) {
            toggle.addEventListener('click', (e) => {
                e.stopPropagation();
                menu.classList.toggle('active');
                toggle.classList.toggle('active');

                // Update aria-expanded
                const expanded = menu.classList.contains('active');
                toggle.setAttribute('aria-expanded', expanded);
            });

            // Close menu when clicking outside
            document.addEventListener('click', (e) => {
                if (!toggle.contains(e.target) && !menu.contains(e.target)) {
                    menu.classList.remove('active');
                    toggle.classList.remove('active');
                    toggle.setAttribute('aria-expanded', 'false');
                }
            });

            // Close menu when clicking a link
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

    // Crypto Ticker — powered by the internal /investments/api/ticker/ endpoint (CoinGecko)
    async function initCryptoTicker() {
        // Ensure the ticker container exists in the DOM.
        // Pages like dashboard/investment-plans include it in their HTML;
        // all other pages get it injected here so it appears site-wide.
        let tickerContainer = document.querySelector('.crypto-ticker-horizontal');
        if (!tickerContainer) {
            tickerContainer = document.createElement('div');
            tickerContainer.className = 'crypto-ticker-horizontal';
            tickerContainer.innerHTML = '<div class="ticker-track"></div>';
            document.body.insertBefore(tickerContainer, document.body.firstChild);
        }

        // Apply inline styles so the bar renders correctly even before style.css
        // has fully loaded (style.css uses media="print"→onload lazy-loading).
        tickerContainer.style.cssText = [
            'position:fixed', 'top:0', 'left:0', 'right:0', 'z-index:1001',
            'height:40px', 'overflow:hidden', 'display:flex', 'align-items:center',
            'background:rgba(10,16,32,0.98)',
            'border-bottom:1px solid rgba(212,175,55,0.35)',
            'backdrop-filter:blur(8px)',
        ].join(';');

        // Inject the @keyframes definition once so the ticker animation always
        // works — even when style.css is still lazy-loading.
        if (!document.getElementById('ewc-ticker-kf')) {
            var kfStyle = document.createElement('style');
            kfStyle.id = 'ewc-ticker-kf';
            kfStyle.textContent = '@keyframes ewcTicker{from{transform:translateX(0)}to{transform:translateX(-50%)}}';
            document.head.appendChild(kfStyle);
        }

        const tickerTrack = tickerContainer.querySelector('.ticker-track');
        if (!tickerTrack) return;

        tickerTrack.style.cssText = [
            'display:flex', 'align-items:center', 'gap:0', 'white-space:nowrap',
            'animation:ewcTicker 45s linear infinite',
        ].join(';');

        // Static fallback data shown while live prices load or if the API is
        // temporarily unreachable (CoinGecko free tier).
        const fallbackCoins = [
            { symbol: 'BTC',  price: 84000,    change: 1.25  },
            { symbol: 'ETH',  price: 2000,     change: -0.85 },
            { symbol: 'USDT', price: 1.00,     change: 0.00  },
            { symbol: 'USDC', price: 1.00,     change: 0.00  },
            { symbol: 'LTC',  price: 92,       change: 0.60  },
            { symbol: 'BNB',  price: 580,      change: 0.92  },
            { symbol: 'SOL',  price: 135,      change: 2.15  },
            { symbol: 'XRP',  price: 2.20,     change: 1.35  },
            { symbol: 'ADA',  price: 0.72,     change: -0.45 },
            { symbol: 'DOGE', price: 0.18,     change: 3.20  },
        ];

        function renderTicker(coins) {
            let html = '';
            coins.forEach(c => {
                const rawPrice = c.price_usd !== undefined ? c.price_usd : c.price;
                if (rawPrice === null || rawPrice === undefined) return;
                const numPrice = parseFloat(rawPrice);
                const change = parseFloat(c.change_24h !== undefined ? c.change_24h : (c.change || 0));
                const changeFixed  = Math.abs(change).toFixed(2);
                const changeColor  = change >= 0 ? '#10b981' : '#ef4444';
                const changeSymbol = change >= 0 ? '▲' : '▼';
                const priceStr = numPrice.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: numPrice < 0.01 ? 6 : 2 });
                // Use inline styles on every item for guaranteed rendering
                html += `<span style="display:inline-flex;align-items:center;gap:5px;padding:0 18px;height:40px;border-right:1px solid rgba(212,175,55,0.18);font-size:0.78rem;font-family:inherit;">`
                      + `<span style="font-weight:700;color:#d4af37;">${c.symbol}</span>`
                      + `<span style="color:#f1f5f9;font-weight:500;">$${priceStr}</span>`
                      + `<span style="color:${changeColor};font-size:0.72rem;">${changeSymbol}${changeFixed}%</span>`
                      + `</span>`;
            });
            // Duplicate for seamless infinite loop
            tickerTrack.innerHTML = html + html;
        }

        // Show fallback immediately so the bar is never empty
        renderTicker(fallbackCoins);

        // Fetch live prices from the internal endpoint (which uses CoinGecko)
        try {
            const response = await fetch('/investments/api/ticker/');
            if (response.ok) {
                const json = await response.json();
                if (json.success && json.tickers && json.tickers.length) {
                    // Only replace fallback if we got actual price data back
                    const withPrices = json.tickers.filter(t => t.price_usd !== null);
                    if (withPrices.length) renderTicker(withPrices);
                }
            }
        } catch (_) {
            // Network error — fallback data already rendered; silently continue
        }
    }

    // Toast Notifications
    function showToast(message, type = 'info') {
        const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };

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
        z-index: 9999;
        transform: translateX(120%);
        transition: transform 0.3s ease;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#3b82f6'};
        box-shadow: 0 10px 40px rgba(0,0,0,0.3);
    `;

        document.body.appendChild(toast);

        setTimeout(() => toast.style.transform = 'translateX(0)', 10);
        setTimeout(() => {
            toast.style.transform = 'translateX(120%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    // Play Sound
    function playSound(type) {
        const sounds = {
            success: '/assets/sounds/success.mp3',
            error: '/assets/sounds/error.mp3',
            notification: '/assets/sounds/notification.mp3'
        };

        try {
            const audio = new Audio(sounds[type] || sounds.notification);
            audio.volume = 0.3;
            audio.play().catch(() => { });
        } catch (e) { }
    }

    // Format Currency
    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD'
        }).format(amount);
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

        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    // Initialize on DOM Load
    document.addEventListener('DOMContentLoaded', () => {
        initMobileMenu();
        initSmoothScroll();
        initCryptoTicker();
        initScrollAnimations();
        initNavbarScroll();

        // Refresh ticker every 60 seconds
        setInterval(initCryptoTicker, 60000);
    });

    // Export functions globally
    window.showToast = showToast;
    window.formatCurrency = formatCurrency;
    window.formatDate = formatDate;
    window.playSound = playSound;
    
    // Logout function - redirects to Django logout view
    window.logout = function() {
        window.location.href = '/accounts/logout/';
    };

})();


