// 03_Demo_Interface/business_metrics.js - Business Metrics Visualization
// Adaptive Mind Framework - Session 9
// Real-time business impact visualization and metrics dashboard

/**
 * Business Metrics Visualization Engine
 * Integrates with ROI calculator and demo backend for real-time business impact display
 */
class BusinessMetricsEngine {
    constructor(backendUrl = 'http://localhost:8000', containerId = 'business-metrics-container') {
        this.backendUrl = backendUrl;
        this.containerId = containerId;
        this.updateInterval = 5000; // 5 seconds
        this.metricsHistory = [];
        this.chartInstances = {};
        this.realTimeEnabled = false;

        // Business impact categories
        this.impactCategories = {
            'revenue_protection': {
                name: 'Revenue Protection',
                icon: '💰',
                format: 'currency',
                target: 2400000,
                current: 0
            },
            'cost_savings': {
                name: 'Cost Savings',
                icon: '💵',
                format: 'currency',
                target: 485000,
                current: 0
            },
            'productivity_gains': {
                name: 'Productivity Gains',
                icon: '⚡',
                format: 'percentage',
                target: 35,
                current: 0
            },
            'reliability_improvement': {
                name: 'Reliability Score',
                icon: '🛡️',
                format: 'percentage',
                target: 99,
                current: 75
            },
            'customer_satisfaction': {
                name: 'Customer Satisfaction',
                icon: '😊',
                format: 'percentage',
                target: 95,
                current: 77
            },
            'time_to_market': {
                name: 'Time to Market',
                icon: '🚀',
                format: 'percentage_reduction',
                target: 50,
                current: 0
            }
        };

        // KPI thresholds
        this.kpiThresholds = {
            'excellent': 90,
            'good': 75,
            'fair': 60,
            'poor': 0
        };

        this.initialize();
    }

    /**
     * Initialize the business metrics engine
     */
    async initialize() {
        console.log('🚀 Initializing Business Metrics Engine...');

        try {
            // Create the metrics dashboard UI
            this.createMetricsDashboard();

            // Load historical data
            await this.loadHistoricalMetrics();

            // Start real-time updates if enabled
            this.startRealTimeUpdates();

            // Setup event listeners
            this.setupEventListeners();

            console.log('✅ Business Metrics Engine initialized successfully');

        } catch (error) {
            console.error('❌ Failed to initialize Business Metrics Engine:', error);
            this.showError('Failed to initialize metrics dashboard');
        }
    }

