# 03_Demo_Interface/websocket_handler.py

"""
WebSocket Manager for Adaptive Mind Framework Demo Dashboard
SESSION 7 - Enhanced Demo Backend Integration (further refined in Session 8)

This module is responsible for:
1. Managing active WebSocket connections from the frontend.
2. Broadcasting real-time metric updates to all connected clients.
3. Sending specific updates to individual clients.

Created: August 16, 2025 (Initial)
Updated: August 18, 2025 (Session 8 Refinement and Robustness)
Author: Adaptive Mind Framework Team
Version: 1.1
"""

import sys
import asyncio
import json
import logging
import random  # For mock data in __main__
from datetime import datetime, timezone  # Needed for json.dumps default

# Standardized path setup (relative to current file)
from pathlib import Path
from typing import Any, Dict, List, Optional

CURRENT_DIR = Path(__file__).parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
FRAMEWORK_CORE_PATH = (
    PROJECT_ROOT / "01_Framework_Core" / "antifragile_framework"
)
DATABASE_LAYER_PATH = PROJECT_ROOT / "05_Database_Layer"
TELEMETRY_PATH = PROJECT_ROOT / "01_Framework_Core" / "telemetry"


sys.path.insert(0, str(FRAMEWORK_CORE_PATH))
sys.path.insert(0, str(DATABASE_LAYER_PATH))
sys.path.insert(0, str(TELEMETRY_PATH))
sys.path.insert(
    0, str(CURRENT_DIR)
)  # For sibling modules within 03_Demo_Interface

# Import RealTimeMetricsCollector for periodic updates
try:
    from real_time_metrics import RealTimeMetricsCollector
except ImportError:
    logging.warning(
        "RealTimeMetricsCollector not available for WebSocketManager demo. Will use local mocks."
    )

    class RealTimeMetricsCollector:
        async def get_live_metrics(self):
            return {
                "total_requests": random.randint(10, 50),
                "avg_response_time_ms": round(random.uniform(150, 350), 2),
                "total_cost_usd": round(random.uniform(0.1, 0.5), 4),
                "avg_cost_per_request": round(random.uniform(0.002, 0.005), 5),
                "total_failovers": random.randint(0, 2),
                "failover_rate_percent": round(random.uniform(0.0, 2.0), 2),
                "latest_bias_score": round(random.uniform(0.05, 0.15), 3),
            }


