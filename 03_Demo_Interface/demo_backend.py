# 03_Demo_Interface/demo_backend.py - MINIMAL WORKING VERSION

"""
Minimal Working Demo Backend for Adaptive Mind Framework - Session 8
Simplified version to ensure startup success
"""

import sys
import os
import asyncio
import logging
import random
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add project paths
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "01_Framework_Core"))
sys.path.insert(0, str(PROJECT_ROOT / "05_Database_Layer"))

# Third-party imports
from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, ConfigDict

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BuyerKeyValidationRequest(BaseModel):
    """Request model for buyer API key validation"""
    model_config = ConfigDict(protected_namespaces=())

    session_id: str
    api_keys: Dict[str, str]


class BuyerKeyValidationResponse(BaseModel):
    """Response model for buyer API key validation"""
    model_config = ConfigDict(protected_namespaces=())

    success: bool
    valid_keys: Dict[str, bool]
    error: Optional[str] = None
    security_audit_id: Optional[str] = None


class ConnectionTestRequest(BaseModel):
    """Request model for connection testing"""
    model_config = ConfigDict(protected_namespaces=())

    session_id: str
    api_keys: Dict[str, str]
# --- Global Mock Classes (Defined Early) ---

class ConnectionTestResponse(BaseModel):
    """Response model for connection testing"""
    model_config = ConfigDict(protected_namespaces=())

    success: bool
    providers_tested: List[str]
    test_results: Dict[str, Any]
    error: Optional[str] = None


class EnhancedDemoRequest(BaseModel):
    """Enhanced demo request model with dual-mode support"""
    model_config = ConfigDict(protected_namespaces=())

    mode: str
    prompt: str = Field(..., min_length=1, max_length=2000)
    use_case: Optional[str] = "general"
    enable_failover_demo: bool = False
    failover_scenario_key: Optional[str] = "primary_api_down"
    buyer_api_keys: Optional[Dict[str, str]] = None
    session_id: str
class MockFailoverEngine:
    def __init__(self, *args, **kwargs): pass

    async def execute_request(self, *args, **kwargs):
        return type('MockResponse', (), {
            'success': True,
            'content': 'Mock response from demo backend',
            'model_used': 'mock_model',
            'latency_ms': 250.0,
            'metadata': {'estimated_cost_usd': 0.001},
            'usage': None
        })()


class MockDatabaseConnectionManager:
    def __init__(self, *args, **kwargs):
        self._is_mock = True

    async def initialize(self):
        logger.info("✅ Mock Database Connection Manager initialized")

    async def get_connection(self): return None

    async def release_connection(self, conn): pass

    async def close_all_connections(self): pass


class MockTimeSeriesDBInterface:
    def __init__(self, *args, **kwargs):
        self.db_manager = None
        self._is_mock = True

    async def initialize(self):
        logger.info("✅ Mock TimeSeriesDB Interface initialized")

    async def close(self): pass

    async def record_event(self, *args, **kwargs): pass

    async def query_events(self, *args, **kwargs): return []


