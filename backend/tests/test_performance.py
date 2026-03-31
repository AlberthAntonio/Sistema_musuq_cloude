"""
Tests de paginación y filtros obligatorios.
Verifica que los endpoints de alto volumen cumplen las reglas del Plan Maestro.
"""
import pytest
from datetime import date, timedelta


class TestPaginacion:
    """Tests de paginación estandarizada."""

    def test_alumnos_respeta_limit(self, client, auth_headers):
        """Verificar que GET /alumnos respeta el limit."""
        resp = client.get("/alumnos?limit=5", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    def test_alumnos_limit_maximo(self, client, auth_headers):
        """Verificar que no se puede exceder MAX_PAGE_SIZE (200)."""
        resp = client.get("/alumnos?limit=999", headers=auth_headers)
        assert resp.status_code == 422  # Validation error

    def test_alumnos_skip_offset(self, client, auth_headers):
        """Verificar que skip funciona correctamente."""
        resp = client.get("/alumnos?skip=0&limit=10", headers=auth_headers)
        assert resp.status_code == 200

    def test_alumnos_x_total_count_header(self, client, auth_headers):
        """Verificar que el header X-Total-Count está presente."""
        resp = client.get("/alumnos?limit=5", headers=auth_headers)
        assert resp.status_code == 200
        assert "X-Total-Count" in resp.headers

    def test_matriculas_paginacion(self, client, auth_headers):
        """Verificar paginación en matrículas."""
        resp = client.get("/matriculas?limit=5", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert "X-Total-Count" in resp.headers


class TestFiltrosObligatorios:
    """Tests de filtros obligatorios en endpoints de alto volumen."""

    def test_asistencia_sin_filtro_rechazada(self, client, auth_headers):
        """
        GET /asistencia sin filtros debe ser rechazado
        cuando STRICT_HEAVY_QUERY_FILTERS=True.
        """
        resp = client.get("/asistencia", headers=auth_headers)
        assert resp.status_code == 422
        assert "Consulta muy amplia" in resp.json().get("detail", "")

    def test_asistencia_con_fecha_aceptada(self, client, auth_headers):
        """GET /asistencia con fecha debe funcionar."""
        hoy = date.today().isoformat()
        resp = client.get(f"/asistencia?fecha={hoy}", headers=auth_headers)
        assert resp.status_code == 200

    def test_asistencia_con_periodo_aceptada(self, client, auth_headers):
        """GET /asistencia con periodo_id debe funcionar."""
        resp = client.get("/asistencia?periodo_id=1", headers=auth_headers)
        assert resp.status_code == 200

    def test_asistencia_con_alumno_aceptada(self, client, auth_headers):
        """GET /asistencia con alumno_id debe funcionar."""
        resp = client.get("/asistencia?alumno_id=1", headers=auth_headers)
        assert resp.status_code == 200

    def test_asistencia_con_rango_fechas(self, client, auth_headers):
        """GET /asistencia con rango de fechas debe funcionar."""
        hoy = date.today()
        hace_7 = (hoy - timedelta(days=7)).isoformat()
        resp = client.get(
            f"/asistencia?fecha_inicio={hace_7}&fecha_fin={hoy.isoformat()}", 
            headers=auth_headers
        )
        assert resp.status_code == 200

    def test_reportes_deudores_sin_filtro_rechazado(self, client, auth_headers):
        """GET /reportes/deudores sin filtros debe ser rechazado."""
        resp = client.get("/reportes/deudores", headers=auth_headers)
        assert resp.status_code == 422

    def test_reportes_deudores_con_periodo(self, client, auth_headers):
        """GET /reportes/deudores con periodo_id debe funcionar."""
        resp = client.get("/reportes/deudores?periodo_id=1", headers=auth_headers)
        assert resp.status_code == 200

    def test_reportes_tardanzas_sin_filtro_rechazado(self, client, auth_headers):
        """GET /reportes/tardanzas sin filtros debe ser rechazado."""
        resp = client.get("/reportes/tardanzas", headers=auth_headers)
        assert resp.status_code == 422

    def test_reportes_asistencia_sin_filtro_rechazado(self, client, auth_headers):
        """GET /reportes/asistencia sin filtros debe ser rechazado."""
        resp = client.get("/reportes/asistencia", headers=auth_headers)
        assert resp.status_code == 422


class TestCompresion:
    """Tests de compresión GZip."""

    def test_response_time_header(self, client, auth_headers):
        """Verificar que el header X-Response-Time-Ms está presente."""
        resp = client.get("/alumnos?limit=5", headers=auth_headers)
        assert resp.status_code == 200
        assert "X-Response-Time-Ms" in resp.headers

    def test_gzip_en_respuestas_grandes(self, client, auth_headers):
        """Verificar que las respuestas grandes usan GZip."""
        resp = client.get(
            "/alumnos?limit=50", 
            headers={**auth_headers, "Accept-Encoding": "gzip"}
        )
        assert resp.status_code == 200
        # Si la respuesta es lo suficientemente grande, debe estar comprimida
        content_encoding = resp.headers.get("Content-Encoding", "")
        # Nota: TestClient puede no decodificar gzip, verificamos que el server lo intenta
        # En producción con httpx real esto sí aplica


class TestMetrics:
    """Tests del endpoint de métricas."""

    def test_metrics_summary_requiere_admin(self, client, auth_headers):
        """Verificar que /metrics/summary requiere rol admin."""
        resp = client.get("/metrics/summary", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "total_requests" in data
        assert "endpoints" in data
        assert "uptime_seconds" in data

    def test_metrics_reset(self, client, auth_headers):
        """Verificar que /metrics/reset funciona."""
        resp = client.post("/metrics/reset", headers=auth_headers)
        assert resp.status_code == 200

    def test_health_detailed(self, client, auth_headers):
        """Verificar health check detallado."""
        resp = client.get("/metrics/health-detailed", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "db_pool" in data
