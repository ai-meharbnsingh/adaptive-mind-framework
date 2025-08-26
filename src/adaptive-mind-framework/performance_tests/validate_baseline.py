# performance_tests/validate_baseline.py

import os
import subprocess
import json
import sys
from pathlib import Path

# Add project root to the Python path to allow importing framework components
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# --- Configuration ---
HOST = "http://127.0.0.1:8000"
LOCUSTFILE = "performance_tests/locustfile.py"
RUN_TIME = "15s"
USERS = 4
SPAWN_RATE = 2
EXPECTED_MEDIAN_RESPONSE_TIME_MS = 25


def run_locust_headless():
    """Runs Locust in headless mode and returns the stats JSON as a string."""
    print("--- Starting Locust Performance Baseline Validation (Gentle Load) ---")
    print(f"Locustfile: {LOCUSTFILE}, Host: {HOST}, Runtime: {RUN_TIME}, Users: {USERS}")

    command = [
        "locust",
        "-f", LOCUSTFILE,
        "--host", HOST,
        "--headless",
        "-u", str(USERS),
        "-r", str(SPAWN_RATE),
        "--run-time", RUN_TIME,
        "--json"
    ]

    try:
        result = subprocess.run(command, check=True, cwd=project_root, capture_output=True, text=True, encoding='utf-8')
        print("Locust run completed successfully.")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print("--- 🔴 ERROR: Locust process failed. ---", file=sys.stderr)
        print("Is the FastAPI server running with PERFORMANCE_TEST_MODE='True'? See README.", file=sys.stderr)
        print(f"\n--- Locust STDERR ---\n{e.stderr}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("--- 🔴 ERROR: 'locust' command not found. ---", file=sys.stderr)
        print("Is Locust installed in your virtual environment? Run 'pip install locust'.", file=sys.stderr)
        return None


def validate_performance(stats_json_string):
    """Validates the performance metrics from the Locust JSON output string."""
    print("\n--- Validating Performance Metrics ---")
    try:
        json_start_index = stats_json_string.find('[')
        if json_start_index == -1:
            print(f"--- 🔴 ERROR: Could not find start of JSON list in Locust output. ---", file=sys.stderr)
            print(f"Received output: {stats_json_string[:500]}...", file=sys.stderr)
            return False

        json_data = stats_json_string[json_start_index:]
        stats_list = json.loads(json_data)

        if not isinstance(stats_list, list):
            print(f"--- 🔴 ERROR: Parsed JSON is not a list as expected. ---", file=sys.stderr)
            return False

        total_requests = sum(s.get("num_requests", 0) for s in stats_list)
        total_failures = sum(s.get("num_failures", 0) for s in stats_list)

        if total_requests == 0:
            print("--- 🟡 WARNING: No requests were made during the test run. ---")
            return True

        # Calculate a weighted average for the median response time
        weighted_median_sum = sum(s.get("median_response_time", 0) * s.get("num_requests", 0) for s in stats_list)
        average_median_response_time = weighted_median_sum / total_requests

        failure_rate = (total_failures / total_requests) * 100

        print(f"Total Requests: {total_requests}")
        print(f"Total Failures: {total_failures}")
        print(f"Average Median Response Time: {average_median_response_time:.2f} ms")
        print(f"Failure Rate: {failure_rate:.2f}%")

        if average_median_response_time > EXPECTED_MEDIAN_RESPONSE_TIME_MS:
            print(
                f"--- 🔴 VALIDATION FAILED: Average median response time ({average_median_response_time:.2f}ms) exceeds threshold ({EXPECTED_MEDIAN_RESPONSE_TIME_MS}ms). ---",
                file=sys.stderr)
            return False

        if failure_rate > 0:
            print(f"--- 🔴 VALIDATION FAILED: Requests failed during test ({failure_rate:.2f}% failure rate). ---",
                  file=sys.stderr)
            return False

        print(f"--- ✅ PERFORMANCE VALIDATION PASSED ---")
        return True

    except (json.JSONDecodeError, KeyError, ZeroDivisionError) as e:
        print(f"--- 🔴 ERROR: Could not read or parse stats from Locust output. ---", file=sys.stderr)
        print(f"Received output snippet: {stats_json_string[:500]}...", file=sys.stderr)
        print(e, file=sys.stderr)
        return False


if __name__ == "__main__":
    stats_output = run_locust_headless()
    if stats_output:
        is_valid = validate_performance(stats_output)
        if not is_valid:
            sys.exit(1)
    else:
        sys.exit(1)