    /**
     * Create the metrics dashboard UI
     */
    createMetricsDashboard() {
        const container = document.getElementById(this.containerId);
        if (!container) {
            console.error(`❌ Container element '${this.containerId}' not found`);
            return;
        }

        const dashboardHTML = `
            <div class="business-metrics-dashboard">
                <div class="dashboard-header">
                    <h2>📊 Business Impact Metrics</h2>
                    <div class="dashboard-controls">
                        <button id="toggle-realtime" class="btn btn-primary">
                            <span id="realtime-status">▶️ Start Real-Time</span>
                        </button>
                        <button id="refresh-metrics" class="btn btn-secondary">🔄 Refresh</button>
                        <button id="export-metrics" class="btn btn-outline">📥 Export</button>
                    </div>
                </div>

                <div class="metrics-overview">
                    <div class="metrics-grid" id="metrics-grid">
                        ${this.createMetricCards()}
                    </div>
                </div>

                <div class="charts-section">
                    <div class="chart-container">
                        <h3>📈 Business Impact Trends</h3>
                        <canvas id="business-impact-chart" width="400" height="200"></canvas>
                    </div>

                    <div class="chart-container">
                        <h3>💹 ROI Performance</h3>
                        <canvas id="roi-performance-chart" width="400" height="200"></canvas>
                    </div>
                </div>

                <div class="detailed-metrics">
                    <div class="metric-details-tabs">
                        <button class="tab-button active" data-tab="financial">💰 Financial</button>
                        <button class="tab-button" data-tab="operational">⚙️ Operational</button>
                        <button class="tab-button" data-tab="strategic">🎯 Strategic</button>
                        <button class="tab-button" data-tab="competitive">🏆 Competitive</button>
                    </div>

                    <div class="tab-content" id="tab-content">
                        ${this.createDetailedTabs()}
                    </div>
                </div>

                <div class="alerts-section" id="alerts-section">
                    <h3>🚨 Key Insights & Alerts</h3>
                    <div class="alerts-container" id="alerts-container">
                        <!-- Dynamic alerts will be inserted here -->
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = dashboardHTML;

        // Initialize charts after DOM is ready
        setTimeout(() => {
            this.initializeCharts();
        }, 100);
    }

    /**
     * Create metric cards HTML
     */
    createMetricCards() {
        return Object.keys(this.impactCategories).map(key => {
            const category = this.impactCategories[key];
            return `
                <div class="metric-card" data-metric="${key}">
                    <div class="metric-header">
                        <span class="metric-icon">${category.icon}</span>
                        <span class="metric-name">${category.name}</span>
                    </div>
                    <div class="metric-value">
                        <span class="current-value" id="${key}-current">--</span>
                        <span class="target-indicator">/ ${this.formatValue(category.target, category.format)}</span>
                    </div>
                    <div class="metric-progress">
                        <div class="progress-bar">
                            <div class="progress-fill" id="${key}-progress" style="width: 0%"></div>
                        </div>
                        <span class="progress-percentage" id="${key}-percentage">0%</span>
                    </div>
                    <div class="metric-trend" id="${key}-trend">
                        <span class="trend-indicator">📊</span>
                        <span class="trend-text">Baseline</span>
                    </div>
                </div>
            `;
        }).join('');
    }

    /**
     * Create detailed tabs content
     */
    createDetailedTabs() {
        return `
            <div class="tab-panel active" id="financial-tab">
                <div class="financial-metrics">
                    <div class="metric-row">
                        <label>Annual Cost Savings:</label>
                        <span id="annual-savings">$0</span>
                    </div>
                    <div class="metric-row">
                        <label>ROI Percentage:</label>
                        <span id="roi-percentage">0%</span>
                    </div>
                    <div class="metric-row">
                        <label>Payback Period:</label>
                        <span id="payback-period">-- months</span>
                    </div>
                    <div class="metric-row">
                        <label>5-Year NPV:</label>
                        <span id="npv-5-year">$0</span>
                    </div>
                    <div class="metric-row">
                        <label>Revenue Protected:</label>
                        <span id="revenue-protected">$0</span>
                    </div>
                </div>
            </div>

            <div class="tab-panel" id="operational-tab">
                <div class="operational-metrics">
                    <div class="metric-row">
                        <label>System Uptime:</label>
                        <span id="system-uptime">--</span>
                    </div>
                    <div class="metric-row">
                        <label>Average Response Time:</label>
                        <span id="avg-response-time">-- ms</span>
                    </div>
                    <div class="metric-row">
                        <label>Failure Rate:</label>
                        <span id="failure-rate">--%</span>
                    </div>
                    <div class="metric-row">
                        <label>Maintenance Time Saved:</label>
                        <span id="maintenance-saved">-- hours</span>
                    </div>
                    <div class="metric-row">
                        <label>API Cost Optimization:</label>
                        <span id="api-optimization">--%</span>
                    </div>
                </div>
            </div>

            <div class="tab-panel" id="strategic-tab">
                <div class="strategic-metrics">
                    <div class="metric-row">
                        <label>Market Position:</label>
                        <span id="market-position">--</span>
                    </div>
                    <div class="metric-row">
                        <label>Innovation Capacity:</label>
                        <span id="innovation-capacity">--</span>
                    </div>
                    <div class="metric-row">
                        <label>Competitive Advantage:</label>
                        <span id="competitive-advantage">--</span>
                    </div>
                    <div class="metric-row">
                        <label>Technology Leadership:</label>
                        <span id="tech-leadership">--</span>
                    </div>
                    <div class="metric-row">
                        <label>Scalability Score:</label>
                        <span id="scalability-score">--</span>
                    </div>
                </div>
            </div>

            <div class="tab-panel" id="competitive-tab">
                <div class="competitive-metrics">
                    <div class="competitor-comparison" id="competitor-comparison">
                        <!-- Dynamic competitor data will be inserted here -->
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Initialize charts using Chart.js or similar library
     */
    initializeCharts() {
        try {
            // Business Impact Trends Chart
            const impactCtx = document.getElementById('business-impact-chart');
            if (impactCtx) {
                this.chartInstances.impactChart = this.createBusinessImpactChart(impactCtx);
            }

            // ROI Performance Chart
            const roiCtx = document.getElementById('roi-performance-chart');
            if (roiCtx) {
                this.chartInstances.roiChart = this.createROIPerformanceChart(roiCtx);
            }

        } catch (error) {
            console.warn('⚠️ Charts library not available, using fallback visualizations');
            this.createFallbackCharts();
        }
    }

    /**
     * Create business impact chart (fallback version)
     */
    createBusinessImpactChart(canvas) {
        const ctx = canvas.getContext('2d');

        // Simple bar chart implementation
        const data = [
            { label: 'Revenue Protection', value: 85, color: '#10B981' },
            { label: 'Cost Savings', value: 92, color: '#3B82F6' },
            { label: 'Productivity', value: 78, color: '#8B5CF6' },
            { label: 'Reliability', value: 99, color: '#F59E0B' }
        ];

        this.drawSimpleBarChart(ctx, data, canvas.width, canvas.height);

        return { data, update: () => this.drawSimpleBarChart(ctx, data, canvas.width, canvas.height) };
    }

    /**
     * Create ROI performance chart (fallback version)
     */
    createROIPerformanceChart(canvas) {
        const ctx = canvas.getContext('2d');

        // Simple line chart for ROI over time
        const data = [
            { month: 'Month 1', roi: 0 },
            { month: 'Month 3', roi: 125 },
            { month: 'Month 6', roi: 285 },
            { month: 'Month 12', roi: 347 },
            { month: 'Year 2', roi: 425 },
            { month: 'Year 3', roi: 520 }
        ];

        this.drawSimpleLineChart(ctx, data, canvas.width, canvas.height);

        return { data, update: () => this.drawSimpleLineChart(ctx, data, canvas.width, canvas.height) };
    }

    /**
     * Draw simple bar chart
     */
    drawSimpleBarChart(ctx, data, width, height) {
        ctx.clearRect(0, 0, width, height);

        const padding = 40;
        const chartWidth = width - 2 * padding;
        const chartHeight = height - 2 * padding;
        const barWidth = chartWidth / data.length * 0.6;
        const maxValue = Math.max(...data.map(d => d.value));

        data.forEach((item, index) => {
            const barHeight = (item.value / maxValue) * chartHeight;
            const x = padding + (index * chartWidth / data.length) + (chartWidth / data.length - barWidth) / 2;
            const y = padding + chartHeight - barHeight;

            // Draw bar
            ctx.fillStyle = item.color;
            ctx.fillRect(x, y, barWidth, barHeight);

            // Draw label
            ctx.fillStyle = '#374151';
            ctx.font = '12px Arial';
            ctx.textAlign = 'center';
            ctx.fillText(item.label, x + barWidth / 2, height - 10);

            // Draw value
            ctx.fillStyle = '#1F2937';
            ctx.font = 'bold 14px Arial';
            ctx.fillText(`${item.value}%`, x + barWidth / 2, y - 5);
        });
    }

    /**
     * Draw simple line chart
     */
    drawSimpleLineChart(ctx, data, width, height) {
        ctx.clearRect(0, 0, width, height);

        const padding = 40;
        const chartWidth = width - 2 * padding;
        const chartHeight = height - 2 * padding;
        const maxValue = Math.max(...data.map(d => d.roi));

        // Draw axes
        ctx.strokeStyle = '#E5E7EB';
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, height - padding);
        ctx.lineTo(width - padding, height - padding);
        ctx.stroke();

        // Draw data line
        ctx.strokeStyle = '#3B82F6';
        ctx.lineWidth = 3;
        ctx.beginPath();

        data.forEach((point, index) => {
            const x = padding + (index / (data.length - 1)) * chartWidth;
            const y = padding + chartHeight - (point.roi / maxValue) * chartHeight;

            if (index === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }

            // Draw point
            ctx.fillStyle = '#1D4ED8';
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.fill();
        });

        ctx.stroke();

        // Draw labels
        ctx.fillStyle = '#374151';
        ctx.font = '10px Arial';
        ctx.textAlign = 'center';
        data.forEach((point, index) => {
            const x = padding + (index / (data.length - 1)) * chartWidth;
            ctx.fillText(point.month, x, height - 5);
        });
    }

