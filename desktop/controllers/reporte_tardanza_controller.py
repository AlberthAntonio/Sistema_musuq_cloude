from typing import List, Dict, Tuple, Any, Optional
from datetime import datetime, date
import csv
import urllib.parse
from core.api_client import AsistenciaClient, AlumnoClient, ReportesClient

class ReporteTardanzaController:
    """
    Controlador para la gestión de reportes de tardanzas.
    Sistema Musuq Cloud
    """
    
    def __init__(self, auth_token: str = ""):
        self.client = AsistenciaClient()
        self.alumno_client = AlumnoClient()
        self.reportes_client = ReportesClient()
        self.DEBUG = True

        for c in (self.client, self.alumno_client, self.reportes_client):
            if auth_token:
                c.token = auth_token

    def _log(self, mensaje: str, tipo: str = "DEBUG"):
        """Sistema de logging simple"""
        if self.DEBUG:
            print(f"[{tipo}] {mensaje}")

    def filtrar_tardanzas(self, f_inicio: str, f_fin: str, horario: str = "Todos", grupo: str = "Todos", modalidad: str = "Todos") -> Tuple[bool, str, List[Dict]]:
        """
        Obtiene tardanzas usando el endpoint consolidado GET /reportes/tardanzas.
        Los filtros grupo y turno se delegan al backend (consulta SQL directa).
        """
        self._log(f"=== INICIANDO filtrar_tardanzas ===")
        self._log(f"Params: {f_inicio} a {f_fin} | Horario={horario} | Grupo={grupo}")

        try:
            # Convertir fechas dd/mm/yyyy → yyyy-mm-dd
            try:
                d_ini = datetime.strptime(f_inicio, "%d/%m/%Y")
                d_fin = datetime.strptime(f_fin,    "%d/%m/%Y")
            except ValueError as e:
                return False, f"Formato de fecha inválido: {e}", []

            if d_ini > d_fin:
                d_ini, d_fin = d_fin, d_ini

            d_ini_api = d_ini.strftime("%Y-%m-%d")
            d_fin_api = d_fin.strftime("%Y-%m-%d")

            # Mapear "MATUTINO"→turno "MAÑANA", "VESPERTINO"→"TARDE" para la API
            turno_api = None
            if horario and horario != "Todos":
                h_up = horario.upper()
                if "MATUTINO" in h_up or "MAÑANA" in h_up or "MANANA" in h_up:
                    turno_api = "Mañana"
                elif "VESPERTINO" in h_up or "TARDE" in h_up:
                    turno_api = "Tarde"

            grupo_api = grupo if grupo and grupo != "Todos" else None

            success, result = self.reportes_client.tardanzas(
                fecha_inicio=d_ini_api,
                fecha_fin=d_fin_api,
                grupo=grupo_api,
                turno=turno_api,
            )

            if not success:
                error_msg = result.get("error", "Error desconocido") if isinstance(result, dict) else str(result)
                return False, f"Error al consultar servidor: {error_msg}", []

            raw = result if isinstance(result, list) else result.get("items", [])
            self._log(f"Tardanzas recibidas del backend: {len(raw)}")

            datos_filtrados = []
            for item in raw:
                # Filtro adicional de modalidad (no soportado en el endpoint)
                if modalidad and modalidad != "Todos":
                    if (item.get("modalidad") or "").upper() != modalidad.upper():
                        continue

                # Convertir fecha a dd/mm/yyyy para la vista
                fecha_raw = item.get("fecha", "")
                if hasattr(fecha_raw, "strftime"):
                    fecha_fmt = fecha_raw.strftime("%d/%m/%Y")
                else:
                    try:
                        fecha_fmt = datetime.strptime(str(fecha_raw)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
                    except Exception:
                        fecha_fmt = str(fecha_raw)

                fila = {
                    "id_asistencia": item.get("asistencia_id"),
                    "codigo":        item.get("codigo_matricula", "--"),
                    "nombre":        item.get("nombre_completo", ""),
                    "estado":        "TARDANZA",
                    "horario":       item.get("turno", "--"),
                    "grupo":         item.get("grupo") or "--",
                    "fecha":         fecha_fmt,
                    "hora":          item.get("hora") or "--:--",
                    "celular":       item.get("celular_padre") or "N/A",
                    "observacion":   item.get("observacion") or "",
                    "turno":         item.get("turno", ""),
                }
                datos_filtrados.append(fila)

            self._log(f"Tardanzas procesadas: {len(datos_filtrados)}")
            return True, f"Se encontraron {len(datos_filtrados)} tardanzas", datos_filtrados

        except Exception as e:
            self._log(f"ERROR CRÍTICO: {str(e)}", "ERROR")
            return False, f"Error interno: {str(e)}", []

    def obtener_estadisticas(self, datos: List[Dict]) -> Dict[str, Any]:
        """Calcula estadísticas de tardanzas"""
        if not datos:
            return {"total": 0, "por_horario": {}, "por_grupo": {}, "estudiantes_unicos": 0}
        
        stats = {
            "total": len(datos),
            "por_horario": {},
            "por_grupo": {},
            "estudiantes_unicos": len(set(d["codigo"] for d in datos)),
            "por_fecha": {}
        }
        
        for fila in datos:
            h = fila.get("horario", "DESCONOCIDO")
            stats["por_horario"][h] = stats["por_horario"].get(h, 0) + 1
            
            g = fila.get("grupo", "DESCONOCIDO")
            stats["por_grupo"][g] = stats["por_grupo"].get(g, 0) + 1
            
            f = fila.get("fecha", "DESCONOCIDA")
            stats["por_fecha"][f] = stats["por_fecha"].get(f, 0) + 1
        
        return stats

    def enviar_whatsapp(self, celular: str, alumno_nombre: str, fecha: str, hora: str) -> Tuple[bool, str]:
        """Prepara mensaje WhatsApp para tardanza"""
        if not celular or celular in ["N/A", "None", ""]:
            return False, "Sin número de celular"
        
        celular = celular.replace(" ", "").replace("-", "")
        mensaje = f"Hola, le informamos que {alumno_nombre} llegó con tardanza el {fecha} a las {hora}."
        url = f"https://wa.me/{celular}?text={urllib.parse.quote(mensaje)}"
        return True, url

    def exportar_csv(self, datos: List[Dict], filename: str = "Tardanzas.csv") -> Tuple[bool, str]:
        """Exporta a CSV"""
        try:
            if not datos:
                return False, "No hay datos"
            
            with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=["codigo", "nombre", "horario", "grupo", "fecha", "hora", "celular", "observacion"])
                writer.writeheader()
                for fila in datos:
                    writer.writerow({k: fila.get(k, "") for k in ["codigo", "nombre", "horario", "grupo", "fecha", "hora", "celular", "observacion"]})
            
            self._log(f"CSV exportado: {filename}")
            return True, f"Guardado: {filename}"
        except Exception as e:
            self._log(f"Error exportar CSV: {e}", "ERROR")
            return False, f"Error: {e}"
