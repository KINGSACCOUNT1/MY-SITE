/**
 * Language Switcher - Multi-language Support
 */

const translations = {
    en: {
        welcome: 'Welcome',
        dashboard: 'Dashboard',
        balance: 'Balance',
        invested: 'Total Invested',
        profit: 'Total Profit',
        withdrawn: 'Withdrawn',
        invest: 'Invest',
        deposit: 'Deposit',
        withdraw: 'Withdraw',
        logout: 'Logout',
        login: 'Login',
        signup: 'Sign Up'
    },
    es: {
        welcome: 'Bienvenido',
        dashboard: 'Panel',
        balance: 'Saldo',
        invested: 'Total Invertido',
        profit: 'Ganancia Total',
        withdrawn: 'Retirado',
        invest: 'Invertir',
        deposit: 'Depositar',
        withdraw: 'Retirar',
        logout: 'Cerrar Sesión',
        login: 'Iniciar Sesión',
        signup: 'Registrarse'
    },
    fr: {
        welcome: 'Bienvenue',
        dashboard: 'Tableau de bord',
        balance: 'Solde',
        invested: 'Total Investi',
        profit: 'Profit Total',
        withdrawn: 'Retiré',
        invest: 'Investir',
        deposit: 'Déposer',
        withdraw: 'Retirer',
        logout: 'Déconnexion',
        login: 'Connexion',
        signup: 'S\'inscrire'
    }
};

class LanguageSwitcher {
    constructor() {
        this.currentLang = localStorage.getItem('language') || 'en';
        this.init();
    }

    init() {
        this.createLanguageSelector();
        this.applyTranslations();
    }

    createLanguageSelector() {
        const selector = document.createElement('div');
        selector.className = 'language-selector';
        selector.innerHTML = `
            <select id="lang-select" class="form-select form-select-sm">
                <option value="en" ${this.currentLang === 'en' ? 'selected' : ''}>🇬🇧 English</option>
                <option value="es" ${this.currentLang === 'es' ? 'selected' : ''}>🇪🇸 Español</option>
                <option value="fr" ${this.currentLang === 'fr' ? 'selected' : ''}>🇫🇷 Français</option>
            </select>
        `;
        
        // Find navbar and add selector
        const navbar = document.querySelector('.navbar .container');
        if (navbar) {
            const navbarNav = navbar.querySelector('.navbar-nav');
            if (navbarNav) {
                const li = document.createElement('li');
                li.className = 'nav-item';
                li.appendChild(selector);
                navbarNav.appendChild(li);
            }
        }
        
        // Add event listener
        document.getElementById('lang-select').addEventListener('change', (e) => {
            this.changeLang(e.target.value);
        });
        
        // Add styles
        if (!document.getElementById('lang-selector-styles')) {
            const style = document.createElement('style');
            style.id = 'lang-selector-styles';
            style.textContent = `
                .language-selector {
                    padding: 0 10px;
                }
                .language-selector select {
                    background: rgba(255,255,255,0.2);
                    color: white;
                    border: 1px solid rgba(255,255,255,0.3);
                    padding: 5px 10px;
                    border-radius: 5px;
                    cursor: pointer;
                }
                .language-selector select option {
                    background: #1a1a2e;
                    color: white;
                }
            `;
            document.head.appendChild(style);
        }
    }

    applyTranslations() {
        const lang = translations[this.currentLang];
        
        // Apply translations to elements with data-translate attribute
        document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.getAttribute('data-translate');
            if (lang[key]) {
                element.textContent = lang[key];
            }
        });
    }

    changeLang(lang) {
        this.currentLang = lang;
        localStorage.setItem('language', lang);
        this.applyTranslations();
        
        // Show notification
        if (window.showToast) {
            window.showToast('Language changed successfully', 'success');
        }
    }
}

// Initialize language switcher
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new LanguageSwitcher());
} else {
    new LanguageSwitcher();
}
