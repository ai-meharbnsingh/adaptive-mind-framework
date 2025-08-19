// 03_Demo_Interface/dual_mode_interface.js

/**
 * Dual-Mode Interface for Adaptive Mind Framework Demo
 * SESSION 7 - Enhanced Demo Backend Integration
 *
 * Provides secure switching between hosted demo mode and buyer evaluation mode,
 * with enterprise-grade API key handling and real-time mode management.
 *
 * Created: August 18, 2025
 * Author: Adaptive Mind Framework Team
 * Version: 1.0
 */

class DualModeInterface {
    constructor() {
        this.currentMode = 'hosted';
        this.buyerKeys = {};
        this.sessionId = this.generateSessionId();
        this.isSecureMode = false;
        this.keyValidationTimeout = null;

        this.initializeInterface();
        this.attachEventListeners();

        console.log('🚀 DualModeInterface initialized');
    }

    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }

    initializeInterface() {
        // Add mode switcher to the page
        this.createModeSwitch();
        this.createBuyerKeyInterface();
        this.createSecurityIndicator();
        this.updateModeDisplay();
    }

    createModeSwitch() {
        const modeSection = document.createElement('div');
        modeSection.className = 'mode-section';
        modeSection.innerHTML = `
            <div class="mode-switch-container">
                <h3>🔄 Demo Mode Selection</h3>
                <div class="mode-buttons">
                    <button id="hosted-mode-btn" class="mode-btn active">
                        🏢 Hosted Demo
                        <span class="mode-desc">Quick demonstration with our API keys</span>
                    </button>
                    <button id="evaluation-mode-btn" class="mode-btn">
                        🔐 Technical Evaluation
                        <span class="mode-desc">Full evaluation with your API keys</span>
                    </button>
                </div>
                <div class="mode-info">
                    <div id="mode-description" class="mode-description"></div>
                </div>
            </div>
        `;

        // Insert after header
        const header = document.querySelector('.header');
        if (header) {
            header.parentNode.insertBefore(modeSection, header.nextSibling);
        }
    }

    createBuyerKeyInterface() {
        const keySection = document.createElement('div');
        keySection.className = 'buyer-key-section';
        keySection.id = 'buyer-key-interface';
        keySection.style.display = 'none';
        keySection.innerHTML = `
            <div class="security-header">
                <h3>🔐 Secure API Key Configuration</h3>
                <div class="security-badges">
                    <span class="security-badge">🛡️ Memory-Only Storage</span>
                    <span class="security-badge">⏱️ Auto-Expiration (60min)</span>
                    <span class="security-badge">🔒 AES-256 Encryption</span>
                </div>
            </div>

            <div class="key-input-form">
                <div class="key-input-group">
                    <label for="openai-key">OpenAI API Key:</label>
                    <div class="input-container">
                        <input type="password" id="openai-key" placeholder="sk-..." maxlength="100">
                        <button type="button" class="toggle-visibility" data-target="openai-key">👁️</button>
                    </div>
                    <div class="key-status" id="openai-status"></div>
                </div>

                <div class="key-input-group">
                    <label for="anthropic-key">Anthropic API Key:</label>
                    <div class="input-container">
                        <input type="password" id="anthropic-key" placeholder="sk-ant-..." maxlength="100">
                        <button type="button" class="toggle-visibility" data-target="anthropic-key">👁️</button>
                    </div>
                    <div class="key-status" id="anthropic-status"></div>
                </div>

                <div class="key-input-group">
                    <label for="google-key">Google AI API Key:</label>
                    <div class="input-container">
                        <input type="password" id="google-key" placeholder="AIza..." maxlength="100">
                        <button type="button" class="toggle-visibility" data-target="google-key">👁️</button>
                    </div>
                    <div class="key-status" id="google-status"></div>
                </div>
            </div>

            <div class="key-actions">
                <button id="validate-keys" class="action-btn validate-btn">
                    🔍 Validate Keys
                </button>
                <button id="clear-keys" class="action-btn clear-btn">
                    🗑️ Clear All Keys
                </button>
                <button id="test-connection" class="action-btn test-btn" style="display: none;">
                    🚀 Test Connection
                </button>
            </div>

            <div class="security-notice">
                <p><strong>🔒 Security Notice:</strong> Your API keys are handled with enterprise-grade security:</p>
                <ul>
                    <li>Keys are stored in memory only (never persisted to disk)</li>
                    <li>Automatic expiration after 60 minutes</li>
                    <li>Encrypted transmission (AES-256)</li>
                    <li>Complete audit trail</li>
                    <li>No key logging or storage in our systems</li>
                </ul>
            </div>
        `;

        // Insert before demo form
        const demoSection = document.querySelector('.section');
        if (demoSection) {
            demoSection.parentNode.insertBefore(keySection, demoSection);
        }
    }

    createSecurityIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'security-indicator';
        indicator.id = 'security-indicator';
        indicator.innerHTML = `
            <div class="indicator-content">
                <span class="indicator-icon">🔓</span>
                <span class="indicator-text">Hosted Mode - Our Keys</span>
                <span class="indicator-status">Standard Security</span>
            </div>
        `;

        // Insert at top of container
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(indicator, container.firstChild);
        }
    }

    attachEventListeners() {
        // Mode switching
        document.addEventListener('click', (e) => {
            if (e.target.id === 'hosted-mode-btn') {
                this.switchToHostedMode();
            } else if (e.target.id === 'evaluation-mode-btn') {
                this.switchToEvaluationMode();
            }
        });

        // Key validation
        document.addEventListener('click', (e) => {
            if (e.target.id === 'validate-keys') {
                this.validateKeys();
            } else if (e.target.id === 'clear-keys') {
                this.clearKeys();
            } else if (e.target.id === 'test-connection') {
                this.testConnection();
            }
        });

        // Visibility toggles
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('toggle-visibility')) {
                this.toggleKeyVisibility(e.target.dataset.target);
            }
        });

        // Real-time key validation
        ['openai-key', 'anthropic-key', 'google-key'].forEach(keyId => {
            const input = document.getElementById(keyId);
            if (input) {
                input.addEventListener('input', () => {
                    clearTimeout(this.keyValidationTimeout);
                    this.keyValidationTimeout = setTimeout(() => {
                        this.validateSingleKey(keyId);
                    }, 500);
                });
            }
        });
    }

    switchToHostedMode() {
        this.currentMode = 'hosted';
        this.isSecureMode = false;
        this.updateModeDisplay();
        this.updateSecurityIndicator();

        // Hide buyer key interface
        const keyInterface = document.getElementById('buyer-key-interface');
        if (keyInterface) {
            keyInterface.style.display = 'none';
        }

        // Update demo form mode
        const modeSelect = document.getElementById('mode');
        if (modeSelect) {
            modeSelect.value = 'hosted';
        }

        console.log('🏢 Switched to Hosted Mode');
    }

    switchToEvaluationMode() {
        this.currentMode = 'evaluation';
        this.updateModeDisplay();

        // Show buyer key interface
        const keyInterface = document.getElementById('buyer-key-interface');
        if (keyInterface) {
            keyInterface.style.display = 'block';
            keyInterface.scrollIntoView({ behavior: 'smooth' });
        }

        // Update demo form mode
        const modeSelect = document.getElementById('mode');
        if (modeSelect) {
            modeSelect.value = 'evaluation';
        }

        console.log('🔐 Switched to Evaluation Mode');
    }

    updateModeDisplay() {
        // Update button states
        const hostedBtn = document.getElementById('hosted-mode-btn');
        const evaluationBtn = document.getElementById('evaluation-mode-btn');

        if (hostedBtn && evaluationBtn) {
            hostedBtn.classList.toggle('active', this.currentMode === 'hosted');
            evaluationBtn.classList.toggle('active', this.currentMode === 'evaluation');
        }

        // Update mode description
        const description = document.getElementById('mode-description');
        if (description) {
            if (this.currentMode === 'hosted') {
                description.innerHTML = `
                    <div class="mode-info-content">
                        <h4>🏢 Hosted Demo Mode</h4>
                        <p>Perfect for executive presentations and quick demonstrations.</p>
                        <ul>
                            <li>✅ Uses our managed API keys</li>
                            <li>✅ Controlled demo scenarios</li>
                            <li>✅ Rate limited for cost control</li>
                            <li>✅ No setup required</li>
                        </ul>
                    </div>
                `;
            } else {
                description.innerHTML = `
                    <div class="mode-info-content">
                        <h4>🔐 Technical Evaluation Mode</h4>
                        <p>Full framework access with your own API keys for thorough evaluation.</p>
                        <ul>
                            <li>🔑 Uses your API keys securely</li>
                            <li>🔧 Full framework capabilities</li>
                            <li>💰 You control costs and usage</li>
                            <li>🛡️ Enterprise-grade security</li>
                        </ul>
                    </div>
                `;
            }
        }
    }

    updateSecurityIndicator() {
        const indicator = document.getElementById('security-indicator');
        if (indicator) {
            const icon = indicator.querySelector('.indicator-icon');
            const text = indicator.querySelector('.indicator-text');
            const status = indicator.querySelector('.indicator-status');

            if (this.currentMode === 'hosted') {
                icon.textContent = '🔓';
                text.textContent = 'Hosted Mode - Our Keys';
                status.textContent = 'Standard Security';
                indicator.className = 'security-indicator hosted';
            } else if (this.isSecureMode) {
                icon.textContent = '🔒';
                text.textContent = 'Evaluation Mode - Your Keys';
                status.textContent = 'Enterprise Security';
                indicator.className = 'security-indicator secure';
            } else {
                icon.textContent = '⚠️';
                text.textContent = 'Evaluation Mode - Keys Required';
                status.textContent = 'Setup Required';
                indicator.className = 'security-indicator warning';
            }
        }
    }

    toggleKeyVisibility(targetId) {
        const input = document.getElementById(targetId);
        const button = document.querySelector(`[data-target="${targetId}"]`);

        if (input && button) {
            if (input.type === 'password') {
                input.type = 'text';
                button.textContent = '🙈';
            } else {
                input.type = 'password';
                button.textContent = '👁️';
            }
        }
    }

    validateSingleKey(keyId) {
        const input = document.getElementById(keyId);
        const status = document.getElementById(keyId.replace('-key', '-status'));

        if (!input || !status) return;

        const value = input.value.trim();
        if (!value) {
            status.innerHTML = '';
            return;
        }

        // Basic format validation
        let isValid = false;
        let message = '';

        switch (keyId) {
            case 'openai-key':
                isValid = value.startsWith('sk-') && value.length >= 20;
                message = isValid ? '✅ Valid format' : '❌ Should start with "sk-" and be at least 20 characters';
                break;
            case 'anthropic-key':
                isValid = value.startsWith('sk-ant-') && value.length >= 20;
                message = isValid ? '✅ Valid format' : '❌ Should start with "sk-ant-" and be at least 20 characters';
                break;
            case 'google-key':
                isValid = value.startsWith('AIza') && value.length >= 20;
                message = isValid ? '✅ Valid format' : '❌ Should start with "AIza" and be at least 20 characters';
                break;
        }

        status.innerHTML = `<span class="${isValid ? 'valid' : 'invalid'}">${message}</span>`;

        if (isValid) {
            this.buyerKeys[keyId.replace('-key', '')] = value;
        } else {
            delete this.buyerKeys[keyId.replace('-key', '')];
        }
    }

    async validateKeys() {
        const validateBtn = document.getElementById('validate-keys');
        const testBtn = document.getElementById('test-connection');

        if (!validateBtn) return;

        validateBtn.disabled = true;
        validateBtn.innerHTML = '🔄 Validating...';

        try {
            // Collect all keys
            const keys = {};
            ['openai', 'anthropic', 'google'].forEach(provider => {
                const input = document.getElementById(`${provider}-key`);
                if (input && input.value.trim()) {
                    keys[provider] = input.value.trim();
                }
            });

            if (Object.keys(keys).length === 0) {
                throw new Error('Please provide at least one API key');
            }

            // Send to backend for validation
            const response = await fetch('/api/validate-buyer-keys', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    api_keys: keys
                })
            });

            const result = await response.json();

            if (result.success) {
                this.isSecureMode = true;
                this.buyerKeys = keys;
                this.updateSecurityIndicator();

                validateBtn.innerHTML = '✅ Keys Validated';
                validateBtn.style.background = '#48bb78';

                if (testBtn) {
                    testBtn.style.display = 'inline-block';
                }

                // Show success message
                this.showNotification('✅ API keys validated successfully! You can now run full evaluations.', 'success');

            } else {
                throw new Error(result.error || 'Validation failed');
            }

        } catch (error) {
            console.error('Key validation error:', error);
            this.showNotification(`❌ Validation failed: ${error.message}`, 'error');

            validateBtn.innerHTML = '❌ Validation Failed';
            validateBtn.style.background = '#f56565';

            setTimeout(() => {
                validateBtn.innerHTML = '🔍 Validate Keys';
                validateBtn.style.background = '#667eea';
                validateBtn.disabled = false;
            }, 3000);
        }
    }

    clearKeys() {
        // Clear all inputs
        ['openai-key', 'anthropic-key', 'google-key'].forEach(keyId => {
            const input = document.getElementById(keyId);
            const status = document.getElementById(keyId.replace('-key', '-status'));

            if (input) input.value = '';
            if (status) status.innerHTML = '';
        });

        // Reset state
        this.buyerKeys = {};
        this.isSecureMode = false;
        this.updateSecurityIndicator();

        // Reset buttons
        const validateBtn = document.getElementById('validate-keys');
        const testBtn = document.getElementById('test-connection');

        if (validateBtn) {
            validateBtn.innerHTML = '🔍 Validate Keys';
            validateBtn.style.background = '#667eea';
            validateBtn.disabled = false;
        }

        if (testBtn) {
            testBtn.style.display = 'none';
        }

        this.showNotification('🗑️ All keys cleared', 'info');
    }

    async testConnection() {
        const testBtn = document.getElementById('test-connection');
        if (!testBtn) return;

        testBtn.disabled = true;
        testBtn.innerHTML = '🔄 Testing...';

        try {
            const response = await fetch('/api/test-buyer-connection', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    session_id: this.sessionId,
                    api_keys: this.buyerKeys
                })
            });

            const result = await response.json();

            if (result.success) {
                testBtn.innerHTML = '✅ Connection Test Passed';
                testBtn.style.background = '#48bb78';

                this.showNotification(`✅ Connection test successful! Tested ${result.providers_tested.join(', ')}`, 'success');
            } else {
                throw new Error(result.error || 'Connection test failed');
            }

        } catch (error) {
            console.error('Connection test error:', error);
            this.showNotification(`❌ Connection test failed: ${error.message}`, 'error');

            testBtn.innerHTML = '❌ Test Failed';
            testBtn.style.background = '#f56565';
        }

        setTimeout(() => {
            testBtn.innerHTML = '🚀 Test Connection';
            testBtn.style.background = '#667eea';
            testBtn.disabled = false;
        }, 3000);
    }

    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(n => n.remove());

        // Create notification
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <span>${message}</span>
            <button class="notification-close">×</button>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);

        // Manual close
        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });
    }

    // Method to get current configuration for demo execution
    getCurrentConfig() {
        return {
            mode: this.currentMode,
            session_id: this.sessionId,
            buyer_api_keys: this.currentMode === 'evaluation' && this.isSecureMode ? this.buyerKeys : null,
            is_secure: this.isSecureMode
        };
    }
}

