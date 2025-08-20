// 03_Demo_Interface/demo_mode_comparison.js - Demo Mode Comparison
// Adaptive Mind Framework - Session 9
// Interactive comparison between hosted and buyer-key demo modes

/**
 * Demo Mode Comparison Engine
 * Showcases the value proposition of both hosted and buyer-evaluation modes
 */
class DemoModeComparison {
    constructor(backendUrl = 'http://localhost:8000') {
        this.backendUrl = backendUrl;
        this.currentMode = 'hosted';
        this.comparisonData = {
            hosted: {
                name: 'Hosted Demo Mode',
                description: 'Complete demonstration using our infrastructure',
                icon: '🌐',
                cost: '$0',
                setup_time: 'Immediate',
                api_usage: 'Our API keys',
                limitations: 'Rate limited for demo purposes',
                data_access: 'Sample data provided',
                customization: 'Standard scenarios',
                security: 'Secure demo environment',
                support: 'Guided demonstration',
                best_for: 'Initial evaluation and proof-of-concept'
            },
            buyer_keys: {
                name: 'Buyer Evaluation Mode',
                description: 'Full evaluation using your API keys and data',
                icon: '🔑',
                cost: 'Your API usage only',
                setup_time: '5 minutes',
                api_usage: 'Your API keys (secure)',
                limitations: 'None - full framework access',
                data_access: 'Your real data',
                customization: 'Your specific use cases',
                security: 'Your security policies',
                support: 'Technical consultation',
                best_for: 'Production evaluation and decision making'
            }
        };

        this.featureMatrix = {
            'Framework Access': {
                hosted: { available: true, level: 'Demo Version', note: 'All core features enabled' },
                buyer_keys: { available: true, level: 'Full Version', note: 'Complete framework access' }
            },
            'Multi-Provider Support': {
                hosted: { available: true, level: 'Limited Providers', note: 'OpenAI, Anthropic, Google' },
                buyer_keys: { available: true, level: 'All Providers', note: 'Any provider you have access to' }
            },
            'Automatic Failover': {
                hosted: { available: true, level: 'Demonstrated', note: 'Live failover demonstrations' },
                buyer_keys: { available: true, level: 'Production Ready', note: 'Real failover with your keys' }
            },
            'Real-Time Monitoring': {
                hosted: { available: true, level: 'Demo Data', note: 'Sample metrics and dashboards' },
                buyer_keys: { available: true, level: 'Live Data', note: 'Real-time metrics from your usage' }
            },
            'Cost Optimization': {
                hosted: { available: true, level: 'Simulated', note: 'Cost optimization demonstrations' },
                buyer_keys: { available: true, level: 'Actual Savings', note: 'Real cost optimization on your bills' }
            },
            'Custom Scenarios': {
                hosted: { available: true, level: 'Standard Cases', note: '5 pre-built industry scenarios' },
                buyer_keys: { available: true, level: 'Your Use Cases', note: 'Test your specific requirements' }
            },
            'Performance Testing': {
                hosted: { available: true, level: 'Demo Load', note: 'Simulated performance testing' },
                buyer_keys: { available: true, level: 'Production Load', note: 'Test with your actual traffic' }
            },
            'Integration Testing': {
                hosted: { available: false, level: 'Not Available', note: 'Cannot integrate with demo environment' },
                buyer_keys: { available: true, level: 'Full Integration', note: 'Test with your existing systems' }
            },
            'Data Privacy': {
                hosted: { available: true, level: 'Demo Environment', note: 'Isolated demo environment' },
                buyer_keys: { available: true, level: 'Your Environment', note: 'Complete data privacy control' }
            },
            'Technical Support': {
                hosted: { available: true, level: 'Demo Guidance', note: 'Guided demonstration sessions' },
                buyer_keys: { available: true, level: 'Implementation Support', note: 'Technical consultation and setup' }
            }
        };

        this.initialize();
    }

    /**
     * Initialize the demo mode comparison interface
     */
    async initialize() {
        console.log('🚀 Initializing Demo Mode Comparison...');

        try {
            // Create the comparison interface
            this.createComparisonInterface();

            // Setup event listeners
            this.setupEventListeners();

            // Load real-time statistics
            await this.loadDemoStatistics();

            console.log('✅ Demo Mode Comparison initialized successfully');

        } catch (error) {
            console.error('❌ Failed to initialize Demo Mode Comparison:', error);
        }
    }

