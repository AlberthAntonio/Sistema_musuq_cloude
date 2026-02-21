from typing import List, Dict, Tuple, Any
from datetime import datetime
from core.api_client import AsistenciaClient

class ReporteInasistenciaController:
    """
    Controlador para reporte y gestión de inasistencias.
    """
    
    def __init__(self):
        self.client = AsistenciaClient()

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

            # 2. Consumo API
            success, result = self.client.listar(
                fecha_inicio=d_query,
                fecha_fin=d_query # Solo un día
            )
            
            if not success:
                return False, "Error de conexión", {}, []
            
            raw_data = result if isinstance(result, list) else result.get("items", [])
            
            # 3. Procesamiento
            procesados = []
            stats = {
                "total": 0,
                "injustificadas": 0,
                "justificadas": 0
            }
            
            for item in raw_data:
                estado = item.get("estado", "").upper()
                
                # Filtrar solo NO ASISTENCIAS o FALTAS
                if estado not in ["FALTA", "INASISTENCIA", "JUSTIFICADO"]:
                    continue
                
                alumno = item.get("alumno", {})
                if not alumno: continue
                
                # Filtros Locales
                alum_horario = str(alumno.get("horario", "")).upper()
                alum_grupo = str(alumno.get("grupo", "")).upper()
                
                if horario != "Todos" and horario.upper() not in alum_horario:
                    continue
                if grupo != "Todos" and grupo != alum_grupo:
                    continue
                    
                # Filtro Injustificadas
                es_justificada = (estado == "JUSTIFICADO")
                if solo_injustificadas and es_justificada:
                    continue
                    
                # Contadores
                stats["total"] += 1
                if es_justificada:
                    stats["justificadas"] += 1
                else:
                    stats["injustificadas"] += 1
                
                # Mapeo
                fila = {
                    "id_asistencia": item.get("id"),
                    "codigo": alumno.get("codigo_matricula", ""),
                    "nombre": f"{alumno.get('apell_paterno')} {alumno.get('apell_materno')}, {alumno.get('nombres')}",
                    "horario": alum_horario,
                    "celular": alumno.get("telefono_apoderado") or "None",
                    "estado": "JUSTIFICADO" if es_justificada else "INASISTENCIA",
                    "reincidente": False # TODO: Calcular si es reincidente (requiere historial)
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
            "estado": "JUSTIFICADO",
            "observacion": motivo
        }
        
        success, res = self.client.actualizar(id_asistencia, data)
        if success:
            return True, "Falta justificada correctamente"
        else:
            return False, f"Error al actualizar: {res}"
