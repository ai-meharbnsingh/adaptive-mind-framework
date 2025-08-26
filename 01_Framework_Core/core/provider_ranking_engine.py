# 01_Framework_Core/core/provider_ranking_engine.py

import sys
import logging
import threading
import asyncio  # Add this line
from datetime import datetime, timezone

# Standardized path setup relative to the current file
# Assuming current file is in PROJECT_ROOT/01_Framework_Core/antifragile_framework/core/
from pathlib import Path
from typing import Dict, List, Any

CURRENT_DIR = Path(__file__).parent
FRAMEWORK_CORE_ROOT = CURRENT_DIR.parent.parent.parent  # Points to 01_Framework_Core
TELEMETRY_PATH = FRAMEWORK_CORE_ROOT / "telemetry"


sys.path.insert(0, str(TELEMETRY_PATH))

# Import core_logger directly
try:
    from telemetry.core_logger import UniversalEventSchema, core_logger
except ImportError as e:
    logging.warning(
        f"Failed to import core telemetry for ProviderRankingEngine: {e}. Logging to console only.",
        exc_info=True,
    )

    # Fallback mock for logging if telemetry isn't available (less ideal for core but robust)
    class MockCoreLogger:
        def log(self, event):
            logging.info(
                f"MockCoreLogger: {event.get('event_type', 'N/A')} - {event.get('payload', {}).get('message', 'N/A')}"
            )

    core_logger = MockCoreLogger()

    class UniversalEventSchema:
        def __init__(self, **kwargs):
            self._data = kwargs

        def get(self, key, default=None):
            return self._data.get(key, default)

        def model_dump(self):
            return self._data  # Mock model_dump


# Enterprise logging setup for this module
logger = logging.getLogger(__name__)


class ProviderRankingEngine:
    """
    A thread-safe class that maintains a real-time performance ranking of providers
    based on an Exponential Moving Average (EMA) of their ResilienceScores.
    """

    def __init__(
        self,
        smoothing_factor: float = 0.2,
        default_score: float = 0.75,
        min_requests_threshold: int = 5,
    ):
        """
        Initializes the ProviderRankingEngine.

        Args:
            smoothing_factor (float): The alpha value for the EMA calculation.
                                      Higher values react faster to recent data. Must be between 0 and 1.
            default_score (float): A default score assigned to new providers or those
                                   below the request threshold to handle the "cold start" problem.
            min_requests_threshold (int): The number of requests a provider must have
                                          before its real EMA score is used for ranking.
        """
        if not (0.0 < smoothing_factor <= 1.0):
            raise ValueError("Smoothing factor must be between 0.0 and 1.0.")
        if not (0.0 <= default_score <= 1.0):
            raise ValueError("Default score must be between 0.0 and 1.0.")
        if not (min_requests_threshold >= 0):
            raise ValueError("Minimum requests threshold must be non-negative.")

        self._alpha = smoothing_factor
        self._default_score = default_score
        self._min_requests = min_requests_threshold

        self._lock = threading.Lock()  # Ensures thread safety for shared state
        self._provider_emas: Dict[str, float] = {}
        self._request_counts: Dict[str, int] = {}
        self.logger = core_logger
        logger.info(
            f"ProviderRankingEngine initialized with alpha={self._alpha}, default_score={self._default_score}, min_requests={self._min_requests}."
        )

    def update_provider_score(self, provider_name: str, resilience_score: float):
        """
        Updates a provider's performance score using the latest ResilienceScore.
        This method is thread-safe.

        Args:
            provider_name (str): The name of the provider to update.
            resilience_score (float): The ResilienceScore from the completed request.
                                      Expected range is 0.0 to 1.0.
        """
        if not (0.0 <= resilience_score <= 1.0):
            self.logger.log(
                UniversalEventSchema(
                    event_type="learning.score.invalid",
                    event_source=self.__class__.__name__,
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    severity="WARNING",
                    payload={
                        "provider": provider_name,
                        "received_score": resilience_score,
                        "reason": "Resilience score out of 0.0-1.0 range.",
                    },
                ).model_dump()
            )
            return

        with self._lock:
            current_count = self._request_counts.get(provider_name, 0)

            # Initialize EMA with first score or default if previous was 0 (cold start problem)
            if (
                provider_name not in self._provider_emas
                or self._provider_emas[provider_name] == 0
            ):
                new_ema = resilience_score
                self._provider_emas[provider_name] = new_ema
            else:
                # Standard EMA update
                previous_ema = self._provider_emas[provider_name]
                new_ema = (self._alpha * resilience_score) + (
                    1 - self._alpha
                ) * previous_ema
                self._provider_emas[provider_name] = new_ema

            self._request_counts[provider_name] = current_count + 1

            self.logger.log(
                UniversalEventSchema(
                    event_type="learning.score.update",
                    event_source=self.__class__.__name__,
                    timestamp_utc=datetime.now(timezone.utc).isoformat(),
                    severity="DEBUG",
                    payload={
                        "provider": provider_name,
                        "new_ema_score": round(new_ema, 4),
                        "resilience_score": round(resilience_score, 4),
                        "request_count": self._request_counts[provider_name],
                    },
                ).model_dump()
            )

    def get_ranked_providers(self) -> List[str]:
        """
        Returns a list of provider names, sorted from highest score to lowest.
        Providers with too few requests (below min_requests_threshold) are ranked by the default score.
        This method is thread-safe.

        Returns:
            List[str]: A sorted list of provider names.
        """
        with self._lock:
            # Create a list of all known providers to ensure none are missed
            all_providers = list(self._provider_emas.keys())

            def _get_effective_score(provider_name: str) -> float:
                """Helper to determine the score used for ranking based on request count."""
                current_requests = self._request_counts.get(provider_name, 0)
                if current_requests >= self._min_requests:
                    return self._provider_emas.get(provider_name, self._default_score)
                # For providers below threshold, return default_score, or their current EMA if it exists and is higher
                # This helps prevent brand new providers with one good score from being penalized too much
                return self._default_score

            sorted_providers = sorted(
                all_providers,
                key=_get_effective_score,
                reverse=True,  # Highest score first
            )
            return sorted_providers

    def get_provider_scores(self) -> Dict[str, Dict[str, Any]]:
        """
        Returns a dictionary of all providers and their current scores and request counts for observability.
        This method is thread-safe.

        Returns:
            Dict[str, Dict]: A dictionary containing detailed stats for each provider.
                            Each inner dict includes 'ema_score' and 'request_count'.
        """
        with self._lock:
            scores_data = {}
            for provider in self._provider_emas:
                scores_data[provider] = {
                    "ema_score": round(
                        self._provider_emas.get(provider, self._default_score),
                        4,
                    ),
                    "request_count": self._request_counts.get(provider, 0),
                }
            return scores_data


