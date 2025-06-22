import asyncio
import time
from collections import defaultdict
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from loguru import logger


@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: datetime
    value: float
    labels: dict[str, str] = field(default_factory=dict)
    
    def add_point(self, value: float, labels: dict[str, str] | None = None):
        """Add a new data point."""
        self.data_points.append(MetricPoint(
            timestamp=datetime.now(),
            value=value,
            labels=labels or {}
        ))
        
        # Keep only last 1000 points to prevent memory issues
        if len(self.data_points) > 1000:
            self.data_points = self.data_points[-1000:]


@dataclass
class Metric:
    """Metric with multiple data points."""
    name: str
    description: str
    unit: str
    data_points: list[MetricPoint] = field(default_factory=list)


class PerformanceMonitor:
    """Monitor application performance metrics."""
    
    def __init__(self):
        self.metrics: dict[str, Metric] = {}
        self.request_times: list[float] = []
        self.error_counts: dict[str, int] = defaultdict(int)
        self.active_connections = 0
        self.total_requests = 0
        self.failed_requests = 0
        
        # Initialize default metrics
        self._init_default_metrics()
    
    def _init_default_metrics(self):
        """Initialize default metrics."""
        self.add_metric("request_duration", "Request duration in seconds", "seconds")
        self.add_metric("requests_per_second", "Requests per second", "requests/sec")
        self.add_metric("error_rate", "Error rate percentage", "percent")
        self.add_metric("active_connections", "Active WebSocket connections", "connections")
        self.add_metric("memory_usage", "Memory usage in MB", "MB")
        self.add_metric("database_connections", "Active database connections", "connections")
    
    def add_metric(self, name: str, description: str, unit: str):
        """Add a new metric."""
        self.metrics[name] = Metric(name, description, unit)
    
    def record_request_time(self, duration: float):
        """Record request duration."""
        self.request_times.append(duration)
        self.total_requests += 1
        
        # Keep only last 1000 requests
        if len(self.request_times) > 1000:
            self.request_times = self.request_times[-1000:]
        
        if "request_duration" in self.metrics:
            self.metrics["request_duration"].add_point(duration)
    
    def record_error(self, error_type: str):
        """Record an error."""
        self.error_counts[error_type] += 1
        self.failed_requests += 1
    
    def set_active_connections(self, count: int):
        """Set active WebSocket connections count."""
        self.active_connections = count
        if "active_connections" in self.metrics:
            self.metrics["active_connections"].add_point(count)
    
    def get_statistics(self) -> dict[str, any]:
        """Get current statistics."""
        if not self.request_times:
            avg_response_time = 0
            min_response_time = 0
            max_response_time = 0
        else:
            avg_response_time = sum(self.request_times) / len(self.request_times)
            min_response_time = min(self.request_times)
            max_response_time = max(self.request_times)
        
        error_rate = (self.failed_requests / max(self.total_requests, 1)) * 100
        
        return {
            "total_requests": self.total_requests,
            "failed_requests": self.failed_requests,
            "error_rate": error_rate,
            "average_response_time": avg_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "active_connections": self.active_connections,
            "error_counts": dict(self.error_counts),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_metrics_summary(self) -> dict[str, any]:
        """Get metrics summary for the last hour."""
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)
        
        summary = {}
        for metric_name, metric in self.metrics.items():
            recent_points = [
                point for point in metric.data_points
                if point.timestamp >= hour_ago
            ]
            
            if recent_points:
                values = [point.value for point in recent_points]
                summary[metric_name] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "unit": metric.unit
                }
        
        return summary


