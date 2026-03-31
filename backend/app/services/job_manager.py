import uuid
import time
from typing import Any, Dict, Optional
from datetime import datetime

class JobStatus:
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class JobManager:
    """
    Gestor ultra-ligero de Trabajos en Segundo Plano en memoria.
    No persiste tras un reinicio de uvicorn, optimizado para ser usado
    conjuntamente con FastAPI BackgroundTasks.
    """
    def __init__(self, result_ttl: int = 3600):
        # Dict de status: {job_id: {"status": ..., "result": ..., "error": ..., "created_at": ...}}
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self.result_ttl = result_ttl

    def create_job(self) -> str:
        """Crea un Job vacío y devuelve tu ticket ID."""
        self._cleanup_expired()
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "status": JobStatus.PENDING,
            "result": None,
            "error": None,
            "created_at": time.time(),
        }
        return job_id

    def set_processing(self, job_id: str):
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = JobStatus.PROCESSING

    def finish_job(self, job_id: str, result: Any):
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = JobStatus.DONE
            self._jobs[job_id]["result"] = result

    def fail_job(self, job_id: str, error_msg: str):
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = JobStatus.FAILED
            self._jobs[job_id]["error"] = error_msg

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        self._cleanup_expired()
        return self._jobs.get(job_id)

    def _cleanup_expired(self):
        """Pequeño recolector de basura (Garbage Collector) para purgar jobs viejos."""
        now = time.time()
        expired_keys = [
            k for k, v in self._jobs.items() 
            if (now - v["created_at"]) > self.result_ttl
        ]
        for k in expired_keys:
            del self._jobs[k]

# Singleton Global para uso del Worker
job_manager = JobManager()
