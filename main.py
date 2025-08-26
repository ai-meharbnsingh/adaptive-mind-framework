#!/usr/bin/env python3
"""
Enhanced FastAPI Application for Adaptive Mind Framework
Session 13: Professional Sales Materials Integration

This module serves the interactive landing page with full JavaScript component integration,
WebSocket support for real-time metrics, and enterprise-grade API endpoints.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import asyncio
import os
from typing import List, Dict, Any
import logging
from datetime import datetime
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Adaptive Mind Enterprise Framework",
    description="Enterprise AI Resilience Platform with Interactive Demo",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")


# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.metrics_cache: Dict[str, Any] = {
            "uptime": 99.97,
            "response_time": 127,
            "cost_savings": 34,
            "requests_processed": 2400000,
            "last_updated": datetime.now().isoformat(),
        }

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"WebSocket connection established. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(
            f"WebSocket connection closed. Total connections: {len(self.active_connections)}"
        )

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to connection: {e}")

    async def broadcast_metrics_update(self):
        """Broadcast real-time metrics to all connected clients"""
        # Simulate real-time metrics updates
        self.metrics_cache.update(
            {
                "uptime": round(99.95 + random.random() * 0.04, 2),
                "response_time": int(120 + random.random() * 20),
                "cost_savings": int(30 + random.random() * 10),
                "requests_processed": self.metrics_cache["requests_processed"]
                + random.randint(100, 1000),
                "last_updated": datetime.now().isoformat(),
            }
        )

        message = json.dumps({"type": "metrics_update", "metrics": self.metrics_cache})
        await self.broadcast(message)


# Initialize connection manager
manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def serve_landing_page():
    """Serve the enhanced interactive landing page"""
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Landing page not found</h1><p>Please ensure index.html exists in the project root.</p>",
            status_code=404,
        )


@app.get("/video.html", response_class=HTMLResponse)
async def serve_video_demo():
    """Serve the animated terminal demo page"""
    try:
        with open("video.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>Video demo not found</h1><p>Please ensure video.html exists in the project root.</p>",
            status_code=404,
        )


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics updates"""
    await manager.connect(websocket)
    try:
        # Send initial metrics
        await manager.send_personal_message(
            json.dumps({"type": "initial_metrics", "metrics": manager.metrics_cache}),
            websocket,
        )

        # Keep connection alive and listen for client messages
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                message = json.loads(data)

                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({"type": "pong"}), websocket
                    )
                elif message.get("type") == "request_metrics":
                    await manager.send_personal_message(
                        json.dumps(
                            {"type": "metrics_update", "metrics": manager.metrics_cache}
                        ),
                        websocket,
                    )

            except asyncio.TimeoutError:
                # Send heartbeat
                await manager.send_personal_message(
                    json.dumps({"type": "heartbeat"}), websocket
                )
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        manager.disconnect(websocket)


@app.get("/api/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "active_connections": len(manager.active_connections),
    }


