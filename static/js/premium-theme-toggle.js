/**
 * F-AI Accountant - Premium Theme Toggle System
 * Professional light/dark mode switching with persistence
 */

// Theme Management System
class PremiumThemeManager {
    constructor() {
        this.storageKey = 'f-ai-accountant-theme';
        this.themes = {
            light: 'light',
            dark: 'dark'
        };
        
        // Initialize theme on page load
        this.init();
    }
    
    init() {
        // Get saved theme or default to light
        const savedTheme = this.getSavedTheme();
        const preferredTheme = savedTheme || this.getSystemPreference();
        
        // Apply theme immediately to prevent flash
        this.applyTheme(preferredTheme, false);
        
        // Update toggle button icon
        this.updateToggleIcon(preferredTheme);
        
        // Add smooth transition after initial load
        setTimeout(() => {
            document.documentElement.style.transition = 'all 0.3s ease';
        }, 100);
    }
    
    getSavedTheme() {
        try {
            return localStorage.getItem(this.storageKey);
        } catch (e) {
            console.warn('LocalStorage not available:', e);
            return null;
        }
    }
    
    saveTheme(theme) {
        try {
            localStorage.setItem(this.storageKey, theme);
        } catch (e) {
            console.warn('Could not save theme preference:', e);
        }
    }
    
    getSystemPreference() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return this.themes.dark;
        }
        return this.themes.light;
    }
    
    getCurrentTheme() {
        return document.documentElement.getAttribute('data-theme') || this.themes.light;
    }
    
    applyTheme(theme, animate = true) {
        // Validate theme
        if (!Object.values(this.themes).includes(theme)) {
            console.warn('Invalid theme:', theme);
            theme = this.themes.light;
        }
        
        // Apply theme with optional animation
        if (animate) {
            document.documentElement.style.transition = 'all 0.3s ease';
        }
        
        document.documentElement.setAttribute('data-theme', theme);
        
        // Update body class for compatibility
        document.body.className = document.body.className
            .replace(/theme-(light|dark)/g, '')
            .trim() + ` theme-${theme}`;
        
        // Save preference
        this.saveTheme(theme);
        
        // Update toggle button
        this.updateToggleIcon(theme);
        
        // Dispatch custom event for other components
        this.dispatchThemeChangeEvent(theme);
        
        // Analytics/logging
        this.logThemeChange(theme);
    }
    
    toggleTheme() {
        const currentTheme = this.getCurrentTheme();
        const newTheme = currentTheme === this.themes.light ? this.themes.dark : this.themes.light;
        
        // Add toggle animation
        this.animateToggle();
        
        // Apply new theme
        this.applyTheme(newTheme);
        
        return newTheme;
    }
    
    updateToggleIcon(theme) {
        const toggleButtons = document.querySelectorAll('.premium-theme-toggle');
        
        toggleButtons.forEach(button => {
            const icon = button.querySelector('i');
            if (icon) {
                // Remove existing theme icons
                icon.className = icon.className.replace(/fa-(sun|moon|palette|adjust|lightbulb)/g, '');
                
                // Add appropriate icon based on theme
                if (theme === this.themes.dark) {
                    icon.classList.add('fa-sun');
                    button.setAttribute('title', 'Switch to Light Mode');
                } else {
                    icon.classList.add('fa-moon');
                    button.setAttribute('title', 'Switch to Dark Mode');
                }
            }
        });
    }
    
    animateToggle() {
        const toggleButtons = document.querySelectorAll('.premium-theme-toggle');
        
        toggleButtons.forEach(button => {
            // Add ripple effect
            button.style.transform = 'scale(0.95)';
            button.style.transition = 'transform 0.1s ease';
            
            setTimeout(() => {
                button.style.transform = 'scale(1.05)';
                setTimeout(() => {
                    button.style.transform = 'scale(1)';
                    button.style.transition = 'all 0.3s ease';
                }, 100);
            }, 100);
            
            // Rotate icon animation
            const icon = button.querySelector('i');
            if (icon) {
                icon.style.transform = 'rotate(360deg)';
                icon.style.transition = 'transform 0.5s ease';
                
                setTimeout(() => {
                    icon.style.transform = 'rotate(0deg)';
                }, 500);
            }
        });
    }
    
    dispatchThemeChangeEvent(theme) {
        const event = new CustomEvent('themeChanged', {
            detail: { theme, timestamp: Date.now() }
        });
        document.dispatchEvent(event);
    }
    
    logThemeChange(theme) {
        console.log(`🎨 Theme changed to: ${theme}`, {
            timestamp: new Date().toISOString(),
            userAgent: navigator.userAgent.slice(0, 50) + '...'
        });
    }
    
    // Listen for system theme changes
    listenForSystemChanges() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            mediaQuery.addEventListener('change', (e) => {
                // Only auto-switch if user hasn't manually set a preference
                const savedTheme = this.getSavedTheme();
                if (!savedTheme) {
                    const newTheme = e.matches ? this.themes.dark : this.themes.light;
                    this.applyTheme(newTheme);
                }
            });
        }
    }
    
    // Force theme (for testing/debugging)
    forceTheme(theme) {
        console.log(`🔧 Forcing theme to: ${theme}`);
        this.applyTheme(theme);
    }
    
    // Reset to system preference
    resetToSystem() {
        try {
            localStorage.removeItem(this.storageKey);
        } catch (e) {
            console.warn('Could not clear theme preference:', e);
        }
        
        const systemTheme = this.getSystemPreference();
        this.applyTheme(systemTheme);
        
        console.log(`🔄 Reset to system theme: ${systemTheme}`);
    }
}

