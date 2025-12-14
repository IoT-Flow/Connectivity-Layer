#!/usr/bin/env python3
"""
Metrics API Demo - How to Use the IoTFlow Prometheus Metrics Endpoint

This script demonstrates how to fetch and parse metrics from the /metrics endpoint.
"""

import requests
import re
from typing import Dict, List, Tuple


class MetricsClient:
    """Client for fetching and parsing Prometheus metrics"""
    
    def __init__(self, base_url: str = "http://localhost:5000", admin_token: str = "test"):
        self.base_url = base_url
        self.admin_token = admin_token
        self.headers = {"Authorization": f"admin {admin_token}"}
    
    def fetch_metrics(self) -> str:
        """Fetch raw metrics from the /metrics endpoint"""
        response = requests.get(f"{self.base_url}/metrics", headers=self.headers)
        response.raise_for_status()
        return response.text
    
    def parse_metrics(self, metrics_text: str) -> Dict[str, List[Tuple[Dict, float]]]:
        """Parse Prometheus metrics text into structured data"""
        metrics = {}
        
        for line in metrics_text.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse metric line: metric_name{labels} value
            match = re.match(r'([a-zA-Z_:][a-zA-Z0-9_:]*)\s+([\d.e+-]+)', line)
            if match:
                name, value = match.groups()
                labels = {}
                
                # Check if there are labels
                if '{' in name:
                    name_part, labels_part = name.split('{', 1)
                    labels_part = labels_part.rstrip('}')
                    
                    # Parse labels
                    for label_pair in re.findall(r'(\w+)="([^"]*)"', labels_part):
                        labels[label_pair[0]] = label_pair[1]
                    
                    name = name_part
                
                if name not in metrics:
                    metrics[name] = []
                
                metrics[name].append((labels, float(value)))
        
        return metrics
    
    def get_redis_metrics(self) -> Dict:
        """Get Redis-specific metrics"""
        metrics_text = self.fetch_metrics()
        all_metrics = self.parse_metrics(metrics_text)
        
        redis_metrics = {
            key: value for key, value in all_metrics.items()
            if key.startswith('redis_')
        }
        
        return redis_metrics
    
    def get_iotdb_metrics(self) -> Dict:
        """Get IoTDB-specific metrics"""
        metrics_text = self.fetch_metrics()
        all_metrics = self.parse_metrics(metrics_text)
        
        iotdb_metrics = {
            key: value for key, value in all_metrics.items()
            if key.startswith('iotdb_')
        }
        
        return iotdb_metrics
    
    def get_system_metrics(self) -> Dict:
        """Get system-level metrics"""
        metrics_text = self.fetch_metrics()
        all_metrics = self.parse_metrics(metrics_text)
        
        system_metrics = {
            key: value for key, value in all_metrics.items()
            if key.startswith('system_')
        }
        
        return system_metrics
    
    def get_iotflow_metrics(self) -> Dict:
        """Get IoTFlow application metrics"""
        metrics_text = self.fetch_metrics()
        all_metrics = self.parse_metrics(metrics_text)
        
        iotflow_metrics = {
            key: value for key, value in all_metrics.items()
            if key.startswith('iotflow_')
        }
        
        return iotflow_metrics
    
    def get_mqtt_metrics(self) -> Dict:
        """Get MQTT broker metrics"""
        metrics_text = self.fetch_metrics()
        all_metrics = self.parse_metrics(metrics_text)
        
        mqtt_metrics = {
            key: value for key, value in all_metrics.items()
            if key.startswith('mqtt_')
        }
        
        return mqtt_metrics
    
    def display_metric(self, name: str, data: List[Tuple[Dict, float]]):
        """Display a single metric with its values"""
        print(f"\n{name}:")
        for labels, value in data:
            if labels:
                label_str = ", ".join([f"{k}={v}" for k, v in labels.items()])
                print(f"  [{label_str}] = {value}")
            else:
                print(f"  {value}")


def main():
    """Main demonstration function"""
    print("=" * 80)
    print("IoTFlow Metrics API Demo")
    print("=" * 80)
    
    # Initialize client
    client = MetricsClient(base_url="http://localhost:5000", admin_token="test")
    
    print("\n1. Fetching Redis Metrics...")
    print("-" * 80)
    redis_metrics = client.get_redis_metrics()
    for name, data in redis_metrics.items():
        client.display_metric(name, data)
    
    print("\n\n2. Fetching IoTDB Metrics...")
    print("-" * 80)
    iotdb_metrics = client.get_iotdb_metrics()
    for name, data in iotdb_metrics.items():
        client.display_metric(name, data)
    
    print("\n\n3. Fetching IoTFlow Application Metrics...")
    print("-" * 80)
    iotflow_metrics = client.get_iotflow_metrics()
    for name, data in iotflow_metrics.items():
        client.display_metric(name, data)
    
    print("\n\n4. Fetching MQTT Metrics...")
    print("-" * 80)
    mqtt_metrics = client.get_mqtt_metrics()
    for name, data in mqtt_metrics.items():
        client.display_metric(name, data)
    
    print("\n\n5. Sample System Metrics (CPU, Memory, Disk)...")
    print("-" * 80)
    system_metrics = client.get_system_metrics()
    
    # Display only key system metrics
    key_metrics = ['system_cpu_usage_percent', 'system_memory_usage_percent', 
                   'system_disk_usage_percent', 'system_load_average']
    
    for metric_name in key_metrics:
        if metric_name in system_metrics:
            client.display_metric(metric_name, system_metrics[metric_name])
    
    print("\n\n" + "=" * 80)
    print("Summary:")
    print("=" * 80)
    print(f"Total Redis Metrics: {len(redis_metrics)}")
    print(f"Total IoTDB Metrics: {len(iotdb_metrics)}")
    print(f"Total IoTFlow Metrics: {len(iotflow_metrics)}")
    print(f"Total MQTT Metrics: {len(mqtt_metrics)}")
    print(f"Total System Metrics: {len(system_metrics)}")
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except requests.exceptions.ConnectionError:
        print("Error: Cannot connect to Flask server. Make sure it's running on localhost:5000")
    except Exception as e:
        print(f"Error: {e}")
