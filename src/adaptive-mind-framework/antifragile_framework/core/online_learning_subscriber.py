# antifragile_framework/core/online_learning_subscriber.py

import logging
from typing import Dict, Any
from pydantic import ValidationError

from antifragile_framework.core.provider_ranking_engine import ProviderRankingEngine
from antifragile_framework.resilience.bias_ledger import BiasLedgerEntry
from telemetry.core_logger import core_logger, UniversalEventSchema

class OnlineLearningSubscriber:
    """
    A subscriber that listens for learning feedback events and updates the
    ProviderRankingEngine with new performance data.
    """

    def __init__(self, ranking_engine: ProviderRankingEngine):
        """
        Initializes the subscriber with a reference to the ranking engine.

        Args:
            ranking_engine (ProviderRankingEngine): The stateful engine that maintains provider scores.
        """
        self.ranking_engine = ranking_engine
        self.logger = core_logger

    def handle_event(self, event_data: Dict[str, Any]): # CORRECTED: Removed 'async'
        """
        Handles incoming events from the EventBus.

        This method safely parses the event data into a BiasLedgerEntry,
        extracts the necessary performance metrics, and updates the ranking engine.

        Args:
            event_data (Dict[str, Any]): The payload from the LEARNING_FEEDBACK_PUBLISHED event.
        """
        try:
            # Safely parse the dictionary back into a Pydantic model for type safety
            ledger_entry = BiasLedgerEntry.model_validate(event_data)

            provider = ledger_entry.final_provider
            score = ledger_entry.resilience_score

            # We only learn from requests that actually used a provider and have a score
            if provider is not None and score is not None:
                self.ranking_engine.update_provider_score(
                    provider_name=provider,
                    resilience_score=score
                )
            else:
                self.logger.log(UniversalEventSchema(
                    event_type="learning.event.skip",
                    event_source=self.__class__.__name__,
                    severity="DEBUG",
                    payload={"reason": "Ledger entry missing provider or resilience score.", "request_id": ledger_entry.request_id}
                ))

        except ValidationError as e:
            # This handles cases where the event data is malformed
            self.logger.log(UniversalEventSchema(
                event_type="learning.event.parse_error",
                event_source=self.__class__.__name__,
                severity="ERROR",
                payload={"error": str(e)}
            ))
        except Exception as e:
            # Catch any other unexpected errors during event handling
            self.logger.log(UniversalEventSchema(
                event_type="learning.event.handler_error",
                event_source=self.__class__.__name__,
                severity="CRITICAL",
                payload={"error": str(e)}
            ))