#!/usr/bin/env python3
"""
Session 5 - Step 4: Demo Integration with Telemetry
02_Testing_Suite/session_5_telemetry_integration/demo_telemetry_integration_test.py

Tests that the existing demo system can properly integrate with telemetry.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


def test_demo_backend_telemetry_integration():
    """Test that demo backend can import and use telemetry"""
    print("🔍 Testing Demo Backend + Telemetry Integration...")

    try:
        # Import demo backend (correct path)
        sys.path.insert(0, str(project_root / "03_Demo_Interface"))
        from demo_backend import app

        print("✅ Demo backend import successful")

        # Test telemetry imports in demo context
        from telemetry import event_topics
        from telemetry.core_logger import UniversalEventSchema, core_logger
        from telemetry.event_bus import event_bus

        print("✅ Telemetry imports in demo context successful")

        # Test creating a demo telemetry event
        from datetime import datetime, timezone

        demo_event = UniversalEventSchema(
            event_type="DEMO_TELEMETRY_TEST",
            event_source="DemoIntegrationTest",
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            severity="INFO",
            payload={
                "demo_integration": True,
                "session": "Session 5 - Step 4",
                "test_type": "demo_backend_integration",
            },
        )

        # Test logging and publishing
        core_logger.log(demo_event)
        event_bus.publish(
            event_topics.API_REQUEST_START, demo_event.model_dump()
        )
        print("✅ Demo telemetry event creation and publishing successful")

        return True

    except Exception as e:
        print(f"❌ Demo integration test failed: {e}")
        return False


def test_framework_demo_complete_integration():
    """Test complete framework + demo + telemetry integration"""
    print("\n🔍 Testing Complete Framework + Demo + Telemetry Integration...")

    try:
        # Test framework core with telemetry
        from antifragile_framework.core.failover_engine import FailoverEngine
        from antifragile_framework.core.learning_engine import LearningEngine
        from antifragile_framework.resilience.bias_ledger import BiasLedger

        print("✅ Framework core imports successful")

        # Test telemetry components
        from telemetry.core_logger import core_logger
        from telemetry.event_bus import event_bus
        from telemetry.time_series_db_interface import TimeSeriesDBInterface

        print("✅ Telemetry components accessible to framework")

        # Test creating a basic database interface (SQLite for testing)
        db_interface = TimeSeriesDBInterface(
            db_url="sqlite:///:memory:", table_name="demo_telemetry_test"
        )
        print("✅ Database interface creation successful")

        # Test learning engine with database interface
        learning_engine = LearningEngine(db_interface)
        print("✅ LearningEngine with database interface successful")

        # Test bias ledger with telemetry (correct constructor)
        bias_ledger = BiasLedger(event_bus=event_bus)
        print("✅ BiasLedger with telemetry components successful")

        return True

    except Exception as e:
        print(f"❌ Complete integration test failed: {e}")
        import traceback

        print(f"Traceback: {traceback.format_exc()}")
        return False


def main():
    """Run Session 5 Step 4 - Demo Integration Testing"""
    print("🚀 SESSION 5 - STEP 4: DEMO INTEGRATION WITH TELEMETRY")
    print("=" * 60)

    tests = [
        (
            "Demo Backend + Telemetry Integration",
            test_demo_backend_telemetry_integration,
        ),
        (
            "Complete Framework + Demo + Telemetry",
            test_framework_demo_complete_integration,
        ),
    ]

    passed_tests = 0
    total_tests = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 40)

        if test_func():
            print(f"✅ {test_name} - PASSED")
            passed_tests += 1
        else:
            print(f"❌ {test_name} - FAILED")

    print("\n" + "=" * 60)
    print(
        f"📊 DEMO INTEGRATION RESULTS: {passed_tests}/{total_tests} tests passed"
    )

    if passed_tests == total_tests:
        print("🎉 DEMO INTEGRATION WITH TELEMETRY - FULLY SUCCESSFUL!")
        print("✅ Session 5 telemetry integration is complete")
        print("✅ Framework + Demo + Telemetry = Ready for Session 6")
        return True
    else:
        print("⚠️  Some demo integration tests failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
