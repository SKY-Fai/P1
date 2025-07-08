/**
 * F-AI Accountant - Professional Navigation System
 * Unified navigation management with smooth scrolling and state handling
 */

(function(window, document) {
    'use strict';

    class FaiNavigation {
        constructor() {
            this.config = {
                smoothScrollDuration: 800,
                activeClass: 'active',
                loadingClass: 'loading'
            };
            
            this.elements = {
                navbar: null,
                uploadSection: null,
                uploadButton: null
            };
            
            this.state = {
                currentPage: this.getCurrentPage(),
                isScrolling: false
            };
            
            this.init();
        }

        // Utility function for debouncing
        debounce(func, wait) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }

        init() {
            try {
                this.findElements();
                this.bindEvents();
                this.setupAccessibility();
                console.log('✅ Navigation system initialized');
            } catch (error) {
                console.error('❌ Navigation initialization failed:', error);
            }
        }

        findElements() {
            this.elements.navbar = document.querySelector('.navbar');
            this.elements.uploadSection = document.querySelector('.dual-upload-section') || 
                                        document.querySelector('#upload-section') ||
                                        document.querySelector('[data-section="upload"]');
            this.elements.uploadButton = document.querySelector('[onclick*="triggerFileUpload"]') ||
                                       document.querySelector('.upload-trigger');
        }

        getCurrentPage() {
            const path = window.location.pathname;
            if (path.includes('automated-accounting')) return 'accounting';
            if (path.includes('validation-dashboard')) return 'validation';
            if (path.includes('admin')) return 'admin';
            return 'dashboard';
        }

        bindEvents() {
            // Upload button functionality
            this.setupUploadTrigger();
            
            // Navigation link handling
            this.setupNavigationLinks();
            
            // Scroll tracking
            this.setupScrollTracking();
            
            // Window resize handling
            window.addEventListener('resize', (function() {
                let timeout;
                return function() {
                    clearTimeout(timeout);
                    timeout = setTimeout(() => this.handleResize(), 250);
                };
            }.bind(this))());
        }

        setupUploadTrigger() {
            // Create global upload trigger function
            window.triggerFileUpload = () => {
                this.handleUploadTrigger();
            };

            // Bind to existing upload buttons
            if (this.elements.uploadButton) {
                this.elements.uploadButton.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.handleUploadTrigger();
                });
            }

            // Bind to any other upload triggers
            document.querySelectorAll('[data-action="upload"]').forEach(button => {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.handleUploadTrigger();
                });
            });
        }

        handleUploadTrigger() {
            const currentPage = this.getCurrentPage();
            
            if (currentPage === 'accounting' && this.elements.uploadSection) {
                // Scroll to upload section on current page
                this.smoothScrollTo(this.elements.uploadSection);
            } else {
                // Redirect to accounting page
                this.navigateToPage('/automated-accounting');
            }
        }

        setupNavigationLinks() {
            // Handle all navigation links
            document.querySelectorAll('a[href]').forEach(link => {
                const href = link.getAttribute('href');
                
                // Skip external links and JavaScript links
                if (href.startsWith('http') || href.startsWith('javascript:') || href === '#') {
                    return;
                }
                
                link.addEventListener('click', (e) => {
                    this.handleNavigationClick(e, link);
                });
            });
        }

        handleNavigationClick(event, link) {
            const href = link.getAttribute('href');
            
            // Add loading state
            this.setLoadingState(true);
            
            // Remove loading state after navigation
            setTimeout(() => {
                this.setLoadingState(false);
            }, 1000);
        }

        setupScrollTracking() {
            let scrollTimeout;
            
            window.addEventListener('scroll', () => {
                this.state.isScrolling = true;
                
                clearTimeout(scrollTimeout);
                scrollTimeout = setTimeout(() => {
                    this.state.isScrolling = false;
                }, 150);
                
                this.updateActiveSection();
            });
        }

        updateActiveSection() {
            const sections = document.querySelectorAll('[data-section]');
            const scrollTop = window.pageYOffset;
            const windowHeight = window.innerHeight;
            
            sections.forEach(section => {
                const rect = section.getBoundingClientRect();
                const isVisible = rect.top < windowHeight / 2 && rect.bottom > windowHeight / 2;
                
                if (isVisible) {
                    this.setActiveSection(section.getAttribute('data-section'));
                }
            });
        }

        setActiveSection(sectionName) {
            // Update navigation active states
            document.querySelectorAll('.nav-link').forEach(link => {
                link.classList.remove(this.config.activeClass);
                
                if (link.getAttribute('href').includes(sectionName)) {
                    link.classList.add(this.config.activeClass);
                }
            });
        }

        smoothScrollTo(element, offset = 80) {
            if (!element) return;

            const targetPosition = element.getBoundingClientRect().top + window.pageYOffset - offset;
            const startPosition = window.pageYOffset;
            const distance = targetPosition - startPosition;
            const duration = this.config.smoothScrollDuration;
            let startTime = null;

            const animateScroll = (currentTime) => {
                if (startTime === null) startTime = currentTime;
                const timeElapsed = currentTime - startTime;
                const progress = Math.min(timeElapsed / duration, 1);
                
                // Easing function
                const ease = this.easeInOutCubic(progress);
                
                window.scrollTo(0, startPosition + (distance * ease));
                
                if (timeElapsed < duration) {
                    requestAnimationFrame(animateScroll);
                } else {
                    // Ensure exact position
                    window.scrollTo(0, targetPosition);
                    this.handleScrollComplete(element);
                }
            };

            requestAnimationFrame(animateScroll);
        }

        easeInOutCubic(t) {
            return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
        }

        handleScrollComplete(element) {
            // Add focus for accessibility
            if (element.getAttribute('tabindex') === null) {
                element.setAttribute('tabindex', '-1');
            }
            element.focus({ preventScroll: true });
            
            // Visual feedback
            element.classList.add('highlight-section');
            setTimeout(() => {
                element.classList.remove('highlight-section');
            }, 2000);
        }

        navigateToPage(url) {
            this.setLoadingState(true);
            window.location.href = url;
        }

        setLoadingState(loading) {
            const body = document.body;
            
            if (loading) {
                body.classList.add(this.config.loadingClass);
                this.showLoadingIndicator();
            } else {
                body.classList.remove(this.config.loadingClass);
                this.hideLoadingIndicator();
            }
        }

        showLoadingIndicator() {
            let indicator = document.querySelector('.navigation-loading');
            
            if (!indicator) {
                indicator = document.createElement('div');
                indicator.className = 'navigation-loading';
                indicator.innerHTML = `
                    <div class="loading-spinner">
                        <i class="fas fa-spinner fa-spin"></i>
                        <span>Loading...</span>
                    </div>
                `;
                document.body.appendChild(indicator);
            }
            
            indicator.style.display = 'flex';
        }

        hideLoadingIndicator() {
            const indicator = document.querySelector('.navigation-loading');
            if (indicator) {
                indicator.style.display = 'none';
            }
        }

        setupAccessibility() {
            // Add ARIA labels and roles
            const navbar = this.elements.navbar;
            if (navbar) {
                navbar.setAttribute('role', 'navigation');
                navbar.setAttribute('aria-label', 'Main navigation');
            }

            // Add skip links
            this.addSkipLinks();
            
            // Add loading indicator styles
            this.addLoadingStyles();
        }

        addSkipLinks() {
            const skipLink = document.createElement('a');
            skipLink.href = '#main-content';
            skipLink.className = 'skip-link';
            skipLink.textContent = 'Skip to main content';
            skipLink.style.cssText = `
                position: absolute;
                top: -40px;
                left: 6px;
                background: var(--primary-color, #dc3545);
                color: white;
                padding: 8px;
                text-decoration: none;
                border-radius: 4px;
                z-index: 9999;
                transition: top 0.3s;
            `;
            
            skipLink.addEventListener('focus', () => {
                skipLink.style.top = '6px';
            });
            
            skipLink.addEventListener('blur', () => {
                skipLink.style.top = '-40px';
            });
            
            document.body.insertBefore(skipLink, document.body.firstChild);
        }

        addLoadingStyles() {
            const style = document.createElement('style');
            style.textContent = `
                .navigation-loading {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0, 0, 0, 0.5);
                    display: none;
                    align-items: center;
                    justify-content: center;
                    z-index: 9999;
                }
                
                .loading-spinner {
                    background: white;
                    padding: 20px;
                    border-radius: 8px;
                    text-align: center;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                
                .loading-spinner i {
                    font-size: 24px;
                    margin-bottom: 10px;
                    color: var(--primary-color, #dc3545);
                }
                
                .highlight-section {
                    animation: highlight-pulse 2s ease-in-out;
                }
                
                @keyframes highlight-pulse {
                    0%, 100% { box-shadow: none; }
                    50% { box-shadow: 0 0 20px rgba(220, 53, 69, 0.3); }
                }
                
                .loading * {
                    cursor: wait !important;
                }
            `;
            document.head.appendChild(style);
        }

        handleResize() {
            // Recalculate positions if needed
            this.updateActiveSection();
        }



        // Public API
        scrollToUpload() {
            this.handleUploadTrigger();
        }

        navigateTo(url) {
            this.navigateToPage(url);
        }

        highlightSection(selector) {
            const element = document.querySelector(selector);
            if (element) {
                this.smoothScrollTo(element);
            }
        }
    }

    // Expose to global scope
    window.FaiNavigation = FaiNavigation;

    // Auto-initialize
    if (window.FaiCore) {
        window.FaiCore.ready(() => {
            if (!window.FaiCore.getModule('navigation')) {
                window.FaiCore.modules.navigation = new FaiNavigation();
            }
        });
    }

})(window, document);