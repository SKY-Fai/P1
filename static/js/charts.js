/**
 * AccuFin360 - Charts and Data Visualization
 * Handles all chart initialization and management using Chart.js
 */

(function($) {
    'use strict';

    // Chart management namespace
    window.AccuFin360 = window.AccuFin360 || {};
    
    AccuFin360.Charts = {
        instances: {},
        defaultColors: {
            primary: '#007bff',
            success: '#28a745',
            warning: '#ffc107',
            danger: '#dc3545',
            info: '#17a2b8',
            secondary: '#6c757d',
            light: '#f8f9fa',
            dark: '#343a40'
        },
        
        gradients: {},
        
        // Initialize all charts on the page
        init: function() {
            this.setupChartDefaults();
            this.initializeCharts();
            console.log('Charts initialized');
        },
        
        // Setup Chart.js global defaults
        setupChartDefaults: function() {
            Chart.defaults.font.family = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif";
            Chart.defaults.font.size = 12;
            Chart.defaults.color = '#495057';
            Chart.defaults.scale.grid.color = 'rgba(0, 0, 0, 0.1)';
            Chart.defaults.plugins.legend.position = 'bottom';
            Chart.defaults.plugins.legend.labels.usePointStyle = true;
            Chart.defaults.plugins.legend.labels.padding = 20;
            Chart.defaults.elements.point.radius = 4;
            Chart.defaults.elements.point.hoverRadius = 6;
            Chart.defaults.elements.line.tension = 0.4;
            Chart.defaults.animation.duration = 1000;
            Chart.defaults.responsive = true;
            Chart.defaults.maintainAspectRatio = false;
        },
        
        // Initialize all charts found on the page
        initializeCharts: function() {
            const self = this;
            
            // Find all canvas elements with chart data
            $('canvas[data-chart]').each(function() {
                const $canvas = $(this);
                const chartType = $canvas.data('chart');
                const chartData = $canvas.data('chart-data');
                const chartOptions = $canvas.data('chart-options') || {};
                
                if (chartType && chartData) {
                    self.createChart($canvas[0], chartType, chartData, chartOptions);
                }
            });
            
            // Initialize specific chart types
            this.initDashboardCharts();
            this.initRevenueCharts();
            this.initCashFlowCharts();
            this.initActivityCharts();
            this.initPerformanceCharts();
        },
        
        // Create a chart instance
        createChart: function(canvas, type, data, options = {}) {
            const ctx = canvas.getContext('2d');
            const chartId = canvas.id || 'chart_' + Math.random().toString(36).substr(2, 9);
            
            // Create gradients if needed
            this.createGradients(ctx);
            
            // Merge with default options
            const defaultOptions = this.getDefaultOptions(type);
            const mergedOptions = $.extend(true, {}, defaultOptions, options);
            
            // Create chart
            const chart = new Chart(ctx, {
                type: type,
                data: this.processChartData(data, type),
                options: mergedOptions
            });
            
            // Store chart instance
            this.instances[chartId] = chart;
            
            return chart;
        },
        
        // Create gradient backgrounds
        createGradients: function(ctx) {
            // Primary gradient
            this.gradients.primary = ctx.createLinearGradient(0, 0, 0, 400);
            this.gradients.primary.addColorStop(0, 'rgba(0, 123, 255, 0.8)');
            this.gradients.primary.addColorStop(1, 'rgba(0, 123, 255, 0.1)');
            
            // Success gradient
            this.gradients.success = ctx.createLinearGradient(0, 0, 0, 400);
            this.gradients.success.addColorStop(0, 'rgba(40, 167, 69, 0.8)');
            this.gradients.success.addColorStop(1, 'rgba(40, 167, 69, 0.1)');
            
            // Warning gradient
            this.gradients.warning = ctx.createLinearGradient(0, 0, 0, 400);
            this.gradients.warning.addColorStop(0, 'rgba(255, 193, 7, 0.8)');
            this.gradients.warning.addColorStop(1, 'rgba(255, 193, 7, 0.1)');
            
            // Info gradient
            this.gradients.info = ctx.createLinearGradient(0, 0, 0, 400);
            this.gradients.info.addColorStop(0, 'rgba(23, 162, 184, 0.8)');
            this.gradients.info.addColorStop(1, 'rgba(23, 162, 184, 0.1)');
        },
        
        // Get default options for chart type
        getDefaultOptions: function(type) {
            const commonOptions = {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'bottom'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#fff',
                        bodyColor: '#fff',
                        borderColor: '#007bff',
                        borderWidth: 1,
                        cornerRadius: 6,
                        displayColors: true
                    }
                }
            };
            
            const typeSpecificOptions = {
                line: {
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        }
                    },
                    elements: {
                        point: {
                            radius: 4,
                            hoverRadius: 6
                        }
                    }
                },
                
                bar: {
                    scales: {
                        x: {
                            grid: {
                                display: false
                            }
                        },
                        y: {
                            beginAtZero: true,
                            grid: {
                                color: 'rgba(0, 0, 0, 0.1)'
                            }
                        }
                    }
                },
                
                doughnut: {
                    cutout: '60%',
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                },
                
                pie: {
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            };
            
            return $.extend(true, {}, commonOptions, typeSpecificOptions[type] || {});
        },
        
        // Process chart data based on type
        processChartData: function(data, type) {
            // Add gradients and colors if not specified
            if (data.datasets) {
                data.datasets.forEach((dataset, index) => {
                    if (!dataset.backgroundColor) {
                        if (type === 'line') {
                            dataset.backgroundColor = this.gradients.primary;
                            dataset.borderColor = this.defaultColors.primary;
                        } else if (type === 'doughnut' || type === 'pie') {
                            dataset.backgroundColor = this.getColorPalette(data.labels.length);
                        } else {
                            dataset.backgroundColor = this.getColorPalette(1)[0];
                        }
                    }
                    
                    if (!dataset.borderColor && type !== 'doughnut' && type !== 'pie') {
                        dataset.borderColor = this.defaultColors.primary;
                    }
                    
                    if (type === 'line' && dataset.fill === undefined) {
                        dataset.fill = true;
                    }
                });
            }
            
            return data;
        },
        
        // Get color palette
        getColorPalette: function(count) {
            const colors = [
                this.defaultColors.primary,
                this.defaultColors.success,
                this.defaultColors.warning,
                this.defaultColors.danger,
                this.defaultColors.info,
                this.defaultColors.secondary,
                '#e83e8c', // Pink
                '#fd7e14', // Orange
                '#20c997', // Teal
                '#6f42c1'  // Purple
            ];
            
            const palette = [];
            for (let i = 0; i < count; i++) {
                palette.push(colors[i % colors.length]);
            }
            
            return palette;
        },
        
        // Initialize dashboard-specific charts
        initDashboardCharts: function() {
            // Revenue trend chart
            const revenueCanvas = document.getElementById('revenueTrendChart');
            if (revenueCanvas) {
                this.createRevenueChart(revenueCanvas);
            }
            
            // Expense breakdown chart
            const expenseCanvas = document.getElementById('expenseBreakdownChart');
            if (expenseCanvas) {
                this.createExpenseChart(expenseCanvas);
            }
        },
        
        // Initialize revenue charts
        initRevenueCharts: function() {
            const revenueCanvas = document.getElementById('revenueChart');
            if (revenueCanvas) {
                const data = {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                    datasets: [{
                        label: 'Revenue',
                        data: [12000, 19000, 15000, 25000, 22000, 30000],
                        borderColor: this.defaultColors.success,
                        backgroundColor: this.gradients.success,
                        tension: 0.4
                    }]
                };
                
                const options = {
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return 'Revenue: $' + context.parsed.y.toLocaleString();
                                }
                            }
                        }
                    }
                };
                
                this.createChart(revenueCanvas, 'line', data, options);
            }
        },
        
        // Initialize cash flow charts
        initCashFlowCharts: function() {
            const cashFlowCanvas = document.getElementById('cashFlowPredictionChart');
            if (cashFlowCanvas) {
                const data = {
                    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'],
                    datasets: [{
                        label: 'Actual Cash Flow',
                        data: [15000, 22000, 18000, 28000, 25000, 32000, null, null, null],
                        borderColor: this.defaultColors.primary,
                        backgroundColor: this.gradients.primary,
                        tension: 0.4
                    }, {
                        label: 'Predicted Cash Flow',
                        data: [null, null, null, null, null, 32000, 35000, 38000, 42000],
                        borderColor: this.defaultColors.success,
                        backgroundColor: 'transparent',
                        borderDash: [5, 5],
                        tension: 0.4
                    }]
                };
                
                const options = {
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                callback: function(value) {
                                    return '$' + value.toLocaleString();
                                }
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': $' + context.parsed.y.toLocaleString();
                                }
                            }
                        }
                    }
                };
                
                this.createChart(cashFlowCanvas, 'line', data, options);
            }
        },
        
        // Initialize activity charts
        initActivityCharts: function() {
            const activityCanvas = document.getElementById('activityChart');
            if (activityCanvas) {
                const data = {
                    labels: ['Create', 'Update', 'Delete', 'Login', 'Export'],
                    datasets: [{
                        data: [45, 30, 5, 15, 5],
                        backgroundColor: [
                            this.defaultColors.success,
                            this.defaultColors.warning,
                            this.defaultColors.danger,
                            this.defaultColors.info,
                            this.defaultColors.secondary
                        ]
                    }]
                };
                
                this.createChart(activityCanvas, 'doughnut', data);
            }
        },
        
        // Initialize performance charts
        initPerformanceCharts: function() {
            const performanceCanvas = document.getElementById('performanceChart');
            if (performanceCanvas) {
                const data = {
                    labels: ['Processing Speed', 'Accuracy Rate', 'User Engagement', 'System Performance', 'Data Quality'],
                    datasets: [{
                        label: 'Current Month',
                        data: [85, 96, 78, 92, 88],
                        backgroundColor: this.defaultColors.primary
                    }, {
                        label: 'Previous Month',
                        data: [78, 94, 75, 89, 85],
                        backgroundColor: this.defaultColors.secondary
                    }]
                };
                
                const options = {
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': ' + context.parsed.y + '%';
                                }
                            }
                        }
                    }
                };
                
                this.createChart(performanceCanvas, 'bar', data, options);
            }
        },
        
        // Create revenue trend chart
        createRevenueChart: function(canvas) {
            const data = {
                labels: ['Q1', 'Q2', 'Q3', 'Q4'],
                datasets: [{
                    label: 'Revenue',
                    data: [150000, 180000, 220000, 280000],
                    borderColor: this.defaultColors.success,
                    backgroundColor: this.gradients.success,
                    tension: 0.4
                }, {
                    label: 'Profit',
                    data: [45000, 60000, 75000, 95000],
                    borderColor: this.defaultColors.primary,
                    backgroundColor: this.gradients.primary,
                    tension: 0.4
                }]
            };
            
            const options = {
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '$' + (value / 1000) + 'K';
                            }
                        }
                    }
                }
            };
            
            this.createChart(canvas, 'line', data, options);
        },
        
        // Create expense breakdown chart
        createExpenseChart: function(canvas) {
            const data = {
                labels: ['Salaries', 'Rent', 'Utilities', 'Marketing', 'Software', 'Other'],
                datasets: [{
                    data: [45, 20, 10, 15, 5, 5],
                    backgroundColor: this.getColorPalette(6)
                }]
            };
            
            const options = {
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.parsed + '%';
                            }
                        }
                    }
                }
            };
            
            this.createChart(canvas, 'doughnut', data, options);
        },
        
        // Update chart data
        updateChart: function(chartId, newData) {
            const chart = this.instances[chartId];
            if (chart) {
                chart.data = this.processChartData(newData, chart.config.type);
                chart.update();
            }
        },
        
        // Destroy chart
        destroyChart: function(chartId) {
            const chart = this.instances[chartId];
            if (chart) {
                chart.destroy();
                delete this.instances[chartId];
            }
        },
        
        // Resize all charts
        resizeCharts: function() {
            Object.values(this.instances).forEach(chart => {
                chart.resize();
            });
        },
        
        // Export chart as image
        exportChart: function(chartId, filename = 'chart.png') {
            const chart = this.instances[chartId];
            if (chart) {
                const url = chart.toBase64Image();
                const link = document.createElement('a');
                link.download = filename;
                link.href = url;
                link.click();
            }
        }
    };
    
    // Initialize charts when document is ready
    $(document).ready(function() {
        AccuFin360.Charts.init();
    });
    
    // Handle window resize
    $(window).on('resize', FaiCore.utils.debounce(() => {
        AccuFin360.Charts.resizeCharts();
    }, 250));
    
    // Handle chart export buttons
    $(document).on('click', '[data-export-chart]', function() {
        const chartId = $(this).data('export-chart');
        const filename = $(this).data('filename') || 'chart.png';
        AccuFin360.Charts.exportChart(chartId, filename);
    });

})(jQuery);
