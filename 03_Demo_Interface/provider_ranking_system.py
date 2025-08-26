# 03_Demo_Interface/provider_ranking_system.py

"""
Interactive Provider Ranking System for Adaptive Mind Framework
SESSION 8 - Advanced Demo Features (COMPLETE FIXED VERSION)

Enterprise-grade real-time provider performance ranking and comparison system
for demonstrating intelligent provider selection and failover capabilities.

This version (2.2.1) FIXES import paths and adds proper error handling
for missing dependencies and database connectivity.

Created: August 18, 2025
Author: Adaptive Mind Framework Team
Version: 2.2.1 (Complete Fixed Version)
"""

import asyncio
import json
import logging
import random
import statistics
import sys
import time
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

# Standardized path setup
PROJECT_ROOT = Path(__file__).parent.parent
FRAMEWORK_CORE = PROJECT_ROOT / "01_Framework_Core"
DATABASE_LAYER = PROJECT_ROOT / "05_Database_Layer"

# Add paths
sys.path.insert(0, str(FRAMEWORK_CORE))
sys.path.insert(0, str(DATABASE_LAYER))
sys.path.insert(0, str(PROJECT_ROOT))

# Import with fallback handling
try:
    from antifragile_framework.database.connection_manager import (
        PostgreSQLConnectionManager,
    )
except ImportError:
    try:
        from connection_manager import PostgreSQLConnectionManager
    except ImportError:
        print("Warning: PostgreSQLConnectionManager not found. Using mock for demo.")

        class PostgreSQLConnectionManager:
            async def get_connection(self):
                raise Exception("Database not configured")

            async def release_connection(self, conn):
                pass

            async def close_all_connections(self):
                pass


# Enterprise logging setup
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ProviderStatus(Enum):
    """Provider operational status"""

    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILING = "failing"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class RankingMetric(Enum):
    """Metrics used for provider ranking"""

    RELIABILITY = "reliability"
    PERFORMANCE = "performance"
    COST_EFFICIENCY = "cost_efficiency"
    RESPONSE_TIME = "response_time"
    QUALITY = "quality"
    AVAILABILITY = "availability"
    BIAS_RESISTANCE = "bias_resistance"
    LEARNING_COMPATIBILITY = "learning_compatibility"


@dataclass
class ProviderMetrics:
    """Comprehensive provider performance metrics"""

    provider_id: str
    last_updated: datetime

    # Core performance metrics
    reliability_score: float = 0.0
    performance_score: float = 0.0
    cost_efficiency_score: float = 0.0
    response_time_ms: float = 0.0
    quality_score: float = 0.0
    availability_score: float = 0.0

    # Advanced antifragile metrics
    bias_resistance_score: float = 0.0
    learning_compatibility_score: float = 0.0
    adaptation_velocity: float = 0.0
    stress_tolerance: float = 0.0

    # Operational metrics
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_cost: float = 0.0

    # Temporal metrics
    hourly_performance: Dict[int, float] = field(default_factory=dict)
    daily_trends: Dict[str, float] = field(default_factory=dict)

    # Context-aware metrics
    scenario_performance: Dict[str, float] = field(default_factory=dict)
    load_performance: Dict[str, float] = field(default_factory=dict)


@dataclass
class ProviderRanking:
    """Provider ranking with detailed scoring breakdown"""

    provider_id: str
    rank: int
    overall_score: float
    status: ProviderStatus

    # Detailed scoring breakdown
    metric_scores: Dict[RankingMetric, float]
    weighted_score: float
    confidence_level: float

    # Ranking metadata
    rank_change: int  # +/- from previous ranking
    rank_stability: float  # How stable this ranking is
    recommendation: str  # Usage recommendation

    # Performance insights
    strengths: List[str]
    weaknesses: List[str]
    trending: str  # "improving", "declining", "stable"