class HealthChecker:
    """Health check utilities."""
    
    def __init__(self):
        self.checks: dict[str, callable] = {}
        self.last_check_results: dict[str, dict[str, any]] = {}
    
    def add_check(self, name: str, check_func: callable):
        """Add a health check."""
        self.checks[name] = check_func
    
    async def run_checks(self) -> dict[str, dict[str, any]]:
        """Run all health checks."""
        results = {}
        
        for name, check_func in self.checks.items():
            try:
                start_time = time.time()
                result = await check_func()
                duration = time.time() - start_time
                
                results[name] = {
                    "status": "healthy" if result else "unhealthy",
                    "duration": duration,
                    "timestamp": datetime.now().isoformat(),
                    "error": None
                }
                
            except Exception as e:
                results[name] = {
                    "status": "unhealthy",
                    "duration": 0,
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
        
        self.last_check_results = results
        return results
    
    def get_overall_status(self) -> str:
        """Get overall health status."""
        if not self.last_check_results:
            return "unknown"
        
        all_healthy = all(
            result["status"] == "healthy"
            for result in self.last_check_results.values()
        )
        
        return "healthy" if all_healthy else "unhealthy"


class AlertManager:
    """Simple alert manager for monitoring."""
    
    def __init__(self):
        self.alerts: list[dict[str, any]] = []
        self.thresholds: dict[str, float] = {
            "error_rate": 5.0,  # 5% error rate
            "response_time": 2.0,  # 2 seconds
            "memory_usage": 512.0,  # 512 MB
        }
    
    def check_alerts(self, metrics: dict[str, any]):
        """Check metrics against thresholds and generate alerts."""
        current_alerts = []
        
        # Check error rate
        if metrics.get("error_rate", 0) > self.thresholds["error_rate"]:
            current_alerts.append({
                "type": "high_error_rate",
                "message": f"Error rate is {metrics['error_rate']:.2f}% (threshold: {self.thresholds['error_rate']}%)",
                "severity": "warning",
                "timestamp": datetime.now().isoformat()
            })
        
        # Check response time
        if metrics.get("average_response_time", 0) > self.thresholds["response_time"]:
            current_alerts.append({
                "type": "high_response_time",
                "message": f"Average response time is {metrics['average_response_time']:.3f}s (threshold: {self.thresholds['response_time']}s)",
                "severity": "warning",
                "timestamp": datetime.now().isoformat()
            })
        
        # Add new alerts
        self.alerts.extend(current_alerts)
        
        # Keep only last 100 alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]
        
        return current_alerts
    
    def get_active_alerts(self) -> list[dict[str, any]]:
        """Get active alerts from the last hour."""
        hour_ago = datetime.now() - timedelta(hours=1)
        return [
            alert for alert in self.alerts
            if datetime.fromisoformat(alert["timestamp"]) >= hour_ago
        ]


# Global instances
performance_monitor = PerformanceMonitor()
health_checker = HealthChecker()
alert_manager = AlertManager()


# Decorator for monitoring function performance
def monitor_performance(func_name: str | None = None):
    """Decorator to monitor function performance."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                performance_monitor.record_request_time(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_monitor.record_request_time(duration)
                performance_monitor.record_error(type(e).__name__)
                raise
        return wrapper
    return decorator


# Background task for monitoring
async def monitoring_task():
    """Background task for continuous monitoring."""
    while True:
        try:
            # Get current statistics
            stats = performance_monitor.get_statistics()
            
            # Check for alerts
            alerts = alert_manager.check_alerts(stats)
            
            # Log if there are alerts
            if alerts:
                for alert in alerts:
                    logger.warning(f"ALERT: {alert['message']}")
            
            # Run health checks
            health_results = await health_checker.run_checks()
            
            # Log health status
            overall_status = health_checker.get_overall_status()
            if overall_status != "healthy":
                logger.error(f"Health check failed: {health_results}")
            
            await asyncio.sleep(60)  # Run every minute
            
        except Exception as e:
            logger.error(f"Error in monitoring task: {e}")
            await asyncio.sleep(60) 


class MonitoringService:
    """Main monitoring service that combines all monitoring functionality."""
    
    def __init__(self):
        self.performance_monitor = performance_monitor
        self.health_checker = health_checker
        self.alert_manager = alert_manager
    
    async def increment_request_count(self, endpoint: str) -> int:
        """Increment request count for an endpoint."""
        # Implementation would go here
        return 1
    
    async def increment_error_count(self, endpoint: str, error_code: int) -> int:
        """Increment error count for an endpoint."""
        # Implementation would go here
        return 1
    
    async def record_response_time(self, endpoint: str, response_time: float) -> bool:
        """Record response time for an endpoint."""
        self.performance_monitor.record_request_time(response_time)
        return True
    
    async def get_request_count(self, endpoint: str) -> int:
        """Get request count for an endpoint."""
        # Implementation would go here
        return 0
    
    async def get_error_count(self, endpoint: str, error_code: int) -> int:
        """Get error count for an endpoint."""
        # Implementation would go here
        return 0
    
    async def get_average_response_time(self, endpoint: str) -> float:
        """Get average response time for an endpoint."""
        stats = self.performance_monitor.get_statistics()
        return stats.get("average_response_time", 0.0)
    
    async def get_health_metrics(self, endpoint: str) -> dict:
        """Get health metrics for an endpoint."""
        stats = self.performance_monitor.get_statistics()
        return {
            "total_requests": stats.get("total_requests", 0),
            "error_rate": stats.get("error_rate", 0.0),
            "average_response_time": stats.get("average_response_time", 0.0),
            "uptime": 0.0
        }
    
    async def record_user_activity(self, user_id: int, activity_type: str) -> bool:
        """Record user activity."""
        # Implementation would go here
        return True
    
    async def get_user_activity(self, user_id: int) -> list[str]:
        """Get user activity."""
        # Implementation would go here
        return []
    
    async def record_system_event(self, event_type: str, event_data: dict) -> bool:
        """Record system event."""
        # Implementation would go here
        return True
    
    async def get_system_events(self, event_type: str) -> list[dict]:
        """Get system events."""
        # Implementation would go here
        return []
    
    async def record_performance_metric(self, metric_name: str, metric_value: float) -> bool:
        """Record performance metric."""
        self.performance_monitor.add_metric(metric_name, "", "")
        return True
    
    async def get_performance_metrics(self, metric_name: str) -> dict:
        """Get performance metrics."""
        # Implementation would go here
        return {
            "count": 0,
            "average": 0.0,
            "min": 0.0,
            "max": 0.0,
            "values": []
        }
    
    async def cleanup_old_data(self, cutoff_time: datetime) -> bool:
        """Cleanup old data."""
        # Implementation would go here
        return True
    
    async def get_all_metrics(self) -> dict:
        """Get all metrics."""
        # Implementation would go here
        return {}


# Global monitoring service instance
monitoring_service = MonitoringService() 