    /**
     * Load historical metrics data
     */
    async loadHistoricalMetrics() {
        try {
            const response = await fetch(`${this.backendUrl}/api/metrics/business-impact`);
            if (response.ok) {
                const data = await response.json();
                this.updateMetricsDisplay(data);
            } else {
                // Use mock data if backend unavailable
                this.updateMetricsDisplay(this.generateMockData());
            }
        } catch (error) {
            console.warn('⚠️ Using mock data for metrics:', error.message);
            this.updateMetricsDisplay(this.generateMockData());
        }
    }

    /**
     * Generate mock data for demonstration
     */
    generateMockData() {
        return {
            revenue_protection: {
                current: 2150000,
                target: 2400000,
                trend: 'increasing',
                change: 15.2
            },
            cost_savings: {
                current: 445000,
                target: 485000,
                trend: 'increasing',
                change: 22.8
            },
            productivity_gains: {
                current: 32,
                target: 35,
                trend: 'increasing',
                change: 8.5
            },
            reliability_improvement: {
                current: 97.2,
                target: 99,
                trend: 'increasing',
                change: 29.6
            },
            customer_satisfaction: {
                current: 89,
                target: 95,
                trend: 'increasing',
                change: 15.6
            },
            time_to_market: {
                current: 42,
                target: 50,
                trend: 'increasing',
                change: 42.0
            },
            financial_metrics: {
                annual_savings: 485000,
                roi_percentage: 347,
                payback_period: 8.2,
                npv_5_year: 1950000,
                revenue_protected: 2400000
            },
            operational_metrics: {
                system_uptime: 99.2,
                avg_response_time: 185,
                failure_rate: 0.8,
                maintenance_saved: 1560,
                api_optimization: 15
            },
            strategic_metrics: {
                market_position: 'Technology Leader',
                innovation_capacity: 'Enhanced',
                competitive_advantage: 'Significant',
                tech_leadership: 'First-mover',
                scalability_score: 95
            }
        };
    }