# Example Usage (for testing this module in isolation)
async def main():
    print("Starting ProviderRankingEngine demo...")

    # Initialize engine
    ranking_engine = ProviderRankingEngine(
        smoothing_factor=0.3, default_score=0.6, min_requests_threshold=3
    )

    print("\n--- Initial State ---")
    print(f"Ranked Providers: {ranking_engine.get_ranked_providers()}")
    print(f"Provider Scores: {ranking_engine.get_provider_scores()}")

    # Simulate some score updates
    print("\n--- Simulating Score Updates ---")
    # Provider A: Consistent good performance
    ranking_engine.update_provider_score("provider_A", 0.9)
    ranking_engine.update_provider_score("provider_A", 0.85)
    ranking_engine.update_provider_score("provider_A", 0.92)

    # Provider B: Starts poor, improves
    ranking_engine.update_provider_score("provider_B", 0.4)
    ranking_engine.update_provider_score("provider_B", 0.6)
    ranking_engine.update_provider_score("provider_B", 0.75)
    ranking_engine.update_provider_score("provider_B", 0.8)

    # Provider C: Starts good, degrades
    ranking_engine.update_provider_score("provider_C", 0.95)
    ranking_engine.update_provider_score("provider_C", 0.8)
    ranking_engine.update_provider_score("provider_C", 0.6)
    ranking_engine.update_provider_score("provider_C", 0.4)

    # Provider D: Few requests, should default score until enough data
    ranking_engine.update_provider_score("provider_D", 0.99)  # 1 request
    ranking_engine.update_provider_score("provider_D", 0.88)  # 2 requests

    # Results after updates
    print("\n--- After First Batch of Updates ---")
    print(f"Ranked Providers: {ranking_engine.get_ranked_providers()}")
    print(f"Provider Scores: {ranking_engine.get_provider_scores()}")

    # Add more data for Provider D to cross threshold
    print("\n--- Provider D crosses threshold ---")
    ranking_engine.update_provider_score(
        "provider_D", 0.95
    )  # 3 requests, now uses real EMA

    print("\n--- After Provider D crosses threshold ---")
    print(f"Ranked Providers: {ranking_engine.get_ranked_providers()}")
    print(f"Provider Scores: {ranking_engine.get_provider_scores()}")

    print("\nProviderRankingEngine demo completed.")


if __name__ == "__main__":
    # Note: No actual async operations in this file, but asyncio.run is used
    # to maintain consistency with other demo scripts' execution patterns.
    asyncio.run(main())
