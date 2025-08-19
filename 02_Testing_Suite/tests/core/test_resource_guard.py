# tests/core/test_resource_guard.py

import time
import pytest
from unittest.mock import MagicMock

from antifragile_framework.core.resource_guard import (
    MonitoredResource,
    ResourceGuard,
    ResourceState,
)
from antifragile_framework.core.exceptions import NoResourcesAvailableError


# --- Fixtures ---

@pytest.fixture
def resource_config():
    """Provides a standard, fast configuration for testing resources."""
    return {
        "cooldown": 10,
        "penalty": 0.5,
        "healing_interval": 20,
        "healing_increment": 0.2
    }


@pytest.fixture
def guard(resource_config):
    """Provides a ResourceGuard with two keys and a fast test configuration."""
    keys = ["key-abc", "key-def"]
    return ResourceGuard(provider_name="test_provider", api_keys=keys, resource_config=resource_config)


# --- Unit Tests ---

def test_get_resource_context_manager_success(guard: ResourceGuard):
    """Tests the happy path of reserving and automatically releasing a resource."""
    resources = guard.get_all_resources()
    res1 = resources[0]

    assert res1.state == ResourceState.AVAILABLE

    with guard.get_resource() as resource:
        assert resource is not None
        assert resource.state == ResourceState.IN_USE

    assert res1.state == ResourceState.AVAILABLE


def test_get_resource_context_manager_failure_releases_without_penalty(guard: ResourceGuard):
    """
    Tests that if an exception occurs, the resource is released but NOT penalized
    by the context manager itself. Penalization is the caller's duty.
    """
    resources = guard.get_all_resources()
    resource_to_fail = resources[0]
    initial_score = resource_to_fail.health_score

    with pytest.raises(ValueError, match="Simulated failure"):
        with guard.get_resource() as resource:
            assert resource.value == resource_to_fail.value
            assert resource.state == ResourceState.IN_USE
            raise ValueError("Simulated failure")

    assert resource_to_fail.state == ResourceState.AVAILABLE
    assert resource_to_fail.health_score == initial_score


def test_resource_unavailable_error(guard: ResourceGuard):
    """Tests that NoResourcesAvailableError is raised when no resources are free."""
    with guard.get_resource():
        with guard.get_resource():
            with pytest.raises(NoResourcesAvailableError, match="No healthy and available resources"):
                with guard.get_resource():
                    pass


def test_penalize_resource_method(guard: ResourceGuard):
    """Tests the explicit penalize_resource method."""
    resource = guard.get_all_resources()[0]
    initial_score = resource.health_score

    guard.penalize_resource(resource.value)

    assert resource.health_score < initial_score
    assert resource.state == ResourceState.COOLING_DOWN


def test_health_score_healing(guard: ResourceGuard, monkeypatch, resource_config):
    """Tests that an available resource's health score recovers over time."""
    resources = guard.get_all_resources()
    res1 = resources[0]

    mock_time = MagicMock()
    monkeypatch.setattr(time, 'monotonic', mock_time)

    # Step 1: Penalize the resource at time 1000
    mock_time.return_value = 1000
    guard.penalize_resource(res1.value)
    assert res1.health_score == 0.5
    assert res1.last_failure_timestamp == 1000

    # Step 2: Advance time past cooldown to become available
    cooldown_time = resource_config["cooldown"]
    mock_time.return_value = 1000 + cooldown_time + 1
    assert res1.is_available() is True
    assert res1.state == ResourceState.AVAILABLE

    # Step 3: Advance time past healing interval to trigger healing
    last_update_time = res1.last_health_update_timestamp
    healing_interval = resource_config["healing_interval"]
    mock_time.return_value = last_update_time + healing_interval + 1

    # Check availability to trigger the healing logic within is_available -> _update_health
    res1.is_available()

    assert res1.health_score == pytest.approx(0.5 + resource_config["healing_increment"])
    assert res1.health_score <= 1.0


def test_full_penalize_cooldown_and_recovery(guard: ResourceGuard, monkeypatch, resource_config):
    """Tests that a penalized resource is unavailable, then becomes available after cooldown."""
    resource_to_penalize = guard.get_all_resources()[0]

    mock_time = MagicMock()
    monkeypatch.setattr(time, 'monotonic', mock_time)

    # 1. Penalize at a specific time
    mock_time.return_value = 1000
    guard.penalize_resource(resource_to_penalize.value)
    assert resource_to_penalize.is_available() is False

    # 2. Simulate time passing to just before the cooldown ends
    cooldown_time = resource_config["cooldown"]
    mock_time.return_value = 1000 + cooldown_time - 0.1
    assert resource_to_penalize.is_available() is False

    # 3. Simulate time passing to just after the cooldown ends
    mock_time.return_value = 1000 + cooldown_time + 0.1
    assert resource_to_penalize.is_available() is True