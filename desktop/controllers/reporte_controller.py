import os
import threading
from typing import List, Tuple, Dict
from datetime import datetime
import importlib

from core.api_client import AlumnoClient, ListasClient

# Clase DTO para mantener compatibilidad con la vista
class AlumnoDTO:
    def __init__(self, data: Dict):
        self.id = data.get("id")
        self.codigo_matricula = data.get("codigo_matricula", "")
        self.dni = data.get("dni", "")
        self.nombres = data.get("nombres", "")
        self.apell_paterno = data.get("apell_paterno", "")
        self.apell_materno = data.get("apell_materno", "")
        self.grupo = data.get("grupo", "")
        self.modalidad = data.get("modalidad", "")
        self.horario = data.get("horario", "")
        
        # Campos extra para reportes
        self.celular_padre_1 = data.get("telefono_apoderado", "") # Ajustar según API
        self.nombre_padre_completo = data.get("nombre_apoderado", "") # Ajustar según API

class ReporteController:
    def __init__(self):
        self.client = AlumnoClient()
        self.listas_client = ListasClient()

    def _cargar_reportlab(self):
        """Carga símbolos de reportlab bajo demanda para evitar crash al importar el módulo."""
        try:
            pagesizes = importlib.import_module("reportlab.lib.pagesizes")
            pdfgen_canvas = importlib.import_module("reportlab.pdfgen.canvas")
            units = importlib.import_module("reportlab.lib.units")
            colors_mod = importlib.import_module("reportlab.lib.colors")
            platypus = importlib.import_module("reportlab.platypus")
            return {
                "A4": pagesizes.A4,
                "landscape": pagesizes.landscape,
                "canvas": pdfgen_canvas,
                "cm": units.cm,
                "colors": colors_mod,
                "Table": platypus.Table,
                "TableStyle": platypus.TableStyle,
            }
        except ImportError:
            return None

    def obtener_filtros_disponibles(self):
        """
        Obtiene filtros únicos desde la memoria (ya que la API no tiene endpoint de agregación).
        """
        # Obtenemos TODOS para filtrar (podría ser pesado si son muchos, pero es lo que hay)
        success, result = self.client.obtener_todos(limit=1000)
        
        grupos = set()
        modalidades = set()
        turnos = set()
        
        if success:
            items = result.get("items", []) if isinstance(result, dict) else result
            for item in items:
                if item.get("grupo"): grupos.add(item["grupo"])
                if item.get("modalidad"): modalidades.add(item["modalidad"])
                if item.get("horario"): turnos.add(item["horario"])
                
        return sorted(list(grupos)), sorted(list(modalidades)), sorted(list(turnos))

    def buscar_alumnos(self, grupo, modalidad, horario):
        """Busca alumnos aplicando filtros en el cliente"""
        # 1. Obtener todos
        success, result = self.client.obtener_todos(limit=1000)
        if not success:
            return []
            
        items = result.get("items", []) if isinstance(result, dict) else result
        alumnos_dto = []
        
        for item in items:
            # Filtros
            if grupo and grupo != "Todos" and item.get("grupo") != grupo:
                continue
            if modalidad and modalidad != "Todas" and item.get("modalidad") != modalidad:
                continue
            if horario and horario != "Todos" and item.get("horario") != horario:
                continue
                
            alumnos_dto.append(AlumnoDTO(item))
            
        # Ordenar por apellido
        alumnos_dto.sort(key=lambda x: x.apell_paterno)
        return alumnos_dto

    def generar_reporte_pdf(self, ids_alumnos, tipo_reporte, titulo_personalizado):
        reportlab = self._cargar_reportlab()
        if reportlab is None:
            return False, "Falta la dependencia 'reportlab'. Instale con: pip install reportlab"

        A4 = reportlab["A4"]
        landscape = reportlab["landscape"]
        canvas = reportlab["canvas"]
        cm = reportlab["cm"]
        colors = reportlab["colors"]
        Table = reportlab["Table"]
        TableStyle = reportlab["TableStyle"]

        if not ids_alumnos:
            return False, "No hay alumnos seleccionados."
            
        # 1. Recuperar alumnos seleccionados (desde API)
        # Optimizacion: Podríamos pasar los objetos ya cargados, pero para mantener 
        # la firma del método original, los buscaremos de nuevo o filtramos de caché.
        # Por simplicidad y consistencia, traemos todos y filtramos en memoria.
        success, result = self.client.obtener_todos(limit=1000)
        if not success:
             return False, "Error al obtener datos."
             
        items = result.get("items", []) if isinstance(result, dict) else result
        alumnos_map = {a["id"]: a for a in items}
        
        lote_alumnos = []
        for id_alu in ids_alumnos:
            if id_alu in alumnos_map:
                lote_alumnos.append(AlumnoDTO(alumnos_map[id_alu]))
        
        lote_alumnos.sort(key=lambda x: x.apell_paterno)

        # --- CONFIGURACIÓN DE PÁGINA ---
        if tipo_reporte in ['asistencia', 'datos', "notas"]:
            pagesize = landscape(A4)
            width, height = landscape(A4)
            max_filas_por_pag = 27 
        else:
            pagesize = A4
            width, height = A4
            max_filas_por_pag = 40 

        filename = f"Reporte_{tipo_reporte}_{datetime.now().strftime('%H%M%S')}.pdf"
        filepath = os.path.join(os.getcwd(), filename)
        
        try:
            c = canvas.Canvas(filepath, pagesize=pagesize)
            
            # --- PAGINACIÓN ---
            for i in range(0, len(lote_alumnos), max_filas_por_pag):
                chunk = lote_alumnos[i : i + max_filas_por_pag]
                
                # Encabezado
                c.setFont("Helvetica-Bold", 16)
                c.drawString(1.5*cm, height - 1*cm, titulo_personalizado.upper())
                
                c.setFont("Helvetica", 10)
                c.drawString(1.5*cm, height - 1.5*cm, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                
                pag_actual = (i // max_filas_por_pag) + 1
                c.drawString(width - 5*cm, height - 1.5*cm, f"Pág. {pag_actual}")

                # Tabla
                data = []
                col_widths = []
                
                if tipo_reporte == 'asistencia':
                    headers = ["N°", "ALUMNO"] + [str(d) for d in range(1, 33)]
                    data.append(headers)
                    col_widths = [1*cm, 7*cm] + [0.6*cm] * 32
                    for idx, alu in enumerate(chunk, 1):
                        num = i + idx
                        data.append([str(num), f"{alu.apell_paterno} {alu.apell_materno}, {alu.nombres}"] + [""]*32)

                elif tipo_reporte == 'notas':
                    headers = ["N°", "ALUMNO", "NOTA 1", "NOTA 2", "NOTA 3", "PROM.", "OBSERV."]
                    data.append(headers)
                    col_widths = [1*cm, 9*cm, 2*cm, 2*cm, 2*cm, 1.5*cm, 6*cm]
                    for idx, alu in enumerate(chunk, 1):
                        num = i + idx
                        data.append([str(num), f"{alu.apell_paterno} {alu.apell_materno}, {alu.nombres}"] + [""]*5)

                elif tipo_reporte == 'datos':
                    headers = ["N°", "ALUMNO", "DNI", "CEL. APODERADO", "NOMBRE APODERADO", "OBSERV."]
                    data.append(headers)
                    col_widths = [1*cm, 7*cm, 2.5*cm, 3*cm, 7*cm, 5*cm]
                    for idx, alu in enumerate(chunk, 1):
                        num = i + idx
                        data.append([
                            str(num), 
                            f"{alu.apell_paterno}, {alu.apell_materno}, {alu.nombres}", 
                            alu.dni, 
                            alu.celular_padre_1 or "-", 
                            alu.nombre_padre_completo or "-", 
                            ""
                        ])
                else: # simple
                    headers = ["N°", "CÓDIGO", "ALUMNO", "DNI", "FIRMA"]
                    data.append(headers)
                    col_widths = [1*cm, 2.5*cm, 7*cm, 2.5*cm, 4*cm]
                    for idx, alu in enumerate(chunk, 1):
                        num = i + idx
                        data.append([str(num), alu.codigo_matricula, f"{alu.apell_paterno}, {alu.apell_materno}, {alu.nombres}", alu.dni, ""])

                table = Table(data, colWidths=col_widths)
                estilo = TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ])
                table.setStyle(estilo)
                table.wrapOn(c, width, height)
                table.drawOn(c, 1.5*cm, height - 3*cm - (len(data) * 0.6*cm))
                
                if (i + max_filas_por_pag) < len(lote_alumnos):
                    c.showPage()
            
            c.save()
            
            if os.name == 'nt': os.startfile(filepath)
            
            return True, f"Reporte generado: {filename}"
            
        except Exception as e:
            return False, str(e)

    # --- PERSISTENCIA EN BACKEND (Listas API) ---

    def guardar_lista_personalizada(self, nombre_lista: str, ids_alumnos: list):
        """Guarda una lista de alumnos en el backend (POST /listas/ + POST /listas/{id}/alumnos)"""
        if not nombre_lista:
            return False, "El nombre de la lista no puede estar vacío"
        # 1. Crear registro de lista
        success, result = self.listas_client.crear({"nombre": nombre_lista})
        if not success:
            return False, result.get("error", "Error al crear la lista")
        lista_id = result.get("id")
        # 2. Asignar alumnos a la lista
        if ids_alumnos and lista_id:
            ok, r = self.listas_client.agregar_alumnos(lista_id, ids_alumnos)
            if not ok:
                return False, r.get("error", "Lista creada pero error al agregar alumnos")
        return True, "Lista guardada correctamente."

    def obtener_listas_guardadas(self):
        """Obtiene todas las listas desde el backend (GET /listas/)"""
        success, result = self.listas_client.obtener_todas(skip=0, limit=500)
        if not success:
            return []
        listas = result if isinstance(result, list) else result.get("items", [])

        class ListaObj:
            def __init__(self, d):
                self.id = d.get("id")
                self.nombre = d.get("nombre", "")
                self.alumnos_ids = [
                    a.get("id") if isinstance(a, dict) else a
                    for a in d.get("alumnos", [])
                ]
        return [ListaObj(d) for d in listas]

    def cargar_alumnos_de_lista(self, lista_id: int):
        """Carga los alumnos de una lista específica desde el backend (GET /listas/{id})"""
        # 1. Obtener lista con alumnos anidados
        success, result = self.listas_client.obtener_por_id(lista_id)
        if not success or not result:
            return []

        alumnos_raw = result.get("alumnos", [])
        if not alumnos_raw:
            return []

        # Si la API devuelve objetos alumno anidados directamente, convertirlos a DTO
        if alumnos_raw and isinstance(alumnos_raw[0], dict) and "nombres" in alumnos_raw[0]:
            return [AlumnoDTO(a) for a in alumnos_raw]

        # Si solo devuelve IDs, traer todos y filtrar
        target_ids = set(
            a.get("id") if isinstance(a, dict) else a for a in alumnos_raw
        )
        success2, result2 = self.client.obtener_todos(limit=1000)
        if not success2:
            return []
        items = result2.get("items", []) if isinstance(result2, dict) else result2
        return [AlumnoDTO(a) for a in items if a.get("id") in target_ids]

    def eliminar_lista(self, lista_id: int):
        """Elimina una lista desde el backend (DELETE /listas/{id})"""
        success, result = self.listas_client.eliminar(lista_id)
        if success:
            return True, "Lista eliminada"
        return False, result.get("error", "Error al eliminar la lista")