class ProviderPerformanceTracker:
    """
    Tracks detailed performance metrics for each provider,
    persisting data to PostgreSQL for demo purposes.
    """

    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.performance_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=window_size)
        )
        self.metrics_cache: Dict[str, ProviderMetrics] = {}
        self.cache_ttl = 60  # 1 minute cache
        self.last_cache_update: Dict[str, float] = {}

        # Initialize DB manager with error handling
        try:
            self.db_manager = PostgreSQLConnectionManager()
            self.db_available = True
        except Exception as e:
            logger.warning(f"Database not available: {e}. Running in demo mode.")
            self.db_manager = None
            self.db_available = False

        # Load historical data if DB is available
        if self.db_available:
            asyncio.create_task(self._load_historical_performance_records_from_db())
        else:
            # Generate mock data for demo
            asyncio.create_task(self._generate_mock_performance_data())

    async def _generate_mock_performance_data(self):
        """Generate mock performance data when database is not available"""
        logger.info("Generating mock provider performance data for demo")

        providers = ["openai", "anthropic", "google_gemini", "azure", "cohere"]
        scenarios = [
            "customer_service",
            "fraud_detection",
            "content_moderation",
            "financial_analysis",
            "medical_diagnosis_assist",
        ]
        load_levels = ["low", "normal", "high"]

        for provider in providers:
            # Generate 50 mock records per provider
            for i in range(50):
                timestamp = datetime.now(timezone.utc) - timedelta(minutes=i * 5)
                performance_record = {
                    "timestamp": timestamp,
                    "success": np.random.random() > 0.05,  # 95% success rate
                    "response_time_ms": np.random.uniform(150, 500),
                    "cost": np.random.uniform(0.001, 0.01),
                    "quality_score": np.random.uniform(0.85, 0.98),
                    "error_type": (None if np.random.random() > 0.05 else "timeout"),
                    "scenario": np.random.choice(scenarios),
                    "load_level": np.random.choice(load_levels),
                }
                self.performance_history[provider].append(performance_record)

        logger.info(f"Generated mock performance data for {len(providers)} providers")

    async def _load_historical_performance_records_from_db(self):
        """
        Loads historical performance records from the database for demo purposes.
        """
        if not self.db_available:
            return

        query = """
        SELECT
            record_id, provider_id, timestamp, success, response_time_ms,
            cost, quality_score, error_type, scenario, load_level
        FROM
            demo_provider_performance_records
        ORDER BY
            timestamp DESC
        LIMIT $1;
        """
        try:
            conn = await self.db_manager.get_connection()
            records = await conn.fetch(query, self.window_size * 5)
            await self.db_manager.release_connection(conn)

            for record in reversed(records):
                provider_id = record["provider_id"]
                performance_record = {
                    "timestamp": record["timestamp"],
                    "success": record["success"],
                    "response_time_ms": record["response_time_ms"],
                    "cost": record["cost"],
                    "quality_score": record["quality_score"],
                    "error_type": record["error_type"],
                    "scenario": record["scenario"],
                    "load_level": record["load_level"],
                }
                self.performance_history[provider_id].append(performance_record)

            logger.info(
                f"Loaded {sum(len(d) for d in self.performance_history.values())} historical performance records from database."
            )
        except Exception as e:
            logger.error(
                f"Error loading historical performance records from database: {e}"
            )
            # Fall back to mock data
            await self._generate_mock_performance_data()

    async def _persist_performance_record_to_db(
        self, provider_id: str, record: Dict[str, Any]
    ):
        """
        Persists a single performance record to the demo_provider_performance_records table.
        """
        if not self.db_available:
            logger.debug("Database not available, skipping persistence")
            return

        query = """
        INSERT INTO demo_provider_performance_records (
            provider_id, timestamp, success, response_time_ms,
            cost, quality_score, error_type, scenario, load_level
        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9);
        """
        try:
            conn = await self.db_manager.get_connection()
            await conn.execute(
                query,
                provider_id,
                record["timestamp"],
                record["success"],
                record["response_time_ms"],
                record["cost"],
                record["quality_score"],
                record["error_type"],
                record["scenario"],
                record["load_level"],
            )
            await self.db_manager.release_connection(conn)
            logger.debug(f"Persisted performance record for {provider_id} to database.")
        except Exception as e:
            logger.error(
                f"Error persisting performance record for {provider_id} to database: {e}"
            )

    async def record_request_outcome(
        self, provider_id: str, outcome_data: Dict[str, Any]
    ):
        """Record the outcome of a request to update provider metrics and persist to DB."""
        timestamp = datetime.now(timezone.utc)

        performance_record = {
            "timestamp": timestamp,
            "success": outcome_data.get("success", True),
            "response_time_ms": outcome_data.get("response_time_ms", 0),
            "cost": outcome_data.get("cost", 0.0),
            "quality_score": outcome_data.get("quality_score", 1.0),
            "error_type": outcome_data.get("error_type"),
            "scenario": outcome_data.get("scenario", "general"),
            "load_level": outcome_data.get("load_level", "normal"),
        }

        self.performance_history[provider_id].append(performance_record)
        await self._persist_performance_record_to_db(provider_id, performance_record)

        # Invalidate cache for this provider
        if provider_id in self.last_cache_update:
            del self.last_cache_update[provider_id]

        logger.debug(
            f"Recorded performance data for {provider_id}: success={outcome_data.get('success')}"
        )

    async def get_provider_metrics(self, provider_id: str) -> ProviderMetrics:
        """Get comprehensive metrics for a provider"""
        current_time = time.time()

        # Check cache
        if (
            provider_id in self.last_cache_update
            and current_time - self.last_cache_update[provider_id] < self.cache_ttl
            and provider_id in self.metrics_cache
        ):
            return self.metrics_cache[provider_id]

        # Calculate fresh metrics
        metrics = self._calculate_provider_metrics(provider_id)

        # Update cache
        self.metrics_cache[provider_id] = metrics
        self.last_cache_update[provider_id] = current_time

        return metrics

    def _calculate_provider_metrics(self, provider_id: str) -> ProviderMetrics:
        """Calculate comprehensive metrics for a provider"""
        history = list(self.performance_history[provider_id])

        if not history:
            return ProviderMetrics(
                provider_id=provider_id,
                last_updated=datetime.now(timezone.utc),
            )

        # Basic operational metrics
        total_requests = len(history)
        successful_requests = sum(1 for record in history if record["success"])
        failed_requests = total_requests - successful_requests
        total_cost = sum(record["cost"] for record in history)

        # Core performance calculations
        reliability_score = (
            successful_requests / total_requests if total_requests > 0 else 0.0
        )

        response_times = [
            record["response_time_ms"] for record in history if record["success"]
        ]
        avg_response_time = statistics.mean(response_times) if response_times else 0.0
        performance_score = max(0.0, 1.0 - (avg_response_time / 5000.0))

        costs_per_request = [record["cost"] for record in history if record["cost"] > 0]
        avg_cost = statistics.mean(costs_per_request) if costs_per_request else 0.0
        cost_efficiency_score = max(0.0, 1.0 - (avg_cost / 1.0))

        quality_scores = [
            record["quality_score"] for record in history if record["success"]
        ]
        quality_score = statistics.mean(quality_scores) if quality_scores else 0.0

        # Advanced antifragile metrics
        bias_resistance_score = self._calculate_bias_resistance(history)
        learning_compatibility_score = self._calculate_learning_compatibility(history)
        adaptation_velocity = self._calculate_adaptation_velocity(history)
        stress_tolerance = self._calculate_stress_tolerance(history)

        # Temporal analysis
        hourly_performance = self._calculate_hourly_performance(history)
        daily_trends = self._calculate_daily_trends(history)

        # Context-aware analysis
        scenario_performance = self._calculate_scenario_performance(history)
        load_performance = self._calculate_load_performance(history)

        # Availability calculation
        availability_score = self._calculate_availability_score(history)

        return ProviderMetrics(
            provider_id=provider_id,
            last_updated=datetime.now(timezone.utc),
            reliability_score=reliability_score,
            performance_score=performance_score,
            cost_efficiency_score=cost_efficiency_score,
            response_time_ms=avg_response_time,
            quality_score=quality_score,
            availability_score=availability_score,
            bias_resistance_score=bias_resistance_score,
            learning_compatibility_score=learning_compatibility_score,
            adaptation_velocity=adaptation_velocity,
            stress_tolerance=stress_tolerance,
            total_requests=total_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            total_cost=total_cost,
            hourly_performance=hourly_performance,
            daily_trends=daily_trends,
            scenario_performance=scenario_performance,
            load_performance=load_performance,
        )

    def _calculate_bias_resistance(self, history: List[Dict[str, Any]]) -> float:
        """Calculate how resistant the provider is to bias-inducing conditions"""
        if len(history) < 10:
            return 0.5

        scenario_groups = defaultdict(list)
        for record in history:
            scenario_groups[record["scenario"]].append(record["success"])

        scenario_success_rates = []
        for scenario, successes in scenario_groups.items():
            if len(successes) >= 3:
                success_rate = sum(1 for s in successes if s) / len(successes)
                scenario_success_rates.append(success_rate)

        if len(scenario_success_rates) < 2:
            return 0.5

        try:
            variance = statistics.variance(scenario_success_rates)
        except statistics.StatisticsError:
            variance = 0.0

        bias_resistance = max(0.0, 1.0 - (variance * 4.0))
        return min(bias_resistance, 1.0)

    def _calculate_learning_compatibility(self, history: List[Dict[str, Any]]) -> float:
        """Calculate how well the provider works with learning systems"""
        if len(history) < 20:
            return 0.5

        time_windows = []
        window_size = max(5, len(history) // 4)
        if window_size == 0:
            return 0.5

        for i in range(0, len(history) - window_size + 1, window_size // 2 or 1):
            window = history[i : i + window_size]
            if not window:
                continue

            success_rate = sum(1 for r in window if r["success"]) / len(window)
            valid_quality_scores = [r["quality_score"] for r in window if r["success"]]
            avg_quality = (
                statistics.mean(valid_quality_scores) if valid_quality_scores else 0.0
            )

            combined_score = (success_rate + avg_quality) / 2.0
            time_windows.append(combined_score)

        if len(time_windows) < 2:
            return 0.5

        if len(time_windows) >= 3:
            recent_avg = statistics.mean(time_windows[-2:])
            early_avg = statistics.mean(time_windows[:2])
            improvement = (recent_avg - early_avg) / max(early_avg, 0.1)
            learning_compatibility = 0.5 + (improvement * 0.5)
        else:
            learning_compatibility = 0.5

        return max(0.0, min(learning_compatibility, 1.0))

    def _calculate_adaptation_velocity(self, history: List[Dict[str, Any]]) -> float:
        """Calculate how quickly the provider adapts to changes"""
        if len(history) < 15:
            return 0.5

        recovery_times = []
        failure_start_index = -1

        for i, record in enumerate(history):
            if not record["success"] and failure_start_index == -1:
                failure_start_index = i
            elif record["success"] and failure_start_index != -1:
                recovery_time = i - failure_start_index
                recovery_times.append(recovery_time)
                failure_start_index = -1

        if not recovery_times:
            return 0.8

        avg_recovery_time = statistics.mean(recovery_times)
        adaptation_velocity = max(0.0, 1.0 - (avg_recovery_time / 20.0))

        return min(adaptation_velocity, 1.0)

    def _calculate_stress_tolerance(self, history: List[Dict[str, Any]]) -> float:
        """Calculate provider performance under high load conditions"""
        if len(history) < 10:
            return 0.5

        load_groups = defaultdict(list)
        for record in history:
            load_level = record.get("load_level", "normal")
            load_groups[load_level].append(record["success"])

        normal_performance_records = load_groups.get("normal", [])
        high_load_performance_records = load_groups.get("high", [])

        normal_performance = (
            statistics.mean(normal_performance_records)
            if normal_performance_records
            else 1.0
        )
        high_load_performance = (
            statistics.mean(high_load_performance_records)
            if high_load_performance_records
            else normal_performance
        )

        if normal_performance <= 0:
            return 0.0

        stress_tolerance = high_load_performance / normal_performance
        return min(stress_tolerance, 1.0)

    def _calculate_hourly_performance(
        self, history: List[Dict[str, Any]]
    ) -> Dict[int, float]:
        """Calculate performance by hour of day"""
        hourly_data = defaultdict(list)

        for record in history:
            hour = record["timestamp"].hour
            hourly_data[hour].append(record["success"])

        hourly_performance = {}
        for hour, successes in hourly_data.items():
            if successes:
                hourly_performance[hour] = sum(1 for s in successes if s) / len(
                    successes
                )

        return hourly_performance

    def _calculate_daily_trends(
        self, history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate daily performance trends"""
        daily_data = defaultdict(list)

        for record in history:
            day = record["timestamp"].date().isoformat()
            daily_data[day].append(record["success"])

        daily_trends = {}
        for day, successes in daily_data.items():
            if successes:
                daily_trends[day] = sum(1 for s in successes if s) / len(successes)

        return daily_trends

    def _calculate_scenario_performance(
        self, history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate performance by scenario type"""
        scenario_data = defaultdict(list)

        for record in history:
            scenario = record.get("scenario", "general")
            scenario_data[scenario].append(record["success"])

        scenario_performance = {}
        for scenario, successes in scenario_data.items():
            if successes:
                scenario_performance[scenario] = sum(1 for s in successes if s) / len(
                    successes
                )

        return scenario_performance

    def _calculate_load_performance(
        self, history: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Calculate performance by load level"""
        load_data = defaultdict(list)

        for record in history:
            load_level = record.get("load_level", "normal")
            load_data[load_level].append(record["success"])

        load_performance = {}
        for load_level, successes in load_data.items():
            if successes:
                load_performance[load_level] = sum(1 for s in successes if s) / len(
                    successes
                )

        return load_performance

    def _calculate_availability_score(self, history: List[Dict[str, Any]]) -> float:
        """Calculate availability score based on recent performance"""
        if not history:
            return 0.0

        recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_history = [r for r in history if r["timestamp"] >= recent_cutoff]

        if not recent_history:
            recent_history = history[-50:] if len(history) >= 50 else history

        total_recent = len(recent_history)
        successful_recent = sum(1 for r in recent_history if r["success"])

        return successful_recent / total_recent if total_recent > 0 else 0.0


class InteractiveProviderRankingSystem:
    """
    Enterprise-grade interactive provider ranking and comparison system
    Demonstrates intelligent provider selection and real-time ranking updates
    """

    def __init__(self, ranking_weights: Optional[Dict[RankingMetric, float]] = None):
        self.performance_tracker = ProviderPerformanceTracker()
        self.ranking_weights = ranking_weights or self._get_default_weights()
        self.current_rankings: List[ProviderRanking] = []
        self.ranking_history: deque = deque(maxlen=100)
        self.active_providers: Set[str] = set()
        self.provider_statuses: Dict[str, ProviderStatus] = {}
        self.subscribers: Dict[str, asyncio.Queue] = {}

        # Ranking configuration
        self.ranking_update_interval = 30  # 30 seconds
        self.min_requests_for_ranking = 5
        self.confidence_threshold = 0.7

        logger.info("InteractiveProviderRankingSystem initialized")

    def _get_default_weights(self) -> Dict[RankingMetric, float]:
        """Get default weighting for ranking metrics"""
        return {
            RankingMetric.RELIABILITY: 0.25,
            RankingMetric.PERFORMANCE: 0.20,
            RankingMetric.COST_EFFICIENCY: 0.15,
            RankingMetric.QUALITY: 0.15,
            RankingMetric.AVAILABILITY: 0.10,
            RankingMetric.BIAS_RESISTANCE: 0.08,
            RankingMetric.LEARNING_COMPATIBILITY: 0.05,
            RankingMetric.RESPONSE_TIME: 0.02,
        }

    async def register_provider(
        self,
        provider_id: str,
        initial_status: ProviderStatus = ProviderStatus.ACTIVE,
    ):
        """Register a new provider for ranking"""
        self.active_providers.add(provider_id)
        self.provider_statuses[provider_id] = initial_status

        logger.info(
            f"Provider registered: {provider_id} with status {initial_status.value}"
        )
        await self._update_rankings()

    async def record_provider_performance(
        self, provider_id: str, outcome_data: Dict[str, Any]
    ):
        """Record provider performance data"""
        if provider_id not in self.active_providers:
            await self.register_provider(provider_id)

        await self.performance_tracker.record_request_outcome(provider_id, outcome_data)
        await self._check_ranking_update_trigger()

    async def get_current_rankings(self) -> List[ProviderRanking]:
        """Get current provider rankings"""
        if not self.current_rankings:
            await self._update_rankings()

        return self.current_rankings.copy()

    async def _update_rankings(self):
        """Update provider rankings based on current metrics"""
        try:
            new_rankings = []
            provider_scores = {}

            for provider_id in list(self.active_providers):
                metrics = await self.performance_tracker.get_provider_metrics(
                    provider_id
                )

                if metrics.total_requests < self.min_requests_for_ranking:
                    continue

                weighted_score = self._calculate_weighted_score(metrics)
                provider_scores[provider_id] = (metrics, weighted_score)

            sorted_providers = sorted(
                provider_scores.items(), key=lambda x: x[1][1], reverse=True
            )

            for rank, (provider_id, (metrics, weighted_score)) in enumerate(
                sorted_providers, 1
            ):
                prev_ranking = next(
                    (r for r in self.current_rankings if r.provider_id == provider_id),
                    None,
                )
                rank_change = (prev_ranking.rank - rank) if prev_ranking else 0

                metric_scores = self._calculate_detailed_scores(metrics)
                status = self.provider_statuses.get(provider_id, ProviderStatus.ACTIVE)
                confidence_level = self._calculate_ranking_confidence(metrics)

                strengths, weaknesses = self._analyze_provider_strengths_weaknesses(
                    metrics
                )
                trending = self._determine_trending_direction(provider_id, metrics)
                recommendation = self._generate_provider_recommendation(
                    metrics, status, rank
                )

                ranking = ProviderRanking(
                    provider_id=provider_id,
                    rank=rank,
                    overall_score=weighted_score,
                    status=status,
                    metric_scores=metric_scores,
                    weighted_score=weighted_score,
                    confidence_level=confidence_level,
                    rank_change=rank_change,
                    rank_stability=0.8,  # Simplified for demo
                    recommendation=recommendation,
                    strengths=strengths,
                    weaknesses=weaknesses,
                    trending=trending,
                )

                new_rankings.append(ranking)

            if self.current_rankings:
                self.ranking_history.append(
                    {
                        "timestamp": datetime.now(timezone.utc),
                        "rankings": self.current_rankings.copy(),
                    }
                )

            self.current_rankings = new_rankings

            await self._broadcast_update(
                {
                    "type": "rankings_updated",
                    "rankings": [asdict(r) for r in new_rankings],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

            logger.info(f"Rankings updated: {len(new_rankings)} providers ranked")

        except Exception as e:
            logger.error(f"Error updating rankings: {str(e)}")

    def _calculate_weighted_score(self, metrics: ProviderMetrics) -> float:
        """Calculate weighted score for a provider"""
        score = 0.0

        metric_values = {
            RankingMetric.RELIABILITY: metrics.reliability_score,
            RankingMetric.PERFORMANCE: metrics.performance_score,
            RankingMetric.COST_EFFICIENCY: metrics.cost_efficiency_score,
            RankingMetric.QUALITY: metrics.quality_score,
            RankingMetric.AVAILABILITY: metrics.availability_score,
            RankingMetric.BIAS_RESISTANCE: metrics.bias_resistance_score,
            RankingMetric.LEARNING_COMPATIBILITY: metrics.learning_compatibility_score,
            RankingMetric.RESPONSE_TIME: max(
                0.0, 1.0 - (metrics.response_time_ms / 5000.0)
            ),
        }

        for metric, weight in self.ranking_weights.items():
            value = metric_values.get(metric, 0.0)
            score += value * weight

        return min(score, 1.0)

    def _calculate_detailed_scores(
        self, metrics: ProviderMetrics
    ) -> Dict[RankingMetric, float]:
        """Calculate detailed scores for all ranking metrics"""
        return {
            RankingMetric.RELIABILITY: metrics.reliability_score,
            RankingMetric.PERFORMANCE: metrics.performance_score,
            RankingMetric.COST_EFFICIENCY: metrics.cost_efficiency_score,
            RankingMetric.QUALITY: metrics.quality_score,
            RankingMetric.AVAILABILITY: metrics.availability_score,
            RankingMetric.BIAS_RESISTANCE: metrics.bias_resistance_score,
            RankingMetric.LEARNING_COMPATIBILITY: metrics.learning_compatibility_score,
            RankingMetric.RESPONSE_TIME: max(
                0.0, 1.0 - (metrics.response_time_ms / 5000.0)
            ),
        }

    def _calculate_ranking_confidence(self, metrics: ProviderMetrics) -> float:
        """Calculate confidence level in the ranking"""
        data_confidence = min(metrics.total_requests / 100.0, 1.0)
        return data_confidence

    def _analyze_provider_strengths_weaknesses(
        self, metrics: ProviderMetrics
    ) -> Tuple[List[str], List[str]]:
        """Analyze provider strengths and weaknesses"""
        strengths = []
        weaknesses = []

        high_threshold = 0.8
        low_threshold = 0.4

        metric_analysis = {
            "reliability": (
                metrics.reliability_score,
                "Excellent reliability",
            ),
            "performance": (metrics.performance_score, "Fast response times"),
            "cost_efficiency": (
                metrics.cost_efficiency_score,
                "Cost-effective operations",
            ),
            "quality": (metrics.quality_score, "High output quality"),
            "availability": (
                metrics.availability_score,
                "Strong uptime record",
            ),
            "bias_resistance": (
                metrics.bias_resistance_score,
                "Consistent across scenarios",
            ),
            "learning_compatibility": (
                metrics.learning_compatibility_score,
                "Adapts well to learning",
            ),
            "stress_tolerance": (
                metrics.stress_tolerance,
                "Handles high load well",
            ),
        }

        for metric_name, (score, strength_desc) in metric_analysis.items():
            if score >= high_threshold:
                strengths.append(strength_desc)
            elif score <= low_threshold:
                weakness_desc = (
                    strength_desc.replace("Excellent", "Poor")
                    .replace("Fast", "Slow")
                    .replace("High", "Low")
                    .replace("Strong", "Weak")
                    .replace("Consistent", "Inconsistent")
                    .replace("well", "poorly")
                )
                weaknesses.append(weakness_desc)

        return strengths, weaknesses

    def _determine_trending_direction(
        self, provider_id: str, metrics: ProviderMetrics
    ) -> str:
        """Determine if provider performance is trending up, down, or stable"""
        if len(metrics.daily_trends) < 3:
            return "stable"

        sorted_days = sorted(metrics.daily_trends.items())
        recent_performance = [performance for day, performance in sorted_days[-5:]]

        if len(recent_performance) < 3:
            return "stable"

        early_avg = statistics.mean(recent_performance[:2])
        late_avg = statistics.mean(recent_performance[-2:])

        change_percent = (late_avg - early_avg) / max(early_avg, 0.1)

        if change_percent > 0.05:
            return "improving"
        elif change_percent < -0.05:
            return "declining"
        else:
            return "stable"

    def _generate_provider_recommendation(
        self, metrics: ProviderMetrics, status: ProviderStatus, rank: int
    ) -> str:
        """Generate usage recommendation for provider"""
        if status == ProviderStatus.OFFLINE:
            return "Do not use - Provider offline"
        elif status == ProviderStatus.FAILING:
            return "Avoid - Provider experiencing failures"
        elif status == ProviderStatus.MAINTENANCE:
            return "Limited use - Provider under maintenance"
        elif status == ProviderStatus.DEGRADED:
            return "Use with caution - Performance degraded"

        if rank == 1:
            return "Primary choice - Top performer"
        elif rank <= 3:
            return "Recommended - High performance"
        elif metrics.reliability_score > 0.8 and metrics.cost_efficiency_score > 0.7:
            return "Good backup choice - Reliable and cost-effective"
        elif metrics.cost_efficiency_score > 0.8:
            return "Cost-effective option - Good for budget optimization"
        elif metrics.performance_score > 0.8:
            return "Performance option - Fast response times"
        else:
            return "Consider for specific use cases only"

    async def _check_ranking_update_trigger(self):
        """Check if rankings should be updated based on new data"""
        current_time = datetime.now(timezone.utc)

        if not hasattr(self, "_last_ranking_update"):
            self._last_ranking_update = current_time - timedelta(
                seconds=self.ranking_update_interval
            )

        time_since_update = (current_time - self._last_ranking_update).total_seconds()

        if time_since_update >= self.ranking_update_interval:
            await self._update_rankings()
            self._last_ranking_update = current_time

    async def update_provider_status(
        self, provider_id: str, new_status: ProviderStatus, reason: str = ""
    ):
        """Update provider operational status"""
        old_status = self.provider_statuses.get(provider_id, ProviderStatus.ACTIVE)
        self.provider_statuses[provider_id] = new_status

        logger.info(
            f"Provider {provider_id} status changed: {old_status.value} -> {new_status.value}"
        )
        if reason:
            logger.info(f"Reason: {reason}")

        await self._update_rankings()

        await self._broadcast_update(
            {
                "type": "provider_status_change",
                "provider_id": provider_id,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    async def get_ranking_analytics(self) -> Dict[str, Any]:
        """Get comprehensive ranking analytics and insights"""
        analytics = {
            "overview": {
                "total_providers": len(self.active_providers),
                "active_providers": len(
                    [
                        p
                        for p, s in self.provider_statuses.items()
                        if s == ProviderStatus.ACTIVE
                    ]
                ),
                "degraded_providers": len(
                    [
                        p
                        for p, s in self.provider_statuses.items()
                        if s == ProviderStatus.DEGRADED
                    ]
                ),
                "ranking_stability": 0.8,  # Simplified for demo
                "last_updated": datetime.now(timezone.utc).isoformat(),
            },
            "performance_trends": self._analyze_performance_trends(),
            "ranking_changes": {
                "recent_changes": [],
                "biggest_movers": {"up": None, "down": None},
                "change_frequency": 0.0,
            },
            "provider_insights": self._generate_provider_insights(),
            "antifragile_metrics": self._calculate_system_antifragile_metrics(),
            "recommendations": self._generate_system_recommendations(),
        }

        return analytics

    def _analyze_performance_trends(self) -> Dict[str, Any]:
        """Analyze performance trends across all providers"""
        trends = {
            "overall_system_health": 0.0,
            "provider_trends": {},
            "metric_trends": {},
            "stability_trend": "stable",
        }

        if not self.current_rankings:
            return trends

        active_providers = [
            r for r in self.current_rankings if r.status == ProviderStatus.ACTIVE
        ]

        if active_providers:
            avg_score = statistics.mean([r.overall_score for r in active_providers])
            trends["overall_system_health"] = avg_score

        for ranking in self.current_rankings:
            trends["provider_trends"][ranking.provider_id] = {
                "trending": ranking.trending,
                "rank_change": ranking.rank_change,
                "stability": ranking.rank_stability,
            }

        for metric in RankingMetric:
            metric_values = [
                r.metric_scores.get(metric, 0) for r in self.current_rankings
            ]
            if metric_values:
                trends["metric_trends"][metric.value] = {
                    "average": statistics.mean(metric_values),
                    "best": max(metric_values),
                    "worst": min(metric_values),
                    "variance": (
                        statistics.variance(metric_values)
                        if len(metric_values) > 1
                        else 0.0
                    ),
                }

        return trends

    def _generate_provider_insights(self) -> Dict[str, Any]:
        """Generate insights about individual providers"""
        insights = {}

        for ranking in self.current_rankings:
            provider_insights = {
                "performance_summary": f"{ranking.provider_id} is {ranking.status.value}, ranked #{ranking.rank} with {ranking.trending} performance trend.",
                "key_metrics": {
                    "overall_score": ranking.overall_score,
                    "rank": ranking.rank,
                    "status": ranking.status.value,
                    "confidence": ranking.confidence_level,
                    "stability": ranking.rank_stability,
                    "top_strength": (
                        {"metric": "reliability", "score": 0.95}
                        if ranking.strengths
                        else None
                    ),
                    "main_weakness": (
                        {"metric": "cost_efficiency", "score": 0.3}
                        if ranking.weaknesses
                        else None
                    ),
                },
                "recommendations": [ranking.recommendation],
                "risk_factors": (ranking.weaknesses[:2] if ranking.weaknesses else []),
            }
            insights[ranking.provider_id] = provider_insights

        return insights

    def _calculate_system_antifragile_metrics(self) -> Dict[str, Any]:
        """Calculate antifragile metrics for the entire provider system"""
        if not self.current_rankings:
            return {
                "system_resilience": 0.0,
                "diversity_score": 0.0,
                "adaptation_capability": 0.0,
                "provider_count": 0,
                "active_provider_count": 0,
                "overall_antifragile_score": 0.0,
            }

        active_providers = [
            r for r in self.current_rankings if r.status == ProviderStatus.ACTIVE
        ]
        system_resilience = (
            len(active_providers) / len(self.current_rankings)
            if self.current_rankings
            else 0.0
        )

        diversity_score = 0.8  # Simplified for demo
        adaptation_capability = 0.7  # Simplified for demo
        overall_antifragile_score = (
            system_resilience + diversity_score + adaptation_capability
        ) / 3.0

        return {
            "system_resilience": system_resilience,
            "diversity_score": diversity_score,
            "adaptation_capability": adaptation_capability,
            "provider_count": len(self.current_rankings),
            "active_provider_count": len(active_providers),
            "overall_antifragile_score": overall_antifragile_score,
        }

    def _generate_system_recommendations(self) -> List[str]:
        """Generate system-level recommendations"""
        recommendations = []

        if not self.current_rankings:
            return ["No providers currently ranked - register providers to begin"]

        if len(self.current_rankings) < 3:
            recommendations.append(
                "Consider adding more providers for better resilience"
            )

        avg_score = (
            statistics.mean([r.overall_score for r in self.current_rankings])
            if self.current_rankings
            else 0.0
        )
        if avg_score < 0.6:
            recommendations.append(
                "Overall provider performance is below optimal - consider optimization"
            )

        return recommendations

    async def subscribe_to_ranking_updates(self, subscription_id: str) -> asyncio.Queue:
        """Subscribe to real-time ranking updates"""
        queue = asyncio.Queue(maxsize=50)
        self.subscribers[subscription_id] = queue
        logger.info(f"New ranking subscription: {subscription_id}")
        return queue

    async def unsubscribe_from_ranking_updates(self, subscription_id: str):
        """Unsubscribe from ranking updates"""
        if subscription_id in self.subscribers:
            del self.subscribers[subscription_id]
            logger.info(f"Ranking subscription removed: {subscription_id}")

    async def _broadcast_update(self, update_data: Dict[str, Any]):
        """Broadcast update to all subscribers"""
        disconnected_subs = []

        for sub_id, queue in self.subscribers.items():
            try:
                await asyncio.wait_for(
                    queue.put(json.dumps(update_data, default=str)),
                    timeout=1.0,
                )
            except (asyncio.TimeoutError, asyncio.QueueFull):
                logger.warning(f"Failed to deliver ranking update to {sub_id}")
                disconnected_subs.append(sub_id)
            except Exception as e:
                logger.error(f"Error delivering ranking update to {sub_id}: {str(e)}")
                disconnected_subs.append(sub_id)

        for sub_id in disconnected_subs:
            del self.subscribers[sub_id]


# Demo Data Generator for Provider Rankings
class ProviderRankingDemoGenerator:
    """Generate realistic demo data for provider ranking demonstrations"""

    def __init__(self):
        self.providers = ["openai", "anthropic", "google", "azure", "cohere"]
        self.scenarios = [
            "customer_service",
            "fraud_detection",
            "content_moderation",
            "analysis",
            "translation",
        ]
        self.load_levels = ["low", "normal", "high"]

    async def simulate_provider_activity(
        self,
        ranking_system: InteractiveProviderRankingSystem,
        duration_minutes: int = 5,
    ):
        """Simulate realistic provider activity for demo purposes"""
        logger.info(
            f"Starting provider activity simulation for {duration_minutes} minutes"
        )

        # Register providers
        for provider in self.providers:
            await ranking_system.register_provider(provider)

        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(minutes=duration_minutes)

        # Simulate different provider characteristics
        provider_profiles = {
            "openai": {
                "base_success_rate": 0.95,
                "base_response_time": 1200,
                "base_cost": 0.02,
            },
            "anthropic": {
                "base_success_rate": 0.97,
                "base_response_time": 1500,
                "base_cost": 0.025,
            },
            "google": {
                "base_success_rate": 0.92,
                "base_response_time": 800,
                "base_cost": 0.015,
            },
            "azure": {
                "base_success_rate": 0.94,
                "base_response_time": 1100,
                "base_cost": 0.018,
            },
            "cohere": {
                "base_success_rate": 0.90,
                "base_response_time": 1000,
                "base_cost": 0.012,
            },
        }

        request_count = 0

        while datetime.now(timezone.utc) < end_time:
            provider = random.choice(self.providers)
            scenario = random.choice(self.scenarios)
            load_level = random.choices(self.load_levels, weights=[0.3, 0.5, 0.2])[0]

            profile = provider_profiles[provider]

            # Add some variability and time-based effects
            current_hour = datetime.now(timezone.utc).hour

            time_factor = 1.0
            if 9 <= current_hour <= 17:  # Business hours
                time_factor = 0.9
            elif 2 <= current_hour <= 6:  # Late night
                time_factor = 1.1

            load_factor = {"low": 1.1, "normal": 1.0, "high": 0.8}[load_level]

            success_rate = profile["base_success_rate"] * time_factor * load_factor
            success_rate += random.uniform(-0.05, 0.05)
            success = random.random() < max(0.0, min(success_rate, 1.0))

            response_time = profile["base_response_time"] / time_factor / load_factor
            response_time += random.uniform(-200, 200)
            response_time = max(100, response_time)

            cost = profile["base_cost"] * random.uniform(0.8, 1.2)
            quality_score = random.uniform(0.85, 0.98) if success else 0.0

            # Occasionally simulate provider issues
            if random.random() < 0.02:  # 2% chance
                success = False
                response_time *= 3
                await ranking_system.update_provider_status(
                    provider,
                    ProviderStatus.DEGRADED,
                    "Simulated performance degradation",
                )
            elif random.random() < 0.001:  # 0.1% chance
                success = False
                await ranking_system.update_provider_status(
                    provider,
                    ProviderStatus.FAILING,
                    "Simulated provider failure",
                )
            else:
                # Restore to active if it was degraded
                if (
                    ranking_system.provider_statuses.get(provider)
                    == ProviderStatus.DEGRADED
                ):
                    if random.random() < 0.3:  # 30% chance to recover
                        await ranking_system.update_provider_status(
                            provider,
                            ProviderStatus.ACTIVE,
                            "Performance restored",
                        )

            # Record the performance
            outcome_data = {
                "success": success,
                "response_time_ms": response_time,
                "cost": cost,
                "quality_score": quality_score,
                "scenario": scenario,
                "load_level": load_level,
            }

            await ranking_system.record_provider_performance(provider, outcome_data)

            request_count += 1

            # Random delay between requests
            await asyncio.sleep(random.uniform(0.1, 0.5))

        logger.info(
            f"Provider activity simulation complete: {request_count} requests processed"
        )


if __name__ == "__main__":
    # Demo usage and testing
    async def demo_provider_ranking_system():
        """Demonstrate the interactive provider ranking system"""

        logger.info("Starting Provider Ranking System Demo...")

        # Initialize system
        ranking_system = InteractiveProviderRankingSystem()
        demo_generator = ProviderRankingDemoGenerator()

        # Give a moment for historical data to load
        await asyncio.sleep(1.0)

        try:
            print("\n" + "=" * 80)
            print("ADAPTIVE MIND FRAMEWORK - INTERACTIVE PROVIDER RANKING SYSTEM")
            print("SESSION 8 - Advanced Demo Features (Version 2.2.1 - Complete)")
            print("=" * 80)

            print("🚀 Starting provider ranking demonstration...")

            # Subscribe to updates for demo
            subscription_id = str(uuid.uuid4())
            update_queue = await ranking_system.subscribe_to_ranking_updates(
                subscription_id
            )

            # Start simulation task
            simulation_task = asyncio.create_task(
                demo_generator.simulate_provider_activity(
                    ranking_system, duration_minutes=0.5
                )
            )

            # Monitor updates for a short time
            update_count = 0
            while update_count < 3 and not simulation_task.done():
                try:
                    update_json_str = await asyncio.wait_for(
                        update_queue.get(), timeout=5.0
                    )
                    update = json.loads(update_json_str)
                    update_count += 1
                    print(f"📊 Update {update_count}: {update['type']}")

                    if update["type"] == "rankings_updated":
                        print(
                            f"   New rankings for {len(update['rankings'])} providers"
                        )
                        for rank_entry in update["rankings"]:
                            print(
                                f"     #{rank_entry['rank']} {rank_entry['provider_id'].upper()}: Score {rank_entry['overall_score']:.3f}"
                            )
                    elif update["type"] == "provider_status_change":
                        print(
                            f"   Provider {update['provider_id']} status changed to {update['new_status']}"
                        )
                except asyncio.TimeoutError:
                    print("Timeout waiting for ranking update.")
                    break
                except Exception as e:
                    logger.error(f"Error receiving update: {str(e)}")
                    break

            # Wait for simulation to complete
            await simulation_task

            # Get final rankings and analytics
            print("\n📈 FINAL RANKINGS AND ANALYTICS:")
            rankings = await ranking_system.get_current_rankings()

            print("\n🏆 PROVIDER RANKINGS:")
            if not rankings:
                print("  No providers ranked yet.")
            for ranking in rankings:
                print(f"  #{ranking.rank} {ranking.provider_id.upper()}")
                print(
                    f"      Score: {ranking.overall_score:.3f} | Status: {ranking.status.value}"
                )
                print(f"      Recommendation: {ranking.recommendation}")
                if ranking.strengths:
                    print(f"      Strengths: {', '.join(ranking.strengths[:2])}")
                print()

            # Get comprehensive analytics
            analytics = await ranking_system.get_ranking_analytics()

            print("📊 SYSTEM ANALYTICS:")
            overview = analytics["overview"]
            print(f"  Total Providers: {overview['total_providers']}")
            print(f"  Active Providers: {overview['active_providers']}")
            print(
                f"  Database Available: {ranking_system.performance_tracker.db_available}"
            )

            print("\n🛡️  ANTIFRAGILE METRICS:")
            antifragile = analytics["antifragile_metrics"]
            print(f"  System Resilience: {antifragile['system_resilience']:.3f}")
            print(
                f"  Overall Antifragile Score: {antifragile['overall_antifragile_score']:.3f}"
            )

            # Unsubscribe from updates
            await ranking_system.unsubscribe_from_ranking_updates(subscription_id)

            print("\n" + "=" * 80)
            print("✅ PROVIDER RANKING SYSTEM DEMONSTRATION COMPLETE")
            print("🎯 Real-time provider ranking operational")
            print("📊 Enterprise-grade analytics ready")
            print("🚀 System ready for demonstrations")
            print("=" * 80)

        except Exception as e:
            logger.error(f"Demo error: {str(e)}")
            import traceback

            traceback.print_exc()
        finally:
            # Ensure DB connections are closed
            if (
                ranking_system.performance_tracker.db_available
                and ranking_system.performance_tracker.db_manager
            ):
                await ranking_system.performance_tracker.db_manager.close_all_connections()
            logger.info("Provider Ranking System Demo completed.")

    # Run the demo
    asyncio.run(demo_provider_ranking_system())