// Initialize theme manager
let themeManager;

// DOM Ready initialization
document.addEventListener('DOMContentLoaded', function() {
    themeManager = new PremiumThemeManager();
    
    // Listen for system theme changes
    themeManager.listenForSystemChanges();
    
    // Add keyboard shortcut (Ctrl/Cmd + Shift + T)
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
            e.preventDefault();
            toggleTheme();
        }
    });
    
    // Add theme change listener for other components
    document.addEventListener('themeChanged', function(e) {
        // Update any theme-dependent components
        updateThemeDependentComponents(e.detail.theme);
    });
});

// Global toggle function (called by HTML buttons)
function toggleTheme() {
    if (themeManager) {
        return themeManager.toggleTheme();
    } else {
        console.warn('Theme manager not initialized');
        // Fallback for immediate execution
        const html = document.documentElement;
        const currentTheme = html.getAttribute('data-theme') || 'light';
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        html.setAttribute('data-theme', newTheme);
        return newTheme;
    }
}

// Helper function to update theme-dependent components
function updateThemeDependentComponents(theme) {
    // Update charts if Chart.js is present
    if (typeof Chart !== 'undefined' && window.chartInstances) {
        Object.values(window.chartInstances).forEach(chart => {
            updateChartTheme(chart, theme);
        });
    }
    
    // Update DataTables if present
    if (typeof $.fn.DataTable !== 'undefined') {
        $('.dataTable').each(function() {
            const table = $(this).DataTable();
            if (table) {
                table.draw(false); // Redraw without changing paging
            }
        });
    }
    
    // Update any custom theme-dependent elements
    updateCustomComponents(theme);
}

// Chart.js theme updater
function updateChartTheme(chart, theme) {
    if (!chart || !chart.options) return;
    
    const isDark = theme === 'dark';
    const textColor = isDark ? '#ffffff' : '#2c3e50';
    const gridColor = isDark ? '#404040' : '#e1e8ed';
    
    // Update chart colors
    if (chart.options.plugins && chart.options.plugins.legend) {
        chart.options.plugins.legend.labels = chart.options.plugins.legend.labels || {};
        chart.options.plugins.legend.labels.color = textColor;
    }
    
    if (chart.options.scales) {
        Object.keys(chart.options.scales).forEach(scaleId => {
            const scale = chart.options.scales[scaleId];
            if (scale.ticks) {
                scale.ticks.color = textColor;
            }
            if (scale.grid) {
                scale.grid.color = gridColor;
            }
        });
    }
    
    chart.update('none'); // Update without animation
}

// Custom components theme updater
function updateCustomComponents(theme) {
    // Add any custom component updates here
    console.log(`🔧 Updating custom components for ${theme} theme`);
    
    // Example: Update custom progress bars, specific icons, etc.
    const customElements = document.querySelectorAll('[data-theme-dependent]');
    customElements.forEach(element => {
        element.setAttribute('data-current-theme', theme);
    });
}

// Utility functions for manual theme management
window.ThemeUtils = {
    getCurrentTheme: () => themeManager ? themeManager.getCurrentTheme() : 'light',
    setTheme: (theme) => themeManager ? themeManager.applyTheme(theme) : null,
    toggleTheme: () => toggleTheme(),
    resetToSystem: () => themeManager ? themeManager.resetToSystem() : null,
    forceTheme: (theme) => themeManager ? themeManager.forceTheme(theme) : null
};

// Export for module systems if needed
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { PremiumThemeManager, toggleTheme };
}

// Console helper for debugging
console.log('🎨 Premium Theme System Loaded');
console.log('💡 Use ThemeUtils.toggleTheme() or press Ctrl+Shift+T to toggle theme');
console.log('🔧 Use ThemeUtils.setTheme("light"|"dark") to set specific theme');