@app.get("/api/metrics")
async def get_metrics():
    """REST endpoint for current system metrics"""
    return {
        "status": "success",
        "data": manager.metrics_cache,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/api/roi-calculate")
async def calculate_roi(request: Request):
    """Enterprise ROI calculation endpoint"""
    try:
        data = await request.json()

        monthly_spend = float(data.get("monthly_spend", 10000))
        industry_sector = data.get("industry_sector", "enterprise")
        team_size = int(data.get("team_size", 25))
        downtime_hours = float(data.get("downtime_hours", 8))

        # Industry-specific multipliers
        industry_multipliers = {
            "finance": {"efficiency": 1.4, "downtime_cost": 50000},
            "healthcare": {"efficiency": 1.2, "downtime_cost": 30000},
            "ecommerce": {"efficiency": 1.6, "downtime_cost": 25000},
            "saas": {"efficiency": 1.5, "downtime_cost": 35000},
            "enterprise": {"efficiency": 1.3, "downtime_cost": 40000},
        }

        multiplier = industry_multipliers.get(
            industry_sector, industry_multipliers["enterprise"]
        )

        # Calculate savings
        monthly_cost_savings = monthly_spend * 0.34  # 34% average cost reduction
        downtime_reduction = downtime_hours * 0.85  # 85% downtime reduction
        downtime_savings = downtime_reduction * multiplier["downtime_cost"]
        efficiency_gains = team_size * 2000 * multiplier["efficiency"]

        total_monthly_savings = (
            monthly_cost_savings + downtime_savings + efficiency_gains
        )
        annual_savings = total_monthly_savings * 12
        implementation_cost = 150000
        roi = (annual_savings - implementation_cost) / implementation_cost * 100
        payback_months = implementation_cost / total_monthly_savings

        return {
            "status": "success",
            "data": {
                "monthly_savings": round(total_monthly_savings),
                "annual_savings": round(annual_savings),
                "roi_percent": round(roi, 1),
                "payback_months": round(payback_months, 1),
                "implementation_cost": implementation_cost,
                "breakdown": {
                    "cost_reduction": round(monthly_cost_savings),
                    "downtime_savings": round(downtime_savings),
                    "efficiency_gains": round(efficiency_gains),
                },
            },
        }

    except Exception as e:
        logger.error(f"ROI calculation error: {e}")
        return {
            "status": "error",
            "message": "Failed to calculate ROI",
            "error": str(e),
        }


@app.get("/api/demo-status")
async def demo_status():
    """Demo system status endpoint"""
    return {
        "status": "operational",
        "components": {
            "dual_mode_interface": "active",
            "roi_calculator": "active",
            "business_metrics": "active",
            "carrier_grade_value_prop": "active",
            "websocket_connection": (
                "active" if manager.active_connections else "inactive"
            ),
            "terminal_demo": "active",  # Added terminal demo status
        },
        "metrics": manager.metrics_cache,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/failover-simulation")
async def simulate_failover():
    """Simulate provider failover for demonstration"""
    steps = [
        {
            "timestamp": datetime.now().isoformat(),
            "step": "Detecting OpenAI latency spike (>2000ms)",
        },
        {
            "timestamp": datetime.now().isoformat(),
            "step": "Circuit breaker triggered for OpenAI",
        },
        {
            "timestamp": datetime.now().isoformat(),
            "step": "Initiating failover to Claude 3.5 Sonnet",
        },
        {
            "timestamp": datetime.now().isoformat(),
            "step": "Provider switch completed successfully",
        },
        {
            "timestamp": datetime.now().isoformat(),
            "step": "Response time normalized: 156ms",
        },
        {
            "timestamp": datetime.now().isoformat(),
            "step": "System operating normally on backup provider",
        },
    ]

    return {
        "status": "success",
        "simulation": "failover_completed",
        "steps": steps,
        "duration_ms": 847,
        "success_rate": 99.97,
    }


# Background task for metrics updates
async def metrics_updater():
    """Background task to update metrics and broadcast to WebSocket clients"""
    while True:
        await asyncio.sleep(5)  # Update every 5 seconds
        if manager.active_connections:
            await manager.broadcast_metrics_update()


@app.on_event("startup")
async def startup_event():
    """Initialize background tasks on startup"""
    logger.info("🚀 Adaptive Mind Enterprise Framework starting up...")
    logger.info(f"📁 Static files directory: {os.path.abspath('static')}")
    logger.info("🔌 WebSocket endpoint available at /ws")
    logger.info("📊 Real-time metrics broadcasting enabled")
    logger.info("🎮 Terminal demo available at /video.html")  # Added terminal demo info

    # Start background metrics updater
    asyncio.create_task(metrics_updater())


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 Adaptive Mind Enterprise Framework shutting down...")


# Development server configuration
if __name__ == "__main__":
    # Check if running in production environment
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0" if os.environ.get("RENDER") else "127.0.0.1"

    logger.info(f"🌐 Starting server on {host}:{port}")
    logger.info("📖 API documentation available at /api/docs")
    logger.info("🔄 WebSocket endpoint available at /ws")
    logger.info("🎮 Terminal demo available at /video.html")

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True if not os.environ.get("RENDER") else False,
        log_level="info",
    )
