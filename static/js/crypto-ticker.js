/**
 * Live Cryptocurrency Price Ticker
 * Displays scrolling crypto prices on all pages
 */

const cryptoSymbols = ['BTC', 'ETH', 'USDT', 'BNB', 'SOL', 'XRP', 'ADA', 'DOGE', 'DOT', 'MATIC'];

class CryptoTicker {
    constructor() {
        this.prices = {};
        this.init();
    }

    init() {
        this.createTickerContainer();
        this.fetchPrices();
        setInterval(() => this.fetchPrices(), 30000); // Update every 30 seconds
    }

    createTickerContainer() {
        if (document.getElementById('crypto-ticker')) return;

        const ticker = document.createElement('div');
        ticker.id = 'crypto-ticker';
        ticker.className = 'crypto-ticker';
        ticker.innerHTML = '<div class="ticker-wrapper"><div class="ticker-content"></div></div>';
        
        // Insert at top of body
        document.body.insertBefore(ticker, document.body.firstChild);
        
        // Add styles
        if (!document.getElementById('crypto-ticker-styles')) {
            const style = document.createElement('style');
            style.id = 'crypto-ticker-styles';
            style.textContent = `
                .crypto-ticker {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
                    color: white;
                    padding: 12px 0;
                    z-index: 9998;
                    overflow: hidden;
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                }
                .ticker-wrapper {
                    overflow: hidden;
                    width: 100%;
                }
                .ticker-content {
                    display: flex;
                    animation: scroll 30s linear infinite;
                    white-space: nowrap;
                }
                .ticker-item {
                    display: inline-flex;
                    align-items: center;
                    margin: 0 30px;
                    font-size: 16px;
                    font-weight: 500;
                }
                .ticker-symbol {
                    font-weight: 700;
                    margin-right: 8px;
                    color: #ffd700;
                }
                .ticker-price {
                    margin-right: 8px;
                }
                .ticker-change {
                    font-size: 11px;
                    padding: 2px 6px;
                    border-radius: 4px;
                }
                .ticker-change.positive {
                    background: rgba(34, 197, 94, 0.2);
                    color: #22c55e;
                }
                .ticker-change.negative {
                    background: rgba(239, 68, 68, 0.2);
                    color: #ef4444;
                }
                @keyframes scroll {
                    0% { transform: translateX(0); }
                    100% { transform: translateX(-50%); }
                }
                @media (max-width: 768px) {
                    .crypto-ticker { padding: 6px 0; }
                    .ticker-item { margin: 0 20px; font-size: 12px; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    async fetchPrices() {
        try {
            const symbols = cryptoSymbols.join(',');
            const response = await fetch(`https://api.binance.com/api/v3/ticker/24hr`);
            const data = await response.json();
            
            // Filter for our symbols
            const relevantData = data.filter(item => {
                const symbol = item.symbol.replace('USDT', '');
                return cryptoSymbols.includes(symbol);
            });
            
            relevantData.forEach(item => {
                const symbol = item.symbol.replace('USDT', '');
                this.prices[symbol] = {
                    price: parseFloat(item.lastPrice),
                    change: parseFloat(item.priceChangePercent)
                };
            });
            
            this.renderTicker();
        } catch (error) {
            console.error('Error fetching crypto prices:', error);
            // Use fallback prices if API fails
            this.useFallbackPrices();
        }
    }

    useFallbackPrices() {
        const fallback = {
            BTC: { price: 65432.50, change: 2.5 },
            ETH: { price: 3456.78, change: 1.8 },
            USDT: { price: 1.00, change: 0.01 },
            BNB: { price: 543.21, change: -0.5 },
            SOL: { price: 123.45, change: 3.2 },
            XRP: { price: 0.65, change: -1.2 },
            ADA: { price: 0.45, change: 0.8 },
            DOGE: { price: 0.12, change: 5.6 },
            DOT: { price: 7.89, change: 1.1 },
            MATIC: { price: 0.89, change: -0.3 }
        };
        this.prices = fallback;
        this.renderTicker();
    }

    renderTicker() {
        const content = document.querySelector('.ticker-content');
        if (!content) return;
        
        let html = '';
        
        // Duplicate content for seamless scroll
        for (let i = 0; i < 2; i++) {
            Object.entries(this.prices).forEach(([symbol, data]) => {
                const changeClass = data.change >= 0 ? 'positive' : 'negative';
                const changeSymbol = data.change >= 0 ? '▲' : '▼';
                const price = data.price >= 1 ? data.price.toFixed(2) : data.price.toFixed(4);
                
                html += `
                    <div class="ticker-item">
                        <span class="ticker-symbol">${symbol}</span>
                        <span class="ticker-price">$${price}</span>
                        <span class="ticker-change ${changeClass}">${changeSymbol} ${Math.abs(data.change).toFixed(2)}%</span>
                    </div>
                `;
            });
        }
        
        content.innerHTML = html;
    }
}

// Initialize ticker when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new CryptoTicker());
} else {
    new CryptoTicker();
}
