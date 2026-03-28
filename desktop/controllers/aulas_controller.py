"""
AulasController — Conecta la vista con la API del backend.
Sistema Musuq Cloud
"""
from typing import List, Dict, Tuple, Optional
from core.api_client import AulasClient


class AulasController:
    """Controlador para el módulo de Aulas."""

    def __init__(self, auth_token: str):
        self.client = AulasClient()
        self.client.token = auth_token

    # ─────────────────────────────────────────────
    #  LECTURA
    # ─────────────────────────────────────────────

    def listar(
        self,
        modalidad: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> List[Dict]:
        """
        Devuelve la lista de aulas.
        En caso de error retorna lista vacía y muestra el error en consola.
        """
        success, result = self.client.listar(modalidad=modalidad, activo=activo)
        if not success:
            print(f"[AulasController] Error al listar aulas: {result.get('error')}")
            return []
        return result if isinstance(result, list) else result.get("items", [])

    def obtener_por_id(self, aula_id: int) -> Optional[Dict]:
        """Devuelve un aula por su ID, o None si no existe o hay error."""
        success, result = self.client.obtener_por_id(aula_id)
        if not success:
            print(f"[AulasController] Error al obtener aula {aula_id}: {result.get('error')}")
            return None
        return result

    def obtener_horarios(self, aula_id: int, periodo: Optional[str] = None) -> List[Dict]:
        """Devuelve los bloques horarios asociados a un aula."""
        success, result = self.client.obtener_horarios(aula_id, periodo)
        if not success:
            print(f"[AulasController] Error al obtener horarios de aula {aula_id}: {result.get('error')}")
            return []
        return result if isinstance(result, list) else result.get("items", [])

    # ─────────────────────────────────────────────
    #  ESCRITURA
    # ─────────────────────────────────────────────

    def crear(
        self,
        nombre: str,
        modalidad: str,
        descripcion: Optional[str],
        grupos: List[str],
        activo: bool = True,
    ) -> Tuple[bool, str]:
        """
        Crea un aula nueva.
        Devuelve (True, aula_dict) en éxito, (False, mensaje_error) en fallo.
        """
        data = {
            "nombre": nombre.strip(),
            "modalidad": modalidad.strip().upper(),
            "descripcion": descripcion or None,
            "grupos": grupos,
            "cursos_ids": [],
            "horarios": [],          # se agregan después desde la vista de horarios
        }
        success, result = self.client.crear(data)
        if success:
            return True, result      # result es el AulaResponse completo
        error = result.get("error") or result.get("detail", "Error al crear el aula")
        return False, str(error)

    def actualizar(
        self,
        aula_id: int,
        *,
        nombre: Optional[str] = None,
        modalidad: Optional[str] = None,
        descripcion: Optional[str] = None,
        activo: Optional[bool] = None,
        grupos: Optional[List[str]] = None,
    ) -> Tuple[bool, str]:
        """
        Actualiza campos de un aula.
        Solo envía los campos que se pasan explícitamente.
        """
        data: Dict = {}
        if nombre is not None:
            data["nombre"] = nombre.strip()
        if modalidad is not None:
            data["modalidad"] = modalidad.strip().upper()
        if descripcion is not None:
            data["descripcion"] = descripcion or None
        if activo is not None:
            data["activo"] = activo
        if grupos is not None:
            data["grupos"] = grupos

        success, result = self.client.actualizar(aula_id, data)
        if success:
            return True, result
        error = result.get("error") or result.get("detail", "Error al actualizar el aula")
        return False, str(error)

    def eliminar(self, aula_id: int) -> Tuple[bool, str]:
        """Elimina un aula por ID."""
        success, result = self.client.eliminar(aula_id)
        if success:
            return True, "Aula eliminada correctamente"
        error = result.get("error") or result.get("detail", "Error al eliminar el aula")
        return False, str(error)
