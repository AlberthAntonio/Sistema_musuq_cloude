import customtkinter as ctk
from tkinter import Canvas
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from sqlalchemy import func, or_
from app.database import SessionLocal
from app.models.alumno_model import Alumno
from app.models.nota_model import Nota
from app.models.sesion_model import SesionExamen
from app.services.academic_service import obtener_cursos

# --- IMPORTACIÓN DE ESTILOS ---
import app.styles.tabla_style as st

class HistorialAcademicoView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.session_db = SessionLocal()
        self.alumno_actual = None

        # Configuración Visual
        self.configure(fg_color=st.Colors.BG_MAIN)

        # --- LAYOUT PRINCIPAL ---
        # Panel Izquierdo: Buscador
        self.panel_izq = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=st.Colors.BG_PANEL)
        self.panel_izq.pack(side="left", fill="y", padx=10, pady=10)
        self.panel_izq.pack_propagate(False)

        # Panel Derecho: El Expediente (Fondo oscuro principal)
        self.panel_der = ctk.CTkFrame(self, fg_color=st.Colors.BG_PANEL) 
        self.panel_der.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(self.panel_izq, text="RÉCORD ACADÉMICO", font=st.Fonts.TITLE, text_color="white").pack(pady=(30, 20))

        # Input Buscador
        fr_input = ctk.CTkFrame(self.panel_izq, fg_color="#4D4D4D", height=40, corner_radius=14)
        fr_input.pack(fill="x", padx=15, pady=5)
        fr_input.pack_propagate(False)
        
        self.entry_busqueda = ctk.CTkEntry(fr_input, placeholder_text="Buscar apellido...", 
                                         border_width=0, fg_color="transparent", text_color="white", height=10)
        self.entry_busqueda.pack(side="left", fill="both", expand=True, padx=10)
        self.entry_busqueda.pack_propagate(False)
        self.entry_busqueda.bind("<Return>", lambda e: self.buscar_alumno())
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self.buscar_alumno())

        # Botón
        ctk.CTkButton(self.panel_izq, text="BUSCAR", fg_color="#2980b9", hover_color="#3498db", 
                      height=35, command=self.buscar_alumno).pack(fill="x", padx=25, pady=10)

        # Lista Resultados
        self.scroll_resultados = ctk.CTkScrollableFrame(self.panel_izq, fg_color="#3B3B3B")
        self.scroll_resultados.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Placeholder inicial
        self.lbl_mensaje = ctk.CTkLabel(self.panel_der, text="📂 Seleccione un alumno para ver su Récord", 
                                        font=("Roboto", 16), text_color="gray")
        self.lbl_mensaje.place(relx=0.5, rely=0.5, anchor="center")

    #DIAGNÓSTICO        

    def buscar_alumno(self):
        texto = self.entry_busqueda.get()
        # Limpiar resultados anteriores
        for w in self.scroll_resultados.winfo_children(): w.destroy()

        query = self.session_db.query(Alumno)
        if texto:
            busqueda = f"%{texto}%"
        query = query.filter(
            or_(
                Alumno.apell_paterno.ilike(busqueda),
                Alumno.apell_materno.ilike(busqueda),
                Alumno.nombres.ilike(busqueda)
            )
        )
        resultados = query.limit(20).all()

        if not resultados:
            ctk.CTkLabel(self.scroll_resultados, text="Sin resultados", text_color="gray").pack(pady=10)

        for alum in resultados:
            btn = ctk.CTkButton(self.scroll_resultados, 
                                text=f"{alum.apell_paterno} {alum.apell_materno}, {alum.nombres}", 
                                fg_color="transparent", border_width=0, text_color="silver",
                                hover_color="#404040", anchor="w", height=35,
                                command=lambda a=alum: self.cargar_expediente(a))
            btn.pack(fill="x", pady=1)

    def cargar_expediente(self, alumno):
        self.alumno_actual = alumno
        
        # Limpiar panel derecho
        for w in self.panel_der.winfo_children(): w.destroy()

        # 1. CABECERA
        self._render_cabecera(alumno)

        # 2. SISTEMA DE PESTAÑAS (Estilo Dark)
        self.tabview = ctk.CTkTabview(self.panel_der, fg_color=st.Colors.BG_MAIN, 
                                      segmented_button_fg_color="#2b2b2b",
                                      segmented_button_selected_color="#2980b9",
                                      segmented_button_unselected_color="#2b2b2b",
                                      text_color="white")
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tab_matriz = self.tabview.add("📊 Matriz de Notas")
        self.tab_grafica = self.tabview.add("📈 Evolución Comparativa")
        self.tab_riesgo = self.tabview.add("⚠️ Semáforo de Riesgo")

        self._render_matriz(alumno)
        self._render_grafica(alumno)
        self._render_riesgo(alumno)

    def _render_cabecera(self, alumno):
        frame_head = ctk.CTkFrame(self.panel_der, fg_color=st.Colors.BG_MAIN, corner_radius=10, border_width=1, border_color="white")
        frame_head.pack(fill="x", padx=10, pady=10)

        # Foto (Simulada)
        ctk.CTkLabel(frame_head, text="👤", font=("Arial", 45), text_color="gray").pack(side="left", padx=20, pady=15)

        # Datos Texto
        info = ctk.CTkFrame(frame_head, fg_color="transparent")
        info.pack(side="left", fill="y", pady=10)
        
        ctk.CTkLabel(info, text=f"{alumno.apell_paterno} {alumno.apell_materno}, {alumno.nombres}", 
                     font=("Roboto", 20, "bold"), text_color="white").pack(anchor="w")
        ctk.CTkLabel(info, text=f"Código: {alumno.codigo_matricula}  |  Grupo: {alumno.grupo}  |  Modalidad: {alumno.modalidad}", 
                     font=("Roboto", 12), text_color="gray").pack(anchor="w")

        # Ranking General
        ranking_simulado = "45 / 500" 
        
        rank_frame = ctk.CTkFrame(frame_head, fg_color="#f39c12", corner_radius=8)
        rank_frame.pack(side="right", padx=20, pady=20)
        ctk.CTkLabel(rank_frame, text="PUESTO GENERAL", font=("Arial", 10, "bold"), text_color="#2c3e50").pack(padx=15, pady=(5,0))
        ctk.CTkLabel(rank_frame, text=ranking_simulado, font=("Arial", 22, "bold"), text_color="black").pack(padx=15, pady=(0,5))

    def _render_matriz(self, alumno):
        """Tabla detallada de notas."""
        scroll = ctk.CTkScrollableFrame(self.tab_matriz, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        sesiones = self.session_db.query(SesionExamen).order_by(SesionExamen.fecha).all()
        cursos = obtener_cursos(alumno.grupo)

        # Header
        ctk.CTkLabel(scroll, text="CURSO", width=200, anchor="w", font=("Roboto", 12, "bold"), text_color="#f39c12").grid(row=0, column=0, sticky="w", padx=10)
        for i, s in enumerate(sesiones):
            ctk.CTkLabel(scroll, text=s.nombre[:4], width=50, font=("Roboto", 11, "bold"), text_color="silver").grid(row=0, column=i+1)

        # Filas
        for r, curso in enumerate(cursos):
            # Nombre del curso
            ctk.CTkLabel(scroll, text=curso, anchor="w", text_color="white", font=("Roboto", 12)).grid(row=r+1, column=0, sticky="w", pady=5, padx=10)
            
            for c, sesion in enumerate(sesiones):
                nota = self.session_db.query(Nota).filter_by(alumno_id=alumno.id, curso_nombre=curso, sesion_id=sesion.id).first()
                val = nota.valor if nota else 0
                
                # Colores estilo Dark Premium
                if val < 11:
                    bg_color = "#c0392b" # Rojo
                    txt_color = "white"
                elif val > 16:
                    bg_color = "#27ae60" # Verde
                    txt_color = "white"
                else:
                    bg_color = "#3a3a3a" # Gris oscuro (Normal)
                    txt_color = "white"
                
                # Badge de nota
                lbl = ctk.CTkLabel(scroll, text=f"{val:.0f}" if nota else "-", width=40, height=25, 
                                   fg_color=bg_color, text_color=txt_color, corner_radius=5, font=("Arial", 11, "bold"))
                lbl.grid(row=r+1, column=c+1, padx=2, pady=2)

    def _render_grafica(self, alumno):
        """Gráfico comparativo con Matplotlib (Estilo Dark)."""
        # 1. Preparar Datos (Lógica intacta)
        sesiones = self.session_db.query(SesionExamen).order_by(SesionExamen.fecha).all()
        fechas = [s.nombre[:6] for s in sesiones]
        ids_sesiones = [s.id for s in sesiones]

        if not sesiones:
            ctk.CTkLabel(self.tab_grafica, text="No hay exámenes registrados.", text_color="gray").pack(pady=20)
            return

        y_alumno = []
        y_grupo = []
        y_academia = []

        for sid in ids_sesiones:
            avg = self.session_db.query(func.avg(Nota.valor)).filter(Nota.alumno_id==alumno.id, Nota.sesion_id==sid).scalar()
            y_alumno.append(avg if avg else 0)

            subq = self.session_db.query(Nota.valor).join(Alumno).filter(Alumno.grupo==alumno.grupo, Nota.sesion_id==sid).all()
            if subq:
                vals = [x[0] for x in subq]
                y_grupo.append(sum(vals)/len(vals))
            else:
                y_grupo.append(0)

            avg_glob = self.session_db.query(func.avg(Nota.valor)).filter(Nota.sesion_id==sid).scalar()
            y_academia.append(avg_glob if avg_glob else 0)

        # 2. Dibujar Gráfico DARK MODE
        plt.close('all')
        
        # Configuración de colores oscuros para Matplotlib
        bg_color = '#2d2d2d' # Color del panel
        plot_color = '#1a1a1a' # Color del fondo del gráfico
        text_color = 'white'
        
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        fig.patch.set_facecolor(bg_color) 
        ax.set_facecolor(plot_color)

        # Líneas (Colores brillantes para contraste)
        ax.plot(fechas, y_academia, color='#e74c3c', linestyle='--', linewidth=1.5, label='Media Academia', marker='x', alpha=0.7)
        ax.plot(fechas, y_grupo, color='#95a5a6', linestyle=':', linewidth=2, label=f'Media Grupo {alumno.grupo}')
        ax.plot(fechas, y_alumno, color='#3498db', linewidth=3, label='ALUMNO', marker='o')

        # Estilizar Ejes y Textos
        ax.set_title("Evolución de Rendimiento Promedio", fontsize=10, color=text_color)
        ax.set_ylim(0, 20)
        
        ax.tick_params(axis='x', colors=text_color)
        ax.tick_params(axis='y', colors=text_color)
        
        ax.spines['bottom'].set_color(text_color)
        ax.spines['top'].set_color(text_color)
        ax.spines['left'].set_color(text_color)
        ax.spines['right'].set_color(text_color)

        ax.grid(True, linestyle='--', alpha=0.2, color="white")
        
        # Leyenda oscura
        legend = ax.legend(loc='lower right', fontsize='small', facecolor=bg_color, edgecolor="white")
        for text in legend.get_texts():
            text.set_color("white")

        # Embed en Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.tab_grafica)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)

        # Panel de Diagnóstico Lateral
        frame_diag = ctk.CTkFrame(self.tab_grafica, fg_color=st.Colors.BG_PANEL, border_width=1, border_color="gray", height=30)
        frame_diag.pack(fill="x", padx=10, pady=5)
        frame_diag.pack_propagate(False)
        
        if y_alumno and y_academia:
            ult_alum = y_alumno[-1]
            ult_acad = y_academia[-1]
            dif = ult_alum - ult_acad
            signo = "+" if dif >= 0 else ""
            color_diag = "#2ecc71" if dif >= 0 else "#e74c3c"
            
            ctk.CTkLabel(frame_diag, text="DIAGNÓSTICO:", font=("Arial", 12, "bold"), text_color="silver").pack(side="left", padx=10)
            ctk.CTkLabel(frame_diag, text=f"Rendimiento actual: {signo}{dif:.1f} ptos vs Media Academia.", 
                         text_color=color_diag, font=("Arial", 12, "bold")).pack(side="left")

    def _render_riesgo(self, alumno):
        """Lista de cursos donde el alumno está por debajo de 11."""
        scroll = ctk.CTkScrollableFrame(self.tab_riesgo, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        cursos = obtener_cursos(alumno.grupo)
        cursos_riesgo = []

        for curso in cursos:
            avg = self.session_db.query(func.avg(Nota.valor)).filter(
                Nota.alumno_id == alumno.id, Nota.curso_nombre == curso
            ).scalar()
            
            if avg and avg < 12.5: 
                cursos_riesgo.append((curso, avg))

        if not cursos_riesgo:
            ctk.CTkLabel(scroll, text="✅", font=("Arial", 60)).pack(pady=(40, 10))
            ctk.CTkLabel(scroll, text="¡Excelente! No tienes cursos en riesgo crítico.", 
                         font=("Arial", 18), text_color="#2ecc71").pack()
            return

        ctk.CTkLabel(scroll, text="⚠️ ÁREAS CRÍTICAS A REFORZAR", font=("Arial", 14, "bold"), text_color="#e74c3c").pack(pady=10)
        
        for curso, nota in cursos_riesgo:
            # Tarjeta Dark con borde rojo
            card = ctk.CTkFrame(scroll, fg_color=st.Colors.BG_PANEL, border_color="#c0392b", border_width=2, corner_radius=10)
            card.pack(fill="x", padx=20, pady=5)
            
            ctk.CTkLabel(card, text=curso, font=("Arial", 14, "bold"), text_color="white").pack(side="left", padx=20, pady=15)
            
            ctk.CTkLabel(card, text=f"Promedio: {nota:.1f}", font=("Arial", 14, "bold"), text_color="#c0392b").pack(side="right", padx=20)
            
            ctk.CTkLabel(card, text="Se recomienda tutoría", font=("Arial", 10, "italic"), text_color="gray").pack(side="right", padx=10)