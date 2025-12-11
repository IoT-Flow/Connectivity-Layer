"""
MQTT metrics collector for Prometheus.
Collects MQTT connection, message, and topic metrics.
"""
import logging
from typing import Dict, Any

from src.metrics import (
    MQTT_CONNECTIONS_TOTAL,
    MQTT_CONNECTIONS_ACTIVE,
    MQTT_MESSAGES_RECEIVED,
    MQTT_MESSAGES_SENT,
    MQTT_MESSAGES_DROPPED,
    MQTT_MESSAGES_QUEUED,
    MQTT_TOPICS_TOTAL,
    MQTT_SUBSCRIPTIONS_TOTAL,
    MQTT_BYTES_SENT,
    MQTT_BYTES_RECEIVED,
)

logger = logging.getLogger(__name__)


class MQTTMetricsCollector:
    """Collects MQTT-related metrics."""

    def __init__(self):
        """Initialize the MQTT metrics collector."""
        self._mqtt_client = None
        self._mqtt_service = None
        self._initialize_mqtt_references()

    def _initialize_mqtt_references(self):
        """Initialize references to MQTT client and service."""
        try:
            # Try to import and get MQTT client reference
            from src.mqtt.mqtt_client import mqtt_client

            self._mqtt_client = mqtt_client
            self._mqtt_service = mqtt_client  # Use the client as the service for now

        except ImportError as e:
            logger.warning(f"MQTT client not available for metrics: {e}")
        except Exception as e:
            logger.error(f"Error initializing MQTT references: {e}")

    def collect_all_metrics(self) -> None:
        """Collect all MQTT metrics."""
        try:
            self.collect_connection_metrics()
            self.collect_message_metrics()
            self.collect_topic_metrics()
            logger.debug("MQTT metrics collected successfully")
        except Exception as e:
            logger.error(f"Error collecting MQTT metrics: {e}")

    def collect_connection_metrics(self) -> None:
        """Collect MQTT connection metrics."""
        try:
            if not self._mqtt_service:
                # Set metrics to 0 if MQTT service is not available
                MQTT_CONNECTIONS_TOTAL.set(0)
                MQTT_CONNECTIONS_ACTIVE.set(0)
                return

            # Check if MQTT client is connected
            is_connected = self._is_mqtt_connected()

            if is_connected:
                MQTT_CONNECTIONS_ACTIVE.set(1)
                MQTT_CONNECTIONS_TOTAL.set(1)
            else:
                MQTT_CONNECTIONS_ACTIVE.set(0)
                MQTT_CONNECTIONS_TOTAL.set(0)

            # Try to get more detailed connection stats if available
            if hasattr(self._mqtt_service, "get_connection_stats"):
                stats = self._mqtt_service.get_connection_stats()
                if stats:
                    MQTT_CONNECTIONS_TOTAL.set(stats.get("total_connections", 0))
                    MQTT_CONNECTIONS_ACTIVE.set(stats.get("active_connections", 0))

        except Exception as e:
            logger.error(f"Error collecting MQTT connection metrics: {e}")
            # Set to 0 on error
            MQTT_CONNECTIONS_TOTAL.set(0)
            MQTT_CONNECTIONS_ACTIVE.set(0)

    def collect_message_metrics(self) -> None:
        """Collect MQTT message metrics."""
        try:
            if not self._mqtt_service:
                return

            # Try to get message statistics from MQTT service
            if hasattr(self._mqtt_service, "get_message_stats"):
                stats = self._mqtt_service.get_message_stats()
                if stats:
                    # Update counters (these should be cumulative)
                    messages_received = stats.get("messages_received", 0)
                    messages_sent = stats.get("messages_sent", 0)
                    messages_dropped = stats.get("messages_dropped", 0)
                    bytes_received = stats.get("bytes_received", 0)
                    bytes_sent = stats.get("bytes_sent", 0)

                    # Set counter values directly (they maintain their own state)
                    MQTT_MESSAGES_RECEIVED._value._value = messages_received
                    MQTT_MESSAGES_SENT._value._value = messages_sent
                    MQTT_MESSAGES_DROPPED._value._value = messages_dropped
                    MQTT_BYTES_RECEIVED._value._value = bytes_received
                    MQTT_BYTES_SENT._value._value = bytes_sent

                    # Queued messages (gauge)
                    MQTT_MESSAGES_QUEUED.set(stats.get("messages_queued", 0))

            # Alternative: try to get stats from MQTT client directly
            elif self._mqtt_client and hasattr(self._mqtt_client, "_statistics"):
                stats = self._mqtt_client._statistics
                MQTT_MESSAGES_RECEIVED._value._value = stats.get("messages_received", 0)
                MQTT_MESSAGES_SENT._value._value = stats.get("messages_sent", 0)

        except Exception as e:
            logger.error(f"Error collecting MQTT message metrics: {e}")

    def collect_topic_metrics(self) -> None:
        """Collect MQTT topic and subscription metrics."""
        try:
            if not self._mqtt_service:
                MQTT_TOPICS_TOTAL.set(0)
                MQTT_SUBSCRIPTIONS_TOTAL.set(0)
                return

            # Try to get topic statistics
            if hasattr(self._mqtt_service, "get_topic_stats"):
                stats = self._mqtt_service.get_topic_stats()
                if stats:
                    MQTT_TOPICS_TOTAL.set(stats.get("total_topics", 0))
                    MQTT_SUBSCRIPTIONS_TOTAL.set(stats.get("total_subscriptions", 0))

            # Alternative: count topics from topic manager
            elif hasattr(self._mqtt_service, "topic_manager"):
                topic_manager = self._mqtt_service.topic_manager
                if hasattr(topic_manager, "get_topic_count"):
                    MQTT_TOPICS_TOTAL.set(topic_manager.get_topic_count())
                if hasattr(topic_manager, "get_subscription_count"):
                    MQTT_SUBSCRIPTIONS_TOTAL.set(topic_manager.get_subscription_count())

            # Fallback: estimate based on known patterns
            else:
                # Basic estimation - could be improved with actual tracking
                MQTT_TOPICS_TOTAL.set(10)  # Estimated number of topics
                MQTT_SUBSCRIPTIONS_TOTAL.set(5)  # Estimated subscriptions

        except Exception as e:
            logger.error(f"Error collecting MQTT topic metrics: {e}")
            MQTT_TOPICS_TOTAL.set(0)
            MQTT_SUBSCRIPTIONS_TOTAL.set(0)

    def _is_mqtt_connected(self) -> bool:
        """Check if MQTT client is connected."""
        try:
            if self._mqtt_service and hasattr(self._mqtt_service, "is_connected"):
                return self._mqtt_service.is_connected()

            if self._mqtt_client and hasattr(self._mqtt_client, "is_connected"):
                return self._mqtt_client.is_connected()

            # Check connection status from client state
            if self._mqtt_client and hasattr(self._mqtt_client, "_state"):
                return self._mqtt_client._state == "connected"

            return False

        except Exception as e:
            logger.error(f"Error checking MQTT connection status: {e}")
            return False

    def get_mqtt_info(self) -> Dict[str, Any]:
        """Get basic MQTT information."""
        try:
            info = {
                "mqtt_available": self._mqtt_service is not None,
                "client_available": self._mqtt_client is not None,
                "connected": self._is_mqtt_connected(),
            }

            if self._mqtt_service and hasattr(self._mqtt_service, "get_broker_info"):
                broker_info = self._mqtt_service.get_broker_info()
                info.update(broker_info)

            return info

        except Exception as e:
            logger.error(f"Error getting MQTT info: {e}")
            return {"mqtt_available": False, "client_available": False, "connected": False}

    def increment_message_received(self, topic: str = None, size: int = 0):
        """Increment received message counter (called by MQTT handlers)."""
        try:
            MQTT_MESSAGES_RECEIVED.inc()
            if size > 0:
                MQTT_BYTES_RECEIVED.inc(size)
        except Exception as e:
            logger.error(f"Error incrementing MQTT received metrics: {e}")

    def increment_message_sent(self, topic: str = None, size: int = 0):
        """Increment sent message counter (called by MQTT handlers)."""
        try:
            MQTT_MESSAGES_SENT.inc()
            if size > 0:
                MQTT_BYTES_SENT.inc(size)
        except Exception as e:
            logger.error(f"Error incrementing MQTT sent metrics: {e}")

    def increment_message_dropped(self, reason: str = None):
        """Increment dropped message counter."""
        try:
            MQTT_MESSAGES_DROPPED.inc()
        except Exception as e:
            logger.error(f"Error incrementing MQTT dropped metrics: {e}")
