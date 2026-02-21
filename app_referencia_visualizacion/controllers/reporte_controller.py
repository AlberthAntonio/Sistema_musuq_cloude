from app.database import SessionLocal
from app.models.alumno_model import Alumno
from app.models.lista_model import ListaGuardada
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import os
from datetime import datetime

class ReporteController:
    def __init__(self):
        self.db = SessionLocal()

    def obtener_filtros_disponibles(self):
        """
        Obtiene listas únicas para los comboboxes (SIN CARRERA).
        Retorna: (grupos, modalidades, turnos)
        """
        def get_distinct(column):
            res = [x[0] for x in self.db.query(column).distinct().all() if x[0]]
            return sorted(res)

        grupos = get_distinct(Alumno.grupo)
        modalidades = get_distinct(Alumno.modalidad)
        turnos = get_distinct(Alumno.horario)

        return grupos, modalidades, turnos

    def buscar_alumnos(self, grupo, modalidad, horario):
        """Busca alumnos aplicando los 3 filtros restantes"""
        query = self.db.query(Alumno)
        
        if grupo and grupo != "Todos":
            query = query.filter(Alumno.grupo == grupo)
        if modalidad and modalidad != "Todas":
            query = query.filter(Alumno.modalidad == modalidad)
        
        # Lógica especial: Si el horario está deshabilitado en la vista,  turno
        # a veces llega como "Todos" o vacío, pero aquí aseguramos el filtro.
        if horario and horario != "Todos":
            query = query.filter(Alumno.horario == horario)
            
        return query.order_by(Alumno.apell_paterno).all()

    def generar_reporte_pdf(self, ids_alumnos, tipo_reporte, titulo_personalizado):
        if not ids_alumnos:
            return False, "No hay alumnos seleccionados."
            
        # 1. Obtener todos los alumnos ordenados
        alumnos_total = self.db.query(Alumno).filter(Alumno.id.in_(ids_alumnos)).order_by(Alumno.apell_paterno).all()

        # --- CONFIGURACIÓN DE PÁGINA ---
        if tipo_reporte in ['asistencia', 'datos', "notas"]:
            pagesize = landscape(A4)
            width, height = landscape(A4)
            max_filas_por_pag = 27 # Menos filas porque es horizontal
        else:
            pagesize = A4
            width, height = A4
            max_filas_por_pag = 40 # Más filas en vertical

        filename = f"Reporte_{tipo_reporte}_{datetime.now().strftime('%H%M%S')}.pdf"
        filepath = os.path.join(os.getcwd(), filename)
        
        c = canvas.Canvas(filepath, pagesize=pagesize)

        # --- LÓGICA DE PAGINACIÓN ---
        # Dividimos la lista de alumnos en trozos (chunks)
        # range(inicio, fin, paso) -> Ej: 0, 30, 60...
        for i in range(0, len(alumnos_total), max_filas_por_pag):
            
            # Seleccionamos el lote actual (Ej: del 0 al 30)
            lote_alumnos = alumnos_total[i : i + max_filas_por_pag]
            
            # --- 1. DIBUJAR ENCABEZADO (Se repite en cada página) ---
            c.setFont("Helvetica-Bold", 16)
            c.drawString(1.5*cm, height - 1*cm, titulo_personalizado.upper())
            
            c.setFont("Helvetica", 10)
            c.drawString(1.5*cm, height - 1.5*cm, f"Fecha: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            
            # Mostrar "Página X" o el total acumulado
            pag_actual = (i // max_filas_por_pag) + 1
            c.drawString(width - 5*cm, height - 1.5*cm, f"Pág. {pag_actual} - Total: {len(alumnos_total)}")

            # --- 2. PREPARAR DATOS DE LA TABLA PARA ESTE LOTE ---
            data = []
            col_widths = []
            
            # Definir cabeceras según tipo
            if tipo_reporte == 'asistencia':
                headers = ["N°", "ALUMNO"] + [str(d) for d in range(1, 33)]
                data.append(headers)
                col_widths = [1*cm, 7*cm] + [0.6*cm] * 32
                
                for idx, alu in enumerate(lote_alumnos, 1):
                    # El índice global es i + idx
                    num = i + idx
                    data.append([str(num), f"{alu.apell_paterno} {alu.apell_materno}, {alu.nombres}"] + [""]*32)

            elif tipo_reporte == 'notas':
                headers = ["N°", "ALUMNO", "NOTA 1", "NOTA 2", "NOTA 3", "PROM.", "OBSERV."]
                data.append(headers)
                col_widths = [1*cm, 9*cm, 2*cm, 2*cm, 2*cm, 1.5*cm, 6*cm]
                
                for idx, alu in enumerate(lote_alumnos, 1):
                    num = i + idx
                    data.append([str(num), f"{alu.apell_paterno} {alu.apell_materno}, {alu.nombres}"] + [""]*5)

            elif tipo_reporte == 'datos':
                headers = ["N°", "ALUMNO", "DNI", "CEL. APODERADO", "NOMBRE APODERADO", "OBSERV."]
                data.append(headers)
                col_widths = [1*cm, 7*cm, 2.5*cm, 3*cm, 7*cm, 5*cm]
                
                for idx, alu in enumerate(lote_alumnos, 1):
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
                
                for idx, alu in enumerate(lote_alumnos, 1):
                    num = i + idx
                    data.append([str(num), alu.codigo_matricula, f"{alu.apell_paterno}, {alu.apell_materno}, {alu.nombres}", alu.dni, ""])

            # --- 3. DIBUJAR LA TABLA ---
            table = Table(data, colWidths=col_widths)
            
            # Estilos (igual que antes)
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

            # Dibujamos en posición fija porque cada "lote" empieza en una hoja nueva limpia
            table.wrapOn(c, width, height)
            table.drawOn(c, 1.5*cm, height - 3*cm - (len(data) * 0.6*cm)) # Ajuste dinámico de altura inicial

            # --- 4. CAMBIO DE PÁGINA ---
            # Si NO es el último lote, creamos una página nueva
            if (i + max_filas_por_pag) < len(alumnos_total):
                c.showPage()  # <--- ESTO CREA LA HOJA NUEVA

        c.save()

        try:
            if os.name == 'nt': os.startfile(filepath)
            else: os.system(f"open '{filepath}'")
        except: pass
            
        return True, f"Reporte generado: {filename}"

    def guardar_lista_personalizada(self, nombre_lista, ids_alumnos):
        """Guarda una selección de alumnos como una lista nueva"""
        if not nombre_lista or not ids_alumnos:
            return False, "Falta nombre o alumnos."

        try:
            # 1. Verificar si ya existe (opcional: podrías sobrescribir) 
            existe = self.db.query(ListaGuardada).filter(ListaGuardada.nombre == nombre_lista).first()
            if existe:
                return False, f"Ya existe una lista llamada '{nombre_lista}'."

            # 2. Crear la lista
            nueva_lista = ListaGuardada(nombre=nombre_lista)
            
            # 3. Asociar alumnos
            alumnos = self.db.query(Alumno).filter(Alumno.id.in_(ids_alumnos)).all()
            nueva_lista.alumnos = alumnos # SQLAlchemy maneja la tabla intermedia solo

            self.db.add(nueva_lista)
            self.db.commit()
            return True, "Lista guardada correctamente."
        except Exception as e:
            self.db.rollback()
            return False, f"Error al guardar: {str(e)}"

    def obtener_listas_guardadas(self):
        """Devuelve los nombres de todas las listas guardadas"""
        self.db.expire_all()
        return self.db.query(ListaGuardada).all()

    def cargar_alumnos_de_lista(self, lista_id):
        """Devuelve los objetos Alumno de una lista específica"""
        lista = self.db.query(ListaGuardada).filter(ListaGuardada.id == lista_id).first()
        if lista:
            return lista.alumnos
        return []

    def eliminar_lista(self, lista_id):
        try:
            lista = self.db.query(ListaGuardada).filter(ListaGuardada.id == lista_id).first()
            if lista:
                self.db.delete(lista)
                self.db.commit()
                return True, "Lista eliminada."
            return False, "Lista no encontrada."
        except Exception as e:
            return False, str(e)