    /**
     * Create the comparison interface
     */
    createComparisonInterface() {
        const container = document.getElementById('demo-mode-comparison');
        if (!container) {
            console.error('❌ Demo mode comparison container not found');
            return;
        }

        const interfaceHTML = `
            <div class="demo-mode-comparison-container">
                <div class="comparison-header">
                    <h2>🎯 Demo Mode Comparison</h2>
                    <p class="subtitle">Choose the evaluation approach that best fits your needs</p>
                </div>

                <div class="mode-selector">
                    <button class="mode-tab active" data-mode="comparison">📊 Side-by-Side</button>
                    <button class="mode-tab" data-mode="hosted">🌐 Hosted Demo</button>
                    <button class="mode-tab" data-mode="buyer_keys">🔑 Buyer Evaluation</button>
                    <button class="mode-tab" data-mode="features">📋 Feature Matrix</button>
                </div>

                <div class="comparison-content">
                    <!-- Side-by-side comparison -->
                    <div class="tab-content active" id="comparison-tab">
                        ${this.createSideBySideComparison()}
                    </div>

                    <!-- Hosted demo details -->
                    <div class="tab-content" id="hosted-tab">
                        ${this.createModeDetails('hosted')}
                    </div>

                    <!-- Buyer keys details -->
                    <div class="tab-content" id="buyer_keys-tab">
                        ${this.createModeDetails('buyer_keys')}
                    </div>

                    <!-- Feature matrix -->
                    <div class="tab-content" id="features-tab">
                        ${this.createFeatureMatrix()}
                    </div>
                </div>

                <div class="recommendation-section">
                    <h3>💡 Our Recommendation</h3>
                    <div class="recommendation-cards">
                        <div class="recommendation-card">
                            <h4>🌐 Start with Hosted Demo</h4>
                            <p>Perfect for initial evaluation and team alignment. See all capabilities without any setup.</p>
                            <button class="btn-primary" onclick="window.demoModeComparison.startHostedDemo()">Start Hosted Demo</button>
                        </div>
                        <div class="recommendation-card highlight">
                            <h4>🔑 Upgrade to Buyer Evaluation</h4>
                            <p>When you're ready for production evaluation with your real data and use cases.</p>
                            <button class="btn-primary" onclick="window.demoModeComparison.setupBuyerEvaluation()">Setup Evaluation</button>
                        </div>
                    </div>
                </div>

                <div class="success-stories">
                    <h3>📈 Customer Success Stories</h3>
                    <div id="success-stories-container">
                        ${this.createSuccessStories()}
                    </div>
                </div>

                <div class="demo-statistics">
                    <h3>📊 Demo Statistics</h3>
                    <div id="demo-stats-container">
                        <!-- Statistics will be loaded dynamically -->
                    </div>
                </div>
            </div>
        `;

        container.innerHTML = interfaceHTML;
    }

    /**
     * Create side-by-side comparison
     */
    createSideBySideComparison() {
        return `
            <div class="side-by-side-comparison">
                <div class="comparison-table">
                    <div class="comparison-header-row">
                        <div class="feature-column">Feature</div>
                        <div class="hosted-column">
                            <div class="mode-icon">🌐</div>
                            <div class="mode-name">Hosted Demo</div>
                        </div>
                        <div class="buyer-column">
                            <div class="mode-icon">🔑</div>
                            <div class="mode-name">Buyer Evaluation</div>
                        </div>
                    </div>
                    ${this.createComparisonRows()}
                </div>

                <div class="comparison-summary">
                    <div class="summary-card hosted">
                        <h4>🌐 Hosted Demo Benefits</h4>
                        <ul>
                            <li>✅ Zero setup time - immediate access</li>
                            <li>✅ No API costs during evaluation</li>
                            <li>✅ Guided demonstration experience</li>
                            <li>✅ All core features showcased</li>
                            <li>✅ Risk-free evaluation</li>
                        </ul>
                    </div>

                    <div class="summary-card buyer-keys">
                        <h4>🔑 Buyer Evaluation Benefits</h4>
                        <ul>
                            <li>🚀 Full production capabilities</li>
                            <li>🚀 Your real data and use cases</li>
                            <li>🚀 Actual cost savings measurement</li>
                            <li>🚀 Integration with your systems</li>
                            <li>🚀 Production-ready evaluation</li>
                        </ul>
                    </div>
                </div>
            </div>
        `;