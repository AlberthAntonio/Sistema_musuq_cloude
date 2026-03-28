from typing import List, Dict, Tuple, Any
from datetime import datetime
from core.api_client import AsistenciaClient, MatriculasClient

class ReporteInasistenciaController:
    """
    Controlador para reporte y gestión de inasistencias.
    """

    # Estados normalizados según el backend refactorizado
    ESTADO_FALTA        = "INASISTENCIA"  # El backend usa "Inasistencia" para faltas no justificadas
    ESTADO_JUSTIFICADO  = "JUSTIFICADO"

    def __init__(self, auth_token: str = ""):
        self.client = AsistenciaClient()
        self.matricula_client = MatriculasClient()
        if auth_token:
            self.client.token = auth_token
            self.matricula_client.token = auth_token

    def obtener_inasistencias_dia(self, fecha: str, horario: str, grupo: str, modalidad: str, solo_injustificadas: bool) -> Tuple[bool, str, Dict, List[Dict]]:
        """
        Obtiene inasistencias de un día específico.
        Retorna: (Success, Msg, Stats, ListaDatos)
        """
        try:
            # 1. Parsing Fecha
            try:
                d_query = datetime.strptime(fecha, "%d/%m/%Y").strftime("%Y-%m-%d")
            except ValueError:
                return False, "Fecha inválida", {}, []

            # 2. Consumo API — estados que interesan
            success, result = self.client.listar(
                fecha_inicio=d_query,
                fecha_fin=d_query
            )

            if not success:
                return False, "Error de conexión", {}, []

            raw_data = result if isinstance(result, list) else result.get("items", [])

            # Caché de matrículas para evitar N+1 requests
            _mat_cache: Dict[int, Dict] = {}

            def _get_matricula(alumno_id: int) -> Dict:
                if alumno_id not in _mat_cache:
                    ok, mat = self.matricula_client.obtener_activa_por_alumno(alumno_id)
                    _mat_cache[alumno_id] = mat if ok and isinstance(mat, dict) else {}
                return _mat_cache[alumno_id]

            # 3. Procesamiento
            procesados = []
            stats = {"total": 0, "injustificadas": 0, "justificadas": 0}

            for item in raw_data:
                estado = item.get("estado", "").upper()

                # Solo faltas/inasistencias y justificados
                if estado not in (self.ESTADO_FALTA, self.ESTADO_JUSTIFICADO):
                    continue

                alumno = item.get("alumno", {}) or {}
                alumno_id = item.get("alumno_id") or alumno.get("id")

                # Obtener datos académicos desde matrícula
                matricula = _get_matricula(alumno_id) if alumno_id else {}
                alum_horario  = str(matricula.get("horario", "")).strip()
                alum_grupo    = str(matricula.get("grupo", "")).strip()
                alum_modalidad = str(matricula.get("modalidad", "")).strip()
                alum_codigo   = matricula.get("codigo_matricula", "")
                # Turno también está en la propia asistencia
                turno_asistencia = str(item.get("turno", "")).strip()
                horario_efectivo = alum_horario or turno_asistencia

                # Filtros
                if horario != "Todos":
                    if horario.lower() not in (horario_efectivo.lower(), turno_asistencia.lower()):
                        continue
                if grupo != "Todos" and grupo != alum_grupo:
                    continue
                if modalidad != "Todos" and modalidad.lower() != alum_modalidad.lower():
                    continue

                es_justificada = (estado == self.ESTADO_JUSTIFICADO)
                if solo_injustificadas and es_justificada:
                    continue

                # Contadores
                stats["total"] += 1
                if es_justificada:
                    stats["justificadas"] += 1
                else:
                    stats["injustificadas"] += 1

                # Mapeo de fila
                nombres      = alumno.get("nombres", "").upper()
                apell_pat    = alumno.get("apell_paterno", "").upper()
                apell_mat    = alumno.get("apell_materno", "").upper()
                nombre_completo = f"{apell_pat} {apell_mat}, {nombres}".strip(", ")

                fila = {
                    "id_asistencia": item.get("id"),
                    "codigo":    alum_codigo.upper(),
                    "nombre":    nombre_completo,
                    "horario":   horario_efectivo.upper(),
                    "celular":   alumno.get("celular_padre_1") or alumno.get("celular_padre") or "N/A",
                    "estado":    self.ESTADO_JUSTIFICADO if es_justificada else self.ESTADO_FALTA,
                    "reincidente": False,
                }
                procesados.append(fila)

            return True, "Ok", stats, procesados

        except Exception as e:
            return False, f"Error: {e}", {}, []

    def justificar_rapida(self, id_asistencia: int, motivo: str) -> Tuple[bool, str]:
        """
        Justificación rápida de una inasistencia.
        """
        if not motivo:
            return False, "Debe ingresar un motivo"
            
        data = {
            "estado": self.ESTADO_JUSTIFICADO,
            "observacion": motivo.upper()
        }
        
        success, res = self.client.actualizar(id_asistencia, data)
        if success:
            return True, "Falta justificada correctamente"
        else:
            return False, f"Error al actualizar: {res}"
