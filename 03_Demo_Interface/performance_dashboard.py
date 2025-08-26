# 03_Demo_Interface/performance_dashboard.py

"""
Dashboard Data Models and Container for Adaptive Mind Framework Demo
SESSION 8 - Advanced Demo Features

Defines data structures (ChartType, ChartData) for consistent charting across the demo.
The PerformanceDashboard class acts as a high-level container for dashboard components.

Created: August 16, 2025 (Initial)
Updated: August 18, 2025 (Session 8 Refinement and Structure)
Author: Adaptive Mind Framework Team
Version: 1.1
"""

import sys
import logging
from dataclasses import dataclass, field
from datetime import datetime  # For potential timestamps in future features
from enum import Enum

# Standardized path setup (relative to current file)
from pathlib import Path
from typing import Any, Dict, List

CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
FRAMEWORK_CORE_PATH = PROJECT_ROOT / "01_Framework_Core" / "antifragile_framework"
DATABASE_LAYER_PATH = PROJECT_ROOT / "05_Database_Layer"
TELEMETRY_PATH = PROJECT_ROOT / "01_Framework_Core" / "telemetry"


sys.path.insert(0, str(FRAMEWORK_CORE_PATH))
sys.path.insert(0, str(DATABASE_LAYER_PATH))
sys.path.insert(0, str(TELEMETRY_PATH))
sys.path.insert(0, str(CURRENT_DIR))  # For sibling modules within 03_Demo_Interface

# Enterprise logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class ChartType(Enum):
    """Defines the types of charts supported by the frontend visualization."""

    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DOUGHNUT = "doughnut"  # Added doughnut chart type


@dataclass
class ChartData:
    """
    Standardized data structure for passing chart data to the frontend.
    Aligns with Chart.js expectations.
    """

    chart_id: str = field(metadata={"description": "Unique ID for the canvas element."})
    title: str = field(metadata={"description": "Title displayed on the chart."})
    chart_type: ChartType = field(
        metadata={"description": "Type of chart (e.g., 'line', 'bar')."}
    )

    # Chart.js 'data' object structure
    labels: List[str] = field(
        default_factory=list,
        metadata={"description": "Labels for the x-axis or segments."},
    )
    datasets: List[Dict[str, Any]] = field(
        default_factory=list,
        metadata={"description": "List of dataset objects for Chart.js."},
    )

    options: Dict[str, Any] = field(
        default_factory=dict,
        metadata={"description": "Optional Chart.js options."},
    )

    def model_dump(self) -> Dict[str, Any]:
        """
        Returns a dictionary representation compatible with Chart.js 'data' property.
        """
        return {"labels": self.labels, "datasets": self.datasets}


class PerformanceDashboard:
    """
    High-level container for the performance dashboard components.
    In Session 8, this class primarily serves as an organizational unit,
    with specific data generation and logic residing in other modules
    like RealTimeMetricsCollector, HistoricalChartsGenerator, etc.
    """

    def __init__(self):
        # In future sessions, this might orchestrate loading of multiple dashboard panels
        # and their respective data sources.
        logger.info("PerformanceDashboard container initialized.")

    async def initialize(self, *args, **kwargs):
        """Placeholder for any future initialization logic."""
        logger.info("PerformanceDashboard initialization placeholder executed.")

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Placeholder for a method that would return comprehensive dashboard data.
        Currently, specific API endpoints return individual chart data.
        """
        logger.warning(
            "get_dashboard_data is a placeholder; fetch specific charts via API endpoints."
        )
        return {
            "status": "partial_data",
            "message": "Access specific chart data via dedicated API endpoints.",
            "timestamp": datetime.now().isoformat(),
        }


if __name__ == "__main__":
    import asyncio
    import json

    async def main():
        print("Starting PerformanceDashboard demo...")

        dashboard = PerformanceDashboard()
        await dashboard.initialize()

        # Example of creating and dumping ChartData
        print("\n--- Example ChartData creation and dump ---")
        sample_chart_data = ChartData(
            chart_id="testChart",
            title="Sample Daily Performance",
            chart_type=ChartType.BAR,
            labels=["Mon", "Tue", "Wed", "Thu", "Fri"],
            datasets=[
                {
                    "label": "Success Rate",
                    "data": [0.95, 0.92, 0.98, 0.90, 0.97],
                    "backgroundColor": "rgba(75, 192, 192, 0.6)",
                }
            ],
        )
        print(f"ChartData instance: {sample_chart_data}")
        print(
            f"Chart.js data dump: {json.dumps(sample_chart_data.model_dump(), indent=2)}"
        )

        # Example of getting placeholder dashboard data
        print("\n--- Getting placeholder dashboard data ---")
        placeholder_data = await dashboard.get_dashboard_data()
        print(json.dumps(placeholder_data, indent=2))

        print("\nPerformanceDashboard demo completed.")

    asyncio.run(main())
