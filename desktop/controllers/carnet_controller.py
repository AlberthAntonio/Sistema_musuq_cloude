import os
import io
from typing import List, Dict, Tuple
from datetime import datetime
from reportlab.lib.pagesizes import landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
import barcode
from barcode.writer import ImageWriter
import qrcode
from PIL import Image

from core.api_client import AlumnoClient


# Definir tamaño tarjeta CR-80 (Estandar Carnet)
# Ancho: 85.60 mm, Alto: 53.98 mm
CARD_WIDTH = 85.60 * mm
CARD_HEIGHT = 53.98 * mm


class AlumnoDTO:
    def __init__(self, data: Dict):
        self.id = data.get("id")
        self.codigo_matricula = data.get("codigo_matricula", "")
        self.dni = data.get("dni", "")
        self.nombres = data.get("nombres", "")
        self.apell_paterno = data.get("apell_paterno", "")
        self.apell_materno = data.get("apell_materno", "")
        self.grupo = data.get("grupo", "")
        self.foto_url = data.get("foto_url", "")  # URL o path local si existe

class CarnetController:
    def __init__(self):
        self.client = AlumnoClient()
        self.fondo_path = None  # Ruta a imagen de fondo personalizada

    def obtener_grupos(self) -> List[str]:
        """Obtiene lista de grupos únicos"""
        success, result = self.client.obtener_todos(limit=1000)
        grupos = set()
        if success:
            items = result.get("items", []) if isinstance(result, dict) else result
            for item in items:
                g = item.get("grupo")
                if g:
                    grupos.add(g)
        return sorted(list(grupos))

    def buscar_alumnos(self, grupo: str = None) -> List[AlumnoDTO]:
        """Busca alumnos, filtro opcional por grupo"""
        success, result = self.client.obtener_todos(limit=1000)
        if not success:
            return []
            
        items = result.get("items", []) if isinstance(result, dict) else result
        alumnos = []
        for item in items:
            if grupo and grupo != "Todos" and item.get("grupo") != grupo:
                continue
            alumnos.append(AlumnoDTO(item))
            
        # Ordenar alfabéticamente
        alumnos.sort(key=lambda x: f"{x.apell_paterno} {x.apell_materno} {x.nombres}")
        return alumnos

    def cargar_plantilla_fondo(self, ruta_imagen: str) -> Tuple[bool, str]:
        """Establece la imagen de fondo para los carnets"""
        if os.path.exists(ruta_imagen):
            self.fondo_path = ruta_imagen
            return True, "Fondo cargado correctamente"
        return False, "El archivo no existe"

    def generar_carnets_pdf(self, ids_alumnos: List[int]) -> Tuple[bool, str]:
        """Genera un archivo PDF con los carnets seleccionados (Anverso y Reverso)"""
        if not ids_alumnos:
            return False, "No hay alumnos seleccionados"

        # Recuperar datos de alumnos
        success, result = self.client.obtener_todos(limit=1000)
        if not success:
            return False, "Error al obtener datos de alumnos"
            
        items = result.get("items", []) if isinstance(result, dict) else result
        map_alumnos = {a['id']: AlumnoDTO(a) for a in items}
        
        lista_final = []
        for uid in ids_alumnos:
            if uid in map_alumnos:
                lista_final.append(map_alumnos[uid])

        if not lista_final:
            return False, "No se encontraron datos para los IDs seleccionados"

        # Configurar PDF
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Carnets_Masivos_{timestamp}.pdf"
        filepath = os.path.join(os.getcwd(), filename)

        try:
            # Usar A4 por defecto para imprimir varios carnets o tamaño tarjeta individual?
            # Imprimiremos en A4, 10 carnets por hoja (2 columnas x 5 filas) para ahorrar papel
            # O mejor: Pagina del tamaño EXACTO del carnet si es para impresora térmica.
            # Asumiremos A4 estándar para impresora de oficina.
            
            # Layout A4: 210mm x 297mm
            # Margen 10mm
            # 2 columnas (85.6mm cada una)
            # 5 filas (54mm cada una)
            
            c = canvas.Canvas(filepath, pagesize=landscape(card_size=(210*mm, 297*mm))) # Portrait A4
            # Revisar: Normalmente los carnets se imprimen en A4. Arreglemos el layout.
            c.setPageSize((210*mm, 297*mm)) 
            
            width_a4, height_a4 = 210*mm, 297*mm
            
            margin_x = 15 * mm
            margin_y = 15 * mm
            
            col_width = CARD_WIDTH + 5*mm
            row_height = CARD_HEIGHT + 5*mm
            
            cols = 2
            rows = 5
            
            x_curr = margin_x
            y_curr = height_a4 - margin_y - CARD_HEIGHT
            
            idx_in_page = 0
            
            for alumno in lista_final:
                # FRENTE
                self._dibujar_cara_frontal(c, x_curr, y_curr, alumno)
                
                # Mover cursor para REVERSO (Lado derecho del mismo carnet? O siguiente posición?)
                # Normalmente: Frente en una hoja, Reverso en otra (impresión doble cara).
                # O: Frente y Reverso lado a lado.
                # Para simplificar: Dibujaremos Frente y Reverso lado a lado.
                # Col 1: Frente, Col 2: Reverso
                
                # Ajuste: Mejor poner REVERSO a la derecha INMEDIATA del FRENTE
                x_reverso = x_curr + CARD_WIDTH + 2*mm
                self._dibujar_cara_posterior(c, x_reverso, y_curr, alumno)
                
                # Avanzar posición (Bajamos una fila)
                y_curr -= (CARD_HEIGHT + 2*mm)
                idx_in_page += 1
                
                if idx_in_page >= rows:
                    c.showPage()
                    idx_in_page = 0
                    x_curr = margin_x
                    y_curr = height_a4 - margin_y - CARD_HEIGHT

            c.save()
            
            if os.name == 'nt':
                os.startfile(filepath)
                
            return True, f"PDF generado correctamente: {filename}"

        except Exception as e:
            import traceback
            traceback.print_exc()
            return False, f"Error generando PDF: {str(e)}"

    def _dibujar_cara_frontal(self, c, x, y, alumno):
        """Dibuja el anverso del carnet en (x, y)"""
        # 1. Fondo / Borde
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setLineWidth(0.5)
        
        if self.fondo_path:
            try:
                c.drawImage(self.fondo_path, x, y, width=CARD_WIDTH, height=CARD_HEIGHT)
            except:
                c.rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        else:
            c.rect(x, y, CARD_WIDTH, CARD_HEIGHT)
            # Header color
            c.setFillColorRGB(0.2, 0.6, 0.86) # Azul Musuq o Theme primary
            c.rect(x, y + CARD_HEIGHT - 10*mm, CARD_WIDTH, 10*mm, fill=1, stroke=0)
            
            # Texto Institución
            c.setFillColorRGB(1, 1, 1)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(x + CARD_WIDTH/2, y + CARD_HEIGHT - 7*mm, "INSTITUCIÓN EDUCATIVA MUSUQ")

        # 2. Foto Placeholder
        c.setFillColorRGB(0.9, 0.9, 0.9)
        c.rect(x + 5*mm, y + 15*mm, 25*mm, 30*mm, fill=1, stroke=1)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.setFont("Helvetica", 6)
        c.drawCentredString(x + 17.5*mm, y + 30*mm, "FOTO")

        # 3. Datos Alumno
        text_x = x + 35*mm
        
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(text_x, y + 40*mm, f"{alumno.apell_paterno}")
        c.drawString(text_x, y + 35*mm, f"{alumno.apell_materno}")
        
        c.setFont("Helvetica", 10)
        c.drawString(text_x, y + 30*mm, f"{alumno.nombres}")
        
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.drawString(text_x, y + 22*mm, f"DNI: {alumno.dni}")
        c.drawString(text_x, y + 18*mm, f"CÓD: {alumno.codigo_matricula}")

        # 4. Código QR / Barras
        # Generar QR en memoria y dibujar
        if alumno.codigo_matricula:
            self._dibujar_qr(c, x + CARD_WIDTH - 20*mm, y + 5*mm, alumno.codigo_matricula, size=15*mm)

    def _dibujar_cara_posterior(self, c, x, y, alumno):
        """Dibuja el reverso del carnet en (x, y)"""
        # Borde
        c.setStrokeColorRGB(0.8, 0.8, 0.8)
        c.setLineWidth(0.5)
        c.rect(x, y, CARD_WIDTH, CARD_HEIGHT)

        # Contenido
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x + CARD_WIDTH/2, y + CARD_HEIGHT - 10*mm, "NORMAS DE USO")
        
        c.setFont("Helvetica", 6)
        text_obj = c.beginText(x + 5*mm, y + CARD_HEIGHT - 15*mm)
        lines = [
            "1. Este carnet es personal e intransferible.",
            "2. Debe portarse visiblemente dentro de la institución.",
            "3. En caso de pérdida, comunicar a Dirección inmediatamente.",
            "4. Válido para el año lectivo vigente."
        ]
        for line in lines:
            text_obj.textLine(line)
        c.drawText(text_obj)
        
        # Firma
        c.line(x + CARD_WIDTH/2 - 20*mm, y + 15*mm, x + CARD_WIDTH/2 + 20*mm, y + 15*mm)
        c.drawCentredString(x + CARD_WIDTH/2, y + 12*mm, "Dirección Académica")

    def _dibujar_qr(self, c, x, y, data, size=20*mm):
        try:
            qr = qrcode.QRCode(box_size=1, border=0)
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convertir a formato compatible con ReportLab
            img_io = io.BytesIO()
            img.save(img_io, format='PNG')
            img_io.seek(0)
            
            c.drawImage(ImageReader(img_io), x, y, width=size, height=size)
        except Exception as e:
            print(f"Error QR: {e}")
