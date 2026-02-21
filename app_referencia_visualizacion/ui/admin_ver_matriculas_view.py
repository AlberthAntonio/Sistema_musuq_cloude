import customtkinter as ctk
from tkinter import messagebox
import threading # <--- HILOS
from app.controllers.alumno_controller import AlumnoController
from app.ui.editar_alumno_window import EditarAlumnoWindow

# --- IMPORTACIÓN DE ESTILOS ---
import app.styles.tabla_style as st

class VerMatriculasView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.controller = AlumnoController()
        
        # --- VARIABLES PARA SCROLL INFINITO Y HILOS ---
        self.lista_alumnos_cache = []    # Todos los datos de la BD (Memoria)
        self.resultados_filtrados = []   # Datos después de aplicar filtros (Memoria)
        self.cantidad_cargada = 0        # Cuántos se ven en pantalla
        self.lote_tamano = 40            # Filas por tanda
        self.cargando_lock = False       # Evitar colisiones
        
        # Variables de selección visual
        self.fila_seleccionada = None      
        self.datos_seleccionados = None    

        # Configuración Visual
        self.configure(fg_color=st.Colors.BG_MAIN)

        # Definición de Anchos (Código, DNI, Alumno, Modality, Grp, Celular)
        self.ANCHOS = [80, 90, 250, 120, 50, 100]

        # Layout: 2 Columnas
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=0) 
        self.grid_rowconfigure(0, weight=1)

        # === SECCIÓN IZQUIERDA: FILTROS Y TABLA ===
        panel_izq = ctk.CTkFrame(self, fg_color="transparent")
        panel_izq.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.lbl_titulo = ctk.CTkLabel(panel_izq, text="VISUALIZACIÓN DE MATRICULAS",
                                     font=st.Fonts.TITLE, text_color="white")
        self.lbl_titulo.pack(pady=(15, 15))

        # --- 1. Barra de Filtros ---
        fr_filtros = ctk.CTkFrame(panel_izq, height=50, fg_color=st.Colors.BG_PANEL, corner_radius=10)
        fr_filtros.pack(fill="x", pady=(0, 10))

        # Buscador
        ctk.CTkLabel(fr_filtros, text="🔍", text_color="gray").pack(side="left", padx=(15, 5))
        self.entry_buscar = ctk.CTkEntry(fr_filtros, placeholder_text="Buscar por DNI, Nombre...", 
                                       width=200, border_width=0, fg_color="#383838", text_color="white")
        self.entry_buscar.pack(side="left", padx=5, pady=10)
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_tabla) # Filtra en memoria (rápido)

        # Separador vertical visual
        ctk.CTkFrame(fr_filtros, width=2, height=20, fg_color="#505050").pack(side="left", padx=10)

        # Filtro: Grupo
        ctk.CTkLabel(fr_filtros, text="Grupo:", text_color="silver", font=("Roboto", 11)).pack(side="left", padx=(5, 2))
        self.cbo_filtro_grupo = ctk.CTkComboBox(fr_filtros, values=["Todos", "A", "B", "C", "D"], width=70, command=self.filtrar_tabla)
        self.cbo_filtro_grupo.set("Todos")
        self.cbo_filtro_grupo.pack(side="left", padx=5)

        # Filtro: Modalidad
        ctk.CTkLabel(fr_filtros, text="Modalidad:", text_color="silver", font=("Roboto", 11)).pack(side="left", padx=(10, 2))
        valores_modalidad = ["Todos", "PRIMERA OPCION", "ORDINARIO", "COLEGIO", "REFORZAMIENTO"]
        self.cbo_filtro_modalidad = ctk.CTkComboBox(fr_filtros, values=valores_modalidad, width=150, command=self.filtrar_tabla)
        self.cbo_filtro_modalidad.set("Todos")
        self.cbo_filtro_modalidad.pack(side="left", padx=5)

        # Botón Actualizar (Ahora llama al hilo)
        self.btn_actualizar = ctk.CTkButton(fr_filtros, text="🔄", width=40, fg_color="#404040", hover_color="#505050", 
                                            command=self.cargar_datos_thread)
        self.btn_actualizar.pack(side="right", padx=10)

        # --- 2. Tabla Custom ---
        self.fr_tabla_container = ctk.CTkFrame(panel_izq, fg_color=st.Colors.BG_PANEL, corner_radius=10)
        self.fr_tabla_container.pack(fill="both", expand=True)

        # Cabecera
        self.crear_cabecera()
        
        # Loader (Oculto)
        self.lbl_loader = ctk.CTkLabel(self.fr_tabla_container, text="Cargando base de datos...", text_color="#f39c12")

        # Cuerpo
        self.scroll_tabla = ctk.CTkScrollableFrame(self.fr_tabla_container, fg_color="transparent")
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- SCROLL INFINITO: HOOK ---
        # Interceptamos la barra de desplazamiento
        self.scroll_tabla._parent_canvas.configure(yscrollcommand=self._hook_scroll)

        # === SECCIÓN DERECHA: PANEL DE GESTIÓN ===
        panel_der = ctk.CTkFrame(self, width=200, fg_color=st.Colors.BG_PANEL, corner_radius=15)
        panel_der.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
        
        ctk.CTkLabel(panel_der, text="GESTIÓN", font=("Roboto", 16, "bold"), text_color="gray").pack(pady=(20, 15))

        self.btn_editar = ctk.CTkButton(panel_der, text="✏️ Editar Datos", fg_color="#f39c12", hover_color="#d35400", command=self.accion_editar)
        self.btn_editar.pack(fill="x", padx=15, pady=8)

        self.btn_ficha = ctk.CTkButton(panel_der, text="🖨️ Ficha Matrícula", fg_color="#34495e", hover_color="#2c3e50", command=self.accion_imprimir)
        self.btn_ficha.pack(fill="x", padx=15, pady=8)

        self.btn_eliminar = ctk.CTkButton(panel_der, text="❌ Anular Matrícula", fg_color="#c0392b", hover_color="#e74c3c", command=self.accion_eliminar)
        self.btn_eliminar.pack(fill="x", padx=15, pady=8)

        ctk.CTkFrame(panel_der, height=2, fg_color="#404040").pack(fill='x', padx=20, pady=20)
        
        self.lbl_total = ctk.CTkLabel(panel_der, text="Total: 0", font=("Roboto", 14, "bold"), text_color="white")
        self.lbl_total.pack(pady=5)

        # Cargar datos iniciales (Hilo)
        self.cargar_datos_thread()

    # ==================== LÓGICA DE SCROLL INFINITO ====================

    def _hook_scroll(self, first, last):
        """Detecta movimiento del scrollbar para cargar más datos"""
        # 1. Actualizar barra visual
        self.scroll_tabla._scrollbar.set(first, last)
        
        # 2. Detectar fondo (90%)
        if self.cargando_lock: return
        try:
            if float(last) > 0.90 and self.cantidad_cargada < len(self.resultados_filtrados):
                self.cargando_lock = True
                self.after(10, self._renderizar_siguiente_lote)
        except: pass

    def _renderizar_siguiente_lote(self):
        """Pinta el siguiente lote de 40 alumnos"""
        inicio = self.cantidad_cargada
        fin = inicio + self.lote_tamano
        lote = self.resultados_filtrados[inicio:fin]

        for i, alu in enumerate(lote):
            # i es el índice dentro del lote, necesitamos un índice global visual si queremos alternar colores
            # aunque en scroll infinito el alternado simple funciona bien
            idx_visual = self.cantidad_cargada + i
            self.crear_fila(alu, idx_visual)
        
        self.cantidad_cargada += len(lote)
        self.cargando_lock = False

    # ==================== LÓGICA DE HILOS ====================

    def cargar_datos_thread(self):
        """Inicia el hilo de carga"""
        self.lbl_total.configure(text="Cargando...")
        self.lbl_loader.pack(pady=5)
        self.btn_actualizar.configure(state="disabled")
        
        # Limpiar tabla
        self.fila_seleccionada = None
        self.datos_seleccionados = None
        for item in self.scroll_tabla.winfo_children(): item.destroy()
        
        threading.Thread(target=self._hilo_traer_datos, daemon=True).start()

    def _hilo_traer_datos(self):
        """(Backend) Trae todo a la RAM"""
        datos = self.controller.obtener_todos()
        self.after(0, lambda: self._finalizar_carga_datos(datos))

    def _finalizar_carga_datos(self, datos):
        """(Main) Guarda cache y aplica filtros"""
        self.lista_alumnos_cache = datos
        self.lbl_loader.pack_forget()
        self.btn_actualizar.configure(state="normal")
        
        # Aplicar filtros (esto llenará resultados_filtrados y pintará el primer lote)
        self.filtrar_tabla()

    def filtrar_tabla(self, event=None):
        """Filtra en memoria y reinicia el scroll"""
        texto = self.entry_buscar.get().lower()
        grupo_sel = self.cbo_filtro_grupo.get()
        modalidad_sel = self.cbo_filtro_modalidad.get()

        # 1. Limpiar visualmente
        for item in self.scroll_tabla.winfo_children(): item.destroy()
        
        # 2. Filtrar lista completa -> lista filtrada
        self.resultados_filtrados = []
        
        for alu in self.lista_alumnos_cache:
            # Filtro Grupo
            if grupo_sel != "Todos" and alu.grupo != grupo_sel: continue
            
            # Filtro Modalidad
            db_mod = str(alu.modalidad).upper() if alu.modalidad else ""
            if modalidad_sel != "Todos" and db_mod != modalidad_sel: continue

            # Filtro Texto
            nombre_completo = f"{alu.nombres} {alu.apell_paterno} {alu.apell_materno}".lower()
            codigo = alu.codigo_matricula.lower() if alu.codigo_matricula else ""
            dni = str(alu.dni)
            
            if (texto in nombre_completo) or (texto in codigo) or (texto in dni):
                self.resultados_filtrados.append(alu)

        # 3. Actualizar contadores
        self.lbl_total.configure(text=f"Total: {len(self.resultados_filtrados)}")
        self.cantidad_cargada = 0
        self.cargando_lock = False
        
        # 4. Iniciar renderizado del primer lote
        self.scroll_tabla._parent_canvas.yview_moveto(0.0) # Reset scroll arriba
        self._renderizar_siguiente_lote()

    # ==================== MÉTODOS VISUALES TABLA ====================

    def crear_cabecera(self):
        header = ctk.CTkFrame(self.fr_tabla_container, height=40, fg_color=st.Colors.TABLE_HEADER, corner_radius=5)
        header.pack(fill="x", padx=5, pady=(5, 0))
        
        titulos = ["CÓDIGO", "DNI", "ALUMNO", "MODALIDAD", "GRP", "CELULAR"]
        for i, t in enumerate(titulos):
            w = self.ANCHOS[i]
            ctk.CTkLabel(header, text=t, font=("Roboto", 11, "bold"), text_color="white", width=w).pack(side="left", padx=2)

    def crear_fila(self, alu, index):
        bg = st.Colors.ROW_ODD if index % 2 == 0 else st.Colors.ROW_EVEN
        
        row = ctk.CTkFrame(self.scroll_tabla, fg_color=bg, corner_radius=5, height=35)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        def on_click(e): self.seleccionar_fila(row, alu)
        row.bind("<Button-1>", on_click)

        font_row = ("Roboto", 11)
        
        def celda(txt, w, color="white", anchor="center"):
            lbl = ctk.CTkLabel(row, text=str(txt), width=w, text_color=color, font=font_row, anchor=anchor)
            lbl.pack(side="left", padx=2)
            lbl.bind("<Button-1>", on_click)

        celda(alu.codigo_matricula, self.ANCHOS[0])
        celda(alu.dni, self.ANCHOS[1], "gray")
        celda(f"{alu.apell_paterno} {alu.apell_materno}, {alu.nombres}", self.ANCHOS[2], "white", "w")
        celda(alu.modalidad, self.ANCHOS[3], "gray")
        
        lbl_grp = ctk.CTkLabel(row, text=alu.grupo, width=self.ANCHOS[4], text_color="#f1c40f", font=("Arial", 11, "bold"))
        lbl_grp.pack(side="left", padx=2)
        lbl_grp.bind("<Button-1>", on_click)

        celda(alu.celular_padre_1, self.ANCHOS[5], "gray")

    def seleccionar_fila(self, widget_fila, datos_alumno):
        if self.fila_seleccionada and self.fila_seleccionada.winfo_exists():
            try: self.fila_seleccionada.configure(fg_color="#2d2d2d") 
            except: pass

        self.fila_seleccionada = widget_fila
        self.datos_seleccionados = datos_alumno
        self.fila_seleccionada.configure(fg_color="#34495e")

    # ==================== ACCIONES (SIN CAMBIOS) ====================

    def accion_editar(self):
        if not self.datos_seleccionados:
            messagebox.showwarning("Aviso", "Seleccione un alumno para editar.")
            return
        # Callback apunta al hilo para recargar suavemente
        EditarAlumnoWindow(self, self.datos_seleccionados.id, self.cargar_datos_thread)

    def accion_imprimir(self):
        if not self.datos_seleccionados:
            messagebox.showwarning("Aviso", "Seleccione un alumno.")
            return
        messagebox.showinfo("Info", f"Imprimiendo ficha de: {self.datos_seleccionados.nombres}")

    def accion_eliminar(self):
        if not self.datos_seleccionados:
            messagebox.showwarning("Aviso", "Seleccione un alumno para anular.")
            return
        
        alu = self.datos_seleccionados
        mensaje = (f"¿Está SEGURO de anular la matrícula de:\n\n👤 {alu.nombres} {alu.apell_paterno}?\n\n"
                   "⚠️ ESTA ACCIÓN ES IRREVERSIBLE.")

        if messagebox.askyesno("Confirmar Anulación", mensaje, icon='warning'):
            exito, msg = self.controller.eliminar_alumno(alu.id)
            if exito:
                messagebox.showinfo("Éxito", msg)
                self.cargar_datos_thread()
            else:
                messagebox.showerror("Error", msg)