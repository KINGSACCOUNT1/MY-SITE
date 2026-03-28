/**
 * Theme Switcher - Dark/Light Mode
 */

class ThemeSwitcher {
    constructor() {
        this.currentTheme = localStorage.getItem('theme') || 'light';
        this.init();
    }

    init() {
        // Apply saved theme
        this.applyTheme(this.currentTheme);
        
        // Create theme toggle button
        this.createToggleButton();
    }

    createToggleButton() {
        const button = document.createElement('button');
        button.id = 'theme-toggle';
        button.className = 'theme-toggle-btn';
        button.innerHTML = this.currentTheme === 'dark' 
            ? '<i class="fas fa-sun"></i>' 
            : '<i class="fas fa-moon"></i>';
        button.title = 'Toggle Theme';
        
        button.onclick = () => this.toggleTheme();
        
        // Add to page
        document.body.appendChild(button);
        
        // Add styles
        if (!document.getElementById('theme-toggle-styles')) {
            const style = document.createElement('style');
            style.id = 'theme-toggle-styles';
            style.textContent = `
                .theme-toggle-btn {
                    position: fixed;
                    bottom: 80px;
                    right: 20px;
                    width: 50px;
                    height: 50px;
                    border-radius: 50%;
                    border: none;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    font-size: 20px;
                    cursor: pointer;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                    z-index: 9997;
                    transition: transform 0.3s ease, box-shadow 0.3s ease;
                }
                .theme-toggle-btn:hover {
                    transform: scale(1.1);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.4);
                }
                
                /* Dark Theme Styles */
                body.dark-theme {
                    background-color: #1a1a2e;
                    color: #eee;
                }
                body.dark-theme .navbar {
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%) !important;
                }
                body.dark-theme .card {
                    background-color: #16213e;
                    color: #eee;
                    border-color: #2a2a4e;
                }
                body.dark-theme .table {
                    color: #eee;
                }
                body.dark-theme .form-control {
                    background-color: #2a2a4e;
                    color: #eee;
                    border-color: #3a3a5e;
                }
                body.dark-theme .btn-primary {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                }
                body.dark-theme footer {
                    background-color: #0f0f1e !important;
                }
                
                @media (max-width: 768px) {
                    .theme-toggle-btn { 
                        width: 45px; 
                        height: 45px; 
                        bottom: 70px; 
                        right: 15px; 
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    applyTheme(theme) {
        if (theme === 'dark') {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
        
        this.currentTheme = theme;
        localStorage.setItem('theme', theme);
    }

    toggleTheme() {
        const newTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(newTheme);
        
        // Update button icon
        const button = document.getElementById('theme-toggle');
        button.innerHTML = newTheme === 'dark' 
            ? '<i class="fas fa-sun"></i>' 
            : '<i class="fas fa-moon"></i>';
    }
}

// Initialize theme switcher
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new ThemeSwitcher());
} else {
    new ThemeSwitcher();
}
