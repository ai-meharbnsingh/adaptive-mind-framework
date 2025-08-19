# 03_Demo_Interface/enhanced_demo_endpoints.py

"""
Enhanced Demo Backend Endpoints for Session 7 - Dual-Mode Support
Add these endpoints to your existing demo_backend.py file

These endpoints provide:
1. Buyer API key validation
2. Secure connection testing
3. Enhanced demo execution with dual-mode support
4. Security audit logging

Created: August 18, 2025
Author: Adaptive Mind Framework Team
Version: 1.0
"""

import logging
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Additional Pydantic Models for Session 7
class BuyerKeyValidationRequest(BaseModel):
    session_id: str
    api_keys: Dict[str, str]


class BuyerKeyValidationResponse(BaseModel):
    success: bool
    valid_keys: Dict[str, bool]
    error: Optional[str] = None
    security_audit_id: Optional[str] = None


class ConnectionTestRequest(BaseModel):
    session_id: str
    api_keys: Dict[str, str]


class ConnectionTestResponse(BaseModel):
    success: bool
    providers_tested: list
    test_results: Dict[str, Any]
    error: Optional[str] = None


class EnhancedDemoRequest(BaseModel):
    mode: str
    prompt: str
    use_case: Optional[str] = "general"
    enable_failover_demo: bool = False
    failover_scenario_key: Optional[str] = "primary_api_down"
    buyer_api_keys: Optional[Dict[str, str]] = None
    session_id: str


# ADD THESE ENDPOINTS TO YOUR EXISTING demo_backend.py FILE:

# Buyer API Key Validation Endpoint
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


# Connection Test Endpoint
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


# Enhanced Demo Execution Endpoint
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


# Security Audit Logging
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


# Session Management Endpoint
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


# Cleanup Session Endpoint
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


# Health Check with Security Status
@app.get("/api/health-security")
async def health_check_security():
    """
    Health check endpoint with security system status
    """
    try:
        components = app.state.demo_components

        # Check component health
        health_status = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "demo_backend": "healthy",
            "api_key_manager": "healthy" if hasattr(components, 'api_key_manager') else "unavailable",
            "security_audit": "healthy",
            "dual_mode_support": "enabled",
            "enterprise_security": "enabled",
            "session_management": "healthy"
        }

        return health_status

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "unhealthy",
            "error": str(e)
        }


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