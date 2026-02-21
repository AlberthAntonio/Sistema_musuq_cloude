import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from sqlalchemy import func, desc
from app.database import SessionLocal
from app.models.alumno_model import Alumno
from app.models.nota_model import Nota
from app.models.sesion_model import SesionExamen
from app.models.asistencia_model import Asistencia
from app.services.academic_service import obtener_cursos

# --- IMPORTACIÓN DE ESTILOS ---
import app.styles.tabla_style as st

class BoletaNotasView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.session_db = SessionLocal()
        self.alumno_seleccionado = None
        
        # Variable para controlar el widget activo
        self.scroll_activo = None

        # Configuración Visual General
        self.configure(fg_color=st.Colors.BG_MAIN)

        # ================= LAYOUT PRINCIPAL =================
        # Panel Izquierdo: Controles (Estilo Dark Panel)
        self.panel_izq = ctk.CTkScrollableFrame(self, width=320, corner_radius=0, fg_color=st.Colors.BG_PANEL)
        self.panel_izq.pack(side="left", fill="y", padx=(20,0), pady=20)

        # Panel Derecho: Escritorio (Fondo Oscuro para resaltar el papel)
        self.panel_der = ctk.CTkFrame(self, fg_color=st.Colors.BG_PANEL) 
        self.panel_der.pack(side="right", fill="both", expand=True, padx=(10, 20), pady=20)

        self._setup_controles()
        
        # Área de Papel (Scrollable transparente)
        self.scroll_preview = ctk.CTkScrollableFrame(self.panel_der, fg_color="transparent")
        self.scroll_preview.pack(fill="both", expand=True, padx=20, pady=20)
        
        # La "Hoja de Papel" blanca
        self.hoja_papel = ctk.CTkFrame(self.scroll_preview, fg_color="white", width=650, height=850, corner_radius=0)
        self.hoja_papel.pack(pady=20, padx=10)

        # Configurar scroll independiente para cada área
        self._setup_independent_scroll()

    def _setup_controles(self):
        """Configura el menú lateral."""
        ctk.CTkLabel(self.panel_izq, text="GENERADOR DE BOLETAS", 
                     font=("Roboto", 20, "bold"), text_color="white").pack(pady=(30, 20))

        # Filtro Grupo
        self.frame_filtros = ctk.CTkFrame(self.panel_izq, fg_color="transparent")
        self.frame_filtros.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(self.frame_filtros, text="Grupo:", text_color="silver").pack(side="left", padx=5)
        self.combo_grupo = ctk.CTkComboBox(self.frame_filtros, values=["A", "B", "C", "D"], width=80)
        self.combo_grupo.set("A")
        self.combo_grupo.pack(side="left", padx=5)

        # Buscador
        ctk.CTkLabel(self.panel_izq, text="Buscar Alumno:", anchor="w", text_color="gray", font=("Roboto", 12, "bold")).pack(fill="x", padx=20, pady=(10, 5))
        
        self.fr_search = ctk.CTkFrame(self.panel_izq, fg_color="#383838", height=40, corner_radius=20)
        self.fr_search.pack(fill="x", padx=15)
        self.fr_search.pack_propagate(False)
        
        ctk.CTkLabel(self.fr_search, text="🔍", text_color="gray").pack(side="left", padx=(15,5))
        self.entry_buscar = ctk.CTkEntry(self.fr_search, placeholder_text="Apellido o Nombre...", 
                                         border_width=0, fg_color="transparent", text_color="white")
        self.entry_buscar.pack(side="left", fill="both", expand=True)
        self.entry_buscar.bind("<Return>", lambda e: self.buscar_alumno())
        self.entry_buscar.bind("<KeyRelease>", lambda e: self.buscar_alumno())
        
        # Botón buscar
        ctk.CTkButton(self.panel_izq, text="BUSCAR AHORA", fg_color="#34495e", hover_color="#2c3e50", command=self.buscar_alumno).pack(fill="x", padx=15, pady=10)

        # Lista de Resultados
        ctk.CTkLabel(self.panel_izq, text="Resultados:", anchor="w", text_color="gray", font=("Roboto", 12, "bold")).pack(fill="x", padx=20, pady=(5, 5))
        self.scroll_resultados = ctk.CTkScrollableFrame(self.panel_izq, height=200, fg_color="#222222")
        self.scroll_resultados.pack(fill="x", padx=15, pady=5)

        # Opciones de Reporte
        ctk.CTkLabel(self.panel_izq, text="Configuración:", anchor="w", font=("Roboto", 12, "bold"), text_color="#f39c12").pack(fill="x", padx=20, pady=(10, 10))
        
        self.check_asistencia = ctk.CTkCheckBox(self.panel_izq, text="Incluir Asistencia", onvalue=True, offvalue=False, text_color="silver")
        self.check_asistencia.select()
        self.check_asistencia.pack(anchor="w", padx=25, pady=5)

        self.check_ranking = ctk.CTkCheckBox(self.panel_izq, text="Incluir Ranking", onvalue=True, offvalue=False, text_color="silver")
        self.check_ranking.select()
        self.check_ranking.pack(anchor="w", padx=25, pady=5)

        # Botones de Acción
        ctk.CTkButton(self.panel_izq, text="🔄 ACTUALIZAR VISTA", fg_color="#e67e22", hover_color="#d35400",
                      font=("Roboto", 12, "bold"), height=40,
                      command=self.generar_vista_previa).pack(fill="x", padx=15, pady=(30, 10))
        
        self.btn_export = ctk.CTkButton(self.panel_izq, text="📄 EXPORTAR PDF", fg_color="#c0392b", state="disabled")
        self.btn_export.pack(fill="x", padx=15, pady=5)
        
        self.btn_print = ctk.CTkButton(self.panel_izq, text="🖨️ IMPRIMIR", fg_color="#27ae60", state="disabled")
        self.btn_print.pack(fill="x", padx=15, pady=5)

    def _setup_independent_scroll(self):
        """Configura scroll independiente para cada área scrollable."""
        # Lista de widgets scrollables con sus velocidades
        scrollables = [
            (self.panel_izq, 4),
            (self.scroll_resultados, 2),
            (self.scroll_preview, 6)
        ]
        
        for widget, speed in scrollables:
            self._bind_scroll_to_widget(widget, speed)

    def _bind_scroll_to_widget(self, widget, speed=4):
        """
        Vincula el scroll del mouse a un widget específico.
        Solo funciona cuando el mouse está sobre ese widget.
        """
        def on_mousewheel(event):
            try:
                # Calcular delta según la velocidad
                delta = int(-event.delta / 120 * speed)
                widget._parent_canvas.yview_scroll(delta, "units")
            except:
                pass
        
        def on_enter(event):
            # Cuando el mouse entra al widget, activar su scroll
            widget.bind("<MouseWheel>", on_mousewheel)
        
        def on_leave(event):
            # Cuando el mouse sale del widget, desactivar su scroll
            widget.unbind("<MouseWheel>")
        
        # Vincular eventos de entrada/salida
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def buscar_alumno(self):
        """Busca alumnos y crea botones para seleccionarlos."""
        texto = self.entry_buscar.get()
        grupo = self.combo_grupo.get()

        # Limpiar
        for w in self.scroll_resultados.winfo_children(): 
            w.destroy()

        query = self.session_db.query(Alumno).filter(Alumno.grupo == grupo)
        if texto:
            query = query.filter(Alumno.apell_paterno.ilike(f"%{texto}%"))
        
        resultados = query.limit(20).all()

        if not resultados:
            ctk.CTkLabel(self.scroll_resultados, text="No encontrado", text_color="gray").pack(pady=10)
            return

        for alum in resultados:
            btn = ctk.CTkButton(self.scroll_resultados, 
                                text=f"{alum.apell_paterno} {alum.nombres}", 
                                fg_color="transparent", 
                                hover_color="#404040",
                                anchor="w",
                                text_color="silver",
                                height=30,
                                command=lambda a=alum: self.seleccionar_alumno(a))
            btn.pack(fill="x", pady=1)

    def seleccionar_alumno(self, alumno):
        self.alumno_seleccionado = alumno
        self.generar_vista_previa()
        # Habilitar botones al seleccionar
        self.btn_export.configure(state="normal")
        self.btn_print.configure(state="normal")

    def obtener_ranking(self, alumno):
        """Calcula el puesto del alumno en su grupo basado en promedio simple."""
        companeros = self.session_db.query(Alumno).filter(Alumno.grupo == alumno.grupo).all()
        promedios = []
        
        for comp in companeros:
            notas = self.session_db.query(Nota).filter(Nota.alumno_id == comp.id).all()
            if notas:
                prom = sum([n.valor for n in notas]) / len(notas)
                promedios.append((comp.id, prom))
            else:
                promedios.append((comp.id, 0))
        
        promedios.sort(key=lambda x: x[1], reverse=True)
        
        puesto = 0
        mi_promedio = 0
        for idx, (aid, prom) in enumerate(promedios):
            if aid == alumno.id:
                puesto = idx + 1
                mi_promedio = prom
                break
        
        return puesto, len(companeros), mi_promedio

    def generar_vista_previa(self):
        if not self.alumno_seleccionado: 
            return

        # Limpiar Hoja
        for w in self.hoja_papel.winfo_children(): 
            w.destroy()

        alum = self.alumno_seleccionado
        cursos = obtener_cursos(alum.grupo)
        
        # --- 1. ENCABEZADO (ESTILO PAPEL) ---
        header_frame = ctk.CTkFrame(self.hoja_papel, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=30)

        # Logo Simulado
        logo = ctk.CTkFrame(header_frame, width=70, height=70, fg_color="#2c3e50")
        logo.pack(side="left")
        logo.pack_propagate(False)
        
        datos_cole = ctk.CTkFrame(header_frame, fg_color="transparent")
        datos_cole.pack(side="left", padx=20)
        ctk.CTkLabel(datos_cole, text="COLEGIO PRIVADO", font=("Times New Roman", 20, "bold"), text_color="black").pack(anchor="w")
        ctk.CTkLabel(datos_cole, text="\"NOMBRE DE TU COLEGIO\"", font=("Times New Roman", 16), text_color="black").pack(anchor="w")
        ctk.CTkLabel(datos_cole, text="INFORME DE PROGRESO ACADÉMICO 2025", font=("Arial", 11, "bold"), text_color="gray").pack(anchor="w", pady=(5,0))

        # Foto Simulada
        foto = ctk.CTkFrame(header_frame, width=70, height=80, fg_color="#bdc3c7")
        foto.pack(side="right")
        foto.pack_propagate(False)

        # --- 2. DATOS DEL ALUMNO ---
        # Separador
        ctk.CTkFrame(self.hoja_papel, height=2, fg_color="#2c3e50").pack(fill="x", padx=40, pady=(0, 20))

        info_frame = ctk.CTkFrame(self.hoja_papel, fg_color="#f8f9fa", corner_radius=0)
        info_frame.pack(fill="x", padx=40, pady=0)

        puesto, total_alum, promedio_gral = self.obtener_ranking(alum)

        datos = [
            ("Estudiante:", f"{alum.apell_paterno} {alum.apell_materno}, {alum.nombres}"),
            ("Código:", alum.codigo_matricula),
            ("Grado/Grupo:", f"Secundaria - {alum.grupo}"),
            ("Tutor:", "Prof. Encargado"), 
            ("Promedio Gral:", f"{promedio_gral:.2f}"),
            ("Orden de Mérito:", f"{puesto}° de {total_alum}" if self.check_ranking.get() else "---")
        ]

        for i, (k, v) in enumerate(datos):
            row = i // 2
            col = (i % 2) * 2
            ctk.CTkLabel(info_frame, text=k, font=("Arial", 11, "bold"), text_color="#2c3e50").grid(row=row, column=col, sticky="w", padx=10, pady=5)
            ctk.CTkLabel(info_frame, text=v, font=("Arial", 11), text_color="black").grid(row=row, column=col+1, sticky="w", padx=0, pady=5)

        # --- 3. TABLA DE NOTAS ---
        sesiones = self.session_db.query(SesionExamen).order_by(SesionExamen.fecha).all()
        
        # Contenedor Tabla con borde
        tabla_container = ctk.CTkFrame(self.hoja_papel, fg_color="white", border_width=1, border_color="black", corner_radius=0)
        tabla_container.pack(fill="x", padx=40, pady=20)

        # Header Tabla
        header_bg = "#ecf0f1"
        h_frame = ctk.CTkFrame(tabla_container, fg_color=header_bg, corner_radius=0, height=30)
        h_frame.pack(fill="x")
        h_frame.pack_propagate(False)
        
        ctk.CTkLabel(h_frame, text="CURSO / ÁREA", font=("Arial", 10, "bold"), width=150, anchor="w", text_color="black").pack(side="left", padx=5)
        
        right_header = ctk.CTkFrame(h_frame, fg_color="transparent")
        right_header.pack(side="right", padx=5)
        
        for sesion in sesiones:
            nom_corto = sesion.nombre[:6] + ".." if len(sesion.nombre) > 6 else sesion.nombre
            ctk.CTkLabel(right_header, text=nom_corto, font=("Arial", 9, "bold"), width=50, text_color="black").pack(side="left", padx=2)
        ctk.CTkLabel(right_header, text="PROM", font=("Arial", 10, "bold"), width=50, text_color="black").pack(side="left", padx=5)

        # Filas Tabla
        for curso in cursos:
            f_row = ctk.CTkFrame(tabla_container, fg_color="transparent", height=25)
            f_row.pack(fill="x", pady=1)
            f_row.pack_propagate(False)
            
            ctk.CTkLabel(f_row, text=curso, font=("Arial", 10), anchor="w", text_color="black", width=150).pack(side="left", padx=5)
            
            # Contenedor notas derecha
            f_notas = ctk.CTkFrame(f_row, fg_color="transparent")
            f_notas.pack(side="right", padx=5)

            suma_curso = 0
            count_curso = 0
            
            for sesion in sesiones:
                nota = self.session_db.query(Nota).filter_by(alumno_id=alum.id, curso_nombre=curso, sesion_id=sesion.id).first()
                val = nota.valor if nota else 0
                
                if nota:
                    suma_curso += val
                    count_curso += 1
                
                texto_nota = f"{val:.1f}" if nota else "-"
                color_nota = "#c0392b" if val < 11 else "black"

                ctk.CTkLabel(f_notas, text=texto_nota, font=("Arial", 10), text_color=color_nota, width=50).pack(side="left", padx=2)
            
            prom = suma_curso / count_curso if count_curso > 0 else 0
            color_prom = "#c0392b" if prom < 11 else "#2980b9"
            ctk.CTkLabel(f_notas, text=f"{prom:.1f}", font=("Arial", 10, "bold"), text_color=color_prom, width=50).pack(side="left", padx=5)
            
            # Línea separadora
            ctk.CTkFrame(tabla_container, height=1, fg_color="#bdc3c7").pack(fill="x")

        # --- 4. RESUMEN ASISTENCIA ---
        if self.check_asistencia.get():
            asistencias = self.session_db.query(Asistencia).filter(Asistencia.alumno_id == alum.id).all()
            total_asist = len(asistencias)
            puntuales = len([a for a in asistencias if a.estado == "Puntual"])
            tardanzas = len([a for a in asistencias if a.estado == "Tarde"])
            faltas = len([a for a in asistencias if a.estado == "Falta"])

            asist_frame = ctk.CTkFrame(self.hoja_papel, fg_color="#f4f6f7", border_width=1, border_color="#ccc", corner_radius=5)
            asist_frame.pack(fill="x", padx=40, pady=15)
            
            ctk.CTkLabel(asist_frame, text="CONTROL DE ASISTENCIA", font=("Arial", 10, "bold"), text_color="black").pack(anchor="w", padx=10, pady=(5,0))
            resumen = f"Total Días: {total_asist}   |   Puntual: {puntuales}   |   Tardanzas: {tardanzas}   |   Faltas: {faltas}"
            ctk.CTkLabel(asist_frame, text=resumen, font=("Arial", 10), text_color="#555").pack(anchor="w", padx=10, pady=(0,5))

        # --- 5. FIRMAS ---
        footer_frame = ctk.CTkFrame(self.hoja_papel, fg_color="transparent")
        footer_frame.pack(fill="x", padx=40, pady=(60, 20))

        # Espacios de firma
        ctk.CTkLabel(footer_frame, text="_________________________", text_color="black").pack(side="left", padx=20)
        ctk.CTkLabel(footer_frame, text="_________________________", text_color="black").pack(side="right", padx=20)
        
        sub_footer = ctk.CTkFrame(self.hoja_papel, fg_color="transparent")
        sub_footer.pack(fill="x", padx=40)
        ctk.CTkLabel(sub_footer, text="Firma del Tutor", font=("Arial", 9), text_color="black").pack(side="left", padx=50)
        ctk.CTkLabel(sub_footer, text="Dirección Académica", font=("Arial", 9), text_color="black").pack(side="right", padx=40)

        # Mensaje automático
        mensaje = "¡Felicitaciones! Sigue así." if promedio_gral > 16 else ("Se requiere mayor compromiso y estudio." if promedio_gral < 11 else "Desempeño Regular.")
        color_msg = "#27ae60" if promedio_gral > 16 else ("#c0392b" if promedio_gral < 11 else "#e67e22")
        
        ctk.CTkLabel(self.hoja_papel, text=f"OBSERVACIÓN: {mensaje}", font=("Arial", 10, "italic", "bold"), text_color=color_msg).pack(pady=20)