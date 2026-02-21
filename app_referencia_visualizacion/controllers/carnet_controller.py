from app.database import SessionLocal
from app.models.alumno_model import Alumno
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.graphics.barcode import code128
from reportlab.lib.utils import ImageReader
import os
import shutil
from PIL import Image
from datetime import datetime

class CarnetController:
    def __init__(self):
        self.db = SessionLocal()
        # Ruta donde se guardará la imagen de fondo personalizada
        self.ruta_plantilla = os.path.join(os.getcwd(), "plantilla_carnet.png")

    def obtener_grupos(self):
        """Obtiene los grupos únicos para el filtro"""
        return [g[0] for g in self.db.query(Alumno.grupo).distinct().all() if g[0]]

    def buscar_alumnos(self, grupo):
        """Busca alumnos por grupo"""
        return self.db.query(Alumno).filter(Alumno.grupo == grupo).order_by(Alumno.apell_paterno).all()

    # --- GESTIÓN DE LA PLANTILLA ---
    def cargar_plantilla_fondo(self, ruta_origen):
        """Recibe una ruta de imagen y la guarda como plantilla del sistema"""
        try:
            # Validamos que sea una imagen válida abriéndola con PIL
            img = Image.open(ruta_origen)
            # Guardamos/Sobrescribimos en la carpeta del proyecto
            img.save(self.ruta_plantilla)
            return True, "Fondo cargado exitosamente. Se usará en los próximos carnets."
        except Exception as e:
            return False, f"Error al procesar la imagen: {str(e)}"

    def eliminar_plantilla(self):
        """Borra la plantilla para volver al diseño estándar"""
        if os.path.exists(self.ruta_plantilla):
            os.remove(self.ruta_plantilla)
            return True, "Fondo eliminado. Se usará el diseño estándar."
        return False, "No hay ningún fondo personalizado configurado."

    # --- GENERACIÓN DEL PDF ---
    def generar_carnets_pdf(self, ids_alumnos):
        if not ids_alumnos: return False, "Seleccione alumnos."
        
        alumnos = self.db.query(Alumno).filter(Alumno.id.in_(ids_alumnos)).all()
        
        # Guardar en Escritorio > Archivos MUSUQ > Carnets
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        carpeta = os.path.join(desktop, "Archivos MUSUQ", "Carnets")
        os.makedirs(carpeta, exist_ok=True)
        
        filename = f"Carnets_Lote_{datetime.now().strftime('%H%M%S')}.pdf"
        filepath = os.path.join(carpeta, filename)

        c = canvas.Canvas(filepath, pagesize=A4)
        width, height = A4
        
        # Configuración de Grilla (2 columnas x 5 filas = 10 carnets)
        ancho_carnet = 8.5 * cm
        alto_carnet = 5.4 * cm
        margen_x = 1.5 * cm
        margen_y = 1.0 * cm
        sep_x = 0.5 * cm
        sep_y = 0.2 * cm

        x_actual = margen_x
        y_actual = height - margen_y - alto_carnet
        contador_col = 0
        
        for alu in alumnos:
            self.dibujar_un_carnet(c, x_actual, y_actual, ancho_carnet, alto_carnet, alu)
            
            contador_col += 1
            if contador_col < 2: 
                x_actual += ancho_carnet + sep_x
            else: 
                contador_col = 0
                x_actual = margen_x
                y_actual -= (alto_carnet + sep_y)

            # Si ya no cabe otro carnet abajo, nueva página
            if y_actual < 1 * cm:
                c.showPage()
                y_actual = height - margen_y - alto_carnet
                x_actual = margen_x
                contador_col = 0

        c.save()
        try: os.startfile(filepath)
        except: pass
        return True, f"Carnets generados en:\n{filepath}"

    def dibujar_un_carnet(self, c, x, y, w, h, alumno):
        """Dibuja un solo carnet en la posición X, Y"""
        
        # 1. FONDO (Personalizado o Estándar)
        if os.path.exists(self.ruta_plantilla):
            # Dibujar imagen del usuario estirada
            try:
                c.drawImage(ImageReader(self.ruta_plantilla), x, y, width=w, height=h)
            except:
                # Si falla la imagen, dibuja rectángulo blanco por seguridad
                c.setFillColor(colors.white)
                c.rect(x, y, w, h, fill=1)
        else:
            # Diseño Estándar (Blanco con azul)
            c.setStrokeColor(colors.black)
            c.setLineWidth(0.5)
            c.setFillColor(colors.white)
            c.roundRect(x, y, w, h, 8, fill=1, stroke=1)
            
            # Encabezado
            c.setFillColor(colors.HexColor("#2c3e50"))
            c.rect(x, y + h - 1.2*cm, w, 1.2*cm, fill=1, stroke=0)
            c.setFillColor(colors.white)
            c.setFont("Helvetica-Bold", 10)
            c.drawCentredString(x + w/2, y + h - 0.6*cm, "INSTITUCIÓN EDUCATIVA MUSUQ")
            c.setFont("Helvetica", 6)
            c.drawCentredString(x + w/2, y + h - 0.95*cm, "CARNET DE ESTUDIANTE")

        # 2. FOTO (Marcador de posición)
        c.setFillColor(colors.lightgrey)
        # Solo borde si hay plantilla, relleno si es estándar
        relleno = 0 if os.path.exists(self.ruta_plantilla) else 1
        c.rect(x + 0.3*cm, y + 1.4*cm, 2.3*cm, 2.8*cm, fill=relleno, stroke=1)
        
        if not os.path.exists(self.ruta_plantilla):
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 5)
            c.drawCentredString(x + 1.45*cm, y + 2.8*cm, "FOTO")

        # 3. TEXTOS (Datos del alumno)
        text_x = x + 2.9*cm
        c.setFillColor(colors.black) # Asumimos texto negro (cuidado con fondos oscuros)
        
        c.setFont("Helvetica-Bold", 11)
        c.drawString(text_x, y + 3.8*cm, f"{alumno.apell_paterno}")
        c.drawString(text_x, y + 3.4*cm, f"{alumno.apell_materno}")
        
        c.setFont("Helvetica", 10)
        c.drawString(text_x, y + 3.0*cm, f"{alumno.nombres}")

        c.setFont("Helvetica", 7)
        c.drawString(text_x, y + 2.4*cm, f"DNI: {alumno.dni}")
        c.drawString(text_x, y + 2.0*cm, f"CÓDIGO:")
        c.setFont("Helvetica-Bold", 8)
        c.drawString(text_x, y + 1.65*cm, f"{alumno.codigo_matricula}")

        # 4. CÓDIGO DE BARRAS (Code 128)
        # Dibujamos el código de barras vectorial
        try:
            barcode = code128.Code128(alumno.codigo_matricula, barHeight=0.7*cm, barWidth=0.8)
            barcode.drawOn(c, x + 1.5*cm, y + 0.3*cm)
        except:
            pass