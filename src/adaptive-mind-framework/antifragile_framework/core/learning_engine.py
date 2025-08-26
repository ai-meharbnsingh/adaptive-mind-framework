# antifragile_framework/core/learning_engine.py

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional, Iterator
from collections import defaultdict
from pydantic import ValidationError

from telemetry.time_series_db_interface import TimeSeriesDBInterface
from telemetry import event_topics
from antifragile_framework.resilience.bias_ledger import BiasLedgerEntry
from antifragile_framework.core.schemas import ProviderPerformanceAnalysis

log = logging.getLogger(__name__)


class LearningEngine:
    """
    The LearningEngine processes historical data from the BiasLedger (via TimeSeriesDBInterface)
    to identify provider performance patterns and inform adaptive strategies.
    """

    def __init__(self, db_interface: TimeSeriesDBInterface):
        if not isinstance(db_interface, TimeSeriesDBInterface):
            raise TypeError("db_interface must be an instance of TimeSeriesDBInterface")
        self.db_interface = db_interface
        log.info("LearningEngine initialized.")

    def get_raw_bias_ledger_entries(self,
                                    start_time: datetime,
                                    end_time: datetime,
                                    batch_size: int = 1000) -> Iterator[BiasLedgerEntry]:
        """
        Retrieves raw BiasLedgerEntry events from the database within a given time range
        and attempts to deserialize them into BiasLedgerEntry Pydantic objects.
        Malformed entries are logged and skipped.
        """
        log.info(f"Retrieving BiasLedger entries from {start_time} to {end_time}...")
        raw_events_generator = self.db_interface.query_events_generator(
            event_type=event_topics.BIAS_LOG_ENTRY_CREATED,
            start_time=start_time,
            end_time=end_time,
            batch_size=batch_size
        )

        for raw_event in raw_events_generator:
            try:
                bias_ledger_entry = BiasLedgerEntry.model_validate(raw_event['payload'])
                yield bias_ledger_entry
            except ValidationError as ve:
                log.warning(
                    f"Skipping malformed BiasLedgerEntry (ValidationError) from DB. Request ID: {raw_event.get('payload', {}).get('request_id', 'N/A')}. "
                    f"Schema version: {raw_event.get('payload', {}).get('schema_version', 'N/A')}. Error: {ve}",
                    exc_info=False
                )
            except Exception as e:
                log.error(
                    f"Skipping malformed BiasLedgerEntry (General Error) from DB. Request ID: {raw_event.get('payload', {}).get('request_id', 'N/A')}. "
                    f"Schema version: {raw_event.get('payload', {}).get('schema_version', 'N/A')}. Error: {e}",
                    exc_info=True
                )

    def analyze_provider_performance(self,
                                     start_time: datetime,
                                     end_time: datetime) -> List[ProviderPerformanceAnalysis]:
        """
        Analyzes BiasLedger entries to aggregate performance metrics for each provider/model.
        """
        log.info(f"Analyzing provider performance from {start_time} to {end_time}...")

        aggregated_data = defaultdict(lambda: defaultdict(lambda: {
            'total_requests': 0,
            'successful_requests': 0,
            'total_latency_ms': 0.0,
            'error_distribution': defaultdict(int),
            'mitigation_attempted_count': 0,
            'mitigation_successful_count': 0,
            'failover_occurred_count': 0,
            'circuit_breaker_tripped_count': 0,
            'resilience_scores_sum': 0.0,
            'resilience_score_count': 0
        }))

        for entry in self.get_raw_bias_ledger_entries(start_time, end_time):
            # CORRECTED: Use the new, separate fields from the updated BiasLedgerEntry schema
            provider_name = entry.final_provider or 'unknown'
            model_name = entry.final_model or 'unknown'

            provider_model_metrics = aggregated_data[provider_name][model_name]
            provider_model_metrics['total_requests'] += 1

            if entry.outcome == 'SUCCESS' or entry.outcome == 'MITIGATED_SUCCESS':
                provider_model_metrics['successful_requests'] += 1
                provider_model_metrics['total_latency_ms'] += entry.total_latency_ms
            else:
                error_type = 'unknown_failure'
                if entry.resilience_events:
                    for event in reversed(entry.resilience_events):
                        if event.get('event_type') == event_topics.API_CALL_FAILURE and event.get('payload', {}).get('error_type'):
                            error_type = event['payload']['error_type']
                            break
                        elif event.get('event_type') == event_topics.ALL_PROVIDERS_FAILED:
                            error_type = 'all_providers_failed'
                            break
                provider_model_metrics['error_distribution'][error_type] += 1

            if entry.mitigation_attempted:
                provider_model_metrics['mitigation_attempted_count'] += 1
                if entry.mitigation_succeeded:
                    provider_model_metrics['mitigation_successful_count'] += 1

            for event in entry.resilience_events:
                if event.get('event_type') in [event_topics.PROVIDER_FAILOVER, event_topics.MODEL_FAILOVER, event_topics.API_KEY_ROTATION]:
                    provider_model_metrics['failover_occurred_count'] += 1
                elif event.get('event_type') == event_topics.CIRCUIT_TRIPPED:
                    provider_model_metrics['circuit_breaker_tripped_count'] += 1

            if entry.resilience_score is not None:
                provider_model_metrics['resilience_scores_sum'] += entry.resilience_score
                provider_model_metrics['resilience_score_count'] += 1

        results: List[ProviderPerformanceAnalysis] = []

        for provider_name, models_data in aggregated_data.items():
            for model_name, metrics in models_data.items():
                total_requests = metrics['total_requests']
                successful_requests = metrics['successful_requests']
                mitigation_attempted = metrics['mitigation_attempted_count']
                mitigation_successful = metrics['mitigation_successful_count']

                success_rate = successful_requests / total_requests if total_requests > 0 else 0.0
                avg_latency_ms = metrics['total_latency_ms'] / successful_requests if successful_requests > 0 else 0.0
                mitigation_success_rate = mitigation_successful / mitigation_attempted if mitigation_attempted > 0 else 0.0
                failover_rate = metrics['failover_occurred_count'] / total_requests if total_requests > 0 else 0.0
                circuit_breaker_trip_rate = metrics['circuit_breaker_tripped_count'] / total_requests if total_requests > 0 else 0.0
                avg_resilience_score = metrics['resilience_scores_sum'] / metrics['resilience_score_count'] if metrics['resilience_score_count'] > 0 else 1.0

                results.append(
                    ProviderPerformanceAnalysis(
                        provider_name=provider_name,
                        model_name=model_name,
                        total_requests=total_requests,
                        successful_requests=successful_requests,
                        success_rate=success_rate,
                        avg_latency_ms=avg_latency_ms,
                        error_distribution=dict(metrics['error_distribution']),
                        mitigation_attempted_count=mitigation_attempted,
                        mitigation_successful_count=mitigation_successful,
                        mitigation_success_rate=mitigation_success_rate,
                        failover_occurred_count=metrics['failover_occurred_count'],
                        failover_rate=failover_rate,
                        circuit_breaker_tripped_count=metrics['circuit_breaker_tripped_count'],
                        circuit_breaker_trip_rate=circuit_breaker_trip_rate,
                        avg_resilience_score=avg_resilience_score,
                        analysis_period_start=start_time,
                        analysis_period_end=end_time
                    )
                )
        log.info(f"Provider performance analysis complete. Generated {len(results)} analysis objects.")
        return results