// CSS Styles for the dual-mode interface
const dualModeStyles = `
<style>
/* Mode Switch Styles */
.mode-section {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 25px;
    border-radius: 12px;
    margin: 20px 0;
}

.mode-switch-container h3 {
    margin: 0 0 20px 0;
    font-size: 1.5em;
}

.mode-buttons {
    display: flex;
    gap: 15px;
    margin-bottom: 20px;
}

.mode-btn {
    flex: 1;
    background: rgba(255, 255, 255, 0.1);
    border: 2px solid rgba(255, 255, 255, 0.3);
    color: white;
    padding: 20px;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.3s ease;
    text-align: left;
    font-size: 16px;
    font-weight: bold;
}

.mode-btn:hover {
    background: rgba(255, 255, 255, 0.2);
    border-color: rgba(255, 255, 255, 0.5);
}

.mode-btn.active {
    background: rgba(255, 255, 255, 0.25);
    border-color: white;
    box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);
}

.mode-desc {
    display: block;
    font-size: 12px;
    font-weight: normal;
    margin-top: 5px;
    opacity: 0.8;
}

.mode-info-content {
    background: rgba(255, 255, 255, 0.1);
    padding: 15px;
    border-radius: 8px;
    border-left: 4px solid white;
}

.mode-info-content h4 {
    margin: 0 0 10px 0;
}

.mode-info-content ul {
    margin: 10px 0 0 0;
    padding-left: 20px;
}

.mode-info-content li {
    margin-bottom: 5px;
}

/* Security Indicator Styles */
.security-indicator {
    position: sticky;
    top: 0;
    z-index: 100;
    padding: 12px 20px;
    border-radius: 8px;
    margin-bottom: 20px;
    border: 2px solid;
    transition: all 0.3s ease;
}

.security-indicator.hosted {
    background: #e6fffa;
    border-color: #38b2ac;
    color: #234e52;
}

.security-indicator.secure {
    background: #f0fff4;
    border-color: #48bb78;
    color: #22543d;
}

.security-indicator.warning {
    background: #fffaf0;
    border-color: #ed8936;
    color: #7b341e;
}

.indicator-content {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-weight: bold;
}

.indicator-icon {
    font-size: 1.2em;
    margin-right: 10px;
}

/* Buyer Key Interface Styles */
.buyer-key-section {
    background: #f7fafc;
    border: 2px solid #e2e8f0;
    border-radius: 12px;
    padding: 25px;
    margin: 20px 0;
}

.security-header h3 {
    margin: 0 0 15px 0;
    color: #2d3748;
}

.security-badges {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}

.security-badge {
    background: #48bb78;
    color: white;
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
}

.key-input-form {
    display: grid;
    gap: 20px;
    margin-bottom: 25px;
}

.key-input-group label {
    display: block;
    font-weight: bold;
    margin-bottom: 8px;
    color: #2d3748;
}

.input-container {
    position: relative;
    display: flex;
    align-items: center;
}

.input-container input {
    flex: 1;
    padding: 12px 50px 12px 12px;
    border: 2px solid #e2e8f0;
    border-radius: 8px;
    font-family: monospace;
    font-size: 14px;
}

.input-container input:focus {
    border-color: #667eea;
    outline: none;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.toggle-visibility {
    position: absolute;
    right: 10px;
    background: none;
    border: none;
    cursor: pointer;
    font-size: 16px;
    padding: 5px;
}

.key-status {
    margin-top: 5px;
    min-height: 20px;
    font-size: 12px;
}

.key-status .valid {
    color: #48bb78;
    font-weight: bold;
}

.key-status .invalid {
    color: #f56565;
    font-weight: bold;
}

.key-actions {
    display: flex;
    gap: 15px;
    flex-wrap: wrap;
    margin-bottom: 20px;
}

.action-btn {
    padding: 12px 20px;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: bold;
    transition: all 0.3s ease;
}

.validate-btn {
    background: #667eea;
    color: white;
}

.clear-btn {
    background: #f56565;
    color: white;
}

.test-btn {
    background: #48bb78;
    color: white;
}

.action-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

.security-notice {
    background: #e6fffa;
    border: 1px solid #38b2ac;
    border-radius: 8px;
    padding: 15px;
    color: #234e52;
}

.security-notice p {
    margin: 0 0 10px 0;
    font-weight: bold;
}

.security-notice ul {
    margin: 0;
    padding-left: 20px;
}

.security-notice li {
    margin-bottom: 5px;
}

/* Notification Styles */
.notification {
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 15px 20px;
    border-radius: 8px;
    color: white;
    font-weight: bold;
    z-index: 1000;
    max-width: 400px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    animation: slideIn 0.3s ease;
}

.notification.success {
    background: #48bb78;
}

.notification.error {
    background: #f56565;
}

.notification.info {
    background: #4299e1;
}

.notification-close {
    background: none;
    border: none;
    color: white;
    font-size: 18px;
    cursor: pointer;
    margin-left: 15px;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Responsive Design */
@media (max-width: 768px) {
    .mode-buttons {
        flex-direction: column;
    }

    .security-badges {
        flex-direction: column;
    }

    .key-actions {
        flex-direction: column;
    }

    .indicator-content {
        flex-direction: column;
        text-align: center;
        gap: 10px;
    }
}
</style>
`;