# Enterprise logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class WebSocketManager:
    """
    Manages WebSocket connections to broadcast real-time data to connected clients.
    Ensures robust message delivery and connection management.
    """

    def __init__(self):
        self.active_connections: List[Any] = []  # Stores WebSocket objects
        self.message_queue_per_client: Dict[Any, asyncio.Queue] = (
            {}
        )  # Queue for each client
        self.broadcast_task: Optional[asyncio.Task] = None
        logger.info("WebSocketManager initialized.")

    async def connect(self, websocket: Any):
        """
        Registers a new WebSocket connection.
        """
        await websocket.accept()
        self.active_connections.append(websocket)
        self.message_queue_per_client[websocket] = asyncio.Queue()
        logger.info(
            f"New WebSocket connected. Total active: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: Any):
        """
        Removes a disconnected WebSocket connection.
        """
        try:
            self.active_connections.remove(websocket)
            if websocket in self.message_queue_per_client:
                del self.message_queue_per_client[websocket]
            logger.info(
                f"WebSocket disconnected. Total active: {len(self.active_connections)}"
            )
        except ValueError:
            logger.warning(
                "Attempted to disconnect a WebSocket that was not in active_connections."
            )

    async def send_personal_message(
        self, message: Dict[str, Any], websocket: Any
    ):
        """
        Sends a message to a specific WebSocket client.
        """
        try:
            # Ensure datetime objects are serialized correctly
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(
                f"Failed to send personal message to WebSocket: {e}",
                exc_info=True,
            )
            self.disconnect(websocket)  # Disconnect on send failure

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcasts a message to all active WebSocket clients.
        Uses a per-client queue to prevent blocking the main loop.
        """
        disconnected_clients = []
        for connection in list(self.active_connections):  # Iterate over a copy
            try:
                # Put message in client's queue; non-blocking
                await self.message_queue_per_client[connection].put(message)
            except asyncio.QueueFull:
                logger.warning(
                    f"Client queue full for {connection.client}. Disconnecting due to backlog."
                )
                disconnected_clients.append(connection)
            except (
                KeyError
            ):  # Client might have disconnected between list() and here
                pass  # Already handled by disconnect
            except Exception as e:
                logger.error(
                    f"Error queuing message for client {connection.client}: {e}",
                    exc_info=True,
                )
                disconnected_clients.append(connection)

        for client in disconnected_clients:
            self.disconnect(client)

        # Start a listener task for each newly connected client to consume from its queue
        # This is typically handled where the WebSocket connection is accepted (e.g., FastAPI route)
        # However, to explicitly ensure messages are sent:
        for connection in self.active_connections:
            if not hasattr(
                connection, "_websocket_listener_task"
            ):  # Check if task exists
                connection._websocket_listener_task = asyncio.create_task(
                    self._websocket_listener(connection)
                )

    async def _websocket_listener(self, websocket: Any):
        """
        Internal task for each WebSocket to consume messages from its queue and send.
        """
        queue = self.message_queue_per_client.get(websocket)
        if not queue:
            logger.warning(
                f"No queue found for websocket {websocket.client}. Listener exiting."
            )
            return

        try:
            while True:
                message = await queue.get()
                if message is None:  # Sentinel value for shutdown
                    break
                await self.send_personal_message(message, websocket)
                queue.task_done()
        except Exception as e:
            logger.error(
                f"WebSocket listener task failed for {websocket.client}: {e}",
                exc_info=True,
            )
            self.disconnect(websocket)
        finally:
            if hasattr(websocket, "_websocket_listener_task"):
                del (
                    websocket._websocket_listener_task
                )  # Clean up task attribute

    async def broadcast_dashboard_updates_periodically(
        self,
        metrics_collector: RealTimeMetricsCollector,
        interval_seconds: int = 15,
    ):
        """
        Starts a background task to periodically fetch live metrics and broadcast them.
        """
        if self.broadcast_task and not self.broadcast_task.done():
            logger.warning("Periodic broadcast task already running.")
            return

        logger.info(
            f"Starting periodic dashboard update broadcast every {interval_seconds} seconds."
        )

        async def _periodic_task():
            while True:
                try:
                    # Fetch overall live metrics from the collector
                    live_metrics_data = (
                        await metrics_collector.get_live_metrics()
                    )
                    await self.broadcast(
                        {
                            "type": "dashboard_update",
                            "data": live_metrics_data,
                            "timestamp": datetime.now(
                                timezone.utc
                            ).isoformat(),
                        }
                    )
                except Exception as e:
                    logger.error(
                        f"Error during periodic dashboard update broadcast: {e}",
                        exc_info=True,
                    )
                await asyncio.sleep(interval_seconds)

        self.broadcast_task = asyncio.create_task(_periodic_task())

    async def shutdown(self):
        """
        Gracefully shuts down the WebSocket manager, cancelling broadcast tasks
        and closing all connections.
        """
        logger.info("Shutting down WebSocketManager...")
        if self.broadcast_task:
            self.broadcast_task.cancel()
            try:
                await self.broadcast_task
            except asyncio.CancelledError:
                logger.info("Periodic broadcast task cancelled.")

        # Send sentinel value to all queues to stop listener tasks
        for websocket in list(self.active_connections):
            if websocket in self.message_queue_per_client:
                await self.message_queue_per_client[websocket].put(
                    None
                )  # Sentinel value

        # Wait for listener tasks to complete (with a timeout)
        await asyncio.gather(
            *[
                task
                for task in [
                    getattr(conn, "_websocket_listener_task", None)
                    for conn in self.active_connections
                ]
                if task is not None and not task.done()
            ],
            return_exceptions=True,
        )  # Gather with return_exceptions to not fail on individual task errors

        for websocket in list(self.active_connections):
            try:
                await websocket.close()
            except Exception as e:
                logger.warning(
                    f"Error closing WebSocket connection during shutdown: {e}"
                )
            self.disconnect(websocket)
        logger.info(
            "WebSocketManager shutdown complete. All connections closed."
        )


if __name__ == "__main__":
    import random  # Need random for mock metrics collector

    async def main():
        print("Starting WebSocketManager demo...")

        # Mock RealTimeMetricsCollector for standalone testing
        mock_metrics_collector = (
            RealTimeMetricsCollector()
        )  # This class now includes a mock for itself if DB is unavailable

        manager = WebSocketManager()

        # Simulate a client connecting
        class MockWebSocket:
            def __init__(self, client_id):
                self.client = f"client_{client_id}"
                self._messages_sent = []

            async def accept(self):
                print(f"MockWebSocket {self.client} accepted.")

            async def send_text(self, message):
                self._messages_sent.append(message)
                print(
                    f"MockWebSocket {self.client} received: {message[:100]}..."
                )  # Print first 100 chars

            async def receive_text(self):
                # Simulate client sending keep-alive or nothing for a while
                await asyncio.sleep(1)
                return "keep-alive"

            async def close(self):
                print(f"MockWebSocket {self.client} closed.")

        mock_ws1 = MockWebSocket(1)
        mock_ws2 = MockWebSocket(2)

        # Connect clients
        await manager.connect(mock_ws1)
        await manager.connect(mock_ws2)

        # Start periodic broadcast
        manager.broadcast_dashboard_updates_periodically(
            mock_metrics_collector, interval_seconds=2
        )

        # Simulate some time passing
        print("\n--- Simulating 5 seconds of activity ---")
        await asyncio.sleep(5)

        # Send a direct message to one client
        print("\n--- Sending direct message to mock_ws1 ---")
        await manager.send_personal_message(
            {"type": "custom_alert", "message": "High anomaly detected!"},
            mock_ws1,
        )
        await asyncio.sleep(0.5)  # Allow time for message to be processed

        # Disconnect one client
        print("\n--- Disconnecting mock_ws2 ---")
        manager.disconnect(mock_ws2)
        await asyncio.sleep(1)

        # Simulate more time
        print("\n--- Simulating 3 more seconds with one client ---")
        await asyncio.sleep(3)

        # Shut down
        print("\n--- Shutting down WebSocketManager ---")
        await manager.shutdown()

        # Check messages sent by mock clients
        print(f"\nMock_ws1 messages sent: {len(mock_ws1._messages_sent)}")
        print(f"Mock_ws2 messages sent: {len(mock_ws2._messages_sent)}")

        print("\nWebSocketManager demo completed.")

    asyncio.run(main())
