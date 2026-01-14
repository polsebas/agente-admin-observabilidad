import pytest
from unittest.mock import MagicMock, patch
from tools import prometheus_tool

@pytest.fixture
def mock_prometheus():
    with patch("tools.prometheus_tool._prom") as mock_prom:
        yield mock_prom

def test_get_monitored_services_success(mock_prometheus):
    # Mock de la respuesta de Prometheus para count(up) by (service)
    mock_prometheus.custom_query.return_value = [
        {"metric": {"service": "auth-service"}, "value": [1234567890, "1"]},
        {"metric": {"service": "payment-service"}, "value": [1234567890, "1"]}
    ]
    
    services = prometheus_tool.get_monitored_services()
    
    assert "auth-service" in services
    assert "payment-service" in services
    assert len(services) == 2
    mock_prometheus.custom_query.assert_called_with('count(up) by (service)')

def test_get_monitored_services_empty(mock_prometheus):
    mock_prometheus.custom_query.return_value = []
    
    services = prometheus_tool.get_monitored_services()
    
    assert services == []

def test_get_monitored_services_error(mock_prometheus):
    mock_prometheus.custom_query.side_effect = Exception("Connection error")
    
    services = prometheus_tool.get_monitored_services()
    
    assert services == []

def test_get_service_health_dynamic(mock_prometheus):
    # Mock de la respuesta de up{service!=""}
    mock_prometheus.custom_query.return_value = [
        {"metric": {"service": "auth-service", "instance": "10.0.0.1:8080", "__name__": "up"}, "value": [1234567890, "1"]},
        {"metric": {"service": "payment-service", "instance": "10.0.0.2:8080", "__name__": "up"}, "value": [1234567890, "0"]}
    ]
    
    health = prometheus_tool.get_service_health()
    
    assert len(health) == 2
    mock_prometheus.custom_query.assert_called_with('up{service!=""}')
