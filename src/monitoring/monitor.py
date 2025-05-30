import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
from dataclasses import dataclass
import psutil
import os

@dataclass
class SystemMetrics:
    cpu_percent: float
    memory_percent: float
    disk_usage: Dict[str, float]
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cpu_percent": self.cpu_percent,
            "memory_percent": self.memory_percent,
            "disk_usage": self.disk_usage,
            "timestamp": self.timestamp
        }

@dataclass
class AgentMetrics:
    agent_id: str
    status: str
    tasks_processed: int
    errors_count: int
    avg_processing_time: float
    last_active: str
    memory_usage: float
    cpu_usage: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "status": self.status,
            "tasks_processed": self.tasks_processed,
            "errors_count": self.errors_count,
            "avg_processing_time": self.avg_processing_time,
            "last_active": self.last_active,
            "memory_usage": self.memory_usage,
            "cpu_usage": self.cpu_usage
        }

class AetheroMonitor:
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger('aethero_monitor')
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.system_metrics: List[SystemMetrics] = []
        self.alert_thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 80.0,
            "disk_percent": 90.0
        }
        self.alert_callbacks: List[callable] = []
        self.running = True

    async def start_monitoring(self, interval: int = 60):
        """Start the monitoring loop."""
        self.logger.info("Starting Aethero monitoring system")
        while self.running:
            try:
                await self.collect_metrics()
                await asyncio.sleep(interval)
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(5)  # Brief pause before retry

    async def collect_metrics(self):
        """Collect system and agent metrics."""
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        metrics = SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_usage={
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": disk.percent
            }
        )

        self.system_metrics.append(metrics)
        self.logger.info(f"Collected system metrics: {json.dumps(metrics.to_dict())}")

        # Check thresholds and alert if necessary
        await self._check_alerts(metrics)

    def update_agent_metrics(self, agent_id: str, metrics: Dict[str, Any]):
        """Update metrics for a specific agent."""
        self.agent_metrics[agent_id] = AgentMetrics(
            agent_id=agent_id,
            status=metrics.get("status", "unknown"),
            tasks_processed=metrics.get("tasks_processed", 0),
            errors_count=metrics.get("errors_count", 0),
            avg_processing_time=metrics.get("avg_processing_time", 0.0),
            last_active=metrics.get("last_active", datetime.now().isoformat()),
            memory_usage=metrics.get("memory_usage", 0.0),
            cpu_usage=metrics.get("cpu_usage", 0.0)
        )
        
        self.logger.info(f"Updated metrics for agent {agent_id}")

    def get_system_metrics(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get system metrics history."""
        metrics = self.system_metrics
        if limit:
            metrics = metrics[-limit:]
        return [m.to_dict() for m in metrics]

    def get_agent_metrics(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a specific agent or all agents."""
        if agent_id:
            return self.agent_metrics.get(agent_id, {}).to_dict()
        return {aid: metrics.to_dict() for aid, metrics in self.agent_metrics.items()}

    def add_alert_callback(self, callback: callable):
        """Add a callback for alerts."""
        self.alert_callbacks.append(callback)

    async def _check_alerts(self, metrics: SystemMetrics):
        """Check metrics against thresholds and trigger alerts if necessary."""
        alerts = []

        if metrics.cpu_percent > self.alert_thresholds["cpu_percent"]:
            alerts.append(f"High CPU usage: {metrics.cpu_percent}%")

        if metrics.memory_percent > self.alert_thresholds["memory_percent"]:
            alerts.append(f"High memory usage: {metrics.memory_percent}%")

        if metrics.disk_usage["percent"] > self.alert_thresholds["disk_percent"]:
            alerts.append(f"High disk usage: {metrics.disk_usage['percent']}%")

        if alerts:
            alert_data = {
                "timestamp": datetime.now().isoformat(),
                "alerts": alerts,
                "metrics": metrics.to_dict()
            }
            
            for callback in self.alert_callbacks:
                try:
                    await callback(alert_data)
                except Exception as e:
                    self.logger.error(f"Alert callback failed: {str(e)}")

# Example usage
async def example_alert_callback(alert_data: Dict[str, Any]):
    """Example alert callback."""
    print(f"ALERT: {json.dumps(alert_data, indent=2)}")

async def main():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create monitor
    monitor = AetheroMonitor()
    
    # Add alert callback
    monitor.add_alert_callback(example_alert_callback)
    
    # Start monitoring in background
    monitoring_task = asyncio.create_task(monitor.start_monitoring(interval=5))
    
    # Simulate some agent metrics updates
    monitor.update_agent_metrics("agent1", {
        "status": "active",
        "tasks_processed": 10,
        "errors_count": 0,
        "avg_processing_time": 0.5,
        "memory_usage": 45.2,
        "cpu_usage": 12.3
    })
    
    # Wait for some metrics collection
    await asyncio.sleep(10)
    
    # Get metrics
    system_metrics = monitor.get_system_metrics(limit=5)
    agent_metrics = monitor.get_agent_metrics()
    
    print("\nSystem Metrics:")
    print(json.dumps(system_metrics, indent=2))
    
    print("\nAgent Metrics:")
    print(json.dumps(agent_metrics, indent=2))
    
    # Stop monitoring
    monitor.running = False
    await monitoring_task

if __name__ == "__main__":
    asyncio.run(main())
