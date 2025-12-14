#!/usr/bin/env python3
"""
Real-time Metrics Monitor for IoTFlow

This script displays key metrics in real-time from the /metrics endpoint.
Run this to monitor Redis, IoTDB, MQTT, and system health.
"""

import requests
import time
import os
import sys


def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')


def get_metric_value(metrics_text, metric_name, label_filter=None):
    """Extract a metric value from Prometheus text format"""
    for line in metrics_text.split('\n'):
        if line.startswith(metric_name):
            # Handle metrics with labels
            if label_filter and '{' in line:
                if all(f'{k}="{v}"' in line for k, v in label_filter.items()):
                    parts = line.split()
                    if len(parts) >= 2:
                        return float(parts[-1])
            # Handle simple metrics
            elif ' ' in line:
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        return float(parts[-1])
                    except ValueError:
                        continue
    return None


def format_bytes(bytes_value):
    """Format bytes to human-readable format"""
    if bytes_value is None:
        return "N/A"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.2f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.2f} PB"


def get_status_icon(status_value):
    """Get status icon based on value"""
    if status_value is None:
        return "❓"
    return "🟢" if status_value == 1.0 else "🔴"


def monitor(base_url="http://localhost:5000", admin_token="test", interval=5):
    """Main monitoring loop"""
    url = f"{base_url}/metrics"
    headers = {"Authorization": f"admin {admin_token}"}
    
    print("Starting IoTFlow Metrics Monitor...")
    print("Press Ctrl+C to exit\n")
    time.sleep(2)
    
    error_count = 0
    max_errors = 3
    
    while True:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            metrics = response.text
            error_count = 0  # Reset error count on success
            
            clear_screen()
            print("=" * 70)
            print("                IoTFlow Real-time Metrics Monitor")
            print("=" * 70)
            print(f"⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}".ljust(50), end="")
            print(f"🔄 Refresh: {interval}s")
            print("=" * 70)
            
            # Redis Metrics
            print("\n🔴 REDIS CACHE")
            print("-" * 70)
            redis_status = get_metric_value(metrics, 'redis_status')
            redis_memory = get_metric_value(metrics, 'redis_memory_used_bytes')
            redis_keys = get_metric_value(metrics, 'redis_keys_total')
            redis_hits = get_metric_value(metrics, 'redis_cache_hits_total')
            redis_misses = get_metric_value(metrics, 'redis_cache_misses_total')
            
            print(f"  Status:     {get_status_icon(redis_status)} {'UP' if redis_status == 1.0 else 'DOWN'}")
            print(f"  Memory:     {format_bytes(redis_memory)}")
            print(f"  Keys:       {redis_keys:.0f}" if redis_keys else "  Keys:       N/A")
            
            if redis_hits is not None and redis_misses is not None:
                total = redis_hits + redis_misses
                hit_rate = (redis_hits / total * 100) if total > 0 else 0
                print(f"  Hit Rate:   {hit_rate:.1f}%")
            
            # IoTDB Metrics
            print("\n💾 IOTDB TIME-SERIES DATABASE")
            print("-" * 70)
            iotdb_status = get_metric_value(metrics, 'iotdb_connection_status')
            iotdb_query_rate = get_metric_value(metrics, 'iotdb_query_success_rate')
            iotdb_write_rate = get_metric_value(metrics, 'iotdb_write_success_rate')
            
            print(f"  Status:           {get_status_icon(iotdb_status)} {'Connected' if iotdb_status == 1.0 else 'Disconnected'}")
            print(f"  Query Success:    {iotdb_query_rate:.1f}%" if iotdb_query_rate else "  Query Success:    N/A")
            print(f"  Write Success:    {iotdb_write_rate:.1f}%" if iotdb_write_rate else "  Write Success:    N/A")
            
            # MQTT Metrics
            print("\n📡 MQTT BROKER")
            print("-" * 70)
            mqtt_connections = get_metric_value(metrics, 'mqtt_connections_active')
            mqtt_topics = get_metric_value(metrics, 'mqtt_topics_total')
            mqtt_subscriptions = get_metric_value(metrics, 'mqtt_subscriptions_total')
            mqtt_received = get_metric_value(metrics, 'mqtt_messages_received_total')
            mqtt_sent = get_metric_value(metrics, 'mqtt_messages_sent_total')
            
            print(f"  Active Connections:  {mqtt_connections:.0f}" if mqtt_connections else "  Active Connections:  N/A")
            print(f"  Topics:              {mqtt_topics:.0f}" if mqtt_topics else "  Topics:              N/A")
            print(f"  Subscriptions:       {mqtt_subscriptions:.0f}" if mqtt_subscriptions else "  Subscriptions:       N/A")
            print(f"  Messages Received:   {mqtt_received:.0f}" if mqtt_received else "  Messages Received:   N/A")
            print(f"  Messages Sent:       {mqtt_sent:.0f}" if mqtt_sent else "  Messages Sent:       N/A")
            
            # System Metrics
            print("\n🖥️  SYSTEM RESOURCES")
            print("-" * 70)
            cpu_usage = get_metric_value(metrics, 'system_cpu_usage_percent')
            memory_usage = get_metric_value(metrics, 'system_memory_usage_percent')
            memory_total = get_metric_value(metrics, 'system_memory_total_bytes')
            memory_used = get_metric_value(metrics, 'system_memory_used_bytes')
            load_1min = get_metric_value(metrics, 'system_load_average', {'period': '1min'})
            
            if cpu_usage:
                cpu_bar = "█" * int(cpu_usage / 5) + "░" * (20 - int(cpu_usage / 5))
                print(f"  CPU Usage:    [{cpu_bar}] {cpu_usage:.1f}%")
            
            if memory_usage:
                mem_bar = "█" * int(memory_usage / 5) + "░" * (20 - int(memory_usage / 5))
                print(f"  Memory:       [{mem_bar}] {memory_usage:.1f}%")
                if memory_used and memory_total:
                    print(f"                {format_bytes(memory_used)} / {format_bytes(memory_total)}")
            
            if load_1min:
                print(f"  Load Avg:     {load_1min:.2f}")
            
            # IoTFlow Application Metrics
            print("\n📊 IOTFLOW APPLICATION")
            print("-" * 70)
            total_devices = get_metric_value(metrics, 'iotflow_devices_total')
            active_devices = get_metric_value(metrics, 'iotflow_devices_active')
            online_devices = get_metric_value(metrics, 'iotflow_devices_online')
            total_users = get_metric_value(metrics, 'iotflow_users_total')
            telemetry_messages = get_metric_value(metrics, 'iotflow_telemetry_messages_total')
            
            print(f"  Total Devices:       {total_devices:.0f}" if total_devices else "  Total Devices:       0")
            print(f"  Active Devices:      {active_devices:.0f}" if active_devices else "  Active Devices:      0")
            print(f"  Online Devices:      {online_devices:.0f}" if online_devices else "  Online Devices:      0")
            print(f"  Total Users:         {total_users:.0f}" if total_users else "  Total Users:         0")
            print(f"  Telemetry Messages:  {telemetry_messages:.0f}" if telemetry_messages else "  Telemetry Messages:  0")
            
            # HTTP Metrics
            print("\n🌐 HTTP API")
            print("-" * 70)
            http_requests = get_metric_value(metrics, 'http_requests_total')
            requests_in_progress = get_metric_value(metrics, 'http_requests_in_progress')
            
            print(f"  Total Requests:      {http_requests:.0f}" if http_requests else "  Total Requests:      N/A")
            print(f"  In Progress:         {requests_in_progress:.0f}" if requests_in_progress else "  In Progress:         0")
            
            print("\n" + "=" * 70)
            print("Press Ctrl+C to exit | Monitoring endpoint: " + url)
            print("=" * 70)
            
            time.sleep(interval)
            
        except requests.exceptions.ConnectionError:
            error_count += 1
            clear_screen()
            print("=" * 70)
            print("❌ CONNECTION ERROR")
            print("=" * 70)
            print(f"\nCannot connect to Flask server at {base_url}")
            print("\nPlease ensure:")
            print("  1. Flask server is running")
            print("  2. Server is accessible at the specified URL")
            print(f"  3. Admin token is correct: '{admin_token}'")
            print(f"\nRetrying in {interval} seconds... (attempt {error_count}/{max_errors})")
            
            if error_count >= max_errors:
                print("\n❌ Maximum connection errors reached. Exiting...")
                sys.exit(1)
            
            time.sleep(interval)
            
        except requests.exceptions.HTTPError as e:
            error_count += 1
            clear_screen()
            print("=" * 70)
            print("❌ HTTP ERROR")
            print("=" * 70)
            print(f"\nHTTP Error: {e}")
            print(f"Status Code: {e.response.status_code}")
            
            if e.response.status_code == 401:
                print("\n❌ Authentication failed. Check your admin token.")
                sys.exit(1)
            
            print(f"\nRetrying in {interval} seconds...")
            time.sleep(interval)
            
        except KeyboardInterrupt:
            clear_screen()
            print("\n" + "=" * 70)
            print("🛑 Monitoring stopped by user")
            print("=" * 70)
            print("\nThank you for using IoTFlow Metrics Monitor!")
            print()
            break
            
        except Exception as e:
            error_count += 1
            clear_screen()
            print("=" * 70)
            print("❌ UNEXPECTED ERROR")
            print("=" * 70)
            print(f"\nError: {e}")
            print(f"\nRetrying in {interval} seconds...")
            
            if error_count >= max_errors:
                print("\n❌ Maximum errors reached. Exiting...")
                raise
            
            time.sleep(interval)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Real-time metrics monitor for IoTFlow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s
  %(prog)s --url http://localhost:5000 --token mytoken
  %(prog)s --interval 10
        """
    )
    
    parser.add_argument(
        '--url',
        default='http://localhost:5000',
        help='Base URL of the Flask server (default: http://localhost:5000)'
    )
    
    parser.add_argument(
        '--token',
        default='test',
        help='Admin authentication token (default: test)'
    )
    
    parser.add_argument(
        '--interval',
        type=int,
        default=5,
        help='Refresh interval in seconds (default: 5)'
    )
    
    args = parser.parse_args()
    
    try:
        monitor(base_url=args.url, admin_token=args.token, interval=args.interval)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
