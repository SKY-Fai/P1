/**
 * AccuFin360 - Data Validation JavaScript
 * Handles client-side validation for forms and data uploads
 */

(function($) {
    'use strict';

    // Validation namespace
    window.AccuFin360 = window.AccuFin360 || {};
    
    AccuFin360.Validation = {
        rules: {},
        messages: {},
        
        // Initialize validation
        init: function() {
            this.setupValidationRules();
            this.bindValidationEvents();
            this.initializeFormValidation();
            console.log('Validation system initialized');
        },
        
        // Setup validation rules
        setupValidationRules: function() {
            this.rules = {
                required: function(value) {
                    return value !== null && value !== undefined && value.toString().trim() !== '';
                },
                
                email: function(value) {
                    if (!value) return true; // Optional field
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    return emailRegex.test(value);
                },
                
                numeric: function(value) {
                    if (!value) return true; // Optional field
                    return !isNaN(parseFloat(value)) && isFinite(value);
                },
                
                currency: function(value) {
                    if (!value) return true; // Optional field
                    const currencyRegex = /^\$?[0-9,]+(\.[0-9]{2})?$/;
                    return currencyRegex.test(value.toString().replace(/\s/g, ''));
                },
                
                date: function(value) {
                    if (!value) return true; // Optional field
                    const date = new Date(value);
                    return date instanceof Date && !isNaN(date);
                },
                
                minLength: function(value, min) {
                    if (!value) return true; // Optional field
                    return value.toString().length >= min;
                },
                
                maxLength: function(value, max) {
                    if (!value) return true; // Optional field
                    return value.toString().length <= max;
                },
                
                pattern: function(value, pattern) {
                    if (!value) return true; // Optional field
                    const regex = new RegExp(pattern);
                    return regex.test(value);
                },
                
                phone: function(value) {
                    if (!value) return true; // Optional field
                    const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
                    const cleaned = value.toString().replace(/[^\d\+]/g, '');
                    return phoneRegex.test(cleaned);
                },
                
                accountCode: function(value) {
                    if (!value) return true; // Optional field
                    const accountRegex = /^[A-Z0-9]{3,10}$/i;
                    return accountRegex.test(value);
                },
                
                gstin: function(value) {
                    if (!value) return true; // Optional field
                    const gstinRegex = /^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$/;
                    return gstinRegex.test(value);
                },
                
                percentage: function(value) {
                    if (!value) return true; // Optional field
                    const num = parseFloat(value);
                    return !isNaN(num) && num >= 0 && num <= 100;
                },
                
                positiveNumber: function(value) {
                    if (!value) return true; // Optional field
                    const num = parseFloat(value);
                    return !isNaN(num) && num > 0;
                },
                
                equalTo: function(value, targetSelector) {
                    const targetValue = $(targetSelector).val();
                    return value === targetValue;
                }
            };
            
            this.messages = {
                required: 'This field is required.',
                email: 'Please enter a valid email address.',
                numeric: 'Please enter a valid number.',
                currency: 'Please enter a valid currency amount.',
                date: 'Please enter a valid date.',
                minLength: 'Please enter at least {0} characters.',
                maxLength: 'Please enter no more than {0} characters.',
                pattern: 'Please enter a value in the correct format.',
                phone: 'Please enter a valid phone number.',
                accountCode: 'Please enter a valid account code (3-10 alphanumeric characters).',
                gstin: 'Please enter a valid GSTIN (15 characters).',
                percentage: 'Please enter a percentage between 0 and 100.',
                positiveNumber: 'Please enter a positive number.',
                equalTo: 'Please enter the same value again.'
            };
        },
        
        // Bind validation events
        bindValidationEvents: function() {
            const self = this;
            
            // Real-time validation on input
            $(document).on('input blur', '[data-validate]', function() {
                self.validateField($(this));
            });
            
            // Form submission validation
            $(document).on('submit', 'form[data-validate-form]', function(e) {
                if (!self.validateForm($(this))) {
                    e.preventDefault();
                    return false;
                }
            });
            
            // File validation
            $(document).on('change', 'input[type="file"][data-validate-file]', function() {
                self.validateFile($(this));
            });
            
            // Custom validation triggers
            $(document).on('validate', '[data-validate]', function() {
                self.validateField($(this));
            });
        },
        
        // Initialize form validation
        initializeFormValidation: function() {
            // Add validation attributes based on input types
            $('input[type="email"]').attr('data-validate', 'email');
            $('input[type="tel"]').attr('data-validate', 'phone');
            $('input[type="date"]').attr('data-validate', 'date');
            $('input[type="number"]').attr('data-validate', 'numeric');
            
            // Add required validation
            $('input[required], select[required], textarea[required]').each(function() {
                const existing = $(this).attr('data-validate') || '';
                const rules = existing ? existing + '|required' : 'required';
                $(this).attr('data-validate', rules);
            });
        },
        
        // Validate a single field
        validateField: function($field) {
            const rules = $field.attr('data-validate');
            if (!rules) return true;
            
            const value = $field.val();
            const ruleArray = rules.split('|');
            let isValid = true;
            let errorMessage = '';
            
            // Clear previous validation state
            $field.removeClass('is-valid is-invalid');
            $field.siblings('.invalid-feedback, .valid-feedback').remove();
            
            // Apply each rule
            for (let rule of ruleArray) {
                const [ruleName, ruleParam] = rule.split(':');
                
                if (this.rules[ruleName]) {
                    const result = this.rules[ruleName](value, ruleParam);
                    if (!result) {
                        isValid = false;
                        errorMessage = this.getErrorMessage(ruleName, ruleParam);
                        break;
                    }
                }
            }
            
            // Apply validation state
            if (isValid && value) {
                $field.addClass('is-valid');
                $field.after('<div class="valid-feedback">Looks good!</div>');
            } else if (!isValid) {
                $field.addClass('is-invalid');
                $field.after(`<div class="invalid-feedback">${errorMessage}</div>`);
            }
            
            return isValid;
        },
        
        // Validate entire form
        validateForm: function($form) {
            let isValid = true;
            
            // Validate all fields with validation rules
            $form.find('[data-validate]').each((index, element) => {
                if (!this.validateField($(element))) {
                    isValid = false;
                }
            });
            
            // Custom form validation
            const customValidator = $form.attr('data-custom-validator');
            if (customValidator && window[customValidator]) {
                isValid = window[customValidator]($form) && isValid;
            }
            
            // Focus on first invalid field
            if (!isValid) {
                $form.find('.is-invalid').first().focus();
            }
            
            return isValid;
        },
        
        // Validate file upload
        validateFile: function($input) {
            const file = $input[0].files[0];
            if (!file) return true;
            
            const validationRules = $input.attr('data-validate-file');
            if (!validationRules) return true;
            
            const rules = validationRules.split('|');
            let isValid = true;
            let errorMessage = '';
            
            // Clear previous validation
            $input.removeClass('is-valid is-invalid');
            $input.siblings('.invalid-feedback, .valid-feedback').remove();
            
            for (let rule of rules) {
                const [ruleName, ruleParam] = rule.split(':');
                
                switch (ruleName) {
                    case 'maxSize':
                        const maxSizeBytes = this.parseFileSize(ruleParam);
                        if (file.size > maxSizeBytes) {
                            isValid = false;
                            errorMessage = `File size must be less than ${ruleParam}`;
                        }
                        break;
                        
                    case 'extensions':
                        const allowedExtensions = ruleParam.split(',');
                        const fileExtension = file.name.split('.').pop().toLowerCase();
                        if (!allowedExtensions.includes(fileExtension)) {
                            isValid = false;
                            errorMessage = `File must be one of: ${allowedExtensions.join(', ')}`;
                        }
                        break;
                        
                    case 'mimeTypes':
                        const allowedMimeTypes = ruleParam.split(',');
                        if (!allowedMimeTypes.includes(file.type)) {
                            isValid = false;
                            errorMessage = `Invalid file type: ${file.type}`;
                        }
                        break;
                }
                
                if (!isValid) break;
            }
            
            // Apply validation state
            if (isValid) {
                $input.addClass('is-valid');
                $input.after('<div class="valid-feedback">File is valid!</div>');
            } else {
                $input.addClass('is-invalid');
                $input.after(`<div class="invalid-feedback">${errorMessage}</div>`);
            }
            
            return isValid;
        },
        
        // Get error message for rule
        getErrorMessage: function(ruleName, ruleParam) {
            let message = this.messages[ruleName] || 'Invalid value';
            
            // Replace placeholders
            if (ruleParam) {
                message = message.replace('{0}', ruleParam);
            }
            
            return message;
        },
        
        // Parse file size string to bytes
        parseFileSize: function(sizeString) {
            const units = {
                'B': 1,
                'KB': 1024,
                'MB': 1024 * 1024,
                'GB': 1024 * 1024 * 1024
            };
            
            const match = sizeString.match(/^(\d+(?:\.\d+)?)\s*([A-Z]{1,2})$/i);
            if (!match) return 0;
            
            const size = parseFloat(match[1]);
            const unit = match[2].toUpperCase();
            
            return size * (units[unit] || 1);
        },
        
        // Add custom validation rule
        addRule: function(name, validator, message) {
            this.rules[name] = validator;
            this.messages[name] = message;
        },
        
        // Remove validation from field
        clearValidation: function($field) {
            $field.removeClass('is-valid is-invalid');
            $field.siblings('.invalid-feedback, .valid-feedback').remove();
        },
        
        // Show validation summary
        showValidationSummary: function($form, errors) {
            const existingSummary = $form.find('.validation-summary');
            existingSummary.remove();
            
            if (errors.length === 0) return;
            
            const summaryHtml = `
                <div class="validation-summary alert alert-danger">
                    <h6><i class="fas fa-exclamation-triangle me-2"></i>Please correct the following errors:</h6>
                    <ul class="mb-0">
                        ${errors.map(error => `<li>${error}</li>`).join('')}
                    </ul>
                </div>
            `;
            
            $form.prepend(summaryHtml);
        }
    };
    
    // File upload validation helpers
    AccuFin360.FileValidation = {
        
        // Validate Excel/CSV structure
        validateSpreadsheetStructure: function(file, requiredColumns = []) {
            return new Promise((resolve) => {
                const reader = new FileReader();
                
                reader.onload = function(e) {
                    try {
                        let data;
                        
                        if (file.name.endsWith('.csv')) {
                            // Parse CSV
                            const csvText = e.target.result;
                            const lines = csvText.split('\n');
                            const headers = lines[0].split(',').map(h => h.trim().replace(/"/g, ''));
                            data = { headers };
                        } else if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
                            // For Excel files, we'd need a library like SheetJS
                            // For now, just return success
                            resolve({ isValid: true, message: 'Excel file detected' });
                            return;
                        }
                        
                        // Check required columns
                        const missingColumns = requiredColumns.filter(col => 
                            !data.headers.some(header => 
                                header.toLowerCase().includes(col.toLowerCase())
                            )
                        );
                        
                        if (missingColumns.length > 0) {
                            resolve({
                                isValid: false,
                                message: `Missing required columns: ${missingColumns.join(', ')}`
                            });
                        } else {
                            resolve({
                                isValid: true,
                                message: 'File structure is valid',
                                headers: data.headers
                            });
                        }
                        
                    } catch (error) {
                        resolve({
                            isValid: false,
                            message: 'Unable to parse file structure'
                        });
                    }
                };
                
                reader.onerror = function() {
                    resolve({
                        isValid: false,
                        message: 'Error reading file'
                    });
                };
                
                reader.readAsText(file);
            });
        },
        
        // Validate accounting data format
        validateAccountingFormat: function(data) {
            const errors = [];
            
            // Check for required financial columns
            const requiredColumns = ['date', 'description', 'amount'];
            const missingColumns = requiredColumns.filter(col => 
                !data.headers.some(header => 
                    header.toLowerCase().includes(col.toLowerCase())
                )
            );
            
            if (missingColumns.length > 0) {
                errors.push(`Missing required columns: ${missingColumns.join(', ')}`);
            }
            
            // Additional format checks would go here
            // For example, checking date formats, numeric formats, etc.
            
            return {
                isValid: errors.length === 0,
                errors: errors
            };
        }
    };
    
    // Custom validators for specific forms
    window.validateInvoiceForm = function($form) {
        let isValid = true;
        const errors = [];
        
        // Check that subtotal + tax = total
        const subtotal = parseFloat($form.find('[name="subtotal"]').val()) || 0;
        const tax = parseFloat($form.find('[name="tax_amount"]').val()) || 0;
        const total = parseFloat($form.find('[name="total_amount"]').val()) || 0;
        
        if (Math.abs((subtotal + tax) - total) > 0.01) {
            errors.push('Total amount must equal subtotal plus tax amount');
            isValid = false;
        }
        
        // Check that at least one item is added
        const itemCount = $form.find('[name="item_name[]"]').length;
        if (itemCount === 0) {
            errors.push('At least one invoice item is required');
            isValid = false;
        }
        
        if (errors.length > 0) {
            AccuFin360.Validation.showValidationSummary($form, errors);
        }
        
        return isValid;
    };
    
    window.validateGSTForm = function($form) {
        let isValid = true;
        const errors = [];
        
        // Validate GST calculations
        const taxableAmount = parseFloat($form.find('[name="taxable_amount"]').val()) || 0;
        const taxType = $form.find('[name="tax_type"]:checked').val();
        
        if (taxType === 'intrastate') {
            const cgstRate = parseFloat($form.find('[name="cgst_rate"]').val()) || 0;
            const sgstRate = parseFloat($form.find('[name="sgst_rate"]').val()) || 0;
            
            if (cgstRate !== sgstRate) {
                errors.push('CGST and SGST rates must be equal for intrastate transactions');
                isValid = false;
            }
        }
        
        if (errors.length > 0) {
            AccuFin360.Validation.showValidationSummary($form, errors);
        }
        
        return isValid;
    };
    
    // Initialize validation when document is ready
    $(document).ready(function() {
        AccuFin360.Validation.init();
    });

})(jQuery);
