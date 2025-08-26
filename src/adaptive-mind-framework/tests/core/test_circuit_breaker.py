# tests/core/test_circuit_breaker.py

import pytest
import time
import threading
from antifragile_framework.core.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerError,
    CircuitBreakerRegistry
)


# --- Fixtures ---

@pytest.fixture
def breaker_config():
    """Provides a standard, fast configuration for testing circuit breakers."""
    return {
        "failure_threshold": 2,
        "reset_timeout_seconds": 0.1  # Use a very short timeout for tests
    }


@pytest.fixture
def breaker(breaker_config):
    """Provides a CircuitBreaker instance with a fast test configuration."""
    return CircuitBreaker("test_service", **breaker_config)


# --- State Transition and Basic Logic Tests ---

def test_initial_state_is_closed(breaker: CircuitBreaker):
    assert breaker.state == CircuitBreakerState.CLOSED
    breaker.check()  # Should not raise an error


def test_trips_to_open_after_threshold_failures(breaker: CircuitBreaker):
    breaker.record_failure()
    assert breaker.state == CircuitBreakerState.CLOSED

    breaker.record_failure()  # This should meet the threshold of 2
    assert breaker.state == CircuitBreakerState.OPEN

    with pytest.raises(CircuitBreakerError, match="CircuitBreaker for 'test_service' is open."):
        breaker.check()


def test_success_resets_failure_count(breaker: CircuitBreaker):
    breaker.record_failure()
    assert breaker.failure_count == 1

    breaker.record_success()
    assert breaker.failure_count == 0
    assert breaker.state == CircuitBreakerState.CLOSED


def test_moves_to_half_open_after_timeout(breaker: CircuitBreaker):
    breaker.record_failure()
    breaker.record_failure()  # Breaker is now OPEN

    time.sleep(breaker._reset_timeout_seconds + 0.05)  # Wait for reset timeout

    breaker.check()  # Should move to HALF_OPEN and not raise
    assert breaker.state == CircuitBreakerState.HALF_OPEN


def test_failure_in_half_open_state_reopens_circuit(breaker: CircuitBreaker):
    breaker.record_failure()
    breaker.record_failure()  # OPEN

    time.sleep(breaker._reset_timeout_seconds + 0.05)
    breaker.check()
    assert breaker.state == CircuitBreakerState.HALF_OPEN

    # Fail again
    breaker.record_failure()
    assert breaker.state == CircuitBreakerState.OPEN
    with pytest.raises(CircuitBreakerError, match="CircuitBreaker for 'test_service' is open."):
        breaker.check()


def test_success_in_half_open_state_closes_circuit(breaker: CircuitBreaker):
    breaker.record_failure()
    breaker.record_failure()  # OPEN

    time.sleep(breaker._reset_timeout_seconds + 0.05)
    breaker.check()
    assert breaker.state == CircuitBreakerState.HALF_OPEN

    # Succeed
    breaker.record_success()
    assert breaker.state == CircuitBreakerState.CLOSED
    assert breaker.failure_count == 0


# --- Edge Case and Validation Tests (From Audit Feedback) ---

def test_invalid_thresholds_raise_error():
    with pytest.raises(ValueError, match="Failure threshold must be positive."):
        CircuitBreaker("test_service", failure_threshold=0)
    with pytest.raises(ValueError, match="Failure threshold must be positive."):
        CircuitBreaker("test_service", failure_threshold=-1)

    with pytest.raises(ValueError, match="Reset timeout must be positive."):
        CircuitBreaker("test_service", reset_timeout_seconds=0)
    with pytest.raises(ValueError, match="Reset timeout must be positive."):
        CircuitBreaker("test_service", reset_timeout_seconds=-1)


# --- Thread Safety Tests (From Audit Feedback) ---

def test_breaker_thread_safety_under_concurrent_failures():
    # High threshold to prevent tripping during the test
    breaker = CircuitBreaker("concurrent_service", failure_threshold=100)

    def fail_action():
        for _ in range(10):
            breaker.record_failure()

    threads = [threading.Thread(target=fail_action) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Each of the 5 threads recorded 10 failures
    assert breaker.failure_count == 50
    assert breaker.state == CircuitBreakerState.CLOSED


def test_registry_thread_safety_on_get_breaker():
    registry = CircuitBreakerRegistry()
    breakers = []

    def get_action():
        b = registry.get_breaker("shared_service")
        breakers.append(b)

    threads = [threading.Thread(target=get_action) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(breakers) == 10
    first_breaker = breakers[0]
    # Check that all threads received the exact same instance
    for b in breakers[1:]:
        assert b is first_breaker


# --- Registry Tests ---

def test_circuit_breaker_registry_creates_and_retrieves_breakers():
    registry = CircuitBreakerRegistry()

    breaker1 = registry.get_breaker("service_a", failure_threshold=3)
    assert breaker1.service_name == "service_a"
    assert breaker1._failure_threshold == 3

    breaker2 = registry.get_breaker("service_b")
    assert breaker2.service_name == "service_b"

    breaker1_again = registry.get_breaker("service_a")
    assert breaker1 is breaker1_again  # Should be the same instance