# 03_Demo_Interface/historical_charts.py

"""
Historical Performance Charts Generation for Adaptive Mind Framework Demo
SESSION 8 - Advanced Demo Features (FIXED IMPORTS VERSION)

Provides functions to retrieve historical performance data from the database
(via RealTimeMetricsCollector) and format it for charting.

Created: August 18, 2025
Author: Adaptive Mind Framework Team
Version: 1.0.1 (Fixed Imports & Enhanced Error Handling)
"""

import asyncio
import logging
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Standardized path setup
PROJECT_ROOT = Path(__file__).parent.parent
FRAMEWORK_CORE = PROJECT_ROOT / "01_Framework_Core"
DATABASE_LAYER = PROJECT_ROOT / "05_Database_Layer"

# Add paths
sys.path.insert(0, str(FRAMEWORK_CORE))
sys.path.insert(0, str(DATABASE_LAYER))
sys.path.insert(0, str(PROJECT_ROOT))

# Import with fallback handling
try:
    from performance_dashboard import ChartData, ChartType
    from real_time_metrics import RealTimeMetricsCollector

    METRICS_AVAILABLE = True
except ImportError:
    print("Warning: Metrics modules not available. Using mock implementations.")
    METRICS_AVAILABLE = False

    # Mock implementations
    class ChartType:
        LINE = "line"
        BAR = "bar"
        PIE = "pie"
        DOUGHNUT = "doughnut"

    class ChartData:
        def __init__(
            self,
            chart_id: str,
            title: str,
            chart_type: str,
            data: Dict,
            labels: List = None,
            datasets: List = None,
        ):
            self.chart_id = chart_id
            self.title = title
            self.chart_type = chart_type
            self.data = data
            self.labels = labels or []
            self.datasets = datasets or []

        def model_dump(self):
            return {
                "chart_id": self.chart_id,
                "title": self.title,
                "chart_type": self.chart_type,
                "data": self.data,
                "labels": self.labels,
                "datasets": self.datasets,
            }

    class RealTimeMetricsCollector:
        def __init__(self):
            pass

        async def get_aggregated_metrics(
            self,
            start_time,
            end_time,
            aggregate_by,
            metric_type,
            session_id=None,
        ):
            # Generate mock aggregated data
            mock_data = []
            current_time = datetime.now(timezone.utc)

            if aggregate_by == "hour":
                for i in range(24):  # Last 24 hours
                    ts = (current_time - timedelta(hours=i)).isoformat()
                    mock_data.append(
                        {
                            "time_bucket": ts,
                            "avg_response_time_ms": random.uniform(180, 350),
                            "total_cost_usd": random.uniform(0.01, 0.05),
                            "failover_count": random.randint(0, 2),
                            "total_requests": random.randint(20, 80),
                        }
                    )
            elif aggregate_by == "day":
                for i in range(7):  # Last 7 days
                    ts = (current_time - timedelta(days=i)).isoformat()
                    mock_data.append(
                        {
                            "time_bucket": ts,
                            "avg_response_time_ms": random.uniform(200, 400),
                            "total_cost_usd": random.uniform(0.5, 2.0),
                            "failover_count": random.randint(0, 5),
                            "total_requests": random.randint(100, 500),
                        }
                    )

            return {"data": mock_data}

        class MetricType:
            DEMO_EXECUTION = "demo_execution"


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class HistoricalChartsGenerator:
    """
    Generates historical data for performance charts by querying the RealTimeMetricsCollector.
    """

    def __init__(self, metrics_collector: Optional[RealTimeMetricsCollector] = None):
        self.metrics_collector = metrics_collector or RealTimeMetricsCollector()
        logger.info("HistoricalChartsGenerator initialized.")

    async def get_response_time_history(
        self,
        time_window_hours: int = 24,
        interval_minutes: int = 60,
        session_id: Optional[str] = None,
    ) -> ChartData:
        """
        Retrieves historical average response times and formats them for a line chart.
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=time_window_hours)

        try:
            # Aggregate metrics from the metrics collector
            aggregated_data = await self.metrics_collector.get_aggregated_metrics(
                start_time=start_time,
                end_time=end_time,
                aggregate_by="hour" if time_window_hours <= 24 else "day",
                metric_type=self.metrics_collector.MetricType.DEMO_EXECUTION,
                session_id=session_id,
            )

            labels = []
            data = []

            # Sort data by time bucket for chronological display
            sorted_data = sorted(
                aggregated_data.get("data", []),
                key=lambda x: x.get("time_bucket", ""),
            )

            for entry in sorted_data:
                try:
                    # Format label based on aggregation period
                    timestamp_str = entry.get(
                        "time_bucket", datetime.now(timezone.utc).isoformat()
                    )
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                    else:
                        timestamp = timestamp_str

                    if time_window_hours <= 24:
                        labels.append(timestamp.strftime("%H:%M"))
                    else:
                        labels.append(timestamp.strftime("%Y-%m-%d"))

                    response_time = entry.get("avg_response_time_ms", 0.0)
                    data.append(round(float(response_time), 1))
                except Exception as e:
                    logger.error(f"Error processing entry: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error getting response time history: {e}")
            labels = []
            data = []

        if not data:  # Fallback to mock data if no real data
            labels = [f"{i:02d}:00" for i in range(24)]
            data = [round(random.uniform(150, 400), 1) for _ in range(24)]
            logger.warning(
                "No real response time data found for charts. Using mock data."
            )

        return ChartData(
            chart_id="responseTimeChart",
            title="Response Time History",
            chart_type=ChartType.LINE,
            data={"labels": labels, "datasets": [{"data": data}]},
            labels=labels,
            datasets=[
                {
                    "label": "Avg Response Time (ms)",
                    "data": data,
                    "borderColor": "#6366f1",
                    "backgroundColor": "rgba(99, 102, 241, 0.1)",
                    "fill": True,
                    "tension": 0.4,
                }
            ],
        )

    async def get_cost_history(
        self,
        time_window_hours: int = 24,
        interval_minutes: int = 60,
        session_id: Optional[str] = None,
    ) -> ChartData:
        """
        Retrieves historical total cost and formats them for a line chart.
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=time_window_hours)

        try:
            aggregated_data = await self.metrics_collector.get_aggregated_metrics(
                start_time=start_time,
                end_time=end_time,
                aggregate_by="hour" if time_window_hours <= 24 else "day",
                metric_type=self.metrics_collector.MetricType.DEMO_EXECUTION,
                session_id=session_id,
            )

            labels = []
            data = []

            sorted_data = sorted(
                aggregated_data.get("data", []),
                key=lambda x: x.get("time_bucket", ""),
            )

            for entry in sorted_data:
                try:
                    timestamp_str = entry.get(
                        "time_bucket", datetime.now(timezone.utc).isoformat()
                    )
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                    else:
                        timestamp = timestamp_str

                    if time_window_hours <= 24:
                        labels.append(timestamp.strftime("%H:%M"))
                    else:
                        labels.append(timestamp.strftime("%Y-%m-%d"))

                    cost = entry.get("total_cost_usd", 0.0)
                    data.append(round(float(cost), 4))
                except Exception as e:
                    logger.error(f"Error processing cost entry: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error getting cost history: {e}")
            labels = []
            data = []

        if not data:  # Fallback to mock data if no real data
            labels = [f"{i:02d}:00" for i in range(24)]
            data = [round(random.uniform(0.005, 0.045), 4) for _ in range(24)]
            logger.warning("No real cost data found for charts. Using mock data.")

        return ChartData(
            chart_id="costChart",
            title="Cost History",
            chart_type=ChartType.LINE,
            data={"labels": labels, "datasets": [{"data": data}]},
            labels=labels,
            datasets=[
                {
                    "label": "Total Cost ($)",
                    "data": data,
                    "borderColor": "#10b981",
                    "backgroundColor": "rgba(16, 185, 129, 0.1)",
                    "fill": True,
                    "tension": 0.4,
                }
            ],
        )

    async def get_failover_history(
        self,
        time_window_hours: int = 24,
        interval_minutes: int = 60,
        session_id: Optional[str] = None,
    ) -> ChartData:
        """
        Retrieves historical failover event counts and formats them for a bar chart.
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=time_window_hours)

        try:
            aggregated_data = await self.metrics_collector.get_aggregated_metrics(
                start_time=start_time,
                end_time=end_time,
                aggregate_by="hour" if time_window_hours <= 24 else "day",
                metric_type=self.metrics_collector.MetricType.DEMO_EXECUTION,
                session_id=session_id,
            )

            labels = []
            data = []

            sorted_data = sorted(
                aggregated_data.get("data", []),
                key=lambda x: x.get("time_bucket", ""),
            )

            for entry in sorted_data:
                try:
                    timestamp_str = entry.get(
                        "time_bucket", datetime.now(timezone.utc).isoformat()
                    )
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                    else:
                        timestamp = timestamp_str

                    if time_window_hours <= 24:
                        labels.append(timestamp.strftime("%H:%M"))
                    else:
                        labels.append(timestamp.strftime("%Y-%m-%d"))

                    failover_count = entry.get("failover_count", 0)
                    data.append(int(failover_count))
                except Exception as e:
                    logger.error(f"Error processing failover entry: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error getting failover history: {e}")
            labels = []
            data = []

        if not data:  # Fallback to mock data if no real data
            labels = [f"{i:02d}:00" for i in range(24)]
            data = [random.randint(0, 4) for _ in range(24)]
            logger.warning("No real failover data found for charts. Using mock data.")

        return ChartData(
            chart_id="failoverChart",
            title="Failover Events",
            chart_type=ChartType.BAR,
            data={"labels": labels, "datasets": [{"data": data}]},
            labels=labels,
            datasets=[
                {
                    "label": "Failover Count",
                    "data": data,
                    "backgroundColor": "rgba(239, 68, 68, 0.8)",
                    "borderColor": "#ef4444",
                    "borderWidth": 1,
                }
            ],
        )

    async def get_request_volume_history(
        self,
        time_window_hours: int = 24,
        interval_minutes: int = 60,
        session_id: Optional[str] = None,
    ) -> ChartData:
        """
        Retrieves historical request volume and formats them for a line chart.
        """
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=time_window_hours)

        try:
            aggregated_data = await self.metrics_collector.get_aggregated_metrics(
                start_time=start_time,
                end_time=end_time,
                aggregate_by="hour" if time_window_hours <= 24 else "day",
                metric_type=self.metrics_collector.MetricType.DEMO_EXECUTION,
                session_id=session_id,
            )

            labels = []
            data = []

            sorted_data = sorted(
                aggregated_data.get("data", []),
                key=lambda x: x.get("time_bucket", ""),
            )

            for entry in sorted_data:
                try:
                    timestamp_str = entry.get(
                        "time_bucket", datetime.now(timezone.utc).isoformat()
                    )
                    if isinstance(timestamp_str, str):
                        timestamp = datetime.fromisoformat(
                            timestamp_str.replace("Z", "+00:00")
                        )
                    else:
                        timestamp = timestamp_str

                    if time_window_hours <= 24:
                        labels.append(timestamp.strftime("%H:%M"))
                    else:
                        labels.append(timestamp.strftime("%Y-%m-%d"))

                    request_count = entry.get("total_requests", 0)
                    data.append(int(request_count))
                except Exception as e:
                    logger.error(f"Error processing request volume entry: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error getting request volume history: {e}")
            labels = []
            data = []

        if not data:  # Fallback to mock data if no real data
            labels = [f"{i:02d}:00" for i in range(24)]
            data = [random.randint(20, 100) for _ in range(24)]
            logger.warning(
                "No real request volume data found for charts. Using mock data."
            )

        return ChartData(
            chart_id="requestVolumeChart",
            title="Request Volume History",
            chart_type=ChartType.LINE,
            data={"labels": labels, "datasets": [{"data": data}]},
            labels=labels,
            datasets=[
                {
                    "label": "Total Requests",
                    "data": data,
                    "borderColor": "#8b5cf6",
                    "backgroundColor": "rgba(139, 92, 246, 0.1)",
                    "fill": True,
                    "tension": 0.4,
                }
            ],
        )

    async def get_provider_distribution_chart(
        self, time_window_hours: int = 24
    ) -> ChartData:
        """
        Retrieves provider usage distribution for a pie/doughnut chart.
        """
        end_time = datetime.now(timezone.utc)
        end_time - timedelta(hours=time_window_hours)

        try:
            # This would need a different aggregation method for provider distribution
            # For now, we'll generate mock data based on realistic provider usage
            pass
        except Exception as e:
            logger.error(f"Error getting provider distribution: {e}")

        # Mock provider distribution data
        labels = [
            "OpenAI",
            "Anthropic",
            "Google Gemini",
            "Azure OpenAI",
            "Cohere",
        ]
        data = [35, 25, 20, 15, 5]  # Percentages
        colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#a855f7"]

        return ChartData(
            chart_id="providerDistributionChart",
            title="Provider Usage Distribution",
            chart_type=ChartType.DOUGHNUT,
            data={
                "labels": labels,
                "datasets": [{"data": data, "backgroundColor": colors}],
            },
            labels=labels,
            datasets=[
                {
                    "label": "Usage %",
                    "data": data,
                    "backgroundColor": colors,
                    "borderWidth": 2,
                    "borderColor": "#ffffff",
                }
            ],
        )

    async def get_comprehensive_dashboard_data(
        self, time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Gets all chart data for a comprehensive dashboard in one call.
        """
        try:
            # Get all charts concurrently for better performance
            charts_data = await asyncio.gather(
                self.get_response_time_history(time_window_hours),
                self.get_cost_history(time_window_hours),
                self.get_failover_history(time_window_hours),
                self.get_request_volume_history(time_window_hours),
                self.get_provider_distribution_chart(time_window_hours),
                return_exceptions=True,
            )

            (
                response_time_chart,
                cost_chart,
                failover_chart,
                volume_chart,
                provider_chart,
            ) = charts_data

            # Handle any exceptions in the results
            charts = {}
            chart_names = [
                "response_time",
                "cost",
                "failover",
                "request_volume",
                "provider_distribution",
            ]

            for i, (name, chart) in enumerate(zip(chart_names, charts_data)):
                if isinstance(chart, Exception):
                    logger.error(f"Error getting {name} chart: {chart}")
                    # Create a minimal fallback chart
                    charts[name] = {
                        "chart_id": f"{name}Chart",
                        "title": f"{name.replace('_', ' ').title()} Chart",
                        "error": str(chart),
                    }
                else:
                    charts[name] = (
                        chart.model_dump() if hasattr(chart, "model_dump") else chart
                    )

            return {
                "charts": charts,
                "time_window_hours": time_window_hours,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Error getting comprehensive dashboard data: {e}")
            return {
                "charts": {},
                "time_window_hours": time_window_hours,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "status": "error",
                "error": str(e),
            }


if __name__ == "__main__":
    # Example usage for testing
    async def main():
        print("Starting HistoricalChartsGenerator demo...")

        # Use mock metrics collector for testing
        metrics_collector = RealTimeMetricsCollector()
        generator = HistoricalChartsGenerator(metrics_collector)

        print("\n--- Response Time History ---")
        rt_chart = await generator.get_response_time_history()
        chart_data = (
            rt_chart.model_dump() if hasattr(rt_chart, "model_dump") else rt_chart
        )
        print(
            f"Chart ID: {chart_data.get('chart_id')}, Title: {chart_data.get('title')}"
        )
        if chart_data.get("labels"):
            print(f"Labels: {chart_data['labels'][-5:]}")  # Print last 5 labels
        if chart_data.get("datasets") and chart_data["datasets"]:
            print(
                f"Data: {chart_data['datasets'][0]['data'][-5:]}"
            )  # Print last 5 data points

        print("\n--- Cost History ---")
        cost_chart = await generator.get_cost_history()
        cost_data = (
            cost_chart.model_dump() if hasattr(cost_chart, "model_dump") else cost_chart
        )
        print(f"Chart ID: {cost_data.get('chart_id')}, Title: {cost_data.get('title')}")
        if cost_data.get("labels"):
            print(f"Labels: {cost_data['labels'][-5:]}")
        if cost_data.get("datasets") and cost_data["datasets"]:
            print(f"Data: {cost_data['datasets'][0]['data'][-5:]}")

        print("\n--- Failover History ---")
        failover_chart = await generator.get_failover_history()
        failover_data = (
            failover_chart.model_dump()
            if hasattr(failover_chart, "model_dump")
            else failover_chart
        )
        print(
            f"Chart ID: {failover_data.get('chart_id')}, Title: {failover_data.get('title')}"
        )
        if failover_data.get("labels"):
            print(f"Labels: {failover_data['labels'][-5:]}")
        if failover_data.get("datasets") and failover_data["datasets"]:
            print(f"Data: {failover_data['datasets'][0]['data'][-5:]}")

        print("\n--- Comprehensive Dashboard Data ---")
        dashboard_data = await generator.get_comprehensive_dashboard_data()
        print(f"Status: {dashboard_data.get('status')}")
        print(f"Charts available: {list(dashboard_data.get('charts', {}).keys())}")

        print("\nHistoricalChartsGenerator demo completed.")

    asyncio.run(main())
