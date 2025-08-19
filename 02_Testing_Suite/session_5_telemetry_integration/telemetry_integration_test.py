#!/usr/bin/env python3
"""
Session 5 - Telemetry Integration Validation Suite
02_Testing_Suite/session_5_telemetry_integration/telemetry_integration_test.py

Validates that all telemetry components integrate correctly with the framework.
Follows our established testing organization pattern.
"""

import sys
import os
import traceback
from pathlib import Path

# Add the project root to Python path for proper imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_telemetry_module_imports():
    """Test all telemetry module imports are functional"""
    print("🔍 Testing Telemetry Module Imports...")

    try:
        # Test core telemetry imports
        from telemetry.time_series_db_interface import TimeSeriesDBInterface, initialize_and_subscribe_db_interface
        print("✅ TimeSeriesDBInterface import successful")

        from telemetry.core_logger import core_logger, UniversalEventSchema, AdaptiveMindLogger
        print("✅ core_logger, UniversalEventSchema, AdaptiveMindLogger import successful")

        from telemetry.event_bus import EventBus, event_bus
        print("✅ EventBus and event_bus singleton import successful")

        from telemetry import event_topics
        print("✅ event_topics import successful")

        from telemetry.telemetry_subscriber import TelemetrySubscriber
        print("✅ TelemetrySubscriber import successful")

        # All core telemetry imports successful - framework integration ready
        print("✅ All essential telemetry imports successful")

        return True

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


def test_framework_telemetry_integration():
    """Test that framework files can import telemetry modules as designed"""
    print("\n🔍 Testing Framework-Telemetry Integration...")

    critical_integration_tests = [
        {
            "framework_component": "learning_engine.py",
            "import_statement": "from telemetry.time_series_db_interface import TimeSeriesDBInterface",
            "description": "LearningEngine database interface integration"
        },
        {
            "framework_component": "bias_ledger.py",
            "import_statement": "from telemetry.core_logger import core_logger, UniversalEventSchema",
            "description": "BiasLedger logging integration"
        },
        {
            "framework_component": "framework components",
            "import_statement": "from telemetry.event_bus import EventBus",
            "description": "Framework EventBus integration"
        },
        {
            "framework_component": "all framework files",
            "import_statement": "from telemetry import event_topics",
            "description": "Event topics constants access"
        }
    ]

    success_count = 0
    total_tests = len(critical_integration_tests)

    for test in critical_integration_tests:
        try:
            exec(test["import_statement"])
            print(f"✅ {test['description']} - SUCCESS")
            success_count += 1
        except ImportError as e:
            print(f"❌ {test['description']} - FAILED: {e}")
        except Exception as e:
            print(f"❌ {test['description']} - UNEXPECTED ERROR: {e}")

    print(f"\n📊 Framework Integration Tests: {success_count}/{total_tests} passed")
    return success_count == total_tests


def test_telemetry_functionality():
    """Test basic telemetry functionality works as expected"""
    print("\n🔍 Testing Basic Telemetry Functionality...")

    try:
        from telemetry.core_logger import UniversalEventSchema
        from telemetry.event_bus import event_bus
        from telemetry import event_topics
        from datetime import datetime, timezone

        # Test 1: UniversalEventSchema creation and validation
        test_event = UniversalEventSchema(
            event_type="TELEMETRY_INTEGRATION_TEST",
            event_source="Session5ValidationSuite",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            severity="INFO",
            payload={
                "test_type": "Session 5 Integration Test",
                "validation": "telemetry_functionality",
                "framework_integration": True
            }
        )
        print("✅ UniversalEventSchema creation and validation successful")

        # Test 2: Event bus publish (should execute without errors)
        event_bus.publish("TELEMETRY_TEST_EVENT", test_event.model_dump())
        print("✅ EventBus publish mechanism functional")

        # Test 3: Event topics constants accessibility
        required_topics = [
            'BIAS_LOG_ENTRY_CREATED',
            'API_CALL_SUCCESS',
            'API_CALL_FAILURE',
            'CIRCUIT_TRIPPED',
            'RESOURCE_PENALIZED'
        ]

        for topic in required_topics:
            assert hasattr(event_topics, topic), f"Missing required event topic: {topic}"

        print("✅ All required event topics constants accessible")

        # Test 4: TimeSeriesDBInterface instantiation (with SQLite for testing)
        from telemetry.time_series_db_interface import TimeSeriesDBInterface
        test_db_interface = TimeSeriesDBInterface(
            db_url="sqlite:///:memory:",  # In-memory SQLite for testing
            table_name="test_telemetry"
        )
        print("✅ TimeSeriesDBInterface instantiation successful")

        return True

    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        return False


def test_session_5_success_criteria():
    """Validate Session 5 success criteria from master plan"""
    print("\n🔍 Testing Session 5 Success Criteria...")

    success_criteria = [
        ("All telemetry imports resolve correctly", test_telemetry_module_imports),
        ("Framework can import telemetry components", test_framework_telemetry_integration),
        ("Basic telemetry functionality operational", test_telemetry_functionality)
    ]

    passed_criteria = 0
    total_criteria = len(success_criteria)

    for criterion_name, test_func in success_criteria:
        print(f"\n📋 Validating: {criterion_name}")
        print("-" * 50)

        if test_func():
            print(f"✅ SUCCESS CRITERIA MET: {criterion_name}")
            passed_criteria += 1
        else:
            print(f"❌ SUCCESS CRITERIA FAILED: {criterion_name}")

    return passed_criteria, total_criteria


def main():
    """Run Session 5 Telemetry Integration Validation Suite"""
    print("🚀 ADAPTIVE MIND - SESSION 5 TELEMETRY INTEGRATION VALIDATION")
    print("=" * 70)
    print("Following established 02_Testing_Suite organization pattern")
    print("=" * 70)

    # Execute comprehensive validation
    passed_criteria, total_criteria = test_session_5_success_criteria()

    print("\n" + "=" * 70)
    print(f"📊 SESSION 5 VALIDATION RESULTS: {passed_criteria}/{total_criteria} criteria met")

    if passed_criteria == total_criteria:
        print("🎉 SESSION 5 TELEMETRY INTEGRATION - FULLY SUCCESSFUL!")
        print("✅ Ready to proceed to Step 3: Demo Integration Testing")
        print("✅ All telemetry imports resolved")
        print("✅ Framework-telemetry integration operational")
        print("✅ Telemetry functionality validated")
        return True
    else:
        print("⚠️  Session 5 integration incomplete - need to resolve issues")
        print("📋 Review failed criteria above before proceeding")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)