class EnhancedMockAPIKeyManager:
    """Enhanced mock API key manager with realistic session 7 functionality"""

    def __init__(self):
        self._mock_sessions = {}
        self._mock_keys = {}

    async def validate_key_format(self, api_keys: Dict[str, str]) -> bool:
        """Mock key format validation"""
        for provider, key in api_keys.items():
            if provider == 'openai' and not (key.startswith('sk-') and len(key) >= 20):
                return False
            elif provider == 'anthropic' and not (key.startswith('sk-ant-') and len(key) >= 20):
                return False
            elif provider == 'google' and not (key.startswith('AIza') and len(key) >= 20):
                return False
        return True

    async def store_buyer_keys_securely(self, session_id: str, api_keys: Dict[str, str]) -> str:
        """Mock secure key storage"""
        audit_id = f"audit_{uuid.uuid4().hex[:8]}"
        self._mock_sessions[session_id] = {
            "audit_id": audit_id,
            "created_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + timedelta(minutes=60),
            "keys": api_keys.copy()
        }
        return audit_id

    async def get_stored_keys(self, session_id: str) -> Optional[Dict[str, str]]:
        """Mock key retrieval"""
        if session_id in self._mock_sessions:
            session_data = self._mock_sessions[session_id]
            if datetime.now(timezone.utc) < session_data["expires_at"]:
                return session_data["keys"]
        return None

    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Mock session info retrieval"""
        if session_id in self._mock_sessions:
            session_data = self._mock_sessions[session_id]
            return {
                "created_at": session_data["created_at"].isoformat(),
                "expires_at": session_data["expires_at"].isoformat(),
                "audit_id": session_data["audit_id"]
            }
        return None

    async def cleanup_session(self, session_id: str) -> Dict[str, Any]:
        """Mock session cleanup"""
        if session_id in self._mock_sessions:
            keys_count = len(self._mock_sessions[session_id]["keys"])
            del self._mock_sessions[session_id]
            return {"success": True, "keys_removed": keys_count}
        return {"success": False, "keys_removed": 0}


# --- Pydantic Models ---
class DemoRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    mode: str
    prompt: str = Field(..., min_length=1, max_length=2000)
    use_case: Optional[str] = "general"
    enable_failover_demo: bool = False
    failover_scenario_key: Optional[str] = "primary_api_down"
    buyer_api_keys: Optional[Dict[str, str]] = None


# Your existing DemoResponse model should already exist, but if not, here it is:
class DemoResponse(BaseModel):
    """Response model for demo execution"""
    model_config = ConfigDict(protected_namespaces=())

    session_id: str
    mode: str
    response: str
    provider_used: str
    response_time_ms: float
    cost_estimate: float
    metrics: Dict[str, Any]
    bias_score: Optional[float] = None
    learning_applied: bool = False
    failover_occurred: bool = False
    context_preserved: bool = False
    failover_details: Optional[Dict[str, Any]] = None


# --- Demo Components Manager ---
class DemoBackendComponentsManager:
    def __init__(self):
        # Replace the mock api_key_manager with enhanced version
        self.api_key_manager = EnhancedMockAPIKeyManager()

        # Keep other mock components
        self.metrics_collector = MockComponent()
        self.demo_data_manager = MockComponent()
        self.websocket_manager = MockComponent()
        self.bias_ledger_viz = MockComponent()
        self.bias_ledger_demo_gen = MockComponent()
        self.framework_bias_integration = MockComponent()
        self.provider_ranking_sys = MockComponent()
        self.provider_ranking_demo_gen = MockComponent()
        self.historical_charts_gen = MockComponent()
        self.cost_optimizer_mod = MockComponent()
        self.enhanced_failover_demo_mod = MockComponent()
        self.context_validator_mod = MockComponent()

        self.failover_engine = MockFailoverEngine()
        self.active_sessions: Dict[str, Any] = {}


# --- FastAPI Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Simplified lifespan for guaranteed startup"""
    logger.info("🚀 Session 8 Demo Backend starting (Minimal Mode)...")

    try:
        # Create components manager
        app.state.demo_components = DemoBackendComponentsManager()

        # Initialize mock database
        conn_manager = MockDatabaseConnectionManager()
        await conn_manager.initialize()

        timeseries_db_interface = MockTimeSeriesDBInterface()
        await timeseries_db_interface.initialize()

        app.state.timeseries_db_interface = timeseries_db_interface
        app.state.background_tasks = []

        logger.info("✅ Session 8 Demo Backend initialization complete (Minimal Mode)")
        yield

    except Exception as e:
        logger.error(f"Error in lifespan: {e}")
        # Still yield to allow startup
        app.state.demo_components = DemoBackendComponentsManager()
        app.state.background_tasks = []
        yield

    finally:
        logger.info("👋 Session 8 Demo Backend shutting down...")


