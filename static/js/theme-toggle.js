// F-AI Accountant - Theme Toggle Functionality
// Professional light/dark mode switcher with persistence

class ThemeManager {
    constructor() {
        this.currentTheme = this.getStoredTheme() || 'light';
        this.themeToggle = null;
        this.init();
    }

    init() {
        this.createThemeToggle();
        this.applyTheme(this.currentTheme);
        this.bindEvents();
    }

    createThemeToggle() {
        // Create the theme toggle button
        const toggleButton = document.createElement('button');
        toggleButton.className = 'theme-toggle';
        toggleButton.innerHTML = this.getToggleHTML();
        toggleButton.setAttribute('aria-label', 'Toggle theme');
        toggleButton.setAttribute('title', 'Switch between light and dark mode');
        
        // Add to document
        document.body.appendChild(toggleButton);
        this.themeToggle = toggleButton;
    }

    getToggleHTML() {
        if (this.currentTheme === 'light') {
            return '<i class="fas fa-moon"></i><span>Dark Mode</span>';
        } else {
            return '<i class="fas fa-sun"></i><span>Light Mode</span>';
        }
    }

    bindEvents() {
        if (this.themeToggle) {
            this.themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }

        // Listen for system theme changes
        if (window.matchMedia) {
            window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
                if (!this.hasStoredTheme()) {
                    this.applyTheme(e.matches ? 'dark' : 'light');
                }
            });
        }
    }

    toggleTheme() {
        this.currentTheme = this.currentTheme === 'light' ? 'dark' : 'light';
        this.applyTheme(this.currentTheme);
        this.storeTheme(this.currentTheme);
        this.updateToggleButton();
        this.announceThemeChange();
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.currentTheme = theme;
        
        // Update meta theme-color for mobile browsers
        this.updateMetaThemeColor(theme);
        
        // Trigger custom event for other components
        window.dispatchEvent(new CustomEvent('themeChanged', { 
            detail: { theme: theme } 
        }));
    }

    updateToggleButton() {
        if (this.themeToggle) {
            this.themeToggle.innerHTML = this.getToggleHTML();
            
            // Add animation class
            this.themeToggle.classList.add('theme-switching');
            setTimeout(() => {
                this.themeToggle.classList.remove('theme-switching');
            }, 300);
        }
    }

    updateMetaThemeColor(theme) {
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }
        
        const themeColors = {
            light: '#ffffff',
            dark: '#1f2937'
        };
        
        metaThemeColor.content = themeColors[theme] || themeColors.light;
    }

    storeTheme(theme) {
        try {
            localStorage.setItem('fai-theme', theme);
        } catch (e) {
            console.warn('Unable to store theme preference:', e);
        }
    }

    getStoredTheme() {
        try {
            return localStorage.getItem('fai-theme');
        } catch (e) {
            console.warn('Unable to retrieve stored theme:', e);
            return null;
        }
    }

    hasStoredTheme() {
        return this.getStoredTheme() !== null;
    }

    getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    announceThemeChange() {
        // Announce theme change for screen readers
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = `Theme changed to ${this.currentTheme} mode`;
        
        document.body.appendChild(announcement);
        setTimeout(() => {
            document.body.removeChild(announcement);
        }, 1000);
    }

    // Public API
    setTheme(theme) {
        if (theme === 'light' || theme === 'dark') {
            this.currentTheme = theme;
            this.applyTheme(theme);
            this.storeTheme(theme);
            this.updateToggleButton();
        }
    }

    getTheme() {
        return this.currentTheme;
    }
}

// Additional CSS for theme switching animation
const themeToggleCSS = `
.theme-toggle.theme-switching {
    transform: scale(0.95);
}

.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

/* Smooth transitions for theme changes */
* {
    transition: background-color 0.3s ease, 
                color 0.3s ease, 
                border-color 0.3s ease,
                box-shadow 0.3s ease !important;
}

/* Override transitions for interactive elements */
.btn, .form-control, .card, .navbar-nav .nav-link {
    transition: all 0.3s ease !important;
}

/* Ensure charts and complex elements transition smoothly */
.chart-container, .table, .modal-content {
    transition: background-color 0.3s ease, 
                color 0.3s ease, 
                border-color 0.3s ease !important;
}

/* Special handling for DataTables if present */
.dataTables_wrapper {
    transition: all 0.3s ease !important;
}

/* Ensure all text maintains readability during transitions */
[data-theme="dark"] {
    color-scheme: dark;
}

[data-theme="light"] {
    color-scheme: light;
}
`;

// Initialize theme manager when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Add theme toggle CSS
    const style = document.createElement('style');
    style.textContent = themeToggleCSS;
    document.head.appendChild(style);
    
    // Initialize theme manager
    window.themeManager = new ThemeManager();
    
    // Make it globally accessible
    window.setTheme = (theme) => window.themeManager.setTheme(theme);
    window.getTheme = () => window.themeManager.getTheme();
    
    console.log('F-AI Accountant Theme System initialized');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ThemeManager;
}