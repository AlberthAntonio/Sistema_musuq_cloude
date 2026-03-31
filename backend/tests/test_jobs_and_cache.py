import pytest
import time

from app.core.cache import app_cache
from app.services.job_manager import job_manager

class TestJobsAndCache:

    def setup_method(self):
        """Asegurarse que cada test empiece con caché y colas limpias."""
        app_cache.clear()
        job_manager._jobs.clear()
        
    def test_cache_hit_on_metrics(self, client, auth_headers):
        """Verifica que /metrics/summary cachea correctamente la respuesta y los subsecuentes leen memoria."""
        
        # Petición 1: Llenar caché
        res1 = client.get("/metrics/summary", headers=auth_headers)
        assert res1.status_code == 200
        
        # Petición 2: Leer de caché (debe ser muy rapido)
        res2 = client.get("/metrics/summary", headers=auth_headers)
        assert res2.status_code == 200
        assert len(app_cache._cache) == 1
        
    def test_async_report_job_lifecycle(self, client, auth_headers):
        """Valida que pasar async_mode=true genere un Job, que podamos consultar su status y su finalización."""
        
        # Iniciar reporte pesado en background
        res_job = client.get("/reportes/deudores?periodo_id=1&async_mode=true", headers=auth_headers)
        assert res_job.status_code == 200
        
        body = res_job.json()
        assert "job_id" in body
        assert body["status"] == "pending"
        
        job_id = body["job_id"]
        
        # TestClient de starlette ejecuta las BackgroundTasks inmediatamente después de la request, 
        # por lo que el job ya debe estar en estado 'done' o 'failed'.
        res_status = client.get(f"/reportes/jobs/{job_id}/status", headers=auth_headers)
        assert res_status.status_code == 200
        
        status_body = res_status.json()
        assert status_body["status"] in ["done", "failed"]
        
        if status_body["status"] == "done":
            res_download = client.get(f"/reportes/jobs/{job_id}/download", headers=auth_headers)
            assert res_download.status_code == 200
            assert isinstance(res_download.json(), list)