    /**
     * Update metrics display
     */
    updateMetricsDisplay(data) {
        // Update main metric cards
        Object.keys(this.impactCategories).forEach(key => {
            if (data[key]) {
                const metric = data[key];
                const category = this.impactCategories[key];

                // Update current value
                const currentElement = document.getElementById(`${key}-current`);
                if (currentElement) {
                    currentElement.textContent = this.formatValue(metric.current, category.format);
                }

                // Update progress bar
                const progress = (metric.current / category.target) * 100;
                const progressElement = document.getElementById(`${key}-progress`);
                if (progressElement) {
                    progressElement.style.width = `${Math.min(100, progress)}%`;
                    progressElement.className = `progress-fill ${this.getProgressClass(progress)}`;
                }

                // Update percentage
                const percentageElement = document.getElementById(`${key}-percentage`);
                if (percentageElement) {
                    percentageElement.textContent = `${progress.toFixed(1)}%`;
                }

                // Update trend
                const trendElement = document.getElementById(`${key}-trend`);
                if (trendElement && metric.trend) {
                    const trendIcon = metric.trend === 'increasing' ? '📈' :
                                    metric.trend === 'decreasing' ? '📉' : '➡️';
                    const changeText = metric.change ? `+${metric.change.toFixed(1)}%` : 'Stable';
                    trendElement.innerHTML = `
                        <span class="trend-indicator">${trendIcon}</span>
                        <span class="trend-text">${changeText}</span>
                    `;
                }
            }
        });

        // Update detailed tabs
        this.updateDetailedMetrics(data);

        // Update alerts
        this.updateAlerts(data);

        // Store for history
        this.metricsHistory.push({
            timestamp: new Date(),
            data: data
        });

        // Keep only last 50 data points
        if (this.metricsHistory.length > 50) {
            this.metricsHistory = this.metricsHistory.slice(-50);
        }
    }

