"""
Tests de los endpoints de autenticación.
Cubre: login, logout flow, refresh token, /me, /verify.
"""
import pytest


class TestAuth:
    """Tests para los endpoints de autenticación."""

    def test_login_correcto(self, client):
        """POST /auth/login con credenciales válidas retorna TokenPair."""
        response = client.post(
            "/auth/login",
            data={"username": "test_admin", "password": "testpass123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_credenciales_incorrectas(self, client):
        """POST /auth/login con contraseña incorrecta retorna 401."""
        response = client.post(
            "/auth/login",
            data={"username": "test_admin", "password": "WRONG_PASS"},
        )
        assert response.status_code == 401
        assert "detail" in response.json()

    def test_login_usuario_inexistente(self, client):
        """POST /auth/login con usuario que no existe retorna 401."""
        response = client.post(
            "/auth/login",
            data={"username": "fantasma", "password": "cualquier"},
        )
        assert response.status_code == 401

    def test_refresh_token_valido(self, client):
        """POST /auth/refresh con refresh token válido retorna nuevo par de tokens."""
        # Primero hacer login para obtener refresh token
        login_r = client.post(
            "/auth/login",
            data={"username": "test_admin", "password": "testpass123"},
        )
        refresh_token = login_r.json()["refresh_token"]

        # Usar el refresh token
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_token_invalido(self, client):
        """POST /auth/refresh con token inválido retorna 401."""
        response = client.post(
            "/auth/refresh",
            json={"refresh_token": "token-inventado-invalido"},
        )
        assert response.status_code == 401

    def test_me_con_token(self, client, auth_headers):
        """GET /auth/me con token válido retorna info del usuario."""
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "test_admin"
        assert data["rol"] == "admin"

    def test_me_sin_token(self, client):
        """GET /auth/me sin token retorna 401."""
        response = client.get("/auth/me")
        assert response.status_code == 401

    def test_verify_token_valido(self, client, auth_headers):
        """POST /auth/verify con token válido retorna valid=True."""
        response = client.post("/auth/verify", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["valid"] is True

    def test_request_id_en_header(self, client):
        """Las respuestas deben incluir X-Request-ID en los headers."""
        response = client.get("/health")
        assert "x-request-id" in response.headers
