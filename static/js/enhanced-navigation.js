/**
 * Enhanced Navigation System for F-AI Accountant
 * Fixes responsiveness and ensures proper navigation functionality across the entire software
 */

class EnhancedNavigation {
    constructor() {
        this.init();
    }

    init() {
        console.log('Enhanced Navigation System Initializing...');
        this.initializeBootstrapComponents();
        this.setupNavigationHandlers();
        this.setupMobileResponsiveness();
        this.fixFileInteractionNavigation();
        console.log('✅ Enhanced Navigation System Ready');
    }

    initializeBootstrapComponents() {
        // Initialize Bootstrap dropdowns
        const dropdownElements = document.querySelectorAll('[data-bs-toggle="dropdown"]');
        dropdownElements.forEach(element => {
            if (!bootstrap.Dropdown.getInstance(element)) {
                new bootstrap.Dropdown(element);
            }
        });

        // Initialize navbar collapse
        const navbarToggler = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');
        
        if (navbarToggler && navbarCollapse) {
            navbarToggler.addEventListener('click', (e) => {
                e.preventDefault();
                const bsCollapse = bootstrap.Collapse.getOrCreateInstance(navbarCollapse);
                bsCollapse.toggle();
            });
        }
    }

    setupNavigationHandlers() {
        // Handle all navigation links
        const navLinks = document.querySelectorAll('.nav-link:not(.dropdown-toggle)');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                this.handleNavigationClick(e, link);
            });
        });

        // Handle dropdown items
        const dropdownItems = document.querySelectorAll('.dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', (e) => {
                this.handleNavigationClick(e, item);
            });
        });
    }

    handleNavigationClick(e, element) {
        const href = element.getAttribute('href');
        
        // Skip if no href or javascript void
        if (!href || href === '#' || href.startsWith('javascript:')) {
            return;
        }

        // Add loading state
        this.showLoadingState(element);

        // Close mobile menu
        this.closeMobileMenu();

        // Handle special cases
        if (href.includes('file-interaction')) {
            console.log('Navigating to File Interaction...');
            setTimeout(() => {
                window.location.href = href;
            }, 100);
        }
    }

    showLoadingState(element) {
        const originalHtml = element.innerHTML;
        const textContent = element.textContent.trim();
        
        // Add spinner
        element.innerHTML = `<i class="fas fa-spinner fa-spin me-1"></i>${textContent}`;
        
        // Reset after timeout
        setTimeout(() => {
            if (element && element.innerHTML.includes('fa-spinner')) {
                element.innerHTML = originalHtml;
            }
        }, 3000);
    }

    closeMobileMenu() {
        const navbarCollapse = document.querySelector('.navbar-collapse');
        if (navbarCollapse && navbarCollapse.classList.contains('show')) {
            const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
            if (bsCollapse) {
                bsCollapse.hide();
            }
        }
    }

    setupMobileResponsiveness() {
        // Handle window resize
        window.addEventListener('resize', () => {
            this.handleResize();
        });

        // Handle orientation change
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleResize();
            }, 100);
        });
    }

    handleResize() {
        const navbarCollapse = document.querySelector('.navbar-collapse');
        if (window.innerWidth > 991 && navbarCollapse && navbarCollapse.classList.contains('show')) {
            const bsCollapse = bootstrap.Collapse.getInstance(navbarCollapse);
            if (bsCollapse) {
                bsCollapse.hide();
            }
        }
    }

    fixFileInteractionNavigation() {
        // Specifically fix File Interaction navigation
        const fileInteractionLink = document.querySelector('a[href*="file-interaction"], a[href*="file_interaction"]');
        
        if (fileInteractionLink) {
            fileInteractionLink.addEventListener('click', (e) => {
                e.preventDefault();
                console.log('File Interaction link clicked');
                
                // Show loading state
                this.showLoadingState(fileInteractionLink);
                
                // Close mobile menu
                this.closeMobileMenu();
                
                // Navigate with proper URL
                setTimeout(() => {
                    window.location.href = '/file-interaction';
                }, 150);
            });
        }

        // Also fix any direct references in navigation
        const navItems = document.querySelectorAll('.nav-item a, .dropdown-item');
        navItems.forEach(item => {
            const text = item.textContent.toLowerCase();
            if (text.includes('file interaction') || text.includes('file upload')) {
                item.addEventListener('click', (e) => {
                    if (!item.href || item.href.includes('#')) {
                        e.preventDefault();
                        this.showLoadingState(item);
                        this.closeMobileMenu();
                        setTimeout(() => {
                            window.location.href = '/file-interaction';
                        }, 150);
                    }
                });
            }
        });
    }

    // Public method to navigate programmatically
    navigateTo(url) {
        if (url && url !== '#') {
            this.closeMobileMenu();
            window.location.href = url;
        }
    }

    // Public method to refresh navigation
    refresh() {
        this.init();
    }
}

// Global navigation functions
window.enhancedNavigateTo = function(url) {
    if (window.enhancedNav) {
        window.enhancedNav.navigateTo(url);
    } else {
        window.location.href = url;
    }
};

window.refreshNavigation = function() {
    if (window.enhancedNav) {
        window.enhancedNav.refresh();
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Wait for Bootstrap to be available
    if (typeof bootstrap !== 'undefined') {
        window.enhancedNav = new EnhancedNavigation();
    } else {
        // Fallback - wait for Bootstrap
        setTimeout(() => {
            if (typeof bootstrap !== 'undefined') {
                window.enhancedNav = new EnhancedNavigation();
            }
        }, 500);
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedNavigation;
}