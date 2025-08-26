# tests/config/test_config_loader.py

import json
from decimal import Decimal
from unittest.mock import mock_open, patch

import pytest
import yaml
from antifragile_framework.config.config_loader import (
    load_provider_profiles,
    load_resilience_config,
)
from antifragile_framework.config.schemas import ProviderProfiles
from pydantic import ValidationError

# --- Fixtures for Mocking Config Files ---


@pytest.fixture
def valid_provider_profiles_data():
    return {
        "schema_version": "1.0",
        "last_updated_utc": "2025-08-19T10:00:00Z",
        "profiles": {
            "openai": {
                "_default": {"input_cpm": "0.50", "output_cpm": "1.50"},
                "gpt-4o": {"input_cpm": "5.00", "output_cpm": "15.00"},
            }
        },
    }


@pytest.fixture
def invalid_provider_profiles_data():
    # Missing 'profiles' key
    return {
        "schema_version": "1.0",
        "last_updated_utc": "2025-08-19T10:00:00Z",
    }


@pytest.fixture
def malformed_provider_profiles_data():
    # 'input_cpm' is not a valid decimal string
    return {
        "schema_version": "1.0",
        "last_updated_utc": "2025-08-19T10:00:00Z",
        "profiles": {
            "openai": {"gpt-4o": {"input_cpm": "five", "output_cpm": "15.00"}}
        },
    }


@pytest.fixture
def valid_resilience_data():
    return {
        "resilience_score_penalties": {
            "base_successful_penalty": 0.0,
            "mitigated_success_penalty": 0.1,
            "api_call_failure_penalty": 0.05,
        }
    }


# --- Tests for load_provider_profiles ---


def test_load_provider_profiles_success(valid_provider_profiles_data):
    """Verify successful loading and validation of a correct provider profiles file."""
    mock_json_content = json.dumps(valid_provider_profiles_data)
    with patch("builtins.open", mock_open(read_data=mock_json_content)):
        with patch("os.path.exists", return_value=True):
            profiles = load_provider_profiles(
                "dummy/path/provider_profiles.json"
            )
            assert isinstance(profiles, ProviderProfiles)
            assert profiles.profiles["openai"]["gpt-4o"].input_cpm == Decimal(
                "5.00"
            )


def test_load_provider_profiles_file_not_found():
    """Verify FileNotFoundError is raised if the config file doesn't exist."""
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            load_provider_profiles()


def test_load_provider_profiles_invalid_json():
    """Verify ValueError is raised for malformed JSON."""
    with patch("builtins.open", mock_open(read_data="{ not json }")):
        with patch("os.path.exists", return_value=True):
            with pytest.raises(ValueError, match="Invalid JSON"):
                load_provider_profiles()


def test_load_provider_profiles_schema_validation_error(
    invalid_provider_profiles_data,
):
    """Verify ValueError is raised if the data doesn't match the Pydantic schema."""
    mock_json_content = json.dumps(invalid_provider_profiles_data)
    with patch("builtins.open", mock_open(read_data=mock_json_content)):
        with patch("os.path.exists", return_value=True):
            with pytest.raises(
                ValueError, match="Provider profiles configuration is invalid"
            ):
                load_provider_profiles()


def test_load_provider_profiles_data_type_error(
    malformed_provider_profiles_data,
):
    """Verify ValueError is raised for incorrect data types within the schema (e.g., bad Decimal string)."""
    mock_json_content = json.dumps(malformed_provider_profiles_data)
    with patch("builtins.open", mock_open(read_data=mock_json_content)):
        with patch("os.path.exists", return_value=True):
            with pytest.raises(
                ValueError, match="Provider profiles configuration is invalid"
            ):
                load_provider_profiles()


# --- Tests for load_resilience_config (Regression Tests) ---


def test_load_resilience_config_success(valid_resilience_data):
    """Verify successful loading of a correct resilience config file."""
    mock_yaml_content = yaml.dump(valid_resilience_data)
    with patch("builtins.open", mock_open(read_data=mock_yaml_content)):
        with patch("os.path.exists", return_value=True):
            config = load_resilience_config(
                "dummy/path/resilience_config.yaml"
            )
            assert (
                config["resilience_score_penalties"][
                    "mitigated_success_penalty"
                ]
                == 0.1
            )


def test_load_resilience_config_file_not_found():
    """Verify FileNotFoundError for resilience config."""
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            load_resilience_config()
