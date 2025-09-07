# tests/core/test_learning_engine.py

import unittest
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import MagicMock, patch
from antifragile_framework.core.learning_engine import LearningEngine
from antifragile_framework.resilience.bias_ledger import BiasLedgerEntry
from antifragile_framework.core.schemas import ProviderPerformanceAnalysis  # FIXED IMPORT PATH
from telemetry import event_topics
from telemetry.time_series_db_interface import TimeSeriesDBInterface


class TestLearningEngine(unittest.TestCase):

    def setUp(self):
        self.mock_db_interface = MagicMock(spec=TimeSeriesDBInterface)
        # Explicitly add the required methods to the mock
        self.mock_db_interface.write_event = MagicMock()
        self.mock_db_interface.read_events = MagicMock()

        # FIXED: Make query_events_generator a proper MagicMock
        self.mock_db_interface.query_events_generator = MagicMock()

        self.learning_engine = LearningEngine(self.mock_db_interface)
        self.start_time = datetime(2025, 8, 1, 0, 0, 0, tzinfo=timezone.utc)
        self.end_time = datetime(2025, 8, 2, 0, 0, 0, tzinfo=timezone.utc)

    def _create_mock_raw_event(
            self, bias_ledger_entry_dict: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "timestamp_utc": datetime.fromisoformat(
                bias_ledger_entry_dict["timestamp_utc"]
            ),
            "event_type": event_topics.BIAS_LOG_ENTRY_CREATED,
            "event_source": "BiasLedger",
            "severity": "INFO",
            "payload": bias_ledger_entry_dict,
        }

    def test_get_raw_bias_ledger_entries_valid_data(self):
        mock_entry_data = [
            BiasLedgerEntry(
                request_id="req1",
                timestamp_utc=self.start_time.isoformat(),
                initial_prompt_hash="h1",
                initial_prompt_preview="p1",
                outcome="SUCCESS",
                total_latency_ms=100.0,
                total_api_calls=1,
                resilience_events=[],
                mitigation_attempted=False,
                final_provider="openai",
                final_model="gpt-4o",
                schema_version=4,
                initial_selection_mode="VALUE_DRIVEN",
                preferred_provider_requested=None,
                failover_reason=None,
                cost_cap_enforced=False,
                cost_cap_skip_reason=None,
            ).model_dump(),
            BiasLedgerEntry(
                request_id="req2",
                timestamp_utc=(self.start_time + timedelta(hours=1)).isoformat(),
                initial_prompt_hash="h2",
                initial_prompt_preview="p2",
                outcome="FAILURE",
                total_latency_ms=200.0,
                total_api_calls=1,
                resilience_events=[],
                mitigation_attempted=False,
                final_provider="anthropic",
                final_model="claude-3",
                schema_version=4,
                initial_selection_mode="VALUE_DRIVEN",
                preferred_provider_requested=None,
                failover_reason=None,
                cost_cap_enforced=False,
                cost_cap_skip_reason=None,
            ).model_dump(),
        ]

        # Create mock events
        mock_events = [self._create_mock_raw_event(data) for data in mock_entry_data]
        print(f"DEBUG: Created {len(mock_events)} mock events")

        # FIXED: Use proper mock setup for a callable function
        self.mock_db_interface.query_events_generator.return_value = iter(mock_events)

        # Call the method and debug the result
        print("DEBUG: About to call get_raw_bias_ledger_entries")
        entries = list(
            self.learning_engine.get_raw_bias_ledger_entries(
                self.start_time, self.end_time
            )
        )
        print(f"DEBUG: Got {len(entries)} entries back")
        if entries:
            print(f"DEBUG: First entry type: {type(entries[0])}")

        self.assertEqual(len(entries), 2)
        # FIXED: Check the structure - entries should be BiasLedgerEntry objects
        self.assertIsInstance(entries[0], BiasLedgerEntry)
        self.assertIsInstance(entries[1], BiasLedgerEntry)
        self.assertEqual(entries[0].request_id, "req1")
        self.assertEqual(entries[1].request_id, "req2")
        self.assertEqual(entries[0].final_provider, "openai")
        self.assertEqual(entries[1].final_provider, "anthropic")

    @patch("antifragile_framework.core.learning_engine.log")
    def test_get_raw_bias_ledger_entries_malformed_data_skipped(self, mock_log):
        malformed_entry_data = {
            "request_id": "malformed_req",
            "timestamp_utc": self.start_time.isoformat(),
            "initial_prompt_preview": "preview",
            "outcome": "SUCCESS",
            "total_latency_ms": 100.0,
            "total_api_calls": 1,
            "resilience_events": [],
            "mitigation_attempted": False,
            "final_provider": "openai",
            "final_model": "gpt-4o",
            "schema_version": 2,  # This is purposefully old/malformed
        }
        valid_entry_data = BiasLedgerEntry(
            request_id="valid_req",
            timestamp_utc=self.start_time.isoformat(),
            initial_prompt_hash="hV",
            initial_prompt_preview="pV",
            outcome="SUCCESS",
            total_latency_ms=100.0,
            total_api_calls=1,
            resilience_events=[],
            mitigation_attempted=False,
            final_provider="openai",
            final_model="gpt-4o",
            schema_version=4,  # UPDATED
            initial_selection_mode="VALUE_DRIVEN",  # NEW
            preferred_provider_requested=None,  # NEW
            failover_reason=None,  # NEW
            cost_cap_enforced=False,  # NEW
            cost_cap_skip_reason=None,  # NEW
        ).model_dump()

        mock_events = [
            self._create_mock_raw_event(malformed_entry_data),
            self._create_mock_raw_event(valid_entry_data),
        ]
        self.mock_db_interface.query_events_generator.return_value = iter(mock_events)

        entries = list(
            self.learning_engine.get_raw_bias_ledger_entries(
                self.start_time, self.end_time
            )
        )
        self.assertEqual(len(entries), 1)
        self.assertIsInstance(entries[0], BiasLedgerEntry)
        self.assertEqual(entries[0].request_id, "valid_req")
        mock_log.warning.assert_called_once()
        self.assertIn(
            "Skipping malformed BiasLedgerEntry (ValidationError)",
            mock_log.warning.call_args[0][0],
        )

    # TEST RESTORED
    @patch("antifragile_framework.core.learning_engine.log")
    def test_get_raw_bias_ledger_entries_different_schema_version(self, mock_log):
        # This test ensures that even if an OLD schema_version comes from the DB,
        # it will be correctly passed through if it matches the current BiasLedgerEntry model's validation requirements
        # for a specific schema_version field. The model_validate will still require all current fields.
        mock_entry_v2_data = BiasLedgerEntry(
            request_id="req_v2",
            timestamp_utc=self.start_time.isoformat(),
            initial_prompt_hash="h1",
            initial_prompt_preview="p1",
            outcome="SUCCESS",
            total_latency_ms=100.0,
            total_api_calls=1,
            resilience_events=[],
            mitigation_attempted=False,
            final_provider="openai",
            final_model="gpt-4o",
            # This is specifically testing an older schema version if it's still parsable
            schema_version=2,
            # NEW: must be included for current model validation
            initial_selection_mode="VALUE_DRIVEN",
            preferred_provider_requested=None,  # NEW
            failover_reason=None,  # NEW
            cost_cap_enforced=False,  # NEW
            cost_cap_skip_reason=None,  # NEW
        ).model_dump()

        mock_events = [self._create_mock_raw_event(mock_entry_v2_data)]
        self.mock_db_interface.query_events_generator.return_value = iter(mock_events)

        entries = list(
            self.learning_engine.get_raw_bias_ledger_entries(
                self.start_time, self.end_time
            )
        )
        self.assertEqual(len(entries), 1)
        self.assertIsInstance(entries[0], BiasLedgerEntry)
        # We assert on the actual schema_version from the mocked data, not the current model's default
        self.assertEqual(entries[0].schema_version, 2)
        mock_log.warning.assert_not_called()

    def test_analyze_provider_performance_basic_success(self):
        entry1_data = BiasLedgerEntry(
            request_id="req1",
            timestamp_utc=self.start_time.isoformat(),
            initial_prompt_hash="h1",
            initial_prompt_preview="p1",
            outcome="SUCCESS",
            total_latency_ms=100.0,
            total_api_calls=1,
            resilience_events=[],
            mitigation_attempted=False,
            final_provider="openai",
            final_model="gpt-4o",
            schema_version=4,  # UPDATED
            initial_selection_mode="VALUE_DRIVEN",  # NEW
            preferred_provider_requested=None,  # NEW
            failover_reason=None,  # NEW
            cost_cap_enforced=False,  # NEW
            cost_cap_skip_reason=None,  # NEW
        ).model_dump()
        entry2_data = BiasLedgerEntry(
            request_id="req2",
            timestamp_utc=(self.start_time + timedelta(minutes=1)).isoformat(),
            initial_prompt_hash="h2",
            initial_prompt_preview="p2",
            outcome="SUCCESS",
            total_latency_ms=150.0,
            total_api_calls=1,
            resilience_events=[],
            mitigation_attempted=False,
            final_provider="openai",
            final_model="gpt-4o",
            schema_version=4,  # UPDATED
            initial_selection_mode="VALUE_DRIVEN",  # NEW
            preferred_provider_requested=None,  # NEW
            failover_reason=None,  # NEW
            cost_cap_enforced=False,  # NEW
            cost_cap_skip_reason=None,  # NEW
        ).model_dump()

        mock_events = [
            self._create_mock_raw_event(entry1_data),
            self._create_mock_raw_event(entry2_data),
        ]
        self.mock_db_interface.query_events_generator.return_value = iter(mock_events)

        analyses = self.learning_engine.analyze_provider_performance(
            self.start_time, self.end_time
        )
        self.assertEqual(len(analyses), 1)
        self.assertIsInstance(analyses[0], ProviderPerformanceAnalysis)
        analysis = analyses[0]
        # RESTORED FULL ASSERTIONS
        self.assertEqual(analysis.provider_name, "openai")
        self.assertEqual(analysis.model_name, "gpt-4o")
        self.assertEqual(analysis.total_requests, 2)
        self.assertEqual(analysis.successful_requests, 2)
        self.assertEqual(analysis.success_rate, 1.0)
        self.assertEqual(analysis.avg_latency_ms, 125.0)
        self.assertEqual(analysis.error_distribution, {})
        self.assertEqual(analysis.mitigation_attempted_count, 0)
        self.assertEqual(analysis.failover_occurred_count, 0)
        self.assertEqual(analysis.circuit_breaker_tripped_count, 0)
        self.assertEqual(analysis.avg_resilience_score, 1.0)

    def test_analyze_provider_performance_mixed_outcomes_and_metrics(self):
        # Data updated to new schema
        entry1 = BiasLedgerEntry(
            request_id="req1",
            timestamp_utc=self.start_time.isoformat(),
            initial_prompt_hash="h1",
            initial_prompt_preview="p1",
            outcome="SUCCESS",
            total_latency_ms=100.0,
            total_api_calls=1,
            resilience_events=[],
            mitigation_attempted=False,
            final_provider="openai",
            final_model="gpt-4o",
            resilience_score=0.9,
            schema_version=4,  # UPDATED
            initial_selection_mode="VALUE_DRIVEN",  # NEW
            preferred_provider_requested=None,  # NEW
            failover_reason=None,  # NEW
            cost_cap_enforced=False,  # NEW
            cost_cap_skip_reason=None,  # NEW
        ).model_dump()
        entry2 = BiasLedgerEntry(
            request_id="req2",
            timestamp_utc=(self.start_time + timedelta(minutes=1)).isoformat(),
            initial_prompt_hash="h2",
            initial_prompt_preview="p2",
            outcome="FAILURE",
            total_latency_ms=50.0,
            total_api_calls=1,
            resilience_events=[
                {
                    "event_type": event_topics.API_CALL_FAILURE,
                    "payload": {"error_type": "rate_limit"},
                }
            ],
            mitigation_attempted=False,
            final_provider="openai",
            final_model="gpt-4o",
            resilience_score=0.5,
            schema_version=4,  # UPDATED
            initial_selection_mode="VALUE_DRIVEN",  # NEW
            preferred_provider_requested=None,  # NEW
            failover_reason="API_ERROR_RATE_LIMIT",  # NEW
            cost_cap_enforced=False,  # NEW
            cost_cap_skip_reason=None,  # NEW
        ).model_dump()
        entry3 = BiasLedgerEntry(
            request_id="req3",
            timestamp_utc=(self.start_time + timedelta(minutes=2)).isoformat(),
            initial_prompt_hash="h3",
            initial_prompt_preview="p3",
            outcome="MITIGATED_SUCCESS",
            total_latency_ms=300.0,
            total_api_calls=2,
            resilience_events=[{"event_type": event_topics.PROVIDER_FAILOVER}],
            mitigation_attempted=True,
            mitigation_succeeded=True,
            final_provider="anthropic",
            final_model="claude-3",
            resilience_score=0.7,
            schema_version=4,  # UPDATED
            initial_selection_mode="VALUE_DRIVEN",  # NEW
            preferred_provider_requested=None,  # NEW
            failover_reason="PROVIDER_FAILOVER",  # NEW
            cost_cap_enforced=False,  # NEW
            cost_cap_skip_reason=None,  # NEW
        ).model_dump()
        entry4 = BiasLedgerEntry(
            request_id="req4",
            timestamp_utc=(self.start_time + timedelta(minutes=3)).isoformat(),
            initial_prompt_hash="h4",
            initial_prompt_preview="p4",
            outcome="SUCCESS",
            total_latency_ms=250.0,
            total_api_calls=2,
            resilience_events=[
                {"event_type": event_topics.CIRCUIT_TRIPPED},
                {"event_type": event_topics.MODEL_FAILOVER},
            ],
            mitigation_attempted=False,
            final_provider="google_gemini",
            final_model="gemini-pro",
            resilience_score=0.8,
            schema_version=4,  # UPDATED
            initial_selection_mode="VALUE_DRIVEN",  # NEW
            preferred_provider_requested=None,  # NEW
            failover_reason="CIRCUIT_TRIPPED_MODEL_FAILOVER",  # NEW
            cost_cap_enforced=False,  # NEW
            cost_cap_skip_reason=None,  # NEW
        ).model_dump()

        mock_events = [
            self._create_mock_raw_event(e) for e in [entry1, entry2, entry3, entry4]
        ]
        self.mock_db_interface.query_events_generator.return_value = iter(mock_events)

        analyses = self.learning_engine.analyze_provider_performance(
            self.start_time, self.end_time
        )
        self.assertEqual(len(analyses), 3)

        # Ensure all analyses are ProviderPerformanceAnalysis objects
        for analysis in analyses:
            self.assertIsInstance(analysis, ProviderPerformanceAnalysis)

        # RESTORED FULL ASSERTIONS
        openai_analysis = next(a for a in analyses if a.provider_name == "openai")
        self.assertEqual(openai_analysis.total_requests, 2)
        self.assertEqual(openai_analysis.successful_requests, 1)
        self.assertEqual(openai_analysis.success_rate, 0.5)
        self.assertEqual(openai_analysis.avg_latency_ms, 100.0)
        self.assertEqual(openai_analysis.error_distribution, {"rate_limit": 1})
        self.assertEqual(openai_analysis.avg_resilience_score, (0.9 + 0.5) / 2)

        anthropic_analysis = next(a for a in analyses if a.provider_name == "anthropic")
        self.assertEqual(anthropic_analysis.total_requests, 1)
        self.assertEqual(anthropic_analysis.successful_requests, 1)
        self.assertEqual(anthropic_analysis.mitigation_attempted_count, 1)
        self.assertEqual(anthropic_analysis.mitigation_successful_count, 1)
        self.assertEqual(anthropic_analysis.mitigation_success_rate, 1.0)
        self.assertEqual(anthropic_analysis.failover_occurred_count, 1)
        self.assertEqual(anthropic_analysis.failover_rate, 1.0)
        self.assertEqual(anthropic_analysis.avg_resilience_score, 0.7)

        google_analysis = next(
            a for a in analyses if a.provider_name == "google_gemini"
        )
        self.assertEqual(google_analysis.total_requests, 1)
        self.assertEqual(google_analysis.successful_requests, 1)
        self.assertEqual(google_analysis.failover_occurred_count, 1)
        self.assertEqual(google_analysis.failover_rate, 1.0)
        self.assertEqual(google_analysis.circuit_breaker_tripped_count, 1)
        self.assertEqual(google_analysis.circuit_breaker_trip_rate, 1.0)
        self.assertEqual(google_analysis.avg_resilience_score, 0.8)

    # TEST RESTORED
    def test_analyze_provider_performance_zero_total_requests(self):
        self.mock_db_interface.query_events_generator.return_value = iter([])
        analyses = self.learning_engine.analyze_provider_performance(
            self.start_time, self.end_time
        )
        self.assertEqual(len(analyses), 0)

        entry_failure_only = BiasLedgerEntry(
            request_id="req_fail_only",
            timestamp_utc=self.start_time.isoformat(),
            initial_prompt_hash="hF",
            initial_prompt_preview="pF",
            outcome="FAILURE",
            total_latency_ms=0.0,
            total_api_calls=1,
            resilience_events=[],
            mitigation_attempted=False,
            final_provider="test_provider",
            final_model="test_model",
            resilience_score=0.2,
            schema_version=4,  # UPDATED
            initial_selection_mode="VALUE_DRIVEN",  # NEW
            preferred_provider_requested=None,  # NEW
            failover_reason="FAILURE_REASON_FOR_TEST",  # NEW
            cost_cap_enforced=False,  # NEW
            cost_cap_skip_reason=None,  # NEW
        ).model_dump()

        mock_events = [self._create_mock_raw_event(entry_failure_only)]
        self.mock_db_interface.query_events_generator.return_value = iter(mock_events)

        analyses = self.learning_engine.analyze_provider_performance(
            self.start_time, self.end_time
        )
        self.assertEqual(len(analyses), 1)
        self.assertIsInstance(analyses[0], ProviderPerformanceAnalysis)
        analysis = analyses[0]
        self.assertEqual(analysis.total_requests, 1)
        self.assertEqual(analysis.successful_requests, 0)
        self.assertEqual(analysis.success_rate, 0.0)
        self.assertEqual(analysis.avg_latency_ms, 0.0)
        self.assertEqual(analysis.avg_resilience_score, 0.2)

    def test_analyze_provider_performance_no_resilience_score(self):
        entry_no_score = BiasLedgerEntry(
            request_id="req_no_score",
            timestamp_utc=self.start_time.isoformat(),
            initial_prompt_hash="hns",
            initial_prompt_preview="pns",
            outcome="SUCCESS",
            total_latency_ms=100.0,
            total_api_calls=1,
            resilience_events=[],
            mitigation_attempted=False,
            final_provider="openai",
            final_model="gpt-4o",
            resilience_score=None,
            schema_version=4,  # UPDATED
            initial_selection_mode="VALUE_DRIVEN",  # NEW
            preferred_provider_requested=None,  # NEW
            failover_reason=None,  # NEW
            cost_cap_enforced=False,  # NEW
            cost_cap_skip_reason=None,  # NEW
        ).model_dump()

        mock_events = [self._create_mock_raw_event(entry_no_score)]
        self.mock_db_interface.query_events_generator.return_value = iter(mock_events)

        analyses = self.learning_engine.analyze_provider_performance(
            self.start_time, self.end_time
        )
        self.assertEqual(len(analyses), 1)
        self.assertIsInstance(analyses[0], ProviderPerformanceAnalysis)
        self.assertEqual(analyses[0].avg_resilience_score, 1.0)