"""
MQTT API Routes for IoTFlow
Provides REST endpoints for MQTT management and monitoring
"""

from flask import Blueprint, request, jsonify, current_app
import json
import time
from datetime import datetime

from ..middleware.auth import require_admin_token
from ..middleware.monitoring import request_metrics_middleware
from ..middleware.security import (
    security_headers_middleware,
    input_sanitization_middleware,
)
from ..mqtt.topics import MQTTTopicManager
from ..utils.logging import get_logger

mqtt_bp = Blueprint("mqtt", __name__, url_prefix="/api/v1/mqtt")
logger = get_logger(__name__)


@mqtt_bp.route("/status", methods=["GET"])
def get_mqtt_status():
    """Get MQTT broker and client status"""
    try:
        mqtt_service = getattr(current_app, "mqtt_service", None)

        if not mqtt_service:
            return (
                jsonify({"error": "MQTT service not initialized", "status": "unavailable"}),
                503,
            )

        status = mqtt_service.get_connection_status()

        return jsonify(
            {
                "status": "success",
                "mqtt_status": status,
                "broker_info": {
                    "host": status["host"],
                    "port": status["port"],
                    "connected": status["connected"],
                    "tls_enabled": status["use_tls"],
                },
            }
        )

    except Exception as e:
        logger.error(f"Error getting MQTT status: {e}")
        return jsonify({"error": "Failed to get MQTT status", "message": str(e)}), 500


