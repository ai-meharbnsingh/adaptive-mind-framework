# 03_Demo_Interface/demo_data_manager.py

"""
Demo Data Manager for Adaptive Mind Framework
Manages demo scenarios, test data, and simulation data for demonstrations.
"""

import asyncio
import logging
import random
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional  # FIXED: Added missing imports
from dataclasses import dataclass
from enum import Enum

# Configure logger
logger = logging.getLogger(__name__)


class ScenarioType(Enum):
    """Types of demo scenarios"""
    GENERAL = "general"
    CUSTOMER_SERVICE = "customer_service"
    FRAUD_DETECTION = "fraud_detection"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    E_COMMERCE = "e_commerce"


@dataclass
class DemoScenario:
    """Demo scenario configuration"""
    scenario_id: str
    name: str
    description: str
    scenario_type: ScenarioType
    prompts: List[str]
    expected_providers: List[str]
    success_criteria: Dict[str, Any]
    metadata: Dict[str, Any]


class DemoDataManager:
    """
    Demo Data Manager for the Adaptive Mind Framework.

    Manages demo scenarios, test data, and simulation configurations
    for comprehensive framework demonstrations.
    """

    def __init__(self):
        """Initialize demo data manager"""
        self.logger = logger
        self.scenarios: Dict[str, DemoScenario] = {}
        self.simulation_data: Dict[str, Any] = {}
        self.is_initialized = False

        # Load default scenarios
        self._load_default_scenarios()

    async def initialize(self, timeseries_db_interface=None):
        """Initialize demo data manager with database interface"""
        try:
            self.timeseries_db_interface = timeseries_db_interface

            # Initialize simulation data
            await self._initialize_simulation_data()

            self.is_initialized = True
            self.logger.info("✅ DemoDataManager initialized successfully")

        except Exception as e:
            self.logger.error(f"❌ Failed to initialize DemoDataManager: {e}")
            self.is_initialized = False

    async def shutdown(self):
        """Shutdown demo data manager"""
        try:
            self.scenarios.clear()
            self.simulation_data.clear()
            self.is_initialized = False
            self.logger.info("DemoDataManager shutdown complete.")
        except Exception as e:
            self.logger.error(f"Error during DemoDataManager shutdown: {e}")

    def _load_default_scenarios(self) -> Dict[str, Any]:  # FIXED: Proper type annotation
        """Load default demo scenarios"""
        default_scenarios = {
            "general": DemoScenario(
                scenario_id="general",
                name="General AI Resilience",
                description="Demonstrates basic framework capabilities",
                scenario_type=ScenarioType.GENERAL,
                prompts=[
                    "Explain the benefits of AI resilience frameworks",
                    "How does intelligent failover improve system reliability?",
                    "What are the key features of antifragile AI systems?"
                ],
                expected_providers=["openai", "anthropic", "google"],
                success_criteria={
                    "max_response_time_ms": 2000,
                    "min_quality_score": 0.8,
                    "max_cost_per_request": 0.01
                },
                metadata={
                    "complexity": "basic",
                    "audience": "general",
                    "duration_minutes": 5
                }
            ),

            "customer_service": DemoScenario(
                scenario_id="customer_service",
                name="Customer Service AI",
                description="AI-powered customer support with failover protection",
                scenario_type=ScenarioType.CUSTOMER_SERVICE,
                prompts=[
                    "Help me track my order #12345",
                    "I need to return a defective product",
                    "What's your refund policy for digital items?"
                ],
                expected_providers=["openai", "anthropic"],
                success_criteria={
                    "max_response_time_ms": 1500,
                    "min_quality_score": 0.9,
                    "max_cost_per_request": 0.005
                },
                metadata={
                    "complexity": "medium",
                    "audience": "business",
                    "duration_minutes": 10,
                    "business_impact": "high"
                }
            ),

            "fraud_detection": DemoScenario(
                scenario_id="fraud_detection",
                name="Fraud Detection AI",
                description="Real-time fraud detection with intelligent routing",
                scenario_type=ScenarioType.FRAUD_DETECTION,
                prompts=[
                    "Analyze this transaction: $5000 purchase from unusual location",
                    "Review account activity for suspicious patterns",
                    "Generate fraud risk assessment report"
                ],
                expected_providers=["anthropic", "google"],
                success_criteria={
                    "max_response_time_ms": 1000,
                    "min_quality_score": 0.95,
                    "max_cost_per_request": 0.008
                },
                metadata={
                    "complexity": "high",
                    "audience": "financial",
                    "duration_minutes": 15,
                    "business_impact": "critical"
                }
            ),

            "finance": DemoScenario(
                scenario_id="finance",
                name="Financial Services AI",
                description="Financial analysis and advisory with enterprise resilience",
                scenario_type=ScenarioType.FINANCE,
                prompts=[
                    "Analyze market trends for Q4 investment strategy",
                    "Generate risk assessment for portfolio allocation",
                    "Explain regulatory compliance requirements"
                ],
                expected_providers=["anthropic", "openai"],
                success_criteria={
                    "max_response_time_ms": 3000,
                    "min_quality_score": 0.92,
                    "max_cost_per_request": 0.012
                },
                metadata={
                    "complexity": "high",
                    "audience": "enterprise",
                    "duration_minutes": 20,
                    "business_impact": "high"
                }
            ),

            "healthcare": DemoScenario(
                scenario_id="healthcare",
                name="Healthcare AI",
                description="Medical information processing with safety guarantees",
                scenario_type=ScenarioType.HEALTHCARE,
                prompts=[
                    "Explain common symptoms of seasonal allergies",
                    "What are best practices for medication management?",
                    "Describe preventive care recommendations"
                ],
                expected_providers=["anthropic", "google"],
                success_criteria={
                    "max_response_time_ms": 2500,
                    "min_quality_score": 0.95,
                    "max_cost_per_request": 0.010
                },
                metadata={
                    "complexity": "high",
                    "audience": "healthcare",
                    "duration_minutes": 25,
                    "business_impact": "critical",
                    "safety_requirements": "high"
                }
            )
        }

        # Store scenarios
        for scenario_key, scenario in default_scenarios.items():
            self.scenarios[scenario_key] = scenario

        self.logger.info(f"✅ Loaded {len(default_scenarios)} default demo scenarios")
        return default_scenarios

    async def _initialize_simulation_data(self):
        """Initialize simulation data for demos"""
        try:
            # Historical performance data
            self.simulation_data["historical_performance"] = self._generate_historical_performance()

            # Cost simulation data
            self.simulation_data["cost_data"] = self._generate_cost_simulation_data()

            # Provider performance metrics
            self.simulation_data["provider_metrics"] = self._generate_provider_metrics()

            # Bias simulation data
            self.simulation_data["bias_events"] = self._generate_bias_simulation_data()

            self.logger.info("✅ Simulation data initialized")

        except Exception as e:
            self.logger.error(f"Error initializing simulation data: {e}")

    def _generate_historical_performance(self) -> List[Dict[str, Any]]:
        """Generate historical performance data for demos"""
        base_time = datetime.now(timezone.utc) - timedelta(hours=24)
        performance_data = []

        for i in range(24):  # 24 hours of data
            timestamp = base_time + timedelta(hours=i)

            # Simulate realistic performance patterns
            base_response_time = 250 + random.uniform(-50, 100)
            success_rate = 0.95 + random.uniform(-0.05, 0.05)

            performance_data.append({
                "timestamp": timestamp.isoformat(),
                "avg_response_time_ms": round(base_response_time, 2),
                "success_rate": round(success_rate, 4),
                "requests_processed": random.randint(50, 200),
                "cost_per_request": round(random.uniform(0.002, 0.008), 6)
            })

        return performance_data

    def _generate_cost_simulation_data(self) -> Dict[str, Any]:
        """Generate cost simulation data"""
        return {
            "total_cost_24h": round(random.uniform(15.0, 25.0), 2),
            "avg_cost_per_request": round(random.uniform(0.004, 0.007), 6),
            "cost_by_provider": {
                "openai": round(random.uniform(8.0, 12.0), 2),
                "anthropic": round(random.uniform(6.0, 10.0), 2),
                "google": round(random.uniform(4.0, 8.0), 2)
            },
            "cost_trend": "decreasing",
            "projected_monthly_cost": round(random.uniform(450.0, 650.0), 2)
        }

    def _generate_provider_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Generate provider performance metrics"""
        providers = ["openai", "anthropic", "google"]
        metrics = {}

        for provider in providers:
            metrics[provider] = {
                "avg_response_time_ms": round(random.uniform(200, 400), 2),
                "success_rate": round(random.uniform(0.92, 0.99), 4),
                "cost_efficiency": round(random.uniform(0.7, 0.95), 3),
                "reliability_score": round(random.uniform(0.85, 0.98), 3),
                "total_requests": random.randint(100, 500),
                "last_updated": datetime.now(timezone.utc).isoformat()
            }

        return metrics

    def _generate_bias_simulation_data(self) -> List[Dict[str, Any]]:
        """Generate bias event simulation data"""
        bias_events = []
        base_time = datetime.now(timezone.utc) - timedelta(hours=12)

        for i in range(10):  # 10 simulated bias events
            event_time = base_time + timedelta(hours=i * 1.2)

            bias_events.append({
                "event_id": str(uuid.uuid4()),
                "timestamp": event_time.isoformat(),
                "bias_type": random.choice(["cost_bias", "performance_bias", "reliability_bias"]),
                "provider": random.choice(["openai", "anthropic", "google"]),
                "impact_level": random.choice(["low", "medium", "high"]),
                "confidence_score": round(random.uniform(0.7, 0.95), 3),
                "description": f"Simulated bias event #{i + 1} for demonstration"
            })

        return bias_events

    # Public interface methods

    async def get_scenario(self, scenario_id: str) -> Optional[DemoScenario]:
        """Get a specific demo scenario"""
        return self.scenarios.get(scenario_id)

    async def get_all_scenarios(self) -> Dict[str, DemoScenario]:
        """Get all available demo scenarios"""
        return self.scenarios.copy()

    async def get_scenario_prompts(self, scenario_id: str) -> List[str]:
        """Get prompts for a specific scenario"""
        scenario = self.scenarios.get(scenario_id)
        return scenario.prompts if scenario else []

    async def get_simulation_data(self, data_type: str) -> Optional[Any]:
        """Get simulation data by type"""
        return self.simulation_data.get(data_type)

    async def add_custom_scenario(self, scenario: DemoScenario) -> bool:
        """Add a custom demo scenario"""
        try:
            self.scenarios[scenario.scenario_id] = scenario
            self.logger.info(f"✅ Added custom scenario: {scenario.scenario_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding custom scenario: {e}")
            return False

    async def update_simulation_data(self, data_type: str, data: Any) -> bool:
        """Update simulation data"""
        try:
            self.simulation_data[data_type] = data
            self.logger.info(f"✅ Updated simulation data: {data_type}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating simulation data: {e}")
            return False

    async def get_scenario_success_criteria(self, scenario_id: str) -> Dict[str, Any]:
        """Get success criteria for a scenario"""
        scenario = self.scenarios.get(scenario_id)
        return scenario.success_criteria if scenario else {}

    async def validate_scenario_result(self, scenario_id: str, result_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate demo result against scenario criteria"""
        criteria = await self.get_scenario_success_criteria(scenario_id)
        if not criteria:
            return {"valid": True, "message": "No criteria defined"}

        validation_results = {}
        is_valid = True

        # Check response time
        if "max_response_time_ms" in criteria:
            response_time = result_data.get("response_time_ms", 0)
            time_valid = response_time <= criteria["max_response_time_ms"]
            validation_results["response_time"] = {
                "valid": time_valid,
                "actual": response_time,
                "threshold": criteria["max_response_time_ms"]
            }
            is_valid = is_valid and time_valid

        # Check quality score
        if "min_quality_score" in criteria:
            quality_score = result_data.get("quality_score", 1.0)
            quality_valid = quality_score >= criteria["min_quality_score"]
            validation_results["quality"] = {
                "valid": quality_valid,
                "actual": quality_score,
                "threshold": criteria["min_quality_score"]
            }
            is_valid = is_valid and quality_valid

        # Check cost
        if "max_cost_per_request" in criteria:
            cost = result_data.get("cost_estimate", 0)
            cost_valid = cost <= criteria["max_cost_per_request"]
            validation_results["cost"] = {
                "valid": cost_valid,
                "actual": cost,
                "threshold": criteria["max_cost_per_request"]
            }
            is_valid = is_valid and cost_valid

        return {
            "valid": is_valid,
            "criteria_met": validation_results,
            "overall_score": sum(1 for r in validation_results.values() if r["valid"]) / max(len(validation_results), 1)
        }

    async def get_demo_statistics(self) -> Dict[str, Any]:
        """Get overall demo statistics"""
        return {
            "total_scenarios": len(self.scenarios),
            "scenario_types": list(set(s.scenario_type.value for s in self.scenarios.values())),
            "total_prompts": sum(len(s.prompts) for s in self.scenarios.values()),
            "simulation_data_types": list(self.simulation_data.keys()),
            "is_initialized": self.is_initialized,
            "last_updated": datetime.now(timezone.utc).isoformat()
        }