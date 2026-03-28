from typing import List, Dict, Any, Tuple, Optional
from core.api_client import DocentesClient

class DocentesController:
    """
    Controlador para el módulo de Docentes.
    Conectado con la API del backend.
    """
    
    def __init__(self, auth_token: str):
        self.docentes_client = DocentesClient()
        self.docentes_client.token = auth_token
        self._cache_docentes = None

    def obtener_docentes(self, busqueda: str = "", filtro: str = "todos", skip: int = 0, limit: int = 100) -> List[Dict]:
        """Retorna lista de docentes normalizada para la vista."""
        success, result = self.docentes_client.obtener_todos(skip=skip, limit=limit)

        if not success:
            print(f"[ERROR] No se pudieron obtener docentes: {result}")
            return []

        raw = result if isinstance(result, list) else result.get("items", [])

        # ── Normalizar cada registro al formato que espera la vista ──────────
        docentes = []
        for d in raw:
            nombres   = d.get("nombres", "") or ""
            apellidos = d.get("apellidos", "") or ""
            nombre_completo = f"{apellidos} {nombres}".strip()
            activo = d.get("activo", True)

            docentes.append({
                "id":           d.get("id"),
                "dni":          d.get("dni", "") or "",
                "nombre":       nombre_completo,
                "nombre_completo": nombre_completo,
                "especialidad": d.get("especialidad", "") or "",
                "cursos":       d.get("cursos", "") or "",
                "estado":       "✅ Activo" if activo else "❌ Inactivo",
                "activo":       activo,
                "celular":      d.get("celular", "") or "",
                "email":        d.get("email", "") or "",
            })

        # ── Filtrar por búsqueda ──────────────────────────────────────────────
        if busqueda:
            b = busqueda.lower()
            docentes = [d for d in docentes if
                        b in d["nombre"].lower() or
                        b in d["dni"] or
                        b in (d["especialidad"] or "").lower()]

        # ── Filtrar por estado ──────────────────────────────────────────────
        if filtro == "activos":
            docentes = [d for d in docentes if d["activo"]]
        elif filtro == "inactivos":
            docentes = [d for d in docentes if not d["activo"]]

        return docentes

    def guardar_docente(self, datos: Dict) -> Tuple[bool, str]:
        """Guarda o actualiza un docente en la API"""
        # ── Mapear campos del formulario al esquema del backend ──────────────
        # El backend espera: nombres, apellidos, dni, celular, email, especialidad
        # El formulario envía: nombres, paterno, materno, tipo_contrato, turno...
        paterno  = datos.get("paterno", "").strip()
        materno  = datos.get("materno", "").strip()
        apellidos = f"{paterno} {materno}".strip()

        payload = {
            "nombres":      datos.get("nombres", "").strip(),
            "apellidos":    apellidos,
            "dni":          datos.get("dni", "").strip() or None,
            "celular":      datos.get("celular", "").strip() or None,
            "email":        datos.get("email", "").strip() or None,
            "especialidad": datos.get("especialidad") if datos.get("especialidad") not in (
                                None, "", "-- Seleccione --") else None,
        }

        docente_id = datos.get("id")

        if docente_id:
            # Actualizar — añadir campo activo
            payload["activo"] = datos.get("activo", True)
            success, result = self.docentes_client.actualizar(docente_id, payload)
            if success:
                return True, "Docente actualizado correctamente"
            else:
                error = result.get("detail") or result.get("error", "Error al actualizar")
                return False, str(error)
        else:
            # Crear
            success, result = self.docentes_client.crear(payload)
            if success:
                return True, "Docente guardado correctamente"
            else:
                error = result.get("detail") or result.get("error", "Error al guardar")
                return False, str(error)

    def obtener_cursos_disponibles(self) -> List[str]:
        """Lista de cursos disponibles (predefinida)"""
        return [
            "Aritmética", "Álgebra", "Geometría", "Trigonometría",
            "Física", "Química", "Biología", "Razonamiento Verbal",
            "Razonamiento Matemático", "Historia", "Geografía",
            "Inglés", "Arte", "Computación", "Educación Física"
        ]

    def obtener_nombres_para_combobox(self) -> List[str]:
        """Retorna solo nombres de docentes activos"""
        docentes = self.obtener_docentes(filtro="activos")
        return [d.get("nombre_completo", "") for d in docentes]

    def obtener_docentes_por_curso(self, curso_id: int) -> List[str]:
        """Retorna nombres de docentes que dictan un curso específico."""
        if not curso_id:
            return []

        success, result = self.docentes_client.obtener_por_curso(curso_id)
        if not success:
            print(f"[ERROR] No se pudieron obtener docentes para el curso {curso_id}: {result}")
            return []

        docentes = result if isinstance(result, list) else result.get("items", [])
        return [d.get("nombre_completo", "") for d in docentes]

    def buscar_por_nombre(self, nombre: str) -> Optional[Dict]:
        """Busca docente por nombre exacto"""
        if not nombre:
            return None

        def _norm(txt: str) -> str:
            return " ".join((txt or "").strip().lower().split())

        objetivo = _norm(nombre)

        success, result = self.docentes_client.buscar(nombre)
        if success:
            docentes = result if isinstance(result, list) else result.get("items", [])
            for d in docentes:
                if _norm(d.get("nombre_completo", "")) == objetivo:
                    return d
            # Si no hay match exacto, aceptar un match parcial cuando solo hay 1 candidato
            if len(docentes) == 1:
                return docentes[0]
            for d in docentes:
                if objetivo and objetivo in _norm(d.get("nombre_completo", "")):
                    return d

        # Fallback: buscar en la lista completa (la API "buscar" no matchea "nombre completo")
        docentes_full = self.obtener_docentes(limit=1000)
        for d in docentes_full:
            if _norm(d.get("nombre_completo", "")) == objetivo:
                return d

        return None

    def eliminar_docente(self, docente_id: int) -> Tuple[bool, str]:
        """Elimina un docente"""
        success, result = self.docentes_client.eliminar(docente_id)
        if success:
            return True, "Docente eliminado correctamente"
        else:
            return False, result.get("error", "Error al eliminar")

    def asignar_cursos(self, docente_id: int, curso_ids: List[int],
                       nombres: List[str] = None) -> Tuple[bool, str]:
        """Asigna (reemplaza) los cursos de un docente usando la API real."""
        if not docente_id:
            return False, "Docente no válido"

        success, result = self.docentes_client.asignar_cursos(docente_id, curso_ids)
        if not success:
            return False, result.get("error", "Error al asignar cursos")

        n = len(nombres or curso_ids)
        return True, f"{n} curso(s) asignado(s) correctamente"

    def obtener_cursos_docente(self, docente_id: int) -> List[Dict]:
        """Obtiene los cursos actualmente asignados a un docente desde la API."""
        if not docente_id:
            return []

        success, result = self.docentes_client.obtener_cursos_docente(docente_id)
        if not success:
            print(f"[ERROR] No se pudieron obtener cursos del docente {docente_id}: {result}")
            return []

        cursos = result if isinstance(result, list) else result.get("items", [])
        # Normalizar por si el backend cambia ligeramente el esquema
        return [
            {
                "id": c.get("id"),
                "nombre": c.get("nombre", ""),
                "descripcion": c.get("descripcion", ""),
            }
            for c in cursos
        ]

