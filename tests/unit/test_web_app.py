"""Unit tests for the FastAPI web application."""

from fastapi.testclient import TestClient

from app.web.app import app

client = TestClient(app)


class TestWebApp:
    """Test suite for FastAPI web application."""

    def test_root_endpoint(self):
        """Test the root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "SaaS Market Intelligence Platform API"
        assert response.json()["version"] == "2.0.0"

    def test_health_endpoint(self):
        """Test the health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert "timestamp" in response.json()

    def test_subscription_endpoint_unauthorized(self):
        """Test subscription endpoint without authorization."""
        response = client.post(
            "/api/subscriptions",
            json={"customer_id": "test_customer", "plan_id": "pro", "amount": 99.00},
        )
        assert response.status_code == 403  # No auth header

    def test_subscription_endpoint_authorized(self):
        """Test subscription endpoint with authorization."""
        headers = {"Authorization": "Bearer test_token"}
        response = client.post(
            "/api/subscriptions",
            json={"customer_id": "test_customer", "plan_id": "pro", "amount": 99.00},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_dashboard_endpoint_authorized(self):
        """Test dashboard endpoint with authorization."""
        headers = {"Authorization": "Bearer test_token"}
        response = client.get("/api/dashboard", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "current_mrr" in data
        assert "daily_revenue" in data
        assert "customer_count" in data

    def test_query_endpoint_authorized(self):
        """Test intelligence query endpoint."""
        headers = {"Authorization": "Bearer test_token"}
        response = client.post(
            "/api/query",
            json={
                "query": "What are the biggest pain points for SaaS founders?",
                "sources": ["reddit", "github"],
            },
            headers=headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "query" in data
        assert "response" in data
        assert "confidence" in data

    def test_revenue_endpoints_authorized(self):
        """Test revenue tracking endpoints."""
        headers = {"Authorization": "Bearer test_token"}

        # Test daily revenue
        response = client.get("/api/revenue/daily", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "daily_revenue" in data
        assert "target_met" in data

        # Test revenue forecast
        response = client.get("/api/revenue/forecast", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert "current_mrr" in data
        assert "forecast" in data
