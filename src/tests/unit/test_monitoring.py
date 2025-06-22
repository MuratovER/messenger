import pytest
from utils.monitoring import MonitoringService, monitoring_service

class TestMonitoringService:
    def test_monitoring_service_init(self):
        """Test MonitoringService initialization."""
        service = MonitoringService()
        assert isinstance(service, MonitoringService)
        assert hasattr(service, "performance_monitor")
        assert hasattr(service, "health_checker")
        assert hasattr(service, "alert_manager")

class TestGlobalInstance:
    def test_monitoring_service_instance(self):
        # Act & Assert
        assert isinstance(monitoring_service, MonitoringService) 