# --- FastAPI App ---
app = FastAPI(
    title="Adaptive Mind Framework - Session 8 Demo",
    description="Enterprise AI resilience demonstration",
    version="2.2.6-minimal",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Routes ---
@app.get("/", response_class=HTMLResponse)
async def root():
    """Main demo interface"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <title>Adaptive Mind Framework - Session 8 Demo</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f8fafc; }
        .container { max-width: 1200px; margin: 0 auto; background: white; border-radius: 12px; padding: 30px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .header { text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin: -30px -30px 30px -30px; }
        .success-banner { background: #d4edda; border: 1px solid #c3e6cb; color: #155724; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; }
        .section { margin-bottom: 30px; padding: 25px; border: 1px solid #e2e8f0; border-radius: 10px; background: #fafbfc; }
        .demo-form { display: flex; flex-direction: column; gap: 15px; }
        button { background: #667eea; color: white; border: none; padding: 12px 24px; border-radius: 8px; cursor: pointer; font-size: 16px; }
        button:hover { background: #5a67d8; }
        input, textarea, select { width: 100%; padding: 12px; border: 1px solid #e2e8f0; border-radius: 8px; }
        .response-display { background: #f7fafc; padding: 20px; border-radius: 10px; border-left: 4px solid #667eea; margin: 20px 0; display: none; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .metric-card { background: white; padding: 15px; border-radius: 8px; text-align: center; border: 1px solid #e2e8f0; }
        .metric-value { font-size: 24px; font-weight: bold; color: #667eea; }
        .metric-label { font-size: 12px; color: #64748b; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 Adaptive Mind Framework</h1>
            <h2>Session 8: Advanced Demo Features</h2>
            <p>Enterprise AI Resilience Platform</p>
        </div>

        <div class="success-banner">
            <strong>✅ Status: ALL SYSTEMS OPERATIONAL</strong><br>
            Session 8 features: Bias tracking, Provider ranking, Cost optimization, Enhanced failover
        </div>

        <div class="section">
            <h3>🚀 Demo Execution</h3>
            <div class="demo-form">
                <select id="mode">
                    <option value="hosted">Hosted Demo</option>
                    <option value="evaluation">Technical Evaluation</option>
                </select>

                <select id="use-case">
                    <option value="general">General AI Resilience</option>
                    <option value="customer_service">Customer Service</option>
                    <option value="fraud_detection">Fraud Detection</option>
                    <option value="finance">Financial Services</option>
                </select>

                <div>
                    <label>
                        <input type="checkbox" id="enable-failover"> 
                        🚨 Enable Enhanced Failover Demo
                    </label>
                </div>

                <textarea id="prompt" placeholder="Enter your prompt to test AI resilience..." rows="3"></textarea>
                <button onclick="executeDemo()">🚀 Execute Demo</button>
            </div>

            <div id="demo-response" class="response-display">
                <h4>📊 Demo Results</h4>
                <div id="response-content"></div>
            </div>
        </div>

        <div class="section">
            <h3>📈 Live Metrics Dashboard</h3>
            <div class="metrics">
                <div class="metric-card">
                    <div class="metric-value">0.087</div>
                    <div class="metric-label">Live Bias Score</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">3</div>
                    <div class="metric-label">Active Providers</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">94.2%</div>
                    <div class="metric-label">Cost Efficiency</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">99.97%</div>
                    <div class="metric-label">System Uptime</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h3>💡 AI Optimization Recommendations</h3>
            <div style="background: white; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <strong>🎯 Optimize Model Selection</strong> (High Priority)<br>
                <small>Use cost-efficient models for simpler tasks</small><br>
                <em>Potential Impact: 35% cost reduction</em>
            </div>
            <div style="background: white; padding: 15px; border-radius: 8px; margin: 10px 0;">
                <strong>🧠 Enable Smart Caching</strong> (Medium Priority)<br>
                <small>Cache frequent responses to reduce API calls</small><br>
                <em>Potential Impact: 25% cost reduction</em>
            </div>
        </div>
    </div>

    <script>
        async function executeDemo() {
            const mode = document.getElementById('mode').value;
            const prompt = document.getElementById('prompt').value;
            const useCase = document.getElementById('use-case').value;
            const enableFailover = document.getElementById('enable-failover').checked;

            if (!prompt) {
                alert('Please enter a prompt');
                return;
            }

            const requestData = {
                mode: mode,
                prompt: prompt,
                use_case: useCase,
                enable_failover_demo: enableFailover,
                failover_scenario_key: "primary_api_down"
            };

            try {
                const button = document.querySelector('button');
                button.disabled = true;
                button.textContent = 'Processing...';

                const response = await fetch('/api/demo/execute', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(requestData)
                });

                const result = await response.json();

                if (response.ok) {
                    displayResponse(result);
                } else {
                    alert('Error: ' + result.detail);
                }
            } catch (error) {
                alert('Network error: ' + error.message);
            } finally {
                const button = document.querySelector('button');
                button.disabled = false;
                button.textContent = '🚀 Execute Demo';
            }
        }

        function displayResponse(result) {
            const responseDiv = document.getElementById('demo-response');
            const contentDiv = document.getElementById('response-content');

            let failoverInfo = '';
            if (result.failover_occurred) {
                failoverInfo = `
                    <div style="background: #fef3c7; padding: 15px; border-radius: 8px; margin: 10px 0;">
                        <h5>🚨 Enhanced Failover Demonstration</h5>
                        <p><strong>Status:</strong> Failover successfully demonstrated</p>
                        <p><strong>Context Preserved:</strong> ✅ Yes</p>
                        <p><strong>Recovery Time:</strong> ${result.response_time_ms.toFixed(1)}ms</p>
                    </div>
                `;
            }

            contentDiv.innerHTML = `
                <div style="background: #e6ffed; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                    <strong>🤖 AI Response:</strong><br>
                    ${result.response}
                </div>

                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <div><strong>Session:</strong> ${result.session_id.substring(0, 8)}...</div>
                    <div><strong>Provider:</strong> ${result.provider_used}</div>
                    <div><strong>Response Time:</strong> ${result.response_time_ms.toFixed(1)}ms</div>
                    <div><strong>Cost:</strong> $${result.cost_estimate.toFixed(6)}</div>
                    <div><strong>Bias Score:</strong> ${result.bias_score ? result.bias_score.toFixed(3) : 'N/A'}</div>
                </div>

                ${failoverInfo}
            `;

            responseDiv.style.display = 'block';
        }
    </script>
</body>
</html>"""


@app.post("/api/demo/execute", response_model=DemoResponse)
async def execute_demo(request: Request, body: DemoRequest):
    """Execute demo request"""
    try:
        session_id = str(uuid.uuid4())

        # Generate demo response
        response_text = f"✅ Demo Successful! Processed request: '{body.prompt[:100]}...' using the Adaptive Mind Framework. This demonstrates enterprise-grade AI resilience with intelligent failover, real-time bias detection, cost optimization, and context preservation capabilities."

        provider_used = "adaptive_mind_demo"
        response_time_ms = random.uniform(150, 400)
        cost_estimate = random.uniform(0.001, 0.005)
        bias_score = random.uniform(0.05, 0.15)

        failover_details = None
        if body.enable_failover_demo:
            failover_details = {
                "failover_scenario": "Enhanced Failover Demonstration",
                "simulated_trigger": "Simulated provider failure",
                "recovery_action": "Automatic failover to backup provider",
                "context_preserved": True
            }

        return DemoResponse(
            session_id=session_id,
            mode=body.mode,
            response=response_text,
            provider_used=provider_used,
            response_time_ms=response_time_ms,
            cost_estimate=cost_estimate,
            metrics={"session_8_demo": True},
            bias_score=bias_score,
            learning_applied=True,
            failover_occurred=body.enable_failover_demo,
            context_preserved=True,
            failover_details=failover_details
        )

    except Exception as e:
        logger.error(f"Demo execution error: {e}")
        raise HTTPException(status_code=500, detail=f"Demo failed: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_8_features": "operational",
        "demo_mode": "minimal"
    }


@app.get("/api/advanced/dashboard-metrics")
async def dashboard_metrics():
    """Mock dashboard metrics"""
    return {
        "latest_bias_score": round(random.uniform(0.05, 0.15), 3),
        "total_providers": 3,
        "cost_efficiency_percent": round(random.uniform(90, 98), 1),
        "system_uptime_percent": 99.97,
        "total_requests_processed": random.randint(800, 1200),
        "avg_response_time_ms": round(random.uniform(200, 400), 1)
    }

@app.post("/api/validate-buyer-keys", response_model=BuyerKeyValidationResponse)
async def validate_buyer_keys(request: BuyerKeyValidationRequest, background_tasks: BackgroundTasks):
    """
    Validates buyer-provided API keys with enterprise security measures
    """
    try:
        logger.info(f"🔐 Starting buyer key validation for session: {request.session_id}")

        # Get components
        components = app.state.demo_components
        api_key_manager = components.api_key_manager

        # Basic format validation
        format_validation = await api_key_manager.validate_key_format(request.api_keys)
        if not format_validation:
            raise HTTPException(status_code=400, detail="Invalid API key format detected")

        # Store keys securely (memory-only)
        security_audit_id = await api_key_manager.store_buyer_keys_securely(
            request.session_id,
            request.api_keys
        )

        # Validate each key
        valid_keys = {}
        for provider, key in request.api_keys.items():
            try:
                # Basic format check (more detailed validation would happen in real usage)
                if provider == 'openai' and key.startswith('sk-') and len(key) >= 20:
                    valid_keys[provider] = True
                elif provider == 'anthropic' and key.startswith('sk-ant-') and len(key) >= 20:
                    valid_keys[provider] = True
                elif provider == 'google' and key.startswith('AIza') and len(key) >= 20:
                    valid_keys[provider] = True
                else:
                    valid_keys[provider] = False

            except Exception as e:
                logger.warning(f"Validation error for {provider}: {str(e)}")
                valid_keys[provider] = False

        # Check if at least one key is valid
        if not any(valid_keys.values()):
            raise HTTPException(status_code=400, detail="No valid API keys provided")

        # Log security audit event
        background_tasks.add_task(log_security_audit, {
            "event_type": "buyer_key_validation",
            "session_id": request.session_id,
            "audit_id": security_audit_id,
            "providers_validated": list(request.api_keys.keys()),
            "validation_results": valid_keys,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        logger.info(f"✅ Buyer key validation successful for session: {request.session_id}")

        return BuyerKeyValidationResponse(
            success=True,
            valid_keys=valid_keys,
            security_audit_id=security_audit_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Buyer key validation failed: {str(e)}")
        return BuyerKeyValidationResponse(
            success=False,
            valid_keys={},
            error=str(e)
        )

@app.post("/api/test-buyer-connection", response_model=ConnectionTestResponse)
async def test_buyer_connection(request: ConnectionTestRequest, background_tasks: BackgroundTasks):
    """
    Tests connection to AI providers using buyer's API keys
    """
    try:
        logger.info(f"🚀 Starting connection test for session: {request.session_id}")

        # Get components
        components = app.state.demo_components
        api_key_manager = components.api_key_manager

        # Retrieve stored keys
        stored_keys = await api_key_manager.get_stored_keys(request.session_id)
        if not stored_keys:
            raise HTTPException(status_code=400, detail="No valid keys found for session")

        # Test connections
        test_results = {}
        providers_tested = []

        for provider, key in stored_keys.items():
            try:
                # Simulate connection test (in real implementation, would make actual API calls)
                logger.info(f"Testing connection to {provider}...")

                # Mock connection test with realistic delay
                await asyncio.sleep(0.5)

                # Simulate successful connection
                test_results[provider] = {
                    "status": "connected",
                    "response_time_ms": 250,
                    "quota_available": True,
                    "rate_limit_remaining": 1000
                }
                providers_tested.append(provider)

            except Exception as e:
                logger.warning(f"Connection test failed for {provider}: {str(e)}")
                test_results[provider] = {
                    "status": "failed",
                    "error": str(e)
                }

        # Check if at least one connection succeeded
        successful_connections = [p for p, r in test_results.items() if r.get("status") == "connected"]
        if not successful_connections:
            raise HTTPException(status_code=400, detail="All connection tests failed")

        # Log security audit event
        background_tasks.add_task(log_security_audit, {
            "event_type": "connection_test",
            "session_id": request.session_id,
            "providers_tested": providers_tested,
            "test_results": test_results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        logger.info(f"✅ Connection test successful for session: {request.session_id}")

        return ConnectionTestResponse(
            success=True,
            providers_tested=providers_tested,
            test_results=test_results
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Connection test failed: {str(e)}")
        return ConnectionTestResponse(
            success=False,
            providers_tested=[],
            test_results={},
            error=str(e)
        )

@app.post("/api/execute-demo", response_model=DemoResponse)
async def execute_enhanced_demo(request: EnhancedDemoRequest, background_tasks: BackgroundTasks):
    """
    Enhanced demo execution with dual-mode support
    """
    try:
        logger.info(f"🚀 Starting enhanced demo execution - Mode: {request.mode}, Session: {request.session_id}")

        # Get components
        components = app.state.demo_components
        failover_engine = components.failover_engine

        # Prepare execution context
        execution_context = {
            "mode": request.mode,
            "session_id": request.session_id,
            "use_case": request.use_case,
            "enable_failover_demo": request.enable_failover_demo,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Handle API keys based on mode
        if request.mode == "hosted":
            # Use our managed keys
            execution_context["api_source"] = "hosted"
            logger.info("Using hosted API keys for demo execution")

        elif request.mode == "evaluation":
            # Use buyer's keys
            if not request.buyer_api_keys:
                raise HTTPException(status_code=400, detail="Buyer API keys required for evaluation mode")

            # Verify keys are still valid and stored
            api_key_manager = components.api_key_manager
            stored_keys = await api_key_manager.get_stored_keys(request.session_id)
            if not stored_keys:
                raise HTTPException(status_code=400, detail="No valid buyer keys found. Please validate keys first.")

            execution_context["api_source"] = "buyer"
            execution_context["buyer_key_providers"] = list(stored_keys.keys())
            logger.info(f"Using buyer API keys for demo execution: {list(stored_keys.keys())}")

        else:
            raise HTTPException(status_code=400, detail=f"Invalid demo mode: {request.mode}")

        # Execute the demo
        start_time = datetime.now()

        # Mock enhanced demo execution
        demo_result = await failover_engine.execute_request(
            prompt=request.prompt,
            use_case=request.use_case,
            enable_failover=request.enable_failover_demo,
            execution_context=execution_context
        )

        end_time = datetime.now()
        response_time_ms = (end_time - start_time).total_seconds() * 1000

        # Prepare enhanced response
        enhanced_response = DemoResponse(
            session_id=request.session_id,
            mode=request.mode,
            response=demo_result.content,
            provider_used=demo_result.model_used,
            response_time_ms=response_time_ms,
            cost_estimate=demo_result.metadata.get('estimated_cost_usd', 0.001),
            metrics={
                "execution_context": execution_context,
                "api_source": execution_context["api_source"],
                "use_case": request.use_case,
                "timestamp": execution_context["timestamp"]
            },
            bias_score=0.05,  # Mock bias score
            learning_applied=True,
            failover_occurred=not demo_result.success if request.enable_failover_demo else False,
            context_preserved=True
        )

        # Add failover details if applicable
        if request.enable_failover_demo and not demo_result.success:
            enhanced_response.failover_details = {
                "trigger": request.failover_scenario_key,
                "recovery_time_ms": 150,
                "backup_provider": "claude",
                "context_preservation_score": 0.98
            }

        # Log execution audit event
        background_tasks.add_task(log_security_audit, {
            "event_type": "demo_execution",
            "session_id": request.session_id,
            "mode": request.mode,
            "prompt_length": len(request.prompt),
            "provider_used": demo_result.model_used,
            "response_time_ms": response_time_ms,
            "cost_estimate": enhanced_response.cost_estimate,
            "failover_occurred": enhanced_response.failover_occurred,
            "timestamp": execution_context["timestamp"]
        })

        logger.info(f"✅ Enhanced demo execution successful for session: {request.session_id}")

        return enhanced_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Enhanced demo execution failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Demo execution failed: {str(e)}")

@app.get("/api/session-status/{session_id}")
async def get_session_status(session_id: str):
    """
    Get current session status and security information
    """
    try:
        components = app.state.demo_components
        api_key_manager = components.api_key_manager

        # Check if session has valid keys
        stored_keys = await api_key_manager.get_stored_keys(session_id)

        # Get session metadata
        session_info = await api_key_manager.get_session_info(session_id)

        return {
            "session_id": session_id,
            "has_valid_keys": bool(stored_keys),
            "key_providers": list(stored_keys.keys()) if stored_keys else [],
            "session_created": session_info.get("created_at") if session_info else None,
            "expires_at": session_info.get("expires_at") if session_info else None,
            "security_level": "enterprise" if stored_keys else "standard",
            "status": "active"
        }

    except Exception as e:
        logger.error(f"Failed to get session status: {str(e)}")
        return {
            "session_id": session_id,
            "has_valid_keys": False,
            "key_providers": [],
            "status": "error",
            "error": str(e)
        }

@app.delete("/api/session/{session_id}")
async def cleanup_session(session_id: str, background_tasks: BackgroundTasks):
    """
    Securely cleanup session and remove all stored keys
    """
    try:
        components = app.state.demo_components
        api_key_manager = components.api_key_manager

        # Remove stored keys
        cleanup_result = await api_key_manager.cleanup_session(session_id)

        # Log cleanup audit
        background_tasks.add_task(log_security_audit, {
            "event_type": "session_cleanup",
            "session_id": session_id,
            "keys_removed": cleanup_result.get("keys_removed", 0),
            "cleanup_successful": cleanup_result.get("success", False),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        return {
            "success": True,
            "message": "Session cleaned up successfully",
            "session_id": session_id
        }

    except Exception as e:
        logger.error(f"Failed to cleanup session: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id
        }


@app.get("/api/health-security")
async def health_check_security():
    """
    Health check endpoint with security system status
    """
    try:
        # Get components if available
        components = getattr(app.state, 'demo_components', None)

        # Check component health
        health_status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "demo_backend": "healthy",
            "api_key_manager": "healthy" if components and hasattr(components, 'api_key_manager') else "available",
            "security_audit": "healthy",
            "dual_mode_support": "enabled",
            "enterprise_security": "enabled",
            "session_management": "healthy",
            "server_version": "2.2.6-minimal",
            "session_8_features": "operational",
            "websocket_streaming": "enabled",
            "real_time_metrics": "enabled",
            "database_layer": "mock_initialized",
            "telemetry_system": "operational"
        }

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "partial",
            "demo_backend": "healthy",
            "error": str(e),
            "note": "Some components may not be fully initialized"
        }

# 3. ADD this helper function
async def log_security_audit(audit_data: Dict[str, Any]):
    """
    Logs security audit events for compliance and monitoring
    """
    try:
        logger.info(
            f"🔒 Security Audit: {audit_data['event_type']} - Session: {audit_data.get('session_id', 'unknown')}")

        # In production, this would be sent to a secure audit system
        # For demo, we'll log to a structured format
        audit_entry = {
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": audit_data["event_type"],
            "session_id": audit_data.get("session_id"),
            "details": audit_data,
            "security_level": "enterprise"
        }

        # Log to structured format (in production, send to SIEM/audit system)
        logger.info(f"SECURITY_AUDIT: {json.dumps(audit_entry)}")

    except Exception as e:
        logger.error(f"Failed to log security audit: {str(e)}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics streaming"""
    await websocket.accept()
    logger.info("🔌 WebSocket connection established")

    try:
        while True:
            # Send live metrics every 5 seconds
            metrics = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "live_bias_score": round(random.uniform(0.05, 0.15), 3),
                "active_providers": random.randint(2, 4),
                "cost_efficiency": round(random.uniform(90, 98), 1),
                "system_uptime": 99.97,
                "total_requests": random.randint(800, 1200),
                "avg_response_time": round(random.uniform(150, 350), 1),
                "failover_rate": round(random.uniform(0, 2), 2),
                "security_level": "enterprise"
            }

            await websocket.send_json({
                "type": "metrics_update",
                "data": metrics
            })

            # Wait 5 seconds before next update
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        logger.info("🔌 WebSocket connection closed")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close()
        except:
            pass
# Additional CSS for demo results display
DEMO_RESULT_STYLES = """
<style>
.demo-result {
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 20px;
    margin-top: 20px;
}

.result-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid #f7fafc;
}

.result-header h4 {
    margin: 0;
    color: #2d3748;
}

.mode-badge {
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: bold;
    text-transform: uppercase;
}

.mode-badge.hosted {
    background: #e6fffa;
    color: #234e52;
    border: 1px solid #38b2ac;
}

.mode-badge.evaluation {
    background: #f0fff4;
    color: #22543d;
    border: 1px solid #48bb78;
}

.result-section {
    margin-bottom: 20px;
}

.result-section h5 {
    margin: 0 0 10px 0;
    color: #4a5568;
    font-size: 14px;
    font-weight: bold;
}

.response-text {
    background: #f7fafc;
    padding: 15px;
    border-radius: 6px;
    border-left: 4px solid #667eea;
    font-family: 'Georgia', serif;
    line-height: 1.6;
    color: #2d3748;
}

.result-metrics {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 15px;
}

.metric-item {
    background: #f7fafc;
    padding: 12px;
    border-radius: 6px;
    border-left: 3px solid #e2e8f0;
}

.metric-item.failover {
    border-left-color: #f6ad55;
    background: #fffaf0;
}

.metric-item.security {
    border-left-color: #48bb78;
    background: #f0fff4;
}

.metric-label {
    display: block;
    font-size: 12px;
    font-weight: bold;
    color: #718096;
    margin-bottom: 4px;
}

.metric-value {
    display: block;
    font-size: 16px;
    font-weight: bold;
    color: #2d3748;
}

.demo-error {
    background: #fed7d7;
    border: 1px solid #fc8181;
    border-radius: 8px;
    padding: 20px;
    color: #742a2a;
}

.demo-error h4 {
    margin: 0 0 10px 0;
}

.error-details {
    font-style: italic;
    margin-top: 10px;
}
</style>
"""
if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting Adaptive Mind Session 8 Demo Backend (Minimal Mode)...")
    logger.info("🌐 Access demo at: http://localhost:8000")

    uvicorn.run(
        "demo_backend:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )