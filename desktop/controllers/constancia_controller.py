import os
from typing import List, Dict, Tuple
from datetime import date, datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors

from core.api_client import AlumnoClient


class AlumnoDTO:
    def __init__(self, data: Dict):
        self.id = data.get("id")
        self.codigo_matricula = data.get("codigo_matricula", "S/C")
        self.dni = data.get("dni", "")
        self.nombres = data.get("nombres", "")
        self.apell_paterno = data.get("apell_paterno", "")
        self.apell_materno = data.get("apell_materno", "")
        
        # Ajustar según API real
        self.grupo = data.get("grupo", "U") 
        self.modalidad = data.get("modalidad", "Presencial")
        self.carrera = data.get("carrera", "Educación Secundaria") # Valor por defecto si no viene de API
        self.horario = data.get("horario", "Mañana")

    @property
    def nombre_completo(self):
        return f"{self.apell_paterno} {self.apell_materno}, {self.nombres}"
    
    @property
    def apellidos(self):
        return f"{self.apell_paterno} {self.apell_materno}"


class ConstanciaController:
    def __init__(self):
        self.client = AlumnoClient()

    def buscar_alumnos(self, query: str) -> List[AlumnoDTO]:
        """Busca alumnos por nombre o DNI"""
        if not query:
            return []
            
        success, result = self.client.buscar(query)
        # Fallback si la busqueda de la API no es muy flexible, traemos todos y filtramos
        # (Depende de la implementación de backend existente, asumiremos que client.buscar funciona o usamos client.obtener_todos si falla)
        
        items = []
        if success:
            items = result.get("items", []) if isinstance(result, dict) else result
            # Si el resultado fue vacío o la API de búsqueda es limitada, intentamos fallback local
            # NOTA: En producción idealmente la API hace el trabajo.
        
        if not items and len(query) < 3: # Si es muy corto no hacemos fallback pesado
             return []
             
        # Convertir a DTOs
        alumnos = [AlumnoDTO(item) for item in items]
        return alumnos

    def generar_constancia_pdf(self, tipo_documento: str, alumno: AlumnoDTO, opciones: Dict) -> Tuple[bool, str]:
        """Genera el PDF de la constancia seleccionada"""
        
        try:
            filename = f"Constancia_{alumno.dni}_{date.today().strftime('%Y%m%d_%H%M%S')}.pdf"
            # Guardar en carpeta documentos por defecto
            output_dir = os.path.join(os.getcwd(), "documentos")
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)

            c = canvas.Canvas(filepath, pagesize=A4)
            width, height = A4
            
            # --- MARGENES ---
            margin_left = 3 * cm
            margin_right = 3 * cm
            margin_top = 3 * cm
            
            # --- HEADER ---
            # Logo textual (o imagen si hubiera)
            c.setFont("Times-Bold", 24)
            c.drawCentredString(width/2, height - 2*cm, "IE")
            
            c.setFont("Times-Bold", 14)
            c.drawCentredString(width/2, height - 3*cm, "INSTITUCIÓN EDUCATIVA MUSUQ")
            
            # TITULO DOCUMENTO
            c.setFont("Times-Bold", 18)
            titulo = tipo_documento.upper()
            c.drawCentredString(width/2, height - 6*cm, titulo)
            c.line(margin_left, height - 6.2*cm, width - margin_right, height - 6.2*cm)
            
            # --- CUERPO ---
            c.setFont("Times-Roman", 12)
            y_cursor = height - 9*cm
            line_height = 0.7*cm
            
            texto_cuerpo = []
            
            nombre_alumno = alumno.nombre_completo.upper()
            
            if "Matrícula" in tipo_documento:
                texto_cuerpo = [
                    "La Dirección de la INSTITUCIÓN EDUCATIVA MUSUQ,",
                    "CERTIFICA:",
                    "",
                    f"Que el/la estudiante: {nombre_alumno}",
                    f"Identificado(a) con DNI N°: {alumno.dni}",
                    f"Código de Matrícula: {alumno.codigo_matricula}",
                    "",
                    f"Se encuentra MATRICULADO(A) en el presente año académico {date.today().year}",
                    f"en la modalidad {alumno.modalidad} - Grupo {alumno.grupo}",
                    f"en la carrera de {alumno.carrera}.",
                    "",
                    "Se expide la presente constancia a solicitud del interesado",
                    "para los fines que estime conveniente."
                ]
            elif "Estudios" in tipo_documento:
                texto_cuerpo = [
                    "La Dirección de la INSTITUCIÓN EDUCATIVA MUSUQ,",
                    "HACE CONSTAR:",
                    "",
                    f"Que: {nombre_alumno}",
                    f"Con DNI N°: {alumno.dni} y Código N°: {alumno.codigo_matricula}",
                    "",
                    "Es estudiante REGULAR de esta institución.",
                    f"Actualmente cursa estudios en la carrera de {alumno.carrera},",
                    f"en el horario {alumno.horario}.",
                    "",
                    "Durante su permanencia ha demostrado buena conducta y aprovechamiento.",
                    "Se expide el presente documento para los fines que considere pertinente."
                ]
            else:
                 texto_cuerpo = [
                    "La Dirección de la INSTITUCIÓN EDUCATIVA MUSUQ,",
                    "CERTIFICA:",
                    "",
                    f"Que: {nombre_alumno}",
                    f"DNI N°: {alumno.dni}",
                    "",
                    f"Ha solicitado {tipo_documento}.",
                    "Documento generado automáticamente por el sistema."
                ]

            for linea in texto_cuerpo:
                if linea == "":
                    y_cursor -= line_height
                    continue
                
                # Centrar lineas específicas si se desea, o justificar. Simplificamos a Izquierda o Centro.
                if linea.isupper() and "CERTIFICA" in linea or "HACE CONSTAR" in linea:
                     c.drawCentredString(width/2, y_cursor, linea)
                else:
                    c.drawString(margin_left, y_cursor, linea)
                y_cursor -= line_height

            # --- EXTRAS ---
            if opciones.get("incluir_notas"):
                y_cursor -= 1*cm
                c.setFont("Times-Bold", 11)
                c.drawString(margin_left, y_cursor, "Nota: Historial de notas adjunto (Simulado).")

            # --- FECHA Y FIRMA ---
            c.setFont("Times-Roman", 11)
            fecha_str = f"Lima, {date.today().strftime('%d de %B de %Y')}"
            c.drawCentredString(width/2, 5*cm, fecha_str)
            
            c.line(width/2 - 3*cm, 3*cm, width/2 + 3*cm, 3*cm)
            c.setFont("Times-Roman", 9)
            c.drawCentredString(width/2, 2.5*cm, "Dirección Académica")
            
            c.save()
            
            if os.name == 'nt':
                os.startfile(filepath)
                
            return True, f"Documento generado: {filename}"

        except Exception as e:
            return False, f"Error: {str(e)}"
