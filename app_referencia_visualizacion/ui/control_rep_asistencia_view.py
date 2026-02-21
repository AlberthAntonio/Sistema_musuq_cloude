import customtkinter as ctk
from tkinter import ttk
from datetime import date, timedelta
import tkinter.messagebox as messagebox
import threading  # <--- IMPORTANTE: Importamos threading
from tkcalendar import DateEntry
from app.controllers.rep_asistencia_controller import ReporteAsistenciaController

# Intentamos importar reportlab para el PDF
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# --- CONFIGURACIÓN DE COLORES Y ESTILO (DARK PREMIUM) ---
COLOR_BG_MAIN = "#1a1a1a"       # Fondo ultra oscuro
COLOR_PANEL = "#2d2d2d"         # Paneles laterales/tarjetas
COLOR_TABLE_HEADER = "#383838"  # Cabecera de tabla
COLOR_ROW_ODD = "#2d2d2d"       # Fila impar
COLOR_ROW_EVEN = "#333333"      # Fila par

# Colores de Acento
COLOR_PUNTUAL = "#00b894"
COLOR_TARDANZA = "#f39c12"
COLOR_FALTA = "#e74c3c"
COLOR_ASIST = "#0984e3"

class ReporteAsistenciaView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.controller = ReporteAsistenciaController()
        self.alumno_seleccionado_id = None
        self.datos_actuales = None 

        # --- DEFINICIÓN DE ANCHOS FIJOS PARA LA TABLA ---
        # Fecha, Día, Hora, Estado, Obs (Asegura alineación perfecta)
        self.ANCHOS_COLUMNAS = [110, 100, 100, 140, 100, 200]

        self.historial_cache = []  # Cache del historial completo
        self.registros_cargados = 0  # Cuántos se están mostrando
        self.lote_tamano = 20  # Cargar de 20 en 20
        self.cargando_mas = False  # Lock para evitar cargas múltiples

        # Configuración del Frame Principal
        self.configure(fg_color=COLOR_BG_MAIN)

        # Layout Principal: 2 Columnas
        self.grid_columnconfigure(0, weight=1) # Panel Izquierdo
        self.grid_columnconfigure(1, weight=3) # Panel Derecho
        self.grid_rowconfigure(0, weight=1)

        # ===========================================================
        #        PANEL IZQUIERDO: BUSCADOR Y PERFIL
        # ============================================================
        self.panel_izq = ctk.CTkFrame(self, fg_color=COLOR_BG_MAIN, corner_radius=0)
        self.panel_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=0)
        self.panel_izq.pack_propagate(True)

        # Título Lateral
        ctk.CTkLabel(self.panel_izq, text="ASISTENCIA \nPERSONAL", font=("Roboto", 20, "bold"), text_color="white").pack(pady=(20, 10), padx=10)

        # --- Buscador Moderno ---
        self.fr_search = ctk.CTkFrame(self.panel_izq, fg_color="transparent")
        self.fr_search.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(self.fr_search, text="Buscar Alumno", font=("Roboto", 12), text_color="gray").pack(anchor="w", pady=(0,0))

        # Input Visual (Frame redondeado + Entry transparente)
        self.search_box = ctk.CTkFrame(self.fr_search, fg_color="#383838", corner_radius=50, height=40)
        self.search_box.pack(fill="x")
        self.search_box.pack_propagate(False)

        ctk.CTkLabel(self.search_box, text="🔍", font=("Arial", 14)).pack(side="left", padx=(15, 5))
        
        self.ent_busqueda = ctk.CTkEntry(self.search_box, placeholder_text="Nombre o DNI...", 
                                         border_width=0, fg_color="transparent", text_color="white")
        self.ent_busqueda.pack(side="left", fill="both", expand=True)
        self.ent_busqueda.bind("<KeyRelease>", self.realizar_busqueda)

        # Lista de Resultados (ScrollableFrame)
        self.lista_resultados = ctk.CTkScrollableFrame(self.panel_izq, height=150, fg_color="#383838")
        self.lista_resultados.pack(pady=10, padx=10, fill="both", expand=True)

        # --- Tarjeta de Perfil (Oculta al inicio) ---
        self.card_perfil = ctk.CTkFrame(self.panel_izq, fg_color="#3a3a3a", corner_radius=10)
        self.card_perfil.pack(pady=10, padx=10, fill="x", side="bottom")

        # Icono y Nombre
        ctk.CTkLabel(self.card_perfil, text="👤", font=("Arial", 40)).pack(pady=(6,0))
        self.lbl_nombre = ctk.CTkLabel(self.card_perfil, text="--", font=("Roboto", 16, "bold"), text_color="white", wraplength=180)
        self.lbl_nombre.pack(pady=(5,0))

        # Contenedor de datos del perfil
        self.info_grid = ctk.CTkFrame(self.card_perfil, fg_color="transparent")
        self.info_grid.pack(fill="x", pady=10, padx=10)
        
        # Etiquetas (se actualizarán dinámicamente)
        self.lbl_codigo = ctk.CTkLabel(self.info_grid, text="COD: --", text_color="gray80", font=("Roboto", 11))
        self.lbl_codigo.pack()
        self.lbl_grupo = ctk.CTkLabel(self.info_grid, text="Grupo: --", text_color="#f1c40f", font=("Roboto", 12, "bold"))
        self.lbl_grupo.pack(pady=(5, 0))

        # Botón PDF (Estilo Rojo Premium)
        self.btn_pdf = ctk.CTkButton(self.panel_izq, text="📄  DESCARGAR REPORTE", 
                                     font=("Roboto", 13, "bold"),
                                     fg_color="#c0392b", hover_color="#e74c3c",
                                     height=45, corner_radius=25,
                                     command=self.generar_pdf)
        self.btn_pdf.pack(fill="x", padx=20, pady=10, side="bottom")


        # ============================================================
        #        PANEL DERECHO: DASHBOARD
        # ============================================================
        self.panel_der = ctk.CTkFrame(self, fg_color="transparent")
        self.panel_der.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=(10, 10))

        # --- Fila Superior: Filtros ---
        self.fr_top = ctk.CTkFrame(self.panel_der, fg_color="transparent")
        self.fr_top.pack(fill="x", pady=(0, 20))

        ctk.CTkLabel(self.fr_top, text="📅 Rango de Análisis:", font=("Roboto", 12, "bold"), text_color="gray").pack(side="left", padx=5)
        
        # DateEntries
        self.ent_desde = DateEntry(self.fr_top, width=12, date_pattern='dd/mm/yyyy', background='#2980b9', foreground='white', borderwidth=0)
        self.ent_desde.pack(side="left", padx=5)
        self.ent_desde.set_date(date.today() - timedelta(days=30))

        ctk.CTkLabel(self.fr_top, text="➡", text_color="gray").pack(side="left", padx=5)
        
        self.ent_hasta = DateEntry(self.fr_top, width=12, date_pattern='dd/mm/yyyy', background='#2980b9', foreground='white', borderwidth=0)
        self.ent_hasta.pack(side="left", padx=5)

        self.btn_actualizar = ctk.CTkButton(self.fr_top, text="🔄 ACTUALIZAR", width=120, fg_color="#404040", hover_color="gray30", command=self.cargar_datos_alumno)
        self.btn_actualizar.pack(side="left", padx=15)

        # --- Tarjetas de Métricas (KPIs) ---
        self.metrics_container = ctk.CTkFrame(self.panel_der, fg_color="transparent")
        self.metrics_container.pack(fill="x", pady=(0, 20))
        self.metrics_container.columnconfigure((0,1,2,3), weight=1)

        # INICIALIZAR TARJETAS EN 0 (Para que se vean al inicio)
        self.crear_tarjeta_metrica(0, "PUNTUALES", "0", "⏰", COLOR_PUNTUAL)
        self.crear_tarjeta_metrica(1, "TARDANZAS", "0", "⏳", COLOR_TARDANZA)
        self.crear_tarjeta_metrica(2, "FALTAS", "0", "❌", COLOR_FALTA)
        self.crear_tarjeta_metrica(3, "% EFECTIVIDAD", "0%", "📈", COLOR_ASIST, is_progress=True)

        # --- TABLA DE ASISTENCIA ---
        self.container_tabla = ctk.CTkFrame(self.panel_der, fg_color=COLOR_PANEL, corner_radius=10)
        self.container_tabla.pack(fill="both", expand=True)

        # 1. Cabecera (Fija)
        self.crear_cabecera_tabla()

        # 2. Cuerpo (Scrolleable)
        self.scroll_tabla = ctk.CTkScrollableFrame(self.container_tabla, fg_color="transparent")
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)

        self.scroll_tabla._parent_canvas.configure(yscrollcommand=self._hook_scroll)

        # 3. Estado Vacío (Overlay)
        self.empty_state = ctk.CTkFrame(self.scroll_tabla, fg_color="transparent")
        self.empty_state.pack(fill="both", expand=True, pady=80)
        
        ctk.CTkLabel(self.empty_state, text="📅", font=("Arial", 60)).pack(pady=10)
        ctk.CTkLabel(self.empty_state, text="Seleccione un alumno", font=("Roboto", 18, "bold"), text_color="gray").pack()
        ctk.CTkLabel(self.empty_state, text="para ver su historial de asistencia", font=("Roboto", 14), text_color="gray50").pack()

        # ===== AGREGAR LABEL DE CARGANDO MÁS =====
        self.lbl_cargando_mas = ctk.CTkLabel(
            self.scroll_tabla,
            text="⏳ Cargando más registros...",
            text_color="#3498db",
            font=("Roboto", 10, "italic")
        )

    # ============================================================
    #                 MÉTODOS VISUALES (Helpers)
    # ============================================================
    def crear_cabecera_tabla(self):
        header = ctk.CTkFrame(self.container_tabla, height=45, fg_color=COLOR_TABLE_HEADER, corner_radius=10)
        header.pack(fill="x", padx=5, pady=(5,0))
        
        cols = ["FECHA", "DÍA", "HORA", "ESTADO", "TURNO","OBSERVACIÓN"]
        
        # Crear columnas usando PACK con ancho fijo (Igual que las filas)
        for i, col in enumerate(cols):
            ancho = self.ANCHOS_COLUMNAS[i]
            lbl = ctk.CTkLabel(header, text=col, font=("Roboto", 12, "bold"), text_color="white", width=ancho)
            lbl.pack(side="left", padx=2)

    def crear_tarjeta_metrica(self, col_index, titulo, valor, icono, color, is_progress=False):
        # Card Container
        card = ctk.CTkFrame(self.metrics_container, fg_color=COLOR_PANEL, corner_radius=10)
        card.grid(row=0, column=col_index, sticky="ew", padx=5)
        
        # Contenido
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", padx=20, pady=15)

        ctk.CTkLabel(content, text=titulo, font=("Roboto", 11, "bold"), text_color=color).pack(anchor="w")
        ctk.CTkLabel(content, text=valor, font=("Roboto", 28, "bold"), text_color="white").pack(anchor="w", pady=(0, 5))
         # Icono fondo
        ctk.CTkLabel(card, text=icono, font=("Arial", 40), text_color="#535353").place(relx=0.85, rely=0.5, anchor="center")


        if is_progress:
            try:
                # Convertir "85%" a 0.85
                val_float = float(valor.replace("%","")) / 100
            except: 
                val_float = 0
            prog = ctk.CTkProgressBar(content, width=100, height=6, progress_color=color, fg_color="#404040")
            prog.pack(anchor="w", pady=5)
            prog.set(val_float)
        else:
            ctk.CTkFrame(content, height=2, width=30, fg_color=color).pack(anchor="w", pady=5)

    def _hook_scroll(self, first, last):
        """Hook del scrollbar para detectar cuando llega al final"""
        # 1. Actualizar scrollbar
        try:
            self.scroll_tabla._scrollbar.set(first, last)
        except:
            pass
        
        # 2. Validaciones
        if self.cargando_mas:
            return
        if not hasattr(self, 'historial_cache'):
            return
        if not self.historial_cache:
            return
        
        # 3. Detectar si llegamos al 90%
        try:
            posicion_actual = float(last)
            
            if (posicion_actual >= 0.90 and 
                self.registros_cargados < len(self.historial_cache)):
                
                self.cargando_mas = True
                
                # Mostrar indicador
                try:
                    if self.lbl_cargando_mas.winfo_exists():
                        self.lbl_cargando_mas.pack(pady=10)
                except:
                    pass
                
                # Cargar siguiente lote
                self.after(200, self._renderizar_siguiente_lote)
        
        except Exception as e:
            if "bad window path" not in str(e):
                print(f"Error en _hook_scroll: {e}")
            self.cargando_mas = False


    # ============================================================
    #                 LÓGICA DEL CONTROLADOR (CON HILOS)
    # ============================================================
    def realizar_busqueda(self, event=None):
        """Inicia la búsqueda en un hilo separado"""
        texto = self.ent_busqueda.get()
        # Creamos el hilo y lo iniciamos
        threading.Thread(target=self._busqueda_en_hilo, args=(texto,), daemon=True).start()

    def _busqueda_en_hilo(self, texto):
        """Función que corre en segundo plano para la búsqueda"""
        resultados = self.controller.buscar_alumnos(texto)
        # Volvemos al hilo principal para actualizar la UI
        self.after(0, lambda: self._actualizar_lista_busqueda(resultados))

    def _actualizar_lista_busqueda(self, resultados):
        """Actualiza la UI con los resultados de búsqueda (Hilo Principal)"""
        # Limpiar lista anterior
        for widget in self.lista_resultados.winfo_children():
            widget.destroy()

        if not resultados:
            ctk.CTkLabel(self.lista_resultados, text="Sin resultados", text_color="gray").pack(pady=10)
            return

        for alu in resultados:
            # Botón estilizado como fila de lista
            btn = ctk.CTkButton(self.lista_resultados, 
                                text=f"{alu.apell_paterno} {alu.nombres}\n({alu.dni})", 
                                fg_color="transparent", 
                                hover_color="#404040",
                                border_width=0, 
                                text_color=("gray80"), anchor="w", height=40,
                                command=lambda id=alu.id: self.seleccionar_alumno(id))
            btn.pack(fill="x", pady=2)
            # Separador sutil
            ctk.CTkFrame(self.lista_resultados, height=1, fg_color="#404040").pack(fill="x")

    def seleccionar_alumno(self, alumno_id):
        self.alumno_seleccionado_id = alumno_id
        self.cargar_datos_alumno()

    def cargar_datos_alumno(self):
        """Inicia la carga de datos del alumno en un hilo separado"""
        if not self.alumno_seleccionado_id: return
        
        # Bloquear botón momentáneamente para evitar doble clic
        self.btn_actualizar.configure(state="disabled", text="Cargando...")

        f_ini = self.ent_desde.get()
        f_fin = self.ent_hasta.get()

        # Iniciamos el hilo
        threading.Thread(target=self._cargar_datos_en_hilo, args=(self.alumno_seleccionado_id, f_ini, f_fin), daemon=True).start()

    def _cargar_datos_en_hilo(self, id_alumno, f_ini, f_fin):
        """Función en segundo plano que consulta a la BD"""
        exito, msg, datos = self.controller.obtener_perfil_completo(id_alumno, f_ini, f_fin)
        # Regresar al hilo principal
        self.after(0, lambda: self._actualizar_dashboard(exito, msg, datos))

    def _actualizar_dashboard(self, exito, msg, datos):
        """Actualiza todo el panel derecho con los datos (Hilo Principal)"""
        self.btn_actualizar.configure(state="normal", text="🔄 ACTUALIZAR")
        
        if not exito:
            messagebox.showerror("Error", msg)
            return
        
        self.scroll_tabla._parent_canvas.yview_moveto(0.0)
        self.lista_resultados._parent_canvas.yview_moveto(0.0)
        
        self.datos_actuales = datos
        
        # 1. Actualizar Perfil Visual
        alu = datos["alumno"]
        self.lbl_nombre.configure(text=f"{alu.nombres}\n{alu.apell_paterno} {alu.apell_materno}")
        self.lbl_codigo.configure(text=f"DNI: {alu.dni} | COD: {alu.codigo_matricula}")
        self.lbl_grupo.configure(text=f"Grupo: {alu.grupo or '-'} | Horario: {alu.horario or '-'}")
        
        # 2. Actualizar KPIs
        stats = datos["stats"]
        
        for widget in self.metrics_container.winfo_children():
            widget.destroy()
        
        self.crear_tarjeta_metrica(0, "PUNTUALES", str(stats["puntual"]), "⏰", COLOR_PUNTUAL)
        self.crear_tarjeta_metrica(1, "TARDANZAS", str(stats["tardanza"]), "⏳", COLOR_TARDANZA)
        self.crear_tarjeta_metrica(2, "FALTAS", str(stats["falta"]), "❌", COLOR_FALTA)
        self.crear_tarjeta_metrica(3, "% EFECTIVIDAD", f"{stats['efectividad']}%", "📈", COLOR_ASIST, is_progress=True)
        
        # ===== 3. INICIALIZAR TABLA CON SCROLL INFINITO =====
        # Limpiar tabla
        for widget in self.scroll_tabla.winfo_children():
            widget.destroy()
        
        # Resetear variables
        self.historial_cache = datos["historial"]
        self.registros_cargados = 0
        self.cargando_mas = False
        
        # Validar si hay datos
        if not datos["historial"]:
            self.empty_state.pack(fill="both", expand=True, pady=80)
            return
        
        # Cargar primer lote
        self._renderizar_siguiente_lote()
        # ====================================================

    def _renderizar_siguiente_lote(self):
        """Renderiza el siguiente grupo de N registros"""
        # Calcular rango
        inicio = self.registros_cargados
        fin = inicio + self.lote_tamano
        
        # Extraer lote
        lote = self.historial_cache[inicio:fin]
        
        # Renderizar cada registro
        for item in lote:
            # Calcular índice global para colores alternados
            index_global = self.registros_cargados
            self._crear_fila_optimizada(item, index_global)
            self.registros_cargados += 1
        
        # Ocultar indicador
        try:
            self.lbl_cargando_mas.pack_forget()
        except:
            pass
        
        # Liberar lock
        self.cargando_mas = False
        
        # Debug
        print(f"📊 Historial: {self.registros_cargados}/{len(self.historial_cache)}")

    def _crear_fila_optimizada(self, fila, index):
        """Crea una fila optimizada para scroll infinito"""
        # Determinar color de fila (Zebra)
        bg_row = COLOR_ROW_ODD if index % 2 == 0 else COLOR_ROW_EVEN
        
        # --- LÓGICA DE ESTADOS E ICONOS ---
        estado = fila["estado"]
        color_st = "white"
        icon = "❓"
        
        if estado == "PUNTUAL":
            color_st = COLOR_PUNTUAL
            icon = "✅"
        elif estado == "TARDANZA":
            color_st = COLOR_TARDANZA
            icon = "⏳"
        elif estado in ["INASISTENCIA"]:
            color_st = COLOR_FALTA
            icon = "❌"
        elif estado == "JUSTIFICADO":
            color_st = COLOR_ASIST
            icon = "📄"
        
        # Crear Fila
        row = ctk.CTkFrame(self.scroll_tabla, fg_color=bg_row, corner_radius=5, height=40)
        row.pack(fill="x", pady=2)
        
        # --- CELDAS USANDO ANCHO FIJO ---
        # 1. Fecha
        ctk.CTkLabel(row, text=fila["fecha"], text_color="white", 
                    font=("Roboto Mono", 12, "bold"), 
                    width=self.ANCHOS_COLUMNAS[0]).pack(side="left", padx=2)
        
        # 2. Día
        ctk.CTkLabel(row, text=fila["dia"], text_color="gray", 
                    width=self.ANCHOS_COLUMNAS[1]).pack(side="left", padx=2)
        
        # 3. Hora
        ctk.CTkLabel(row, text=fila["hora"], text_color="white", 
                    font=("Roboto Mono", 12, "bold"), 
                    width=self.ANCHOS_COLUMNAS[2]).pack(side="left", padx=2)
        
        # 4. Estado (Frame contenedor)
        f_st = ctk.CTkFrame(row, fg_color="transparent", 
                            width=self.ANCHOS_COLUMNAS[3], height=30)
        f_st.pack(side="left", padx=2)
        f_st.pack_propagate(False)
        
        ctk.CTkLabel(f_st, text=icon, font=("Arial", 14)).pack(side="left", padx=(10, 5))
        ctk.CTkLabel(f_st, text=estado, text_color=color_st, 
                    font=("Roboto", 11, "bold")).pack(side="left")
        
        # 5. Turno
        turno_txt = fila["turno"] or "-"
        ctk.CTkLabel(row, text=turno_txt, text_color="gray", anchor="w",
                    width=self.ANCHOS_COLUMNAS[4]).pack(side="left", padx=2)
        
        # 6. Observación
        obs_txt = fila["obs"]
        if len(obs_txt) > 35:
            obs_txt = obs_txt[:32] + "..."
        ctk.CTkLabel(row, text=obs_txt, text_color="gray", anchor="w",
                    width=self.ANCHOS_COLUMNAS[5]).pack(side="left", padx=2)




    # ============================================================
    #                 GENERACIÓN DE PDF (Sin cambios)
    # ============================================================
    def generar_pdf(self):
        if not self.datos_actuales:
            messagebox.showwarning("Atención", "Primero seleccione un alumno y genere los datos.")
            return

        if not REPORTLAB_AVAILABLE:
            self._generar_reporte_texto()
            return

        try:
            alu = self.datos_actuales["alumno"]
            filename = f"Kardex_{alu.apell_paterno}_{date.today()}.pdf"
            
            c = canvas.Canvas(filename, pagesize=A4)
            width, height = A4
            
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 50, f"REPORTE DE ASISTENCIA: {alu.apell_paterno} {alu.nombres}")
            
            c.setFont("Helvetica", 10)
            c.drawString(50, height - 70, f"Código: {alu.codigo_matricula}   |   DNI: {alu.dni}")
            c.drawString(50, height - 85, f"Periodo: {self.ent_desde.get()} al {self.ent_hasta.get()}")
            
            stats = self.datos_actuales["stats"]
            resumen = f"Puntuales: {stats['puntual']}   |   Tardanzas: {stats['tardanza']}   |   Faltas: {stats['falta']}   |   Efectividad: {stats['efectividad']}%"
            c.setFont("Helvetica-Bold", 10)
            c.drawString(50, height - 110, resumen)
            
            c.line(50, height - 120, width - 50, height - 120)
            
            y = height - 140
            c.setFont("Helvetica-Bold", 9)
            c.drawString(50, y, "FECHA")
            c.drawString(120, y, "HORA")
            c.drawString(180, y, "ESTADO")
            c.drawString(300, y, "OBSERVACIÓN")
            y -= 20
            
            c.setFont("Helvetica", 9)
            for fila in self.datos_actuales["historial"]:
                if y < 50:
                    c.showPage()
                    y = height - 50
                
                c.drawString(50, y, fila["fecha"])
                c.drawString(120, y, fila["hora"])
                c.drawString(180, y, fila["estado"])
                c.drawString(300, y, fila["obs"][:40])
                y -= 15
                
            c.save()
            messagebox.showinfo("PDF Generado", f"Se ha guardado el reporte exitosamente:\n{filename}")
            
            import os
            os.startfile(filename)

        except Exception as e:
            messagebox.showerror("Error PDF", f"Hubo un error al crear el PDF: {e}")

    def _generar_reporte_texto(self):
        try:
            alu = self.datos_actuales["alumno"]
            filename = f"Kardex_{alu.apell_paterno}_{date.today()}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"REPORTE DE ASISTENCIA: {alu.apell_paterno} {alu.nombres}\n")
                f.write("="*50 + "\n")
                for fila in self.datos_actuales["historial"]:
                    f.write(f"{fila['fecha']} | {fila['hora']} | {fila['estado']} | {fila['obs']}\n")
            
            messagebox.showinfo("TXT Generado", f"Se generó un archivo de texto simple:\n{filename}")
            import os
            os.startfile(filename)
        except Exception as e:
            messagebox.showerror("Error TXT", f"Error: {e}")