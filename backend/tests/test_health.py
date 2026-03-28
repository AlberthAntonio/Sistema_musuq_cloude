"""
Tests de los endpoints de health check.
"""
import pytest


class TestHealth:
    """Tests para los endpoints de salud del servidor."""

    def test_health_ok(self, client):
        """GET /health debe retornar status healthy."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_db_ok(self, client):
        """GET /health/db debe retornar conexión a BD activa."""
        response = client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"

    def test_root(self, client):
        """GET / debe retornar información de la app."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "app" in data
        assert "version" in data
        assert data["status"] == "running"
