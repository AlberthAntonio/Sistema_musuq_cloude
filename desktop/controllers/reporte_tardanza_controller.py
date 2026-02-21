from typing import List, Dict, Tuple, Any, Optional
from datetime import datetime, date
import csv
import urllib.parse
from core.api_client import AsistenciaClient, AlumnoClient

class ReporteTardanzaController:
    """
    Controlador para la gestión de reportes de tardanzas.
    Sistema Musuq Cloud - Versión Mejorada con Validaciones
    """
    
    def __init__(self):
        self.client = AsistenciaClient()
        self.alumno_client = AlumnoClient()
        self.DEBUG = True

    def _log(self, mensaje: str, tipo: str = "DEBUG"):
        """Sistema de logging simple"""
        if self.DEBUG:
            print(f"[{tipo}] {mensaje}")

    def filtrar_tardanzas(self, f_inicio: str, f_fin: str, horario: str = "Todos", grupo: str = "Todos", modalidad: str = "Todos") -> Tuple[bool, str, List[Dict]]:
        """
        Obtiene la lista de tardanzas filtradas desde el backend.
        
        Args:
            f_inicio: Fecha inicial "dd/mm/yyyy"
            f_fin: Fecha final "dd/mm/yyyy"
            horario: Filtro de horario ("Todos", "MATUTINO", "VESPERTINO", etc.)
            grupo: Filtro de grupo ("Todos", "A", "B", "C", "D")
            modalidad: Filtro de modalidad (reservado para futuro)
            
        Returns:
            (Exito, Mensaje, Lista_de_datos)
        """
        self._log(f"=== INICIANDO filtrar_tardanzas ===")
        self._log(f"Params: {f_inicio} a {f_fin} | Horario={horario} | Grupo={grupo}")
        
        try:
            # ============= PASO 1: VALIDAR Y CONVERTIR FECHAS =============
            try:
                d_ini = datetime.strptime(f_inicio, "%d/%m/%Y")
                d_fin = datetime.strptime(f_fin, "%d/%m/%Y")
                self._log(f"Fechas válidas: {d_ini.date()} a {d_fin.date()}")
            except ValueError as e:
                self._log(f"ERROR conversión fechas: {e}", "ERROR")
                return False, f"Formato de fecha inválido: {e}", []

            # Validar orden
            if d_ini > d_fin:
                self._log(f"Fechas invertidas detectadas, corrigiendo", "WARNING")
                d_ini, d_fin = d_fin, d_ini

            # Convertir a formato API
            d_ini_api = d_ini.strftime("%Y-%m-%d")
            d_fin_api = d_fin.strftime("%Y-%m-%d")
            dias_rango = (d_fin - d_ini).days + 1
            self._log(f"Rango final: {dias_rango} días | API: {d_ini_api} a {d_fin_api}")

            # ============= PASO 2: CONSULTAR BACKEND =============
            page_limit = 500
            skip = 0
            raw_data = []
            self._log(f"GET /asistencia/?fecha_inicio={d_ini_api}&fecha_fin={d_fin_api}")

            while True:
                success, result = self.client.listar(
                    fecha_inicio=d_ini_api,
                    fecha_fin=d_fin_api,
                    skip=skip,
                    limit=page_limit
                )
                
                if not success:
                    error_msg = result if isinstance(result, str) else str(result.get("error", "Error desconocido"))
                    self._log(f"ERROR API: {error_msg}", "ERROR")
                    return False, f"Error al consultar servidor: {error_msg}", []

                batch = result if isinstance(result, list) else result.get("items", [])
                raw_data.extend(batch)
                self._log(f"Lote recibido: {len(batch)} | Acumulado: {len(raw_data)}")

                if len(batch) < page_limit:
                    break

                skip += page_limit

            self._log("Respuesta API recibida")

            # ============= PASO 3: PROCESAR RESPUESTA =============
            self._log(f"Registros totales en rango: {len(raw_data)}")

            # ============= PASO 4: FILTRAR POR ESTADO TARDANZA =============
            tardanzas_raw = [
                item for item in raw_data 
                if item.get("estado", "").upper() == "TARDANZA"
            ]
            self._log(f"Tardanzas encontradas: {len(tardanzas_raw)}")

            # ============= PASO 5: TRANSFORMAR Y FILTRAR =============
            datos_filtrados = []
            
            def normalizar_horario(valor: str) -> str:
                texto = (valor or "").strip().upper()
                equivalencias = {
                    "MAÑANA": "MATUTINO",
                    "MANANA": "MATUTINO",
                    "TARDE": "VESPERTINO"
                }
                return equivalencias.get(texto, texto)

            for idx, item in enumerate(tardanzas_raw):
                try:
                    # Obtener datos del alumno
                    alumno = item.get("alumno", {})
                    if not alumno:
                        self._log(f"  [Reg {idx}] Saltado: Sin objeto alumno anidado", "WARNING")
                        continue

                    # Extraer datos
                    alum_codigo = alumno.get("codigo_matricula", "--")
                    alum_nombres = alumno.get("nombres", "").strip()
                    alum_apell_pat = alumno.get("apell_paterno", "").strip()
                    alum_apell_mat = alumno.get("apell_materno", "").strip()
                    alum_horario = str(alumno.get("horario", "DESCONOCIDO")).strip().upper()
                    alum_grupo = str(alumno.get("grupo", "")).strip().upper()
                    alum_modalidad = str(alumno.get("modalidad", "")).strip().upper()
                    alum_telefono = alumno.get("telefono_apoderado") or alumno.get("telefono", "N/A")
                    
                    # Validar nombre completo
                    if not alum_nombres or not alum_apell_pat:
                        self._log(f"  [Reg {idx}] Saltado: Nombre incompleto ({alum_nombres}/{alum_apell_pat})", "WARNING")
                        continue
                    
                    nombre_completo = f"{alum_apell_pat} {alum_apell_mat}, {alum_nombres}".strip()

                    # ===== FILTROS ADICIONALES =====
                    if horario != "Todos":
                        seleccionado = normalizar_horario(horario)
                        horario_alumno = normalizar_horario(alum_horario)
                        turno_asistencia = normalizar_horario(item.get("turno", ""))
                        if seleccionado not in [horario_alumno, turno_asistencia]:
                            continue
                    
                    if grupo != "Todos":
                        if alum_grupo != grupo.upper():
                            continue

                    if modalidad != "Todos":
                        if alum_modalidad != modalidad.upper().strip():
                            continue

                    # ===== CONVERTIR FECHA =====
                    fecha_raw = item.get("fecha", "")
                    try:
                        if "T" in fecha_raw:
                            fecha_raw = fecha_raw.split("T")[0]
                        fecha_fmt = datetime.strptime(fecha_raw, "%Y-%m-%d").strftime("%d/%m/%Y")
                    except Exception as e:
                        fecha_fmt = fecha_raw
                        self._log(f"  [Reg {idx}] Adv: Fecha no convertida ({fecha_raw})", "WARNING")

                    # ===== CONSTRUIR FILA =====
                    fila = {
                        "id_asistencia": item.get("id", 0),
                        "codigo": alum_codigo,
                        "nombre": nombre_completo,
                        "estado": "TARDANZA",
                        "horario": alum_horario,
                        "grupo": alum_grupo,
                        "fecha": fecha_fmt,
                        "hora": item.get("hora", "--:--"),
                        "celular": alum_telefono,
                        "observacion": item.get("observacion", ""),
                        "turno": item.get("turno", "")
                    }
                    
                    datos_filtrados.append(fila)
                    
                except Exception as e:
                    self._log(f"  [Reg {idx}] ERROR: {e}", "ERROR")
                    continue

            self._log(f"Tardanzas procesadas: {len(datos_filtrados)}")
            self._log(f"=== FIN filtrar_tardanzas ===\n")
            
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