// Initialize the dual-mode interface when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Add styles to the page
    document.head.insertAdjacentHTML('beforeend', dualModeStyles);

    // Initialize the interface
    window.dualModeInterface = new DualModeInterface();

    // Enhance the existing demo execution function
    const originalExecuteDemo = window.executeDemo;
    window.executeDemo = async function() {
        const config = window.dualModeInterface.getCurrentConfig();

        // Update the demo request with dual-mode configuration
        const demoRequest = {
            mode: config.mode,
            prompt: document.getElementById('prompt').value,
            use_case: document.getElementById('use-case').value,
            enable_failover_demo: document.getElementById('enable-failover').checked,
            session_id: config.session_id
        };

        // Add buyer keys if in evaluation mode
        if (config.mode === 'evaluation' && config.buyer_api_keys) {
            demoRequest.buyer_api_keys = config.buyer_api_keys;
        }

        try {
            const response = await fetch('/api/execute-demo', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(demoRequest)
            });

            const result = await response.json();

            // Display results
            const responseContent = document.getElementById('response-content');
            if (responseContent) {
                responseContent.innerHTML = `
                    <div class="demo-result">
                        <div class="result-header">
                            <h4>🚀 Demo Execution Results</h4>
                            <span class="mode-badge ${config.mode}">${config.mode.toUpperCase()} MODE</span>
                        </div>
                        <div class="result-content">
                            <div class="result-section">
                                <h5>📝 Response:</h5>
                                <div class="response-text">${result.response}</div>
                            </div>
                            <div class="result-metrics">
                                <div class="metric-item">
                                    <span class="metric-label">Provider Used:</span>
                                    <span class="metric-value">${result.provider_used}</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Response Time:</span>
                                    <span class="metric-value">${result.response_time_ms}ms</span>
                                </div>
                                <div class="metric-item">
                                    <span class="metric-label">Cost Estimate:</span>
                                    <span class="metric-value">${result.cost_estimate}</span>
                                </div>
                                ${result.failover_occurred ? `
                                <div class="metric-item failover">
                                    <span class="metric-label">🔄 Failover:</span>
                                    <span class="metric-value">Successfully handled</span>
                                </div>
                                ` : ''}
                                ${config.mode === 'evaluation' ? `
                                <div class="metric-item security">
                                    <span class="metric-label">🔐 Security:</span>
                                    <span class="metric-value">Enterprise-grade</span>
                                </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }

            // Show success notification
            window.dualModeInterface.showNotification('✅ Demo executed successfully!', 'success');

        } catch (error) {
            console.error('Demo execution error:', error);
            window.dualModeInterface.showNotification(`❌ Demo execution failed: ${error.message}`, 'error');

            const responseContent = document.getElementById('response-content');
            if (responseContent) {
                responseContent.innerHTML = `
                    <div class="demo-error">
                        <h4>❌ Demo Execution Failed</h4>
                        <p>${error.message}</p>
                        <p class="error-details">Please check your configuration and try again.</p>
                    </div>
                `;
            }
        }
    };
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DualModeInterface;
}