@mqtt_bp.route("/publish", methods=["POST"])
def publish_message():
    """Publish a message to MQTT broker"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["topic", "payload"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        topic = data["topic"]
        payload = data["payload"]
        qos = data.get("qos", 1)
        retain = data.get("retain", False)

        # Validate topic
        if not MQTTTopicManager.validate_topic(topic):
            return jsonify({"error": "Invalid topic format", "topic": topic}), 400

        # Get MQTT service
        mqtt_service = getattr(current_app, "mqtt_service", None)
        if not mqtt_service:
            return jsonify({"error": "MQTT service not available"}), 503

        # Publish message
        success = mqtt_service.publish(topic, payload, qos=qos, retain=retain)

        if success:
            logger.info(f"Published message to topic: {topic}")
            return jsonify(
                {
                    "status": "success",
                    "message": "Message published successfully",
                    "topic": topic,
                    "qos": qos,
                    "retain": retain,
                }
            )
        else:
            return jsonify({"error": "Failed to publish message", "topic": topic}), 500

    except Exception as e:
        logger.error(f"Error publishing MQTT message: {e}")
        return jsonify({"error": "Failed to publish message", "message": str(e)}), 500


@mqtt_bp.route("/subscribe", methods=["POST"])
@require_admin_token
def subscribe_to_topic():
    """Subscribe to an MQTT topic (admin only)"""
    try:
        data = request.get_json()

        # Validate required fields
        if "topic" not in data:
            return jsonify({"error": "Missing required field: topic"}), 400

        topic = data["topic"]
        qos = data.get("qos", 1)

        # Get MQTT service
        mqtt_service = getattr(current_app, "mqtt_service", None)
        if not mqtt_service:
            return jsonify({"error": "MQTT service not available"}), 503

        # Subscribe to topic
        success = mqtt_service.subscribe(topic, qos=qos)

        if success:
            logger.info(f"Subscribed to topic: {topic}")
            return jsonify(
                {
                    "status": "success",
                    "message": "Subscribed successfully",
                    "topic": topic,
                    "qos": qos,
                }
            )
        else:
            return (
                jsonify({"error": "Failed to subscribe to topic", "topic": topic}),
                500,
            )

    except Exception as e:
        logger.error(f"Error subscribing to MQTT topic: {e}")
        return jsonify({"error": "Failed to subscribe", "message": str(e)}), 500


@mqtt_bp.route("/topics/device/<device_id>", methods=["GET"])
def get_device_topics(device_id: str):
    """Get all MQTT topics for a specific device"""
    try:
        # Validate device_id format
        if not device_id or len(device_id) < 3:
            return jsonify({"error": "Invalid device ID format"}), 400

        # Get device topics
        device_topics = MQTTTopicManager.get_device_topics(device_id)

        # Organize topics by type
        organized_topics = {}
        for topic_name, topic_path in device_topics.items():
            topic_structure = MQTTTopicManager.get_topic_structure(topic_name)
            topic_type = topic_structure.topic_type.value

            if topic_type not in organized_topics:
                organized_topics[topic_type] = []

            organized_topics[topic_type].append(
                {
                    "name": topic_name,
                    "path": topic_path,
                    "qos": topic_structure.qos.value,
                    "retain": topic_structure.retain,
                    "description": topic_structure.description,
                }
            )

        return jsonify(
            {
                "status": "success",
                "device_id": device_id,
                "topics": organized_topics,
                "total_topics": len(device_topics),
            }
        )

    except Exception as e:
        logger.error(f"Error getting device topics: {e}")
        return jsonify({"error": "Failed to get device topics", "message": str(e)}), 500


@mqtt_bp.route("/topics/structure", methods=["GET"])
def get_topic_structure():
    """Get the complete MQTT topic structure"""
    try:
        # Get wildcard patterns
        patterns = MQTTTopicManager.get_wildcard_patterns()

        # Get all topic structures
        structures = {}
        for topic_name, structure in MQTTTopicManager.TOPIC_STRUCTURES.items():
            structures[topic_name] = {
                "base_path": structure.base_path,
                "topic_type": structure.topic_type.value,
                "qos": structure.qos.value,
                "retain": structure.retain,
                "description": structure.description,
                "full_topic_example": f"{MQTTTopicManager.BASE_TOPIC}/{structure.base_path}",
            }

        return jsonify(
            {
                "status": "success",
                "base_topic": MQTTTopicManager.BASE_TOPIC,
                "wildcard_patterns": patterns,
                "topic_structures": structures,
                "total_structures": len(structures),
            }
        )

    except Exception as e:
        logger.error(f"Error getting topic structure: {e}")
        return (
            jsonify({"error": "Failed to get topic structure", "message": str(e)}),
            500,
        )


@mqtt_bp.route("/topics/validate", methods=["POST"])
def validate_topic():
    """Validate an MQTT topic"""
    try:
        data = request.get_json()

        if "topic" not in data:
            return jsonify({"error": "Missing required field: topic"}), 400

        topic = data["topic"]

        # Validate topic
        is_valid = MQTTTopicManager.validate_topic(topic)
        parsed_topic = MQTTTopicManager.parse_topic(topic) if is_valid else None

        response = {
            "status": "success",
            "topic": topic,
            "is_valid": is_valid,
            "parsed": parsed_topic,
        }

        if not is_valid:
            response["validation_errors"] = []

            # Check specific validation issues
            if not topic.startswith(f"{MQTTTopicManager.BASE_TOPIC}/"):
                response["validation_errors"].append(f"Topic must start with '{MQTTTopicManager.BASE_TOPIC}/'")

            if len(topic.encode("utf-8")) > 65535:
                response["validation_errors"].append("Topic too long (max 65535 bytes)")

            invalid_chars = ["+", "#", "\0"]
            for char in invalid_chars:
                if char in topic.replace(f"{MQTTTopicManager.BASE_TOPIC}/", ""):
                    response["validation_errors"].append(f"Invalid character: '{char}'")

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error validating topic: {e}")
        return jsonify({"error": "Failed to validate topic", "message": str(e)}), 500


@mqtt_bp.route("/device/<device_id>/command", methods=["POST"])
@require_admin_token
def send_device_command(device_id: str):
    """Send a command to a specific device via MQTT"""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["command_type", "command"]
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        command_type = data["command_type"]
        command = data["command"]
        qos = data.get("qos", 2)  # Use QoS 2 for commands to ensure delivery

        # Validate command type
        valid_command_types = ["config", "control", "firmware"]
        if command_type not in valid_command_types:
            return (
                jsonify({"error": f"Invalid command type. Must be one of: {valid_command_types}"}),
                400,
            )

        # Get command topic
        topic_name = f"device_commands_{command_type}"
        try:
            topic = MQTTTopicManager.get_topic(topic_name, device_id=device_id)
        except (KeyError, ValueError) as e:
            return jsonify({"error": f"Invalid topic configuration: {str(e)}"}), 400

        # Prepare command payload
        command_payload = {
            "command": command,
            "timestamp": data.get("timestamp"),
            "command_id": data.get("command_id"),
            "source": "iotflow_api",
        }

        # Get MQTT service
        mqtt_service = getattr(current_app, "mqtt_service", None)
        if not mqtt_service:
            return jsonify({"error": "MQTT service not available"}), 503

        # Send command
        success = mqtt_service.publish(topic, command_payload, qos=qos, retain=True)

        if success:
            logger.info(f"Sent {command_type} command to device {device_id}")
            return jsonify(
                {
                    "status": "success",
                    "message": "Command sent successfully",
                    "device_id": device_id,
                    "command_type": command_type,
                    "topic": topic,
                    "qos": qos,
                }
            )
        else:
            return (
                jsonify(
                    {
                        "error": "Failed to send command",
                        "device_id": device_id,
                        "command_type": command_type,
                    }
                ),
                500,
            )

    except Exception as e:
        logger.error(f"Error sending device command: {e}")
        return jsonify({"error": "Failed to send command", "message": str(e)}), 500


@mqtt_bp.route("/fleet/<group_id>/command", methods=["POST"])
@require_admin_token
def send_fleet_command(group_id: str):
    """Send a command to a fleet/group of devices via MQTT (admin only)"""
    try:
        data = request.get_json()

        # Validate required fields
        if "command" not in data:
            return jsonify({"error": "Missing required field: command"}), 400

        command = data["command"]
        qos = data.get("qos", 2)

        # Get fleet command topic
        try:
            topic = MQTTTopicManager.get_topic("fleet_commands", group_id=group_id)
        except (KeyError, ValueError) as e:
            return jsonify({"error": f"Invalid topic configuration: {str(e)}"}), 400

        # Prepare command payload
        command_payload = {
            "command": command,
            "timestamp": data.get("timestamp"),
            "command_id": data.get("command_id"),
            "group_id": group_id,
            "source": "iotflow_api",
        }

        # Get MQTT service
        mqtt_service = getattr(current_app, "mqtt_service", None)
        if not mqtt_service:
            return jsonify({"error": "MQTT service not available"}), 503

        # Send fleet command
        success = mqtt_service.publish(topic, command_payload, qos=qos, retain=True)

        if success:
            logger.info(f"Sent fleet command to group {group_id}")
            return jsonify(
                {
                    "status": "success",
                    "message": "Fleet command sent successfully",
                    "group_id": group_id,
                    "topic": topic,
                    "qos": qos,
                }
            )
        else:
            return (
                jsonify({"error": "Failed to send fleet command", "group_id": group_id}),
                500,
            )

    except Exception as e:
        logger.error(f"Error sending fleet command: {e}")
        return (
            jsonify({"error": "Failed to send fleet command", "message": str(e)}),
            500,
        )


@mqtt_bp.route("/monitoring/metrics", methods=["GET"])
@require_admin_token
def get_mqtt_metrics():
    """Get comprehensive MQTT monitoring metrics (admin only)"""
    try:
        mqtt_service = getattr(current_app, "mqtt_service", None)
        if not mqtt_service:
            return jsonify({"error": "MQTT service not available"}), 503

        # Get comprehensive connection status and statistics
        status = mqtt_service.get_connection_status()

        # Get Prometheus-style metrics
        prometheus_metrics = _get_prometheus_mqtt_metrics(mqtt_service)

        # Get broker information
        broker_info = _get_broker_information(mqtt_service)

        # Get topic management metrics
        topic_metrics = _get_topic_management_metrics(mqtt_service)

        # Get handler performance metrics
        handler_metrics = _get_handler_performance_metrics(mqtt_service)

        # Get security and authentication metrics
        security_metrics = _get_security_metrics(mqtt_service)

        comprehensive_metrics = {
            "overview": {
                "service_status": "available" if mqtt_service else "unavailable",
                "connection_healthy": status.get("connected", False),
                "uptime_seconds": status.get("connections", {}).get("uptime_seconds", 0),
                "last_activity": status.get("messages", {}).get("last_message_time"),
                "total_throughput": status.get("performance", {}).get("messages_per_second", 0),
            },
            "connection_metrics": {
                "broker_connection": {
                    "host": status.get("host"),
                    "port": status.get("port"),
                    "client_id": status.get("client_id"),
                    "connected": status.get("connected", False),
                    "use_tls": status.get("use_tls", False),
                    "connection_count": status.get("connections", {}).get("total_connections", 0),
                    "reconnection_count": status.get("connections", {}).get("reconnections", 0),
                    "active_connections": status.get("connections", {}).get("active_connections", 0),
                },
                "connection_quality": {
                    "stability_score": _calculate_connection_stability(status),
                    "reconnection_rate": _calculate_reconnection_rate(status),
                    "connection_success_rate": _calculate_connection_success_rate(status),
                },
            },
            "message_metrics": {
                "throughput": {
                    "messages_sent": status.get("messages", {}).get("sent", 0),
                    "messages_received": status.get("messages", {}).get("received", 0),
                    "messages_failed": status.get("messages", {}).get("failed", 0),
                    "messages_per_second": status.get("performance", {}).get("messages_per_second", 0),
                    "total_messages": status.get("messages", {}).get("sent", 0)
                    + status.get("messages", {}).get("received", 0),
                },
                "data_transfer": {
                    "bytes_sent": status.get("data_transfer", {}).get("bytes_sent", 0),
                    "bytes_received": status.get("data_transfer", {}).get("bytes_received", 0),
                    "total_bytes": status.get("data_transfer", {}).get("total_bytes", 0),
                    "bytes_per_second": status.get("performance", {}).get("bytes_per_second", 0),
                    "average_message_size": status.get("performance", {}).get("average_message_size", 0),
                },
                "quality_metrics": {
                    "success_rate": _calculate_message_success_rate(status),
                    "failure_rate": _calculate_message_failure_rate(status),
                    "error_ratio": _calculate_error_ratio(status),
                },
            },
            "topic_metrics": topic_metrics,
            "subscription_metrics": {
                "active_subscriptions": status.get("topics", {}).get("active_subscriptions", 0),
                "subscription_details": status.get("topics", {}).get("subscription_details", {}),
                "subscription_health": _analyze_subscription_health(status),
                "callback_performance": _analyze_callback_performance(status),
            },
            "broker_metrics": broker_info,
            "handler_metrics": handler_metrics,
            "security_metrics": security_metrics,
            "prometheus_metrics": prometheus_metrics,
            "performance_analysis": {
                "bottlenecks": _identify_performance_bottlenecks(status),
                "recommendations": _generate_performance_recommendations(status),
                "health_score": _calculate_overall_health_score(status),
            },
        }

        return jsonify(
            {
                "status": "success",
                "metrics": comprehensive_metrics,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "collection_time_ms": _get_collection_time(),
                    "metrics_version": "2.0",
                    "total_metric_count": _count_total_metrics(comprehensive_metrics),
                },
            }
        )

    except Exception as e:
        logger.error(f"Error getting comprehensive MQTT metrics: {e}")
        return (
            jsonify(
                {"error": "Failed to get MQTT metrics", "message": str(e), "timestamp": datetime.utcnow().isoformat()}
            ),
            500,
        )


def _get_prometheus_mqtt_metrics(mqtt_service):
    """Get Prometheus-compatible MQTT metrics"""
    status = mqtt_service.get_connection_status()

    return {
        "mqtt_connections_total": status.get("connections", {}).get("total_connections", 0),
        "mqtt_connections_active": status.get("connections", {}).get("active_connections", 0),
        "mqtt_messages_sent_total": status.get("messages", {}).get("sent", 0),
        "mqtt_messages_received_total": status.get("messages", {}).get("received", 0),
        "mqtt_messages_failed_total": status.get("messages", {}).get("failed", 0),
        "mqtt_bytes_sent_total": status.get("data_transfer", {}).get("bytes_sent", 0),
        "mqtt_bytes_received_total": status.get("data_transfer", {}).get("bytes_received", 0),
        "mqtt_topics_total": status.get("topics", {}).get("total_topics", 0),
        "mqtt_subscriptions_total": status.get("topics", {}).get("active_subscriptions", 0),
        "mqtt_reconnections_total": status.get("connections", {}).get("reconnections", 0),
        "mqtt_uptime_seconds": status.get("connections", {}).get("uptime_seconds", 0),
        "mqtt_message_rate": status.get("performance", {}).get("messages_per_second", 0),
        "mqtt_data_rate_bytes": status.get("performance", {}).get("bytes_per_second", 0),
    }


def _get_broker_information(mqtt_service):
    """Get detailed broker information and capabilities"""
    status = mqtt_service.get_connection_status()

    return {
        "broker_details": {
            "host": status.get("host"),
            "port": status.get("port"),
            "protocol_version": "MQTT 3.1.1",  # Default for paho-mqtt
            "tls_enabled": status.get("use_tls", False),
            "clean_session": mqtt_service.config.clean_session if hasattr(mqtt_service, "config") else True,
        },
        "broker_capabilities": {
            "max_qos": 2,
            "retain_available": True,
            "wildcard_subscriptions": True,
            "subscription_identifiers": False,
            "shared_subscriptions": False,
        },
        "broker_limits": {
            "max_packet_size": mqtt_service.config.max_inflight_messages if hasattr(mqtt_service, "config") else 20,
            "topic_alias_maximum": 0,
            "receive_maximum": mqtt_service.config.max_inflight_messages if hasattr(mqtt_service, "config") else 20,
        },
    }


def _get_topic_management_metrics(mqtt_service):
    """Get comprehensive topic management metrics"""
    status = mqtt_service.get_connection_status()
    topics_info = status.get("topics", {})

    return {
        "topic_statistics": {
            "total_unique_topics": topics_info.get("total_topics", 0),
            "device_topics": topics_info.get("topic_structure", {}).get("device_topics", 0),
            "system_topics": topics_info.get("topic_structure", {}).get("system_topics", 0),
            "topic_hierarchy_levels": topics_info.get("topic_structure", {}).get("levels", {}),
            "common_patterns": topics_info.get("topic_structure", {}).get("patterns", []),
        },
        "topic_activity": {
            "most_active_topics": _get_most_active_topics(topics_info),
            "topic_message_distribution": _analyze_topic_message_distribution(topics_info),
            "unused_topics": _identify_unused_topics(topics_info),
        },
        "topic_management": {
            "base_topic": MQTTTopicManager.BASE_TOPIC,
            "total_topic_structures": len(MQTTTopicManager.TOPIC_STRUCTURES),
            "available_topic_types": list(MQTTTopicManager.TOPIC_STRUCTURES.keys()),
        },
    }


def _get_handler_performance_metrics(mqtt_service):
    """Get message handler performance metrics"""
    return {
        "handler_statistics": {
            "total_handlers": len(mqtt_service.message_handlers),
            "handler_types": [handler.__class__.__name__ for handler in mqtt_service.message_handlers],
            "callback_count": len(mqtt_service.subscription_callbacks),
        },
        "handler_performance": {
            "average_processing_time": _calculate_average_handler_time(),
            "handler_success_rate": _calculate_handler_success_rate(),
            "handler_error_count": _get_handler_error_count(),
        },
    }


def _get_security_metrics(mqtt_service):
    """Get security and authentication metrics"""
    auth_service = getattr(mqtt_service, "auth_service", None)

    return {
        "authentication": {
            "auth_service_available": auth_service is not None,
            "auth_method": "username_password" if mqtt_service.config.username else "none",
            "tls_enabled": mqtt_service.config.use_tls,
        },
        "security_features": {
            "message_encryption": mqtt_service.config.use_tls,
            "client_certificates": bool(mqtt_service.config.cert_file_path),
            "ca_verification": bool(mqtt_service.config.ca_cert_path),
        },
    }


def _calculate_connection_stability(status):
    """Calculate connection stability score (0-100)"""
    connections = status.get("connections", {})
    total_connections = connections.get("total_connections", 1)
    reconnections = connections.get("reconnections", 0)

    if total_connections == 0:
        return 0

    stability = max(0, 100 - (reconnections / total_connections * 100))
    return round(stability, 2)


def _calculate_reconnection_rate(status):
    """Calculate reconnection rate per hour"""
    connections = status.get("connections", {})
    uptime_hours = connections.get("uptime_seconds", 0) / 3600
    reconnections = connections.get("reconnections", 0)

    if uptime_hours == 0:
        return 0

    return round(reconnections / uptime_hours, 2)


def _calculate_connection_success_rate(status):
    """Calculate connection success rate"""
    connections = status.get("connections", {})
    total_attempts = connections.get("total_connections", 0) + connections.get("reconnections", 0)
    successful = connections.get("total_connections", 0)

    if total_attempts == 0:
        return 100

    return round((successful / total_attempts) * 100, 2)


def _calculate_message_success_rate(status):
    """Calculate message success rate"""
    messages = status.get("messages", {})
    total_sent = messages.get("sent", 0)
    failed = messages.get("failed", 0)

    if total_sent == 0:
        return 100

    successful = total_sent - failed
    return round((successful / total_sent) * 100, 2)


def _calculate_message_failure_rate(status):
    """Calculate message failure rate"""
    return 100 - _calculate_message_success_rate(status)


def _calculate_error_ratio(status):
    """Calculate error ratio (failures per successful message)"""
    messages = status.get("messages", {})
    successful = messages.get("sent", 0) + messages.get("received", 0) - messages.get("failed", 0)
    failed = messages.get("failed", 0)

    if successful == 0:
        return 0 if failed == 0 else float("inf")

    return round(failed / successful, 4)


def _analyze_subscription_health(status):
    """Analyze subscription health"""
    subscriptions = status.get("topics", {}).get("subscription_details", {})

    health_info = {"healthy_subscriptions": 0, "stale_subscriptions": 0, "callback_issues": 0}

    current_time = time.time()
    for topic, details in subscriptions.items():
        subscribed_at = details.get("subscribed_at", current_time)
        age_hours = (current_time - subscribed_at) / 3600

        if age_hours > 24:  # Subscriptions older than 24 hours
            health_info["stale_subscriptions"] += 1
        else:
            health_info["healthy_subscriptions"] += 1

        if details.get("callback_count", 0) == 0:
            health_info["callback_issues"] += 1

    return health_info


def _analyze_callback_performance(status):
    """Analyze callback performance"""
    subscriptions = status.get("topics", {}).get("subscription_details", {})

    total_callbacks = sum(details.get("callback_count", 0) for details in subscriptions.values())
    avg_callbacks_per_subscription = total_callbacks / len(subscriptions) if subscriptions else 0

    return {
        "total_callbacks": total_callbacks,
        "average_callbacks_per_subscription": round(avg_callbacks_per_subscription, 2),
        "subscriptions_without_callbacks": len([s for s in subscriptions.values() if s.get("callback_count", 0) == 0]),
    }


def _get_most_active_topics(topics_info):
    """Get most active topics (placeholder - would need message tracking per topic)"""
    unique_topics = topics_info.get("unique_topics", [])
    return unique_topics[:5]  # Return first 5 as most active (placeholder)


def _analyze_topic_message_distribution(topics_info):
    """Analyze message distribution across topics"""
    total_topics = topics_info.get("total_topics", 0)
    device_topics = topics_info.get("topic_structure", {}).get("device_topics", 0)
    system_topics = topics_info.get("topic_structure", {}).get("system_topics", 0)

    return {
        "device_topic_percentage": round((device_topics / total_topics * 100) if total_topics > 0 else 0, 2),
        "system_topic_percentage": round((system_topics / total_topics * 100) if total_topics > 0 else 0, 2),
        "other_topic_percentage": round(
            ((total_topics - device_topics - system_topics) / total_topics * 100) if total_topics > 0 else 0, 2
        ),
    }


def _identify_unused_topics(topics_info):
    """Identify potentially unused topics"""
    # Placeholder - would need activity tracking per topic
    return []


def _calculate_average_handler_time():
    """Calculate average handler processing time (placeholder)"""
    return 0.05  # 50ms placeholder


def _calculate_handler_success_rate():
    """Calculate handler success rate (placeholder)"""
    return 99.5  # 99.5% placeholder


def _get_handler_error_count():
    """Get handler error count (placeholder)"""
    return 0  # Placeholder


def _identify_performance_bottlenecks(status):
    """Identify potential performance bottlenecks"""
    bottlenecks = []

    # Check message failure rate
    failure_rate = _calculate_message_failure_rate(status)
    if failure_rate > 5:
        bottlenecks.append(f"High message failure rate: {failure_rate}%")

    # Check reconnection rate
    reconnection_rate = _calculate_reconnection_rate(status)
    if reconnection_rate > 1:
        bottlenecks.append(f"High reconnection rate: {reconnection_rate}/hour")

    # Check average message size
    avg_size = status.get("performance", {}).get("average_message_size", 0)
    if avg_size > 1024:  # Messages larger than 1KB
        bottlenecks.append(f"Large average message size: {avg_size} bytes")

    return bottlenecks


def _generate_performance_recommendations(status):
    """Generate performance improvement recommendations"""
    recommendations = []

    # Check connection stability
    stability = _calculate_connection_stability(status)
    if stability < 95:
        recommendations.append("Consider improving network stability or broker configuration")

    # Check message throughput
    msg_rate = status.get("performance", {}).get("messages_per_second", 0)
    if msg_rate < 1:
        recommendations.append("Low message throughput - consider optimizing message publishing")

    # Check subscription count
    sub_count = status.get("topics", {}).get("active_subscriptions", 0)
    if sub_count > 100:
        recommendations.append("High subscription count - consider subscription optimization")

    return recommendations


def _calculate_overall_health_score(status):
    """Calculate overall MQTT health score (0-100)"""
    scores = []

    # Connection stability (30% weight)
    connection_score = _calculate_connection_stability(status)
    scores.append(connection_score * 0.3)

    # Message success rate (40% weight)
    message_score = _calculate_message_success_rate(status)
    scores.append(message_score * 0.4)

    # Performance score (30% weight)
    msg_rate = status.get("performance", {}).get("messages_per_second", 0)
    performance_score = min(100, msg_rate * 10)  # Scale message rate to 0-100
    scores.append(performance_score * 0.3)

    return round(sum(scores), 2)


def _get_collection_time():
    """Get metrics collection time in milliseconds"""
    return 50  # Placeholder - would measure actual collection time


def _count_total_metrics(metrics_dict):
    """Count total number of metrics in the response"""
    count = 0
    for value in metrics_dict.values():
        if isinstance(value, dict):
            count += _count_total_metrics(value)
        else:
            count += 1
    return count


@mqtt_bp.route("/telemetry/<int:device_id>", methods=["POST"])
@security_headers_middleware()
@request_metrics_middleware()
@input_sanitization_middleware()
def mqtt_telemetry(device_id):
    """
    MQTT Telemetry endpoint with API key authentication
    This endpoint accepts telemetry data from devices and validates API key server-side
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Get API key from headers
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            return (
                jsonify(
                    {
                        "error": "API key required",
                        "message": "Include X-API-Key header with your device API key",
                    }
                ),
                401,
            )

        # Get MQTT auth service
        mqtt_auth_service = getattr(current_app, "mqtt_auth_service", None)
        if not mqtt_auth_service:
            return jsonify({"error": "MQTT authentication service not available"}), 503

        # Validate device and API key
        device = mqtt_auth_service.authenticate_device_by_api_key(api_key)
        if not device or device.id != device_id:
            return (
                jsonify(
                    {
                        "error": "Invalid API key or device ID mismatch",
                        "device_id": device_id,
                    }
                ),
                401,
            )

        # Extract telemetry data
        telemetry_data = data.get("data", {})
        timestamp_str = data.get("timestamp")

        if not telemetry_data:
            return (
                jsonify(
                    {
                        "error": "Telemetry data is required",
                        "message": 'Include "data" field with sensor readings',
                    }
                ),
                400,
            )

        # Create MQTT topic for telemetry
        topic = f"iotflow/devices/{device_id}/telemetry"

        # Handle telemetry message through MQTT auth service
        success = mqtt_auth_service.handle_telemetry_message(
            device_id=device_id, api_key=api_key, topic=topic, payload=json.dumps(data)
        )

        if success:
            return (
                jsonify(
                    {
                        "status": "success",
                        "message": "Telemetry data processed successfully",
                        "device_id": device_id,
                        "device_name": device.name,
                        "topic": topic,
                        "timestamp": timestamp_str or datetime.utcnow().isoformat(),
                    }
                ),
                201,
            )
        else:
            return (
                jsonify(
                    {
                        "error": "Failed to process telemetry data",
                        "message": "Check device authorization and data format",
                    }
                ),
                400,
            )

    except Exception as e:
        logger.error(f"Error processing MQTT telemetry: {e}")
        return (
            jsonify(
                {
                    "error": "Internal server error",
                    "message": "Failed to process telemetry data",
                }
            ),
            500,
        )