    /**
     * Update detailed metrics in tabs
     */
    updateDetailedMetrics(data) {
        // Financial metrics
        if (data.financial_metrics) {
            const fm = data.financial_metrics;
            this.updateElement('annual-savings', this.formatCurrency(fm.annual_savings));
            this.updateElement('roi-percentage', `${fm.roi_percentage}%`);
            this.updateElement('payback-period', `${fm.payback_period} months`);
            this.updateElement('npv-5-year', this.formatCurrency(fm.npv_5_year));
            this.updateElement('revenue-protected', this.formatCurrency(fm.revenue_protected));
        }

        // Operational metrics
        if (data.operational_metrics) {
            const om = data.operational_metrics;
            this.updateElement('system-uptime', `${om.system_uptime}%`);
            this.updateElement('avg-response-time', `${om.avg_response_time}ms`);
            this.updateElement('failure-rate', `${om.failure_rate}%`);
            this.updateElement('maintenance-saved', `${om.maintenance_saved} hours`);
            this.updateElement('api-optimization', `${om.api_optimization}%`);
        }

        // Strategic metrics
        if (data.strategic_metrics) {
            const sm = data.strategic_metrics;
            this.updateElement('market-position', sm.market_position);
            this.updateElement('innovation-capacity', sm.innovation_capacity);
            this.updateElement('competitive-advantage', sm.competitive_advantage);
            this.updateElement('tech-leadership', sm.tech_leadership);
            this.updateElement('scalability-score', sm.scalability_score);
        }

        // Update competitive comparison
        this.updateCompetitiveComparison(data);
    }

