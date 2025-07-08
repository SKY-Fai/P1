/**
 * F-AI Accountant - Professional Theme Management System
 * Commercial-grade theme switching with persistence and accessibility
 */

(function(window, document) {
    'use strict';

    class FaiTheme {
        constructor() {
            this.config = {
                storageKey: 'fai-theme',
                defaultTheme: 'light',
                themes: ['light', 'dark'],
                transitions: true
            };
            
            this.elements = {
                html: document.documentElement,
                toggleButtons: []
            };
            
            this.state = {
                currentTheme: this.getStoredTheme() || this.getSystemPreference() || this.config.defaultTheme
            };

            this.init();
        }

        init() {
            try {
                // Apply initial theme
                this.applyTheme(this.state.currentTheme, false);
                
                // Create toggle button if none exists
                this.createToggleButton();
                
                // Bind events
                this.bindEvents();
                
                // Setup accessibility
                this.setupAccessibility();
                
                console.log('✅ Theme system initialized - Current theme:', this.state.currentTheme);
            } catch (error) {
                console.error('❌ Theme system initialization failed:', error);
            }
        }

        getStoredTheme() {
            try {
                return localStorage.getItem(this.config.storageKey);
            } catch (e) {
                console.warn('Cannot access localStorage for theme storage');
                return null;
            }
        }

        getSystemPreference() {
            if (window.matchMedia) {
                return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
            }
            return this.config.defaultTheme;
        }

        createToggleButton() {
            // Find existing toggle buttons
            this.elements.toggleButtons = Array.from(document.querySelectorAll('.theme-toggle'));
            
            if (this.elements.toggleButtons.length === 0) {
                // Create a default toggle button if none exists
                const button = document.createElement('button');
                button.className = 'theme-toggle btn btn-outline-secondary btn-sm';
                button.setAttribute('aria-label', 'Toggle theme');
                button.innerHTML = '<i class="fas fa-moon"></i>';
                
                // Try to add to navbar or body
                const navbar = document.querySelector('.navbar .navbar-nav');
                if (navbar) {
                    const li = document.createElement('li');
                    li.className = 'nav-item';
                    li.appendChild(button);
                    navbar.appendChild(li);
                } else {
                    document.body.appendChild(button);
                }
                
                this.elements.toggleButtons.push(button);
            }
            
            // Update all toggle buttons
            this.updateToggleButton();
        }

        updateToggleButton() {
            this.elements.toggleButtons.forEach(button => {
                const icon = button.querySelector('i');
                if (icon) {
                    if (this.state.currentTheme === 'dark') {
                        icon.className = 'fas fa-sun';
                        button.setAttribute('title', 'Switch to light mode');
                    } else {
                        icon.className = 'fas fa-moon';
                        button.setAttribute('title', 'Switch to dark mode');
                    }
                }
            });
        }

        applyTheme(theme, animate = true) {
            if (!this.config.themes.includes(theme)) {
                console.warn('Invalid theme:', theme);
                return;
            }

            // Disable transitions temporarily if not animating
            if (!animate) {
                document.body.style.transition = 'none';
            }

            // Apply theme
            this.elements.html.setAttribute('data-theme', theme);
            this.state.currentTheme = theme;

            // Update toggle buttons
            this.updateToggleButton();

            // Save to storage
            this.saveTheme(theme);

            // Dispatch custom event
            this.dispatchThemeChangeEvent(theme);

            // Re-enable transitions
            if (!animate) {
                // Force reflow
                document.body.offsetHeight;
                document.body.style.transition = '';
            }

            console.log('🎨 Theme applied:', theme);
        }

        saveTheme(theme) {
            try {
                localStorage.setItem(this.config.storageKey, theme);
            } catch (e) {
                console.warn('Unable to save theme preference to localStorage');
            }
        }

        toggleTheme() {
            const newTheme = this.state.currentTheme === 'light' ? 'dark' : 'light';
            this.applyTheme(newTheme);
        }

        bindEvents() {
            // Bind toggle button clicks
            this.elements.toggleButtons.forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.toggleTheme();
                });
            });

            // Listen for system theme changes
            if (window.matchMedia) {
                const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
                mediaQuery.addEventListener('change', (e) => {
                    // Only auto-switch if user hasn't manually set a preference
                    if (!this.getStoredTheme()) {
                        const systemTheme = e.matches ? 'dark' : 'light';
                        this.applyTheme(systemTheme);
                    }
                });
            }

            // Keyboard shortcut (Ctrl+Shift+T)
            document.addEventListener('keydown', (e) => {
                if (e.ctrlKey && e.shiftKey && e.key === 'T') {
                    e.preventDefault();
                    this.toggleTheme();
                }
            });
        }

        setupAccessibility() {
            // Add ARIA labels
            this.elements.toggleButtons.forEach(button => {
                button.setAttribute('role', 'switch');
                button.setAttribute('aria-checked', this.state.currentTheme === 'dark');
            });

            // Update ARIA on theme change
            document.addEventListener('themechange', (e) => {
                this.elements.toggleButtons.forEach(button => {
                    button.setAttribute('aria-checked', e.detail.theme === 'dark');
                });
            });
        }

        dispatchThemeChangeEvent(theme) {
            const event = new CustomEvent('themechange', {
                detail: { 
                    theme: theme,
                    previousTheme: this.state.currentTheme
                }
            });
            document.dispatchEvent(event);
        }

        // Public API
        getCurrentTheme() {
            return this.state.currentTheme;
        }

        setTheme(theme) {
            this.applyTheme(theme);
        }

        getAvailableThemes() {
            return [...this.config.themes];
        }
    }

    // Expose to global scope
    window.FaiTheme = FaiTheme;

    // Auto-initialize when core is ready
    if (window.FaiCore) {
        window.FaiCore.ready(() => {
            if (!window.FaiCore.getModule('theme')) {
                window.FaiCore.modules.theme = new FaiTheme();
            }
        });
    } else {
        // Fallback initialization
        document.addEventListener('DOMContentLoaded', () => {
            if (!window.FaiTheme.instance) {
                window.FaiTheme.instance = new FaiTheme();
            }
        });
    }

})(window, document);