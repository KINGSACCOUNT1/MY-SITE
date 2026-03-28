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

    // Crypto Ticker — Static display (admin manages wallet addresses separately)
    async function initCryptoTicker() {
        const tickerTrack = document.querySelector('.ticker-track');
        if (!tickerTrack) return;

        const cryptos = [
            { symbol: 'BTC',   name: 'Bitcoin',    price: 84000,    change: 1.25  },
            { symbol: 'ETH',   name: 'Ethereum',   price: 2000,     change: -0.85 },
            { symbol: 'USDT',  name: 'Tether',     price: 1.00,     change: 0.00  },
            { symbol: 'BNB',   name: 'BNB',        price: 580,      change: 0.92  },
            { symbol: 'SOL',   name: 'Solana',     price: 135,      change: 2.15  },
            { symbol: 'XRP',   name: 'XRP',        price: 2.20,     change: 1.35  },
            { symbol: 'USDC',  name: 'USD Coin',   price: 1.00,     change: 0.00  },
            { symbol: 'ADA',   name: 'Cardano',    price: 0.72,     change: -0.45 },
            { symbol: 'AVAX',  name: 'Avalanche',  price: 22,       change: 1.80  },
            { symbol: 'DOGE',  name: 'Dogecoin',   price: 0.18,     change: 3.20  },
            { symbol: 'TRX',   name: 'TRON',       price: 0.24,     change: 0.50  },
            { symbol: 'DOT',   name: 'Polkadot',   price: 5.20,     change: -1.20 },
            { symbol: 'LINK',  name: 'Chainlink',  price: 13.50,    change: 2.30  },
            { symbol: 'MATIC', name: 'Polygon',    price: 0.45,     change: -0.80 },
            { symbol: 'LTC',   name: 'Litecoin',   price: 92,       change: 0.60  },
            { symbol: 'UNI',   name: 'Uniswap',    price: 7.80,     change: 1.10  },
            { symbol: 'SHIB',  name: 'Shiba Inu',  price: 0.0000135,change: 4.50  },
            { symbol: 'ATOM',  name: 'Cosmos',     price: 4.80,     change: -0.70 },
            { symbol: 'XLM',   name: 'Stellar',    price: 0.28,     change: 1.90  },
            { symbol: 'XMR',   name: 'Monero',     price: 215,      change: 0.40  }
        ];

        let tickerHTML = '';
        cryptos.forEach(crypto => {
            const changeFixed = crypto.change.toFixed(2);
            const changeClass = crypto.change >= 0 ? 'positive' : 'negative';
            const changeSymbol = crypto.change >= 0 ? '+' : '';
            tickerHTML += `
                <div class="ticker-item">
                    <span class="crypto-symbol">${crypto.symbol}</span>
                    <span class="crypto-price">$${crypto.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: crypto.price < 0.01 ? 8 : 2 })}</span>
                    <span class="crypto-change ${changeClass}">${changeSymbol}${changeFixed}%</span>
                </div>
            `;
        });

        tickerTrack.innerHTML = tickerHTML + tickerHTML; // Duplicate for seamless loop

        // Update price cards if they exist
        updatePriceCards(cryptos);
    }

    // Update static price cards with live Bybit data
    function updatePriceCards(cryptos) {
        const priceMap = {};
        cryptos.forEach(crypto => {
            priceMap[crypto.symbol] = crypto;
        });

        document.querySelectorAll('.price-card').forEach(card => {
            const symbolEl = card.querySelector('.price-symbol');
            if (!symbolEl) return;

            const symbol = symbolEl.textContent.trim();
            const coinData = priceMap[symbol];

            if (coinData) {
                const priceEl = card.querySelector('.price-value');
                const changeEl = card.querySelector('.price-change');

                if (priceEl) {
                    priceEl.textContent = `$${coinData.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                }
                if (changeEl) {
                    const change = coinData.change.toFixed(1);
                    const isPositive = coinData.change >= 0;
                    changeEl.textContent = `${isPositive ? '+' : ''}${change}%`;
                    changeEl.className = `price-change ${isPositive ? 'positive' : 'negative'}`;
                }
            }
        });
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
        z-index: 200;
        transform: translateX(120%);
        transition: transform 0.3s ease;
        background: ${type === 'success' ? '#00A86B' : type === 'error' ? '#ef4444' : type === 'warning' ? '#FFD700' : '#3b82f6'};
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


