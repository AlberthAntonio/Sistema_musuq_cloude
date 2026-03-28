"""
Tests de los endpoints de alumnos.
Cubre: listar, crear, obtener por ID, buscar, desactivar.
"""
import pytest


class TestAlumnos:
    """Tests para los endpoints de alumnos."""

    def test_listar_alumnos_requiere_auth(self, client):
        """GET /alumnos/ sin token retorna 401."""
        response = client.get("/alumnos/")
        assert response.status_code == 401

    def test_listar_alumnos(self, client, auth_headers):
        """GET /alumnos/ con token retorna lista (posiblemente vacía)."""
        response = client.get("/alumnos/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_crear_alumno(self, client, auth_headers):
        """POST /alumnos/ crea un alumno y retorna 201."""
        payload = {
            "dni": "99887766",
            "nombres": "Juan Carlos",
            "apell_paterno": "Quispe",
            "apell_materno": "Mamani",
            "fecha_nacimiento": "2005-03-15",
            "nombre_padre_completo": "Pedro Quispe",
            "celular_padre_1": "987654321",
        }
        response = client.post("/alumnos/", json=payload, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["dni"] == "99887766"
        assert data["nombres"] == "Juan Carlos"
        assert data["activo"] is True

    def test_crear_alumno_dni_duplicado(self, client, auth_headers):
        """POST /alumnos/ con DNI ya registrado retorna 400."""
        payload = {
            "dni": "99887766",  # mismo DNI del test anterior
            "nombres": "Otro Nombre",
            "apell_paterno": "Otro",
            "apell_materno": "Apellido",
        }
        response = client.post("/alumnos/", json=payload, headers=auth_headers)
        assert response.status_code == 400

    def test_obtener_alumno_por_dni(self, client, auth_headers):
        """GET /alumnos/dni/{dni} retorna el alumno correcto."""
        response = client.get("/alumnos/dni/99887766", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["dni"] == "99887766"

    def test_buscar_alumnos(self, client, auth_headers):
        """GET /alumnos/buscar?q=... retorna resultados."""
        response = client.get("/alumnos/buscar?q=Quispe", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Debe incluir el alumno creado
        assert any("Quispe" in a["nombre_completo"] for a in data)

    def test_obtener_alumno_inexistente(self, client, auth_headers):
        """GET /alumnos/99999 retorna 404."""
        response = client.get("/alumnos/99999", headers=auth_headers)
        assert response.status_code == 404


class TestPeriodos:
    """Tests para los endpoints de periodos académicos."""

    def test_listar_periodos(self, client, auth_headers):
        """GET /periodos/ retorna lista de periodos."""
        response = client.get("/periodos/", headers=auth_headers)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_crear_periodo_solo_admin(self, client, auth_headers):
        """POST /periodos/ crea un periodo (admin)."""
        payload = {
            "nombre": "Test-2026",
            "tipo": "academia",
            "fecha_inicio": "2026-03-01",
            "fecha_fin": "2026-07-31",
            "estado": "activo",
        }
        response = client.post("/periodos/", json=payload, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["nombre"] == "Test-2026"
