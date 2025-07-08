/**
 * AccuFin360 - Main Application JavaScript
 * Handles global functionality, initialization, and common UI interactions
 */

(function($) {
    'use strict';

    // Global application object
    window.AccuFin360 = {
        config: {
            apiBaseUrl: '/api',
            csrfToken: null,
            userId: null,
            userRole: null
        },
        
        utils: {},
        components: {},
        
        // Initialize application
        init: function() {
            this.setupCSRF();
            this.initializeComponents();
            this.bindGlobalEvents();
            this.setupAjaxDefaults();
            this.initializeTooltips();
            this.setupProgressiveEnhancement();
            console.log('AccuFin360 initialized successfully');
        }
    };

    // Utility functions
    AccuFin360.utils = {
        
        // Format currency values
        formatCurrency: function(amount, currency = 'USD') {
            const formatter = new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: currency,
                minimumFractionDigits: 2
            });
            return formatter.format(amount);
        },
        
        // Format numbers with thousand separators
        formatNumber: function(number, decimals = 2) {
            return new Intl.NumberFormat('en-US', {
                minimumFractionDigits: decimals,
                maximumFractionDigits: decimals
            }).format(number);
        },
        
        // Format file size
        formatFileSize: function(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        },
        
        // Validate email format
        validateEmail: function(email) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            return emailRegex.test(email);
        },
        
        // Generate unique ID
        generateId: function() {
            return '_' + Math.random().toString(36).substr(2, 9);
        },
        
        // Debounce function
        debounce: function(func, wait, immediate) {
            let timeout;
            return function executedFunction() {
                const context = this;
                const args = arguments;
                const later = function() {
                    timeout = null;
                    if (!immediate) func.apply(context, args);
                };
                const callNow = immediate && !timeout;
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
                if (callNow) func.apply(context, args);
            };
        },
        
        // Show loading spinner
        showLoading: function(element, message = 'Loading...') {
            const $element = $(element);
            const loadingHtml = `
                <div class="loading-overlay">
                    <div class="text-center">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <div class="mt-2">${message}</div>
                    </div>
                </div>
            `;
            $element.css('position', 'relative').append(loadingHtml);
        },
        
        // Hide loading spinner
        hideLoading: function(element) {
            $(element).find('.loading-overlay').remove();
        },
        
        // Show notification
        showNotification: function(message, type = 'info', duration = 5000) {
            const notificationId = this.generateId();
            const alertClass = type === 'error' ? 'danger' : type;
            const iconClass = {
                'success': 'check-circle',
                'danger': 'exclamation-triangle',
                'warning': 'exclamation-triangle',
                'info': 'info-circle'
            }[alertClass] || 'info-circle';
            
            const notification = $(`
                <div id="${notificationId}" class="alert alert-${alertClass} alert-dismissible fade show position-fixed" 
                     style="top: 20px; right: 20px; z-index: 9999; min-width: 300px;" role="alert">
                    <i class="fas fa-${iconClass} me-2"></i>
                    ${message}
                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                </div>
            `);
            
            $('body').append(notification);
            
            // Auto-remove after duration
            if (duration > 0) {
                setTimeout(() => {
                    $(`#${notificationId}`).alert('close');
                }, duration);
            }
            
            return notificationId;
        },
        
        // Confirm dialog
        confirm: function(message, title = 'Confirm Action') {
            return new Promise((resolve) => {
                const confirmed = window.confirm(`${title}\n\n${message}`);
                resolve(confirmed);
            });
        }
    };

    // Component management
    AccuFin360.components = {
        
        // Initialize all DataTables
        initDataTables: function() {
            $('[data-table]').each(function() {
                const $table = $(this);
                const options = {
                    responsive: true,
                    pageLength: 25,
                    language: {
                        search: "Search:",
                        lengthMenu: "Show _MENU_ entries",
                        info: "Showing _START_ to _END_ of _TOTAL_ entries",
                        emptyTable: "No data available"
                    },
                    dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>rtip'
                };
                
                // Merge custom options
                const customOptions = $table.data('table-options');
                if (customOptions) {
                    $.extend(options, customOptions);
                }
                
                $table.DataTable(options);
            });
        },
        
        // Initialize form validation
        initFormValidation: function() {
            $('form[data-validate]').each(function() {
                const $form = $(this);
                
                $form.on('submit', function(e) {
                    let isValid = true;
                    
                    // Clear previous validation states
                    $form.find('.is-invalid').removeClass('is-invalid');
                    $form.find('.invalid-feedback').remove();
                    
                    // Validate required fields
                    $form.find('[required]').each(function() {
                        const $field = $(this);
                        const value = $field.val().trim();
                        
                        if (!value) {
                            $field.addClass('is-invalid');
                            $field.after('<div class="invalid-feedback">This field is required.</div>');
                            isValid = false;
                        }
                    });
                    
                    // Validate email fields
                    $form.find('input[type="email"]').each(function() {
                        const $field = $(this);
                        const value = $field.val().trim();
                        
                        if (value && !AccuFin360.utils.validateEmail(value)) {
                            $field.addClass('is-invalid');
                            $field.after('<div class="invalid-feedback">Please enter a valid email address.</div>');
                            isValid = false;
                        }
                    });
                    
                    // Validate password confirmation
                    const $password = $form.find('input[name="password"]');
                    const $confirmPassword = $form.find('input[name="confirm_password"]');
                    
                    if ($password.length && $confirmPassword.length) {
                        if ($password.val() !== $confirmPassword.val()) {
                            $confirmPassword.addClass('is-invalid');
                            $confirmPassword.after('<div class="invalid-feedback">Passwords do not match.</div>');
                            isValid = false;
                        }
                    }
                    
                    if (!isValid) {
                        e.preventDefault();
                        // Focus on first invalid field
                        $form.find('.is-invalid').first().focus();
                    }
                });
            });
        },
        
        // Initialize file upload components
        initFileUpload: function() {
            $('[data-file-upload]').each(function() {
                const $container = $(this);
                const $input = $container.find('input[type="file"]');
                const $dropZone = $container.find('[data-drop-zone]');
                
                // Drag and drop functionality
                if ($dropZone.length) {
                    $dropZone.on('dragover', function(e) {
                        e.preventDefault();
                        $(this).addClass('drag-over');
                    });
                    
                    $dropZone.on('dragleave', function(e) {
                        e.preventDefault();
                        $(this).removeClass('drag-over');
                    });
                    
                    $dropZone.on('drop', function(e) {
                        e.preventDefault();
                        $(this).removeClass('drag-over');
                        
                        const files = e.originalEvent.dataTransfer.files;
                        if (files.length > 0) {
                            $input[0].files = files;
                            $input.trigger('change');
                        }
                    });
                }
                
                // File input change handler
                $input.on('change', function() {
                    const files = this.files;
                    if (files.length > 0) {
                        const file = files[0];
                        $container.trigger('fileSelected', [file]);
                    }
                });
            });
        },
        
        // Initialize progress tracking
        initProgressTracking: function() {
            $('[data-progress]').each(function() {
                const $element = $(this);
                const targetValue = parseInt($element.data('progress'));
                const $progressBar = $element.find('.progress-bar');
                
                // Animate progress bar
                $progressBar.animate({
                    width: targetValue + '%'
                }, 1000);
            });
        }
    };

    // Setup CSRF protection
    AccuFin360.setupCSRF = function() {
        // Get CSRF token from meta tag
        const csrfToken = $('meta[name="csrf-token"]').attr('content');
        if (csrfToken) {
            this.config.csrfToken = csrfToken;
        }
    };

    // Initialize all components
    AccuFin360.initializeComponents = function() {
        this.components.initDataTables();
        this.components.initFormValidation();
        this.components.initFileUpload();
        this.components.initProgressTracking();
    };

    // Bind global event handlers
    AccuFin360.bindGlobalEvents = function() {
        
        // Handle AJAX form submissions
        $(document).on('submit', 'form[data-ajax]', function(e) {
            e.preventDefault();
            
            const $form = $(this);
            const url = $form.attr('action') || window.location.href;
            const method = $form.attr('method') || 'POST';
            const $submitBtn = $form.find('button[type="submit"]');
            
            // Show loading state
            const originalText = $submitBtn.html();
            $submitBtn.prop('disabled', true).html('<i class="fas fa-spinner fa-spin me-2"></i>Processing...');
            
            // Prepare form data
            const formData = new FormData(this);
            
            $.ajax({
                url: url,
                method: method,
                data: formData,
                processData: false,
                contentType: false,
                headers: {
                    'X-CSRF-Token': AccuFin360.config.csrfToken
                },
                success: function(response) {
                    if (response.success) {
                        AccuFin360.utils.showNotification(response.message || 'Operation completed successfully', 'success');
                        
                        // Handle redirect
                        if (response.redirect) {
                            setTimeout(() => {
                                window.location.href = response.redirect;
                            }, 1500);
                        }
                    } else {
                        AccuFin360.utils.showNotification(response.message || 'Operation failed', 'error');
                    }
                },
                error: function(xhr) {
                    let message = 'An error occurred';
                    if (xhr.responseJSON && xhr.responseJSON.message) {
                        message = xhr.responseJSON.message;
                    }
                    AccuFin360.utils.showNotification(message, 'error');
                },
                complete: function() {
                    // Restore button state
                    $submitBtn.prop('disabled', false).html(originalText);
                }
            });
        });
        
        // Handle delete confirmations
        $(document).on('click', '[data-confirm-delete]', function(e) {
            e.preventDefault();
            
            const $element = $(this);
            const message = $element.data('confirm-delete') || 'Are you sure you want to delete this item?';
            
            AccuFin360.utils.confirm(message, 'Confirm Delete').then((confirmed) => {
                if (confirmed) {
                    // If it's a link, follow it
                    if ($element.is('a')) {
                        window.location.href = $element.attr('href');
                    }
                    // If it's a form button, submit the form
                    else if ($element.closest('form').length) {
                        $element.closest('form').submit();
                    }
                }
            });
        });
        
        // Handle auto-refresh elements
        $(document).on('click', '[data-auto-refresh]', function() {
            const $element = $(this);
            const interval = parseInt($element.data('auto-refresh')) || 30000;
            
            setInterval(() => {
                location.reload();
            }, interval);
            
            AccuFin360.utils.showNotification(`Auto-refresh enabled (${interval/1000}s)`, 'info');
        });
        
        // Handle print functionality
        $(document).on('click', '[data-print]', function(e) {
            e.preventDefault();
            
            const target = $(this).data('print');
            if (target) {
                const content = $(target).html();
                const printWindow = window.open('', '_blank');
                printWindow.document.write(`
                    <html>
                        <head>
                            <title>Print</title>
                            <link href="https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css" rel="stylesheet">
                            <style>
                                @media print {
                                    .no-print { display: none !important; }
                                }
                            </style>
                        </head>
                        <body>
                            ${content}
                        </body>
                    </html>
                `);
                printWindow.document.close();
                printWindow.print();
            } else {
                window.print();
            }
        });
        
        // Handle copy to clipboard
        $(document).on('click', '[data-copy]', function(e) {
            e.preventDefault();
            
            const text = $(this).data('copy');
            navigator.clipboard.writeText(text).then(() => {
                AccuFin360.utils.showNotification('Copied to clipboard!', 'success', 2000);
            }).catch(() => {
                AccuFin360.utils.showNotification('Failed to copy to clipboard', 'error');
            });
        });
        
        // Handle external links
        $(document).on('click', 'a[href^="http"]', function() {
            $(this).attr('target', '_blank').attr('rel', 'noopener noreferrer');
        });
        
        // Handle back button
        $(document).on('click', '[data-back]', function(e) {
            e.preventDefault();
            window.history.back();
        });
    };

    // Setup AJAX defaults
    AccuFin360.setupAjaxDefaults = function() {
        $.ajaxSetup({
            beforeSend: function(xhr, settings) {
                // Add CSRF token to all AJAX requests
                if (AccuFin360.config.csrfToken && settings.type !== 'GET') {
                    xhr.setRequestHeader('X-CSRFToken', AccuFin360.config.csrfToken);
                }
            },
            error: function(xhr, status, error) {
                // Global error handler
                if (xhr.status === 401) {
                    AccuFin360.utils.showNotification('Session expired. Please log in again.', 'warning');
                    setTimeout(() => {
                        window.location.href = '/auth/login';
                    }, 2000);
                } else if (xhr.status === 403) {
                    AccuFin360.utils.showNotification('Access denied.', 'error');
                } else if (xhr.status >= 500) {
                    AccuFin360.utils.showNotification('Server error. Please try again later.', 'error');
                }
            }
        });
    };

    // Initialize tooltips and popovers
    AccuFin360.initializeTooltips = function() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Initialize Bootstrap popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    };

    // Progressive enhancement
    AccuFin360.setupProgressiveEnhancement = function() {
        // Add 'js-enabled' class to body
        $('body').addClass('js-enabled');
        
        // Hide elements that require JavaScript
        $('.js-only').show();
        $('.no-js-only').hide();
        
        // Enable interactive elements
        $('[data-interactive]').removeClass('disabled');
    };

    // API helper methods
    AccuFin360.api = {
        
        // Generic GET request
        get: function(endpoint, params = {}) {
            return $.get(AccuFin360.config.apiBaseUrl + endpoint, params);
        },
        
        // Generic POST request
        post: function(endpoint, data = {}) {
            return $.post({
                url: AccuFin360.config.apiBaseUrl + endpoint,
                data: JSON.stringify(data),
                contentType: 'application/json',
                headers: {
                    'X-CSRFToken': AccuFin360.config.csrfToken
                }
            });
        },
        
        // Upload file
        uploadFile: function(endpoint, file, onProgress = null) {
            const formData = new FormData();
            formData.append('file', file);
            
            return $.ajax({
                url: AccuFin360.config.apiBaseUrl + endpoint,
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                headers: {
                    'X-CSRFToken': AccuFin360.config.csrfToken
                },
                xhr: function() {
                    const xhr = new window.XMLHttpRequest();
                    if (onProgress) {
                        xhr.upload.addEventListener('progress', function(evt) {
                            if (evt.lengthComputable) {
                                const percentComplete = evt.loaded / evt.total * 100;
                                onProgress(percentComplete);
                            }
                        }, false);
                    }
                    return xhr;
                }
            });
        }
    };

    // Initialize when document is ready
    $(document).ready(function() {
        AccuFin360.init();
    });

    // Handle page visibility change
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            // Page became visible - refresh dynamic content if needed
            $('[data-auto-refresh-on-focus]').each(function() {
                $(this).trigger('refresh');
            });
        }
    });

    // Handle online/offline status
    window.addEventListener('online', function() {
        AccuFin360.utils.showNotification('Connection restored', 'success', 3000);
    });

    window.addEventListener('offline', function() {
        AccuFin360.utils.showNotification('Connection lost - working offline', 'warning', 0);
    });

})(jQuery);