    /**
     * Update competitive comparison
     */
    updateCompetitiveComparison(data) {
        const container = document.getElementById('competitor-comparison');
        if (!container) return;

        const competitors = [
            { name: 'LangChain', reliability: 72, cost: 125000, setup: 'Complex' },
            { name: 'Semantic Kernel', reliability: 68, cost: 145000, setup: 'Very Complex' },
            { name: 'Azure AI', reliability: 75, cost: 118000, setup: 'Moderate' },
            { name: 'Adaptive Mind', reliability: 99, cost: 85000, setup: 'Simple' }
        ];

        const html = competitors.map(comp => `
            <div class="competitor-card ${comp.name === 'Adaptive Mind' ? 'highlight' : ''}">
                <h4>${comp.name}</h4>
                <div class="comp-metric">
                    <span>Reliability:</span>
                    <span class="metric-value">${comp.reliability}%</span>
                </div>
                <div class="comp-metric">
                    <span>Annual Cost:</span>
                    <span class="metric-value">${this.formatCurrency(comp.cost)}</span>
                </div>
                <div class="comp-metric">
                    <span>Setup:</span>
                    <span class="metric-value">${comp.setup}</span>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    /**
     * Update alerts based on metrics
     */
    updateAlerts(data) {
        const container = document.getElementById('alerts-container');
        if (!container) return;

        const alerts = this.generateAlerts(data);

        const html = alerts.map(alert => `
            <div class="alert alert-${alert.type}">
                <span class="alert-icon">${alert.icon}</span>
                <div class="alert-content">
                    <strong>${alert.title}</strong>
                    <p>${alert.message}</p>
                </div>
                <span class="alert-time">${alert.time}</span>
            </div>
        `).join('');

        container.innerHTML = html || '<p class="no-alerts">No critical alerts at this time.</p>';
    }

    /**
     * Generate alerts based on current metrics
     */
    generateAlerts(data) {
        const alerts = [];
        const now = new Date().toLocaleTimeString();

        // Check for high ROI achievement
        if (data.financial_metrics && data.financial_metrics.roi_percentage > 300) {
            alerts.push({
                type: 'success',
                icon: '🎯',
                title: 'Exceptional ROI Achieved',
                message: `ROI of ${data.financial_metrics.roi_percentage}% significantly exceeds target`,
                time: now
            });
        }

        // Check for reliability milestone
        if (data.reliability_improvement && data.reliability_improvement.current > 95) {
            alerts.push({
                type: 'success',
                icon: '🛡️',
                title: 'Reliability Milestone',
                message: `System reliability reached ${data.reliability_improvement.current}%`,
                time: now
            });
        }

        // Check for cost savings
        if (data.cost_savings && data.cost_savings.current > 400000) {
            alerts.push({
                type: 'info',
                icon: '💰',
                title: 'Cost Savings Target Exceeded',
                message: `Annual savings of ${this.formatCurrency(data.cost_savings.current)} achieved`,
                time: now
            });
        }

        // Competitive advantage alert
        alerts.push({
            type: 'info',
            icon: '🏆',
            title: 'Competitive Advantage',
            message: 'Adaptive Mind outperforms all major competitors by 20-30%',
            time: now
        });

        return alerts;
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Real-time toggle
        const toggleButton = document.getElementById('toggle-realtime');
        if (toggleButton) {
            toggleButton.addEventListener('click', () => this.toggleRealTime());
        }

        // Refresh button
        const refreshButton = document.getElementById('refresh-metrics');
        if (refreshButton) {
            refreshButton.addEventListener('click', () => this.loadHistoricalMetrics());
        }

        // Export button
        const exportButton = document.getElementById('export-metrics');
        if (exportButton) {
            exportButton.addEventListener('click', () => this.exportMetrics());
        }

        // Tab switching
        const tabButtons = document.querySelectorAll('.tab-button');
        tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const tabName = e.target.getAttribute('data-tab');
                this.switchTab(tabName);
            });
        });
    }

    /**
     * Toggle real-time updates
     */
    toggleRealTime() {
        this.realTimeEnabled = !this.realTimeEnabled;
        const statusElement = document.getElementById('realtime-status');

        if (this.realTimeEnabled) {
            statusElement.textContent = '⏸️ Stop Real-Time';
            this.startRealTimeUpdates();
        } else {
            statusElement.textContent = '▶️ Start Real-Time';
            this.stopRealTimeUpdates();
        }
    }

    /**
     * Start real-time updates
     */
    startRealTimeUpdates() {
        if (this.updateInterval) {
            this.realTimeTimer = setInterval(() => {
                if (this.realTimeEnabled) {
                    this.loadHistoricalMetrics();
                }
            }, this.updateInterval);
        }
    }

    /**
     * Stop real-time updates
     */
    stopRealTimeUpdates() {
        if (this.realTimeTimer) {
            clearInterval(this.realTimeTimer);
            this.realTimeTimer = null;
        }
    }

    /**
     * Switch between tabs
     */
    switchTab(tabName) {
        // Update buttons
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

        // Update panels
        document.querySelectorAll('.tab-panel').forEach(panel => {
            panel.classList.remove('active');
        });
        document.getElementById(`${tabName}-tab`).classList.add('active');
    }

    /**
     * Export metrics data
     */
    exportMetrics() {
        const exportData = {
            timestamp: new Date().toISOString(),
            current_metrics: this.metricsHistory[this.metricsHistory.length - 1]?.data || {},
            historical_data: this.metricsHistory,
            summary: {
                total_data_points: this.metricsHistory.length,
                time_range: this.metricsHistory.length > 0 ? {
                    start: this.metricsHistory[0].timestamp,
                    end: this.metricsHistory[this.metricsHistory.length - 1].timestamp
                } : null
            }
        };

        this.downloadJSON(exportData, `business_metrics_${new Date().toISOString().split('T')[0]}.json`);
    }

    // Utility methods
    formatValue(value, format) {
        switch (format) {
            case 'currency':
                return this.formatCurrency(value);
            case 'percentage':
                return `${value}%`;
            case 'percentage_reduction':
                return `-${value}%`;
            default:
                return value.toString();
        }
    }

    formatCurrency(value) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }).format(value);
    }

    getProgressClass(percentage) {
        if (percentage >= this.kpiThresholds.excellent) return 'excellent';
        if (percentage >= this.kpiThresholds.good) return 'good';
        if (percentage >= this.kpiThresholds.fair) return 'fair';
        return 'poor';
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    showError(message) {
        console.error('Business Metrics Error:', message);
        // Could show a toast notification or modal here
    }

    downloadJSON(data, filename) {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }

    /**
     * Create fallback charts when Chart.js is not available
     */
    createFallbackCharts() {
        // Simple CSS-based charts
        console.log('📊 Using fallback chart implementation');
    }

    /**
     * Cleanup method
     */
    destroy() {
        this.stopRealTimeUpdates();

        // Cleanup chart instances
        Object.values(this.chartInstances).forEach(chart => {
            if (chart && chart.destroy) {
                chart.destroy();
            }
        });

        console.log('🗑️ Business Metrics Engine cleaned up');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BusinessMetricsEngine;
}

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (typeof window !== 'undefined' && document.getElementById('business-metrics-container')) {
        window.businessMetrics = new BusinessMetricsEngine();
    }
});

console.log('✅ Business Metrics Engine loaded successfully');