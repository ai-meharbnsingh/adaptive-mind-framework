# 03_Demo_Interface/cost_optimizer.py

"""
Advanced Cost Optimization Engine for Adaptive Mind Framework
Provides real-time cost monitoring, optimization recommendations, and business value analysis.
"""


import logging
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from enum import Enum
from typing import Any, Dict, List


# Configure logger
logger = logging.getLogger(__name__)


class CostOptimizationPriority(Enum):
    """Priority levels for cost optimization recommendations"""

    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class CostMetricType(Enum):
    """Types of cost metrics tracked"""

    TOTAL_COST = "total_cost"
    PER_REQUEST_COST = "per_request_cost"
    PROVIDER_COST = "provider_cost"
    MODEL_COST = "model_cost"
    TIME_BASED_COST = "time_based_cost"


@dataclass
class CostRecommendation:
    """Individual cost optimization recommendation"""

    title: str
    description: str
    priority: CostOptimizationPriority
    impact: str
    action_item: str
    estimated_savings_percent: float
    implementation_effort: str


class CostOptimizer:
    """
    Advanced Cost Optimization Engine for the Adaptive Mind Framework.

    Provides real-time cost monitoring, optimization recommendations,
    and business value analysis for AI infrastructure costs.
    """

    def __init__(self, metrics_collector=None, demo_data_manager=None):
        """Initialize cost optimizer with metric sources"""
        self.metrics_collector = metrics_collector
        self.demo_data_manager = demo_data_manager
        self.logger = logger

        # Cost tracking data
        self.cost_history: List[Dict[str, Any]] = []
        self.provider_costs: Dict[str, float] = {
            "openai": 0.0,
            "anthropic": 0.0,
            "google": 0.0,
        }

        # Industry benchmarks (realistic enterprise values)
        self.industry_benchmarks = {
            "avg_cost_per_request": 0.008,  # $0.008 per request
            "enterprise_target_cost": 0.005,  # $0.005 enterprise target
            "cost_efficiency_target": 85.0,  # 85% efficiency target
        }

        # Cost optimization rules
        self.optimization_rules = self._initialize_optimization_rules()

        # Simulated data for demo purposes
        self._initialize_demo_data()

    def _initialize_optimization_rules(self) -> List[Dict[str, Any]]:
        """Initialize cost optimization rules and recommendations"""
        return [
            {
                "rule_id": "model_selection",
                "title": "Optimize Model Selection",
                "description": "Use cost-efficient models for simpler tasks",
                "priority": CostOptimizationPriority.HIGH,
                "potential_savings": 35.0,
                "implementation": "Automatic model routing based on task complexity",
            },
            {
                "rule_id": "provider_routing",
                "title": "Smart Provider Routing",
                "description": "Route requests to most cost-effective providers",
                "priority": CostOptimizationPriority.MEDIUM,
                "potential_savings": 20.0,
                "implementation": "Real-time cost comparison and routing",
            },
            {
                "rule_id": "batch_processing",
                "title": "Enable Batch Processing",
                "description": "Group similar requests to reduce per-call overhead",
                "priority": CostOptimizationPriority.MEDIUM,
                "potential_savings": 15.0,
                "implementation": "Intelligent request batching and queuing",
            },
            {
                "rule_id": "caching_optimization",
                "title": "Intelligent Caching",
                "description": "Cache frequent responses to avoid redundant calls",
                "priority": CostOptimizationPriority.HIGH,
                "potential_savings": 40.0,
                "implementation": "Semantic caching with similarity matching",
            },
        ]

    def _initialize_demo_data(self):
        """Initialize demo data for cost tracking"""
        # Simulate historical cost data
        base_time = datetime.now(timezone.utc) - timedelta(hours=24)

        for i in range(24):  # 24 hours of data
            timestamp = base_time + timedelta(hours=i)

            # Simulate realistic cost progression
            base_cost = 0.005 + (random.random() * 0.003)  # $0.005-$0.008 base
            request_count = random.randint(50, 200)
            total_cost = base_cost * request_count

            self.cost_history.append(
                {
                    "timestamp": timestamp,
                    "total_cost": total_cost,
                    "request_count": request_count,
                    "avg_cost_per_request": base_cost,
                    "provider_breakdown": {
                        "openai": total_cost * random.uniform(0.3, 0.5),
                        "anthropic": total_cost * random.uniform(0.25, 0.4),
                        "google": total_cost * random.uniform(0.2, 0.35),
                    },
                }
            )

        # Update provider totals
        for entry in self.cost_history:
            for provider, cost in entry["provider_breakdown"].items():
                self.provider_costs[provider] += cost

    async def track_request_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        estimated_cost: float,
    ) -> None:
        """Track cost for a single request"""
        try:
            cost_entry = {
                "timestamp": datetime.now(timezone.utc),
                "provider": provider,
                "model": model,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "estimated_cost": estimated_cost,
                "total_tokens": input_tokens + output_tokens,
            }

            # Add to cost history
            self.cost_history.append(cost_entry)

            # Update provider totals
            if provider in self.provider_costs:
                self.provider_costs[provider] += estimated_cost

            # Keep only last 1000 entries for performance
            if len(self.cost_history) > 1000:
                self.cost_history = self.cost_history[-1000:]

            self.logger.info(
                f"Tracked cost: {provider}/{model} - ${estimated_cost:.6f}"
            )

        except Exception as e:
            self.logger.error(f"Error tracking request cost: {e}")

    async def get_cost_efficiency_summary(self) -> Dict[str, Any]:
        """Get comprehensive cost efficiency summary"""
        try:
            # Calculate totals from cost history
            total_requests = len(self.cost_history)
            total_cost = sum(
                entry.get("estimated_cost", entry.get("total_cost", 0))
                for entry in self.cost_history
            )

            avg_cost_per_request = total_cost / max(total_requests, 1)

            # Compare to industry benchmark
            benchmark_cost = self.industry_benchmarks["avg_cost_per_request"]
            cost_reduction_percent = max(
                0,
                ((benchmark_cost - avg_cost_per_request) / benchmark_cost) * 100,
            )

            return {
                "total_requests_overall": total_requests,
                "total_cost_overall_usd": round(total_cost, 4),
                "avg_cost_per_request_overall_usd": round(avg_cost_per_request, 6),
                "industry_benchmark_cost_per_request_usd": benchmark_cost,
                "cost_reduction_vs_benchmark_percent": round(cost_reduction_percent, 1),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cost_efficiency_grade": self._calculate_efficiency_grade(
                    cost_reduction_percent
                ),
                "monthly_projected_cost": round(total_cost * 30, 2),
                "annual_projected_savings": round(
                    (benchmark_cost - avg_cost_per_request) * total_requests * 365,
                    2,
                ),
            }

        except Exception as e:
            self.logger.error(f"Error generating cost efficiency summary: {e}")
            return self._get_mock_cost_summary()

    async def get_cost_breakdown_by_provider(self) -> Dict[str, Any]:
        """Get cost breakdown by provider for visualization"""
        try:
            total_cost = sum(self.provider_costs.values())

            if total_cost == 0:
                # Return demo data if no real data
                return {
                    "chart_id": "cost_by_provider_chart",
                    "title": "Cost Distribution by Provider",
                    "labels": ["OpenAI", "Anthropic", "Google"],
                    "data": [0.45, 0.35, 0.20],
                    "total_cost": 2.50,
                    "cost_percentages": [45.0, 35.0, 20.0],
                }

            # Calculate percentages
            provider_labels = []
            provider_data = []
            cost_percentages = []

            for provider, cost in self.provider_costs.items():
                if cost > 0:
                    percentage = (cost / total_cost) * 100
                    provider_labels.append(provider.title())
                    provider_data.append(round(cost, 4))
                    cost_percentages.append(round(percentage, 1))

            return {
                "chart_id": "cost_by_provider_chart",
                "title": "Cost Distribution by Provider",
                "labels": provider_labels,
                "data": provider_data,
                "total_cost": round(total_cost, 4),
                "cost_percentages": cost_percentages,
            }

        except Exception as e:
            self.logger.error(f"Error generating provider cost breakdown: {e}")
            return self._get_mock_provider_breakdown()

    async def get_cost_optimization_recommendations(
        self, current_mode: str = "hosted"
    ) -> List[Dict[str, Any]]:
        """Generate AI-driven cost optimization recommendations"""
        try:
            recommendations = []

            # Analyze current cost patterns
            cost_analysis = await self._analyze_cost_patterns()

            # Generate recommendations based on analysis
            for rule in self.optimization_rules:
                if self._should_recommend_rule(rule, cost_analysis, current_mode):
                    recommendation = {
                        "title": rule["title"],
                        "description": rule["description"],
                        "priority": rule["priority"].value,
                        "impact": f"{rule['potential_savings']:.1f}% cost reduction",
                        "action_item": rule["implementation"],
                        "estimated_savings_usd": self._calculate_savings_estimate(
                            rule["potential_savings"]
                        ),
                        "implementation_effort": self._estimate_implementation_effort(
                            rule
                        ),
                        "roi_timeline": self._estimate_roi_timeline(rule),
                    }
                    recommendations.append(recommendation)

            # Sort by priority and potential impact
            recommendations.sort(
                key=lambda x: (
                    self._priority_score(x["priority"]),
                    -float(x["estimated_savings_usd"]),
                )
            )

            return recommendations[:5]  # Return top 5 recommendations

        except Exception as e:
            self.logger.error(f"Error generating cost recommendations: {e}")
            return self._get_mock_recommendations()

    async def get_real_time_cost_metrics(self) -> Dict[str, Any]:
        """Get real-time cost metrics for dashboard"""
        try:
            # Get recent cost data (last hour)
            recent_entries = [
                entry
                for entry in self.cost_history
                if entry["timestamp"] > datetime.now(timezone.utc) - timedelta(hours=1)
            ]

            if not recent_entries:
                return self._get_mock_realtime_metrics()

            # Calculate real-time metrics
            recent_cost = sum(
                entry.get("estimated_cost", entry.get("total_cost", 0))
                for entry in recent_entries
            )
            recent_requests = len(recent_entries)

            avg_cost_per_request = recent_cost / max(recent_requests, 1)

            # Cost trend analysis
            cost_trend = self._calculate_cost_trend(recent_entries)

            return {
                "current_hourly_cost": round(recent_cost, 4),
                "requests_last_hour": recent_requests,
                "avg_cost_per_request": round(avg_cost_per_request, 6),
                "cost_trend": cost_trend,
                "projected_daily_cost": round(recent_cost * 24, 2),
                "efficiency_score": self._calculate_efficiency_score(
                    avg_cost_per_request
                ),
                "cost_alerts": self._generate_cost_alerts(
                    recent_cost, avg_cost_per_request
                ),
            }

        except Exception as e:
            self.logger.error(f"Error getting real-time cost metrics: {e}")
            return self._get_mock_realtime_metrics()

    # Helper methods

    def _calculate_efficiency_grade(self, cost_reduction_percent: float) -> str:
        """Calculate efficiency grade based on cost reduction"""
        if cost_reduction_percent >= 40:
            return "A+"
        elif cost_reduction_percent >= 30:
            return "A"
        elif cost_reduction_percent >= 20:
            return "B+"
        elif cost_reduction_percent >= 10:
            return "B"
        else:
            return "C"

    async def _analyze_cost_patterns(self) -> Dict[str, Any]:
        """Analyze cost patterns to inform recommendations"""
        try:
            if not self.cost_history:
                return {"pattern": "insufficient_data"}

            # Analyze provider usage patterns
            provider_usage = {}
            total_cost = 0

            for entry in self.cost_history[-100:]:  # Last 100 entries
                provider = entry.get("provider", "unknown")
                cost = entry.get("estimated_cost", entry.get("total_cost", 0))

                if provider not in provider_usage:
                    provider_usage[provider] = {"count": 0, "cost": 0}

                provider_usage[provider]["count"] += 1
                provider_usage[provider]["cost"] += cost
                total_cost += cost

            # Identify patterns
            patterns = {
                "dominant_provider": (
                    max(provider_usage.items(), key=lambda x: x[1]["cost"])[0]
                    if provider_usage
                    else None
                ),
                "cost_variance": self._calculate_cost_variance(),
                "peak_usage_times": self._identify_peak_times(),
                "optimization_potential": total_cost
                * 0.25,  # Assume 25% optimization potential
            }

            return patterns

        except Exception as e:
            self.logger.error(f"Error analyzing cost patterns: {e}")
            return {"pattern": "analysis_error"}

    def _should_recommend_rule(
        self,
        rule: Dict[str, Any],
        cost_analysis: Dict[str, Any],
        current_mode: str,
    ) -> bool:
        """Determine if a rule should be recommended"""
        # Basic logic - in production this would be more sophisticated
        if cost_analysis.get("pattern") == "insufficient_data":
            return random.random() > 0.5  # Random for demo

        # More likely to recommend high-impact rules
        if rule["potential_savings"] > 30:
            return True

        # Consider current mode
        if current_mode == "evaluation" and rule["rule_id"] == "provider_routing":
            return True

        return random.random() > 0.3

    def _calculate_savings_estimate(self, savings_percent: float) -> float:
        """Calculate estimated dollar savings"""
        total_cost = sum(self.provider_costs.values())
        if total_cost == 0:
            total_cost = 10.0  # Demo assumption

        return round((total_cost * savings_percent / 100), 2)

    def _estimate_implementation_effort(self, rule: Dict[str, Any]) -> str:
        """Estimate implementation effort for a rule"""
        effort_map = {
            "model_selection": "Low - Configuration change",
            "provider_routing": "Medium - Algorithm implementation",
            "batch_processing": "High - Architecture change",
            "caching_optimization": "Medium - Infrastructure setup",
        }

        return effort_map.get(rule["rule_id"], "Medium")

    def _estimate_roi_timeline(self, rule: Dict[str, Any]) -> str:
        """Estimate ROI timeline for a rule"""
        timeline_map = {
            "model_selection": "Immediate",
            "provider_routing": "1-2 weeks",
            "batch_processing": "1-2 months",
            "caching_optimization": "2-4 weeks",
        }

        return timeline_map.get(rule["rule_id"], "1 month")

    def _priority_score(self, priority: str) -> int:
        """Convert priority to numeric score for sorting"""
        priority_scores = {"Critical": 1, "High": 2, "Medium": 3, "Low": 4}
        return priority_scores.get(priority, 3)

    def _calculate_cost_variance(self) -> float:
        """Calculate cost variance over time"""
        if len(self.cost_history) < 2:
            return 0.0

        costs = [
            entry.get("estimated_cost", entry.get("total_cost", 0))
            for entry in self.cost_history[-50:]
        ]

        if not costs:
            return 0.0

        avg_cost = sum(costs) / len(costs)
        variance = sum((cost - avg_cost) ** 2 for cost in costs) / len(costs)

        return round(variance, 6)

    def _identify_peak_times(self) -> List[str]:
        """Identify peak usage times"""
        # Simplified - in production would analyze timestamps
        return ["09:00-11:00", "14:00-16:00"]

    def _calculate_cost_trend(self, entries: List[Dict[str, Any]]) -> str:
        """Calculate cost trend direction"""
        if len(entries) < 2:
            return "stable"

        recent_avg = sum(
            entry.get("estimated_cost", entry.get("total_cost", 0))
            for entry in entries[-10:]
        ) / min(len(entries), 10)

        older_avg = sum(
            entry.get("estimated_cost", entry.get("total_cost", 0))
            for entry in entries[-20:-10]
        ) / min(len(entries) - 10, 10)

        if recent_avg > older_avg * 1.1:
            return "increasing"
        elif recent_avg < older_avg * 0.9:
            return "decreasing"
        else:
            return "stable"

    def _calculate_efficiency_score(self, avg_cost_per_request: float) -> float:
        """Calculate efficiency score (0-100)"""
        benchmark = self.industry_benchmarks["avg_cost_per_request"]
        target = self.industry_benchmarks["enterprise_target_cost"]

        if avg_cost_per_request <= target:
            return 100.0
        elif avg_cost_per_request >= benchmark:
            return 50.0
        else:
            # Linear interpolation between target and benchmark
            ratio = (benchmark - avg_cost_per_request) / (benchmark - target)
            return 50.0 + (ratio * 50.0)

    def _generate_cost_alerts(
        self, recent_cost: float, avg_cost_per_request: float
    ) -> List[Dict[str, str]]:
        """Generate cost alerts based on thresholds"""
        alerts = []

        # High cost per request alert
        if avg_cost_per_request > self.industry_benchmarks["avg_cost_per_request"]:
            alerts.append(
                {
                    "type": "warning",
                    "message": f"Cost per request (${avg_cost_per_request:.6f}) exceeds industry benchmark",
                    "recommendation": "Consider model optimization or provider switching",
                }
            )

        # High hourly cost alert
        if recent_cost > 1.0:  # $1/hour threshold
            alerts.append(
                {
                    "type": "info",
                    "message": f"High usage detected: ${recent_cost:.2f}/hour",
                    "recommendation": "Monitor for cost optimization opportunities",
                }
            )

        return alerts

    # Mock data methods for fallback

    def _get_mock_cost_summary(self) -> Dict[str, Any]:
        """Get mock cost summary for fallback"""
        return {
            "total_requests_overall": 1500,
            "total_cost_overall_usd": 7.5,
            "avg_cost_per_request_overall_usd": 0.005,
            "industry_benchmark_cost_per_request_usd": 0.008,
            "cost_reduction_vs_benchmark_percent": 37.5,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "cost_efficiency_grade": "A",
            "monthly_projected_cost": 225.0,
            "annual_projected_savings": 1642.5,
        }

    def _get_mock_provider_breakdown(self) -> Dict[str, Any]:
        """Get mock provider breakdown for fallback"""
        return {
            "chart_id": "cost_by_provider_chart",
            "title": "Cost Distribution by Provider (Demo)",
            "labels": ["OpenAI", "Anthropic", "Google"],
            "data": [0.35, 0.25, 0.40],
            "total_cost": 1.0,
            "cost_percentages": [35.0, 25.0, 40.0],
        }

    def _get_mock_recommendations(self) -> List[Dict[str, Any]]:
        """Get mock recommendations for fallback"""
        return [
            {
                "title": "Optimize Model Selection",
                "description": "Use cost-efficient models for simpler tasks",
                "priority": "High",
                "impact": "35% cost reduction",
                "action_item": "Implement intelligent model routing",
                "estimated_savings_usd": 87.50,
                "implementation_effort": "Low - Configuration change",
                "roi_timeline": "Immediate",
            },
            {
                "title": "Enable Smart Caching",
                "description": "Cache frequent responses to reduce API calls",
                "priority": "Medium",
                "impact": "25% cost reduction",
                "action_item": "Deploy semantic caching layer",
                "estimated_savings_usd": 62.50,
                "implementation_effort": "Medium - Infrastructure setup",
                "roi_timeline": "2-4 weeks",
            },
        ]

    def _get_mock_realtime_metrics(self) -> Dict[str, Any]:
        """Get mock real-time metrics for fallback"""
        return {
            "current_hourly_cost": 0.25,
            "requests_last_hour": 150,
            "avg_cost_per_request": 0.00167,
            "cost_trend": "stable",
            "projected_daily_cost": 6.0,
            "efficiency_score": 85.5,
            "cost_alerts": [],
        }

    # Additional utility methods for comprehensive cost optimization

    async def get_cost_forecast(self, days: int = 30) -> Dict[str, Any]:
        """Generate cost forecast based on current trends"""
        try:
            if not self.cost_history:
                return self._get_mock_forecast(days)

            # Calculate current daily average
            recent_entries = self.cost_history[-24:]  # Last 24 hours
            daily_cost = sum(
                entry.get("estimated_cost", entry.get("total_cost", 0))
                for entry in recent_entries
            )

            # Simple linear projection
            forecast_data = []
            base_date = datetime.now(timezone.utc).date()

            for day in range(days):
                # Add some variance for realism
                day_cost = daily_cost * (1 + random.uniform(-0.1, 0.1))
                forecast_data.append(
                    {
                        "date": (base_date + timedelta(days=day)).isoformat(),
                        "projected_cost": round(day_cost, 4),
                        "confidence": max(
                            0.6, 0.95 - (day * 0.01)
                        ),  # Decreasing confidence
                    }
                )

            total_forecast = sum(day["projected_cost"] for day in forecast_data)

            return {
                "forecast_period_days": days,
                "total_projected_cost": round(total_forecast, 2),
                "daily_average": round(total_forecast / days, 4),
                "forecast_data": forecast_data,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error generating cost forecast: {e}")
            return self._get_mock_forecast(days)

    def _get_mock_forecast(self, days: int) -> Dict[str, Any]:
        """Generate mock forecast data"""
        base_date = datetime.now(timezone.utc).date()
        daily_cost = 6.0

        forecast_data = []
        for day in range(days):
            day_cost = daily_cost * (1 + random.uniform(-0.1, 0.1))
            forecast_data.append(
                {
                    "date": (base_date + timedelta(days=day)).isoformat(),
                    "projected_cost": round(day_cost, 4),
                    "confidence": max(0.6, 0.95 - (day * 0.01)),
                }
            )

        total_forecast = sum(day["projected_cost"] for day in forecast_data)

        return {
            "forecast_period_days": days,
            "total_projected_cost": round(total_forecast, 2),
            "daily_average": round(total_forecast / days, 4),
            "forecast_data": forecast_data,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def get_cost_comparison_analysis(self) -> Dict[str, Any]:
        """Get detailed cost comparison analysis between providers"""
        try:
            provider_analysis = {}

            for provider, total_cost in self.provider_costs.items():
                # Calculate provider-specific metrics
                provider_entries = [
                    entry
                    for entry in self.cost_history
                    if entry.get("provider") == provider
                ]

                if provider_entries:
                    avg_cost = sum(
                        entry.get("estimated_cost", 0) for entry in provider_entries
                    ) / len(provider_entries)
                    avg_tokens = sum(
                        entry.get("total_tokens", 0) for entry in provider_entries
                    ) / len(provider_entries)
                    cost_per_token = avg_cost / max(avg_tokens, 1)
                else:
                    avg_cost = 0
                    cost_per_token = 0

                provider_analysis[provider] = {
                    "total_cost": round(total_cost, 4),
                    "request_count": len(provider_entries),
                    "avg_cost_per_request": round(avg_cost, 6),
                    "cost_per_token": round(cost_per_token, 8),
                    "market_share": round(
                        (total_cost / max(sum(self.provider_costs.values()), 1)) * 100,
                        1,
                    ),
                }

            # Find most cost-effective provider
            best_provider = (
                min(
                    provider_analysis.items(),
                    key=lambda x: x[1]["avg_cost_per_request"],
                )[0]
                if provider_analysis
                else "unknown"
            )

            return {
                "provider_analysis": provider_analysis,
                "most_cost_effective": best_provider,
                "cost_variance": self._calculate_provider_cost_variance(),
                "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error in cost comparison analysis: {e}")
            return {"error": str(e)}

    def _calculate_provider_cost_variance(self) -> float:
        """Calculate variance in costs between providers"""
        if len(self.provider_costs) < 2:
            return 0.0

        costs = list(self.provider_costs.values())
        avg_cost = sum(costs) / len(costs)
        variance = sum((cost - avg_cost) ** 2 for cost in costs) / len(costs)

        return round(variance, 6)

    async def set_cost_budget(
        self, daily_budget: float, alert_threshold: float = 0.8
    ) -> Dict[str, Any]:
        """Set cost budget and monitoring thresholds"""
        try:
            self.daily_budget = daily_budget
            self.alert_threshold = alert_threshold

            # Calculate current daily spend
            today_entries = [
                entry
                for entry in self.cost_history
                if entry["timestamp"].date() == datetime.now(timezone.utc).date()
            ]

            current_spend = sum(
                entry.get("estimated_cost", entry.get("total_cost", 0))
                for entry in today_entries
            )

            budget_status = {
                "daily_budget": daily_budget,
                "current_spend": round(current_spend, 4),
                "remaining_budget": round(daily_budget - current_spend, 4),
                "budget_utilization_percent": round(
                    (current_spend / daily_budget) * 100, 1
                ),
                "alert_threshold": alert_threshold,
                "budget_status": (
                    "on_track"
                    if current_spend < daily_budget * alert_threshold
                    else "alert"
                ),
            }

            self.logger.info(
                f"Cost budget set: ${daily_budget}/day, current: ${current_spend:.4f}"
            )
            return budget_status

        except Exception as e:
            self.logger.error(f"Error setting cost budget: {e}")
            return {"error": str(e)}
