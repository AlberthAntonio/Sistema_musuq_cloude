import customtkinter as ctk
from tkinter import messagebox
import threading
from app.controllers.reporte_controller import ReporteController
import app.styles.tabla_style as st

class ReporteView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.controller = ReporteController()
        
        # --- VARIABLES DE SELECCIÓN ---
        self.seleccionados = set() 
        self.filas_visuales = {}
        
        # --- VARIABLES SCROLL INFINITO ---
        self.todos_los_alumnos = []  # Guardar toda la data cruda
        self.cantidad_mostrada = 0   # Cuántos se ven actualmente
        self.lote_tamano = 20        # Cargar de 20 en 20
        self.cargando_lock = False   # Candado para no repetir cargas

        # Configuración Visual
        self.configure(fg_color=st.Colors.BG_MAIN)

        # Layout
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=3) 
        self.grid_columnconfigure(2, weight=1) 
        self.grid_rowconfigure(0, weight=1)

        # ============================================================
        # COLUMNA 1: FILTROS
        # ============================================================
        pnl_filtros = ctk.CTkFrame(self, fg_color=st.Colors.BG_PANEL, corner_radius=10)
        pnl_filtros.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")
        
        ctk.CTkLabel(pnl_filtros, text="1. FILTRAR", font=("Roboto", 16, "bold"), text_color="white").pack(pady=(20, 15))

        grupos, modalidades, turnos = self.controller.obtener_filtros_disponibles()

        def crear_filtro(titulo, valores, comando=None):
            ctk.CTkLabel(pnl_filtros, text=titulo, font=("Roboto", 12, "bold"), text_color="silver").pack(anchor="w", padx=15, pady=(10,5))
            cb = ctk.CTkComboBox(pnl_filtros, values=valores, command=comando,
                                 fg_color="#383838", text_color="white", 
                                 dropdown_fg_color="#2b2b2b", border_color="gray", border_width=1)
            cb.pack(fill="x", padx=15, pady=(0,5))
            return cb

        self.cb_grupo = crear_filtro("Grupo/Salón:", ["Todos"] + grupos)
        self.cb_modalidad = crear_filtro("Modalidad:", ["Todas"] + modalidades, self.al_cambiar_modalidad)
        self.cb_horario = crear_filtro("Turno:", ["Todos"] + turnos)

        # Botón Cargar con Threading
        self.btn_cargar = ctk.CTkButton(pnl_filtros, text="🔍 CARGAR ALUMNOS", 
                                        fg_color="#2980b9", hover_color="#3498db", 
                                        font=("Roboto", 12, "bold"), height=40,
                                        command=self.cargar_alumnos_thread)
        self.btn_cargar.pack(padx=15, pady=30, fill="x")

        # ============================================================
        # COLUMNA 2: TABLA CON SCROLL INFINITO
        # ============================================================
        pnl_tabla = ctk.CTkFrame(self, fg_color="transparent")
        pnl_tabla.grid(row=0, column=1, padx=5, pady=10, sticky="nsew")

        ctk.CTkLabel(pnl_tabla, text="2. SELECCIONE ALUMNOS", font=("Roboto", 16, "bold"), text_color="white").pack(pady=(10, 10))
        
        fr_btns = ctk.CTkFrame(pnl_tabla, fg_color="transparent")
        fr_btns.pack(fill="x", pady=5)
        
        self.btn_sel_todo = ctk.CTkButton(fr_btns, text="☑ Seleccionar Todo", width=120, 
                                          fg_color="#34495e", hover_color="#2c3e50", 
                                          command=self.seleccionar_todo)
        self.btn_sel_todo.pack(side="left", padx=0)
        
        self.btn_limpiar = ctk.CTkButton(fr_btns, text="☒ Limpiar", width=100, 
                                         fg_color="transparent", border_width=1, 
                                         text_color="silver", hover_color="#404040", 
                                         command=self.limpiar_seleccion)
        self.btn_limpiar.pack(side="left", padx=10)

        # Container Tabla
        self.container_tabla = ctk.CTkFrame(pnl_tabla, fg_color=st.Colors.BG_PANEL, corner_radius=10)
        self.container_tabla.pack(fill="both", expand=True)

        # Cabecera
        h_frame = ctk.CTkFrame(self.container_tabla, height=40, fg_color=st.Colors.TABLE_HEADER, corner_radius=5)
        h_frame.pack(fill="x", padx=5, pady=(5,0))
        
        ctk.CTkLabel(h_frame, text="✔", width=40, font=("Arial", 14, "bold"), text_color="white").pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="CÓDIGO", width=80, font=("Roboto", 11, "bold"), text_color="white").pack(side="left", padx=5)
        ctk.CTkLabel(h_frame, text="APELLIDOS Y NOMBRES", font=("Roboto", 11, "bold"), text_color="white", anchor="w").pack(side="left", padx=5, expand=True, fill="x")

        # Loader Flotante (usando place)
        self.lbl_loading = ctk.CTkLabel(self.container_tabla, text="⏳ Procesando solicitud...", 
                                       text_color="#f39c12", font=("Roboto", 14, "bold"))

        # Cuerpo Scrollable con hook de scroll
        self.scroll_tabla = ctk.CTkScrollableFrame(self.container_tabla, fg_color="transparent")
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Activar evento de scroll infinito
        self.scroll_tabla._parent_canvas.configure(yscrollcommand=self._hook_scroll)
        
        self.lbl_vacio = ctk.CTkLabel(self.scroll_tabla, text="Use los filtros para cargar datos.", text_color="gray")
        self.lbl_vacio.pack(pady=20)

        # ============================================================
        # COLUMNA 3: CONFIGURACIÓN
        # ============================================================
        pnl_config = ctk.CTkFrame(self, fg_color=st.Colors.BG_PANEL, corner_radius=10)
        pnl_config.grid(row=0, column=2, padx=(5, 10), pady=10, sticky="nsew")

        # --- FAVORITOS ---
        fr_favs = ctk.CTkFrame(pnl_config, fg_color="#34495e", corner_radius=8)
        fr_favs.pack(fill="x", padx=15, pady=20)
        
        ctk.CTkLabel(fr_favs, text="📂 LISTAS GUARDADAS", text_color="white", font=("Roboto", 12, "bold")).pack(pady=(10, 5))
        
        self.cb_listas = ctk.CTkComboBox(fr_favs, values=["-- Seleccionar --"], command=self.cargar_lista_favorita,
                                         fg_color="#2c3e50", border_width=0, button_color="#2c3e50")
        self.cb_listas.set("-- Seleccionar --")
        self.cb_listas.pack(fill="x", padx=10, pady=5)
        
        fr_btns_fav = ctk.CTkFrame(fr_favs, fg_color="transparent")
        fr_btns_fav.pack(fill="x", pady=10)
        
        ctk.CTkButton(fr_btns_fav, text="💾 Guardar Actual", width=100, height=28, 
                      fg_color="#27ae60", hover_color="#2ecc71", font=("Roboto", 11),
                      command=self.guardar_seleccion_actual).pack(side="left", padx=10, expand=True, fill="x")
        
        ctk.CTkButton(fr_btns_fav, text="🗑️", width=30, height=28, 
                      fg_color="#c0392b", hover_color="#e74c3c",
                      command=self.eliminar_lista_actual).pack(side="right", padx=10)

        # --- SEPARADOR ---
        ctk.CTkFrame(pnl_config, height=2, fg_color="gray").pack(fill="x", padx=20, pady=10)

        # --- PDF CONFIG ---
        ctk.CTkLabel(pnl_config, text="3. CONFIGURAR PDF", font=("Roboto", 16, "bold"), text_color="white").pack(pady=10)

        ctk.CTkLabel(pnl_config, text="Título del Reporte:", anchor="w", text_color="silver").pack(fill="x", padx=20, pady=(5,0))
        self.entry_titulo = ctk.CTkEntry(pnl_config, fg_color="#383838", border_width=0, text_color="white")
        self.entry_titulo.insert(0, "Lista Oficial de Clase")
        self.entry_titulo.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(pnl_config, text="Tipo de Reporte:", anchor="w", text_color="silver").pack(fill="x", padx=20, pady=(20,5))
        
        self.var_tipo = ctk.StringVar(value="simple")
        
        def crear_radio(txt, val):
            ctk.CTkRadioButton(pnl_config, text=txt, variable=self.var_tipo, value=val, 
                               text_color="white", border_color="#2980b9", fg_color="#2980b9", 
                               hover_color="#2980b9").pack(anchor="w", padx=25, pady=5)

        crear_radio("Simple (Firma)", "simple")
        crear_radio("Control de Asistencia", "asistencia")
        crear_radio("Registro de Notas", "notas")
        crear_radio("Datos de Contacto", "datos")

        self.btn_generar = ctk.CTkButton(pnl_config, text="GENERAR PDF", height=50, 
                                         fg_color="#e67e22", hover_color="#d35400", 
                                         font=("Roboto", 14, "bold"),
                                         command=self.generar_reporte_thread)
        self.btn_generar.pack(side="bottom", fill="x", padx=20, pady=20)

        self.lbl_contador = ctk.CTkLabel(pnl_config, text="0 alumnos seleccionados", 
                                         font=("Roboto", 16, "bold"), text_color="gray")
        self.lbl_contador.pack(side="bottom", pady=5)

        self.actualizar_combo_listas()

    # ============================================================
    # SCROLL INFINITO - DETECCIÓN Y RENDERIZADO
    # ============================================================
    
    def _hook_scroll(self, first, last):
        """Detecta cuando la barra baja al final para cargar más datos."""
        self.scroll_tabla._scrollbar.set(first, last)
        
        if self.cargando_lock:
            return

        # Si llegamos al 90% del scroll y hay más alumnos por mostrar
        try:
            if float(last) > 0.90 and self.cantidad_mostrada < len(self.todos_los_alumnos):
                self.cargando_lock = True
                self.after(10, self._renderizar_siguiente_lote)
        except:
            pass

    def _renderizar_siguiente_lote(self):
        """Renderiza los siguientes N alumnos."""
        inicio = self.cantidad_mostrada
        fin = inicio + self.lote_tamano
        
        lote = self.todos_los_alumnos[inicio:fin]
        
        for i, alu in enumerate(lote):
            idx_real = inicio + i
            self.crear_fila(alu, idx_real)
            
        self.cantidad_mostrada += len(lote)
        self.cargando_lock = False

    # ============================================================
    # VISUAL: FILAS
    # ============================================================
    
    def crear_fila(self, alu, index):
        bg_color = st.Colors.ROW_ODD if index % 2 == 0 else st.Colors.ROW_EVEN
        row = ctk.CTkFrame(self.scroll_tabla, fg_color=bg_color, corner_radius=5, height=35)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        # Verificar si ya estaba seleccionado
        esta_seleccionado = alu.id in self.seleccionados
        var_check = ctk.BooleanVar(value=esta_seleccionado)
        
        chk = ctk.CTkCheckBox(row, text="", width=24, variable=var_check, 
                              command=lambda: self.toggle_seleccion(alu.id, var_check))
        chk.pack(side="left", padx=(15, 5))
        
        ctk.CTkLabel(row, text=alu.codigo_matricula, width=80, text_color="silver").pack(side="left", padx=5)
        ctk.CTkLabel(row, text=f"{alu.apell_paterno} {alu.apell_materno}, {alu.nombres}", 
                     text_color="white", anchor="w").pack(side="left", padx=5, fill="x", expand=True)

        self.filas_visuales[alu.id] = {"var": var_check, "widget": row}

    def toggle_seleccion(self, id_alumno, var_check):
        if var_check.get():
            self.seleccionados.add(id_alumno)
        else:
            self.seleccionados.discard(id_alumno)
        self.actualizar_contador()

    # ============================================================
    # THREADING - CARGA DE ALUMNOS turno
    # ============================================================

    def cargar_alumnos_thread(self):
        """Inicia la carga de alumnos en un hilo separado."""
        self.limpiar_tabla_visual()
        
        # Mostrar loader
        self.lbl_loading.place(relx=0.5, rely=0.5, anchor="center")
        self.lbl_loading.lift()
        self.update_idletasks()
        
        self.btn_cargar.configure(state="disabled")
        self.lbl_vacio.pack_forget()

        grupo = self.cb_grupo.get()
        modalidad = self.cb_modalidad.get()
        horario = self.cb_horario.get()

        threading.Thread(target=self._proceso_busqueda, args=(grupo, modalidad, horario), daemon=True).start()

    def _proceso_busqueda(self, g, m, h):
        """Worker Thread - Búsqueda en BD."""
        alumnos = self.controller.buscar_alumnos(g, m, h)
        self.after(0, lambda: self._finalizar_carga(alumnos))

    def _finalizar_carga(self, alumnos):
        """Main Thread - Actualiza UI con resultados."""
        self.lbl_loading.place_forget()
        self.btn_cargar.configure(state="normal")
        
        # Guardar todos los alumnos en memoria
        self.todos_los_alumnos = alumnos
        self.cantidad_mostrada = 0
        self.cargando_lock = False
        
        if not alumnos:
            self.lbl_vacio.pack(pady=20)
            self.lbl_vacio.configure(text="No se encontraron alumnos.")
            return
        
        # Renderizar solo el primer lote
        self._renderizar_siguiente_lote()
        
        # Seleccionar todo el lote inicial
        self.seleccionar_todo()

    # ============================================================
    # THREADING - GENERACIÓN DE PDF
    # ============================================================

    def generar_reporte_thread(self):
        """Inicia la generación de PDF en un hilo separado."""
        if not self.seleccionados:
            messagebox.showwarning("Alerta", "Seleccione al menos un alumno.")
            return
        
        ids = list(self.seleccionados)
        tipo = self.var_tipo.get()
        titulo = self.entry_titulo.get()

        self.btn_generar.configure(state="disabled", text="Generando PDF...")
        
        threading.Thread(target=self._proceso_pdf, args=(ids, tipo, titulo), daemon=True).start()

    def _proceso_pdf(self, ids, tipo, titulo):
        """Worker Thread - Generación del PDF."""
        exito, msg = self.controller.generar_reporte_pdf(ids, tipo, titulo)
        self.after(0, lambda: self._finalizar_pdf(exito, msg))

    def _finalizar_pdf(self, exito, msg):
        """Main Thread - Muestra resultado."""
        self.btn_generar.configure(state="normal", text="GENERAR PDF")
        
        if not exito:
            messagebox.showerror("Error", msg)

    # ============================================================
    # LISTAS FAVORITAS
    # ============================================================

    def guardar_seleccion_actual(self):
        if not self.seleccionados:
            messagebox.showwarning("Aviso", "Selecciona alumnos primero.")
            return
        
        nombre = ctk.CTkInputDialog(text="Nombre para esta lista:", title="Guardar Lista").get_input()
        if not nombre:
            return
        
        ids = list(self.seleccionados)
        exito, msg = self.controller.guardar_lista_personalizada(nombre, ids)
        
        if exito:
            messagebox.showinfo("Éxito", msg)
            self.actualizar_combo_listas()
        else:
            messagebox.showerror("Error", msg)

    def actualizar_combo_listas(self):
        listas = self.controller.obtener_listas_guardadas()
        self.listas_map = {l.nombre: l.id for l in listas}
        valores = ["-- Seleccionar --"] + list(self.listas_map.keys())
        self.cb_listas.configure(values=valores)
        self.cb_listas.set("-- Seleccionar --")

    def cargar_lista_favorita(self, nombre_lista):
        if nombre_lista == "-- Seleccionar --":
            return
        
        lista_id = self.listas_map.get(nombre_lista)
        alumnos = self.controller.cargar_alumnos_de_lista(lista_id)
        
        # Reutilizar la lógica de carga lazy
        self._finalizar_carga(alumnos)
        
        if alumnos:
            # Seleccionar todo ya que es una lista guardada
            self.seleccionar_todo()
            self.entry_titulo.delete(0, "end")
            self.entry_titulo.insert(0, nombre_lista)
        else:
            messagebox.showinfo("Info", "Esta lista está vacía.")

    def eliminar_lista_actual(self):
        nombre = self.cb_listas.get()
        if nombre == "-- Seleccionar --":
            return
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar la lista '{nombre}'?"):
            lista_id = self.listas_map.get(nombre)
            self.controller.eliminar_lista(lista_id)
            self.actualizar_combo_listas()
            self.cb_listas.set("-- Seleccionar --")

    # ============================================================
    # FILTROS Y HELPERS
    # ============================================================

    def al_cambiar_modalidad(self, seleccion):
        sel_lower = seleccion.lower()
        if "colegio" in sel_lower or "ordinario" in sel_lower:
            self.cb_turno.set("Todos")
            self.cb_turno.configure(state="disabled")
        else:
            self.cb_turno.configure(state="normal")

    def limpiar_tabla_visual(self):
        for w in self.scroll_tabla.winfo_children():
            w.destroy()
        self.filas_visuales = {}
        self.seleccionados = set()
        self.todos_los_alumnos = []
        self.cantidad_mostrada = 0
        self.actualizar_contador()

    def seleccionar_todo(self):
        """Selecciona TODOS los alumnos (incluso los no visibles)."""
        # Selección lógica de todos
        for alu in self.todos_los_alumnos:
            self.seleccionados.add(alu.id)
        
        # Actualizar visualmente solo los renderizados turno
        for id_alu, data in self.filas_visuales.items():
            data["var"].set(True)
        
        self.actualizar_contador()

    def limpiar_seleccion(self):
        self.seleccionados.clear()
        for id_alu, data in self.filas_visuales.items():
            data["var"].set(False)
        self.actualizar_contador()

    def actualizar_contador(self, event=None):
        count = len(self.seleccionados)
        self.lbl_contador.configure(
            text=f"{count} alumnos seleccionados",
            text_color="#27ae60" if count > 0 else "gray"
        )