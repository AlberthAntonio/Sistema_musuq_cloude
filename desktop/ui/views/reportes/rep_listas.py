"""
ReporteView - Listas para PDF (Alumnos) - VERSIÓN VISUAL PREMIUM
Refactor visual manteniendo la lógica original.
"""

import customtkinter as ctk
from tkinter import messagebox
from customtkinter import CTkFont
import threading

from controllers.reporte_controller import ReporteController
import styles.tabla_style as st
from core.theme_manager import TM


class ReporteListasView(ctk.CTkFrame):
    """
    Vista para crear listas de alumnos y generar PDFs.

    Mantiene la misma lógica original (filtros, scroll infinito, selección,
    listas favoritas y generación de PDF), pero con un diseño visual unificado
    al resto de vistas Musuq Cloud.
    """

    def __init__(self, master, auth_client=None, **kwargs):
        super().__init__(master, fg_color="transparent")

        self.auth_client = auth_client
        self.controller = ReporteController()

        # --- VARIABLES DE SELECCIÓN ---
        self.seleccionados = set()
        self.filas_visuales = {}

        # --- VARIABLES SCROLL INFINITO ---
        self.todos_los_alumnos = []   # Data completa en memoria
        self.cantidad_mostrada = 0    # Cuántos se ven actualmente
        self.lote_tamano = 20         # Cargar de 20 en 20
        self.cargando_lock = False    # Candado para no repetir cargas

        # Layout principal (tres columnas)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Construir UI
        self._crear_columna_filtros()
        self._crear_columna_tabla()
        self._crear_columna_config()

        # Cargar combos de listas favoritas
        self.actualizar_combo_listas()

    # =====================================================================
    # COLUMNA 1: FILTROS (Panel izquierdo)
    # =====================================================================

    def _crear_columna_filtros(self):
        pnl_filtros = ctk.CTkFrame(
            self,
            fg_color=TM.bg_panel(),
            corner_radius=10
        )
        pnl_filtros.grid(row=0, column=0, padx=(15, 8), pady=15, sticky="nsew")

        pnl_filtros.grid_rowconfigure(99, weight=1)

        # Título con icono
        header = ctk.CTkFrame(pnl_filtros, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(18, 10))

        ctk.CTkLabel(
            header,
            text="🧮",
            font=CTkFont(family="Arial", size=26)
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            header,
            text="1. FILTRAR",
            font=CTkFont(family="Roboto", size=16, weight="bold"),
            text_color=TM.text()
        ).pack(side="left")

        grupos, modalidades, turnos = self.controller.obtener_filtros_disponibles()

        def crear_filtro(titulo, valores, comando=None):
            ctk.CTkLabel(
                pnl_filtros,
                text=titulo,
                font=CTkFont(family="Roboto", size=12, weight="bold"),
                text_color=TM.text_secondary()
            ).pack(anchor="w", padx=18, pady=(8, 3))

            cb = ctk.CTkComboBox(
                pnl_filtros,
                values=valores,
                command=comando,
                fg_color=TM.bg_card(),
                text_color=TM.text(),
                dropdown_fg_color=TM.bg_panel(),
                border_color="#404040",
                border_width=1,
                button_color=TM.primary(),
                button_hover_color="#3498db",
                font=CTkFont(family="Roboto", size=11),
                height=34
            )
            cb.pack(fill="x", padx=18, pady=(0, 6))
            return cb

        self.cb_grupo = crear_filtro("Grupo/Salón:", ["Todos"] + grupos)
        self.cb_modalidad = crear_filtro("Modalidad:", ["Todas"] + modalidades, self.al_cambiar_modalidad)
        self.cb_horario = crear_filtro("Horario:", ["Todos"] + turnos)

        # Botón Cargar con estilo destacado
        self.btn_cargar = ctk.CTkButton(
            pnl_filtros,
            text="🔍 CARGAR ALUMNOS",
            fg_color=TM.primary(),
            hover_color="#3498db",
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            height=40,
            corner_radius=8,
            command=self.cargar_alumnos_thread
        )
        self.btn_cargar.pack(padx=18, pady=20, fill="x")

    # =====================================================================
    # COLUMNA 2: TABLA CON SCROLL INFINITO (Centro)
    # =====================================================================

    def _crear_columna_tabla(self):
        pnl_tabla = ctk.CTkFrame(self, fg_color="transparent")
        pnl_tabla.grid(row=0, column=1, padx=8, pady=15, sticky="nsew")

        # Título
        ctk.CTkLabel(
            pnl_tabla,
            text="2. SELECCIONE ALUMNOS",
            font=CTkFont(family="Roboto", size=16, weight="bold"),
            text_color=TM.text()
        ).pack(pady=(5, 8))

        # Botones de selección
        fr_btns = ctk.CTkFrame(pnl_tabla, fg_color="transparent")
        fr_btns.pack(fill="x", pady=(0, 8))

        self.btn_sel_todo = ctk.CTkButton(
            fr_btns,
            text="☑ Seleccionar Todo",
            width=130,
            fg_color="#34495e",
            hover_color="#2c3e50",
            corner_radius=8,
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            command=self.seleccionar_todo
        )
        self.btn_sel_todo.pack(side="left", padx=(0, 8))

        self.btn_limpiar = ctk.CTkButton(
            fr_btns,
            text="☒ Limpiar",
            width=100,
            fg_color="transparent",
            border_width=1,
            border_color="#555555",
            text_color=TM.text_secondary(),
            hover_color="#404040",
            corner_radius=8,
            font=CTkFont(family="Roboto", size=11),
            command=self.limpiar_seleccion
        )
        self.btn_limpiar.pack(side="left")

        # Container Tabla
        self.container_tabla = ctk.CTkFrame(
            pnl_tabla,
            fg_color=TM.bg_panel(),
            corner_radius=10,
        )
        self.container_tabla.pack(fill="both", expand=True)

        # Cabecera
        h_frame = ctk.CTkFrame(
            self.container_tabla,
            height=42,
            fg_color=st.Colors.TABLE_HEADER,
            corner_radius=6
        )
        h_frame.pack(fill="x", padx=6, pady=(6, 0))
        h_frame.pack_propagate(False)

        ctk.CTkLabel(
            h_frame,
            text="✔",
            width=40,
            font=CTkFont(family="Arial", size=14, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=6)

        ctk.CTkLabel(
            h_frame,
            text="CÓDIGO",
            width=90,
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            text_color="white"
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            h_frame,
            text="APELLIDOS Y NOMBRES",
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            text_color="white",
            anchor="w"
        ).pack(side="left", padx=4, expand=True, fill="x")

        # Contenedor fijo para loader + tabla
        body_frame = ctk.CTkFrame(self.container_tabla, fg_color="transparent")
        body_frame.pack(fill="both", expand=True, padx=6, pady=6)

        # Loader (mismo lugar siempre)
        self.lbl_loading = ctk.CTkLabel(
            body_frame,
            text="⏳ Procesando solicitud...",
            text_color=TM.warning(),
            font=CTkFont(family="Roboto", size=14, weight="bold")
        )

        # Cuerpo scrollable
        self.scroll_tabla = ctk.CTkScrollableFrame(
            body_frame,
            fg_color="transparent"
        )
        self.scroll_tabla.pack(fill="both", expand=True)


        # Hook de scroll infinito
        self.scroll_tabla._parent_canvas.configure(yscrollcommand=self._hook_scroll)

        # Estado vacío inicial
        self.lbl_vacio = ctk.CTkLabel(
            self.scroll_tabla,
            text="Use los filtros para cargar datos.",
            text_color="gray",
            font=CTkFont(family="Roboto", size=12)
        )
        self.lbl_vacio.pack(pady=20)

    # =====================================================================
    # COLUMNA 3: CONFIGURACIÓN (Derecha)
    # =====================================================================

    def _crear_columna_config(self):
        pnl_config = ctk.CTkFrame(
            self,
            fg_color=TM.bg_panel(),
            corner_radius=10
        )
        pnl_config.grid(row=0, column=2, padx=(8, 15), pady=15, sticky="nsew")

        pnl_config.grid_rowconfigure(99, weight=1)

        # --- FAVORITOS ---
        fr_favs = ctk.CTkFrame(
            pnl_config,
            fg_color="#34495e",
            corner_radius=8
        )
        fr_favs.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            fr_favs,
            text="📂 LISTAS GUARDADAS",
            text_color="white",
            font=CTkFont(family="Roboto", size=12, weight="bold")
        ).pack(pady=(10, 4))

        self.cb_listas = ctk.CTkComboBox(
            fr_favs,
            values=["-- Seleccionar --"],
            command=self.cargar_lista_favorita,
            fg_color="#2c3e50",
            border_width=0,
            button_color="#2c3e50",
            text_color="white",
            dropdown_fg_color="#2c3e50",
            font=CTkFont(family="Roboto", size=11)
        )
        self.cb_listas.set("-- Seleccionar --")
        self.cb_listas.pack(fill="x", padx=10, pady=4)

        fr_btns_fav = ctk.CTkFrame(fr_favs, fg_color="transparent")
        fr_btns_fav.pack(fill="x", pady=8)

        ctk.CTkButton(
            fr_btns_fav,
            text="💾 Guardar Actual",
            width=100,
            height=28,
            fg_color=TM.success(),
            hover_color="#2ecc71",
            font=CTkFont(family="Roboto", size=11),
            corner_radius=8,
            command=self.guardar_seleccion_actual
        ).pack(side="left", padx=10, expand=True, fill="x")

        ctk.CTkButton(
            fr_btns_fav,
            text="🗑️",
            width=32,
            height=28,
            fg_color=TM.danger(),
            hover_color="#e74c3c",
            corner_radius=8,
            command=self.eliminar_lista_actual
        ).pack(side="right", padx=10)

        # Separador
        ctk.CTkFrame(
            pnl_config,
            height=2,
            fg_color="#555555"
        ).pack(fill="x", padx=20, pady=10)

        # --- CONFIGURACIÓN PDF ---
        ctk.CTkLabel(
            pnl_config,
            text="3. CONFIGURAR PDF",
            font=CTkFont(family="Roboto", size=16, weight="bold"),
            text_color=TM.text()
        ).pack(pady=(5, 8))

        ctk.CTkLabel(
            pnl_config,
            text="Título del Reporte:",
            anchor="w",
            text_color=TM.text_secondary(),
            font=CTkFont(family="Roboto", size=11, weight="bold")
        ).pack(fill="x", padx=20, pady=(5, 0))

        self.entry_titulo = ctk.CTkEntry(
            pnl_config,
            fg_color="#383838",
            border_width=0,
            text_color="white"
        )
        self.entry_titulo.insert(0, "Lista Oficial de Clase")
        self.entry_titulo.pack(fill="x", padx=20, pady=5)

        ctk.CTkLabel(
            pnl_config,
            text="Tipo de Reporte:",
            anchor="w",
            text_color=TM.text_secondary(),
            font=CTkFont(family="Roboto", size=11, weight="bold")
        ).pack(fill="x", padx=20, pady=(15, 5))

        self.var_tipo = ctk.StringVar(value="simple")

        def crear_radio(txt, val):
            ctk.CTkRadioButton(
                pnl_config,
                text=txt,
                variable=self.var_tipo,
                value=val,
                text_color=TM.text(),
                border_color=TM.primary(),
                fg_color=TM.primary(),
                hover_color=TM.primary(),
                font=CTkFont(family="Roboto", size=11)
            ).pack(anchor="w", padx=25, pady=3)

        crear_radio("Simple (Firma)", "simple")
        crear_radio("Control de Asistencia", "asistencia")
        crear_radio("Registro de Notas", "notas")
        crear_radio("Datos de Contacto", "datos")

        # Contador de seleccionados (abajo)
        self.lbl_contador = ctk.CTkLabel(
            pnl_config,
            text="0 alumnos seleccionados",
            font=CTkFont(family="Roboto", size=14, weight="bold"),
            text_color="gray"
        )
        self.lbl_contador.pack(side="bottom", pady=(0, 4))

        # Botón generar PDF (abajo)
        self.btn_generar = ctk.CTkButton(
            pnl_config,
            text="GENERAR PDF",
            height=46,
            fg_color="#e67e22",
            hover_color="#d35400",
            font=CTkFont(family="Roboto", size=14, weight="bold"),
            corner_radius=8,
            command=self.generar_reporte_thread
        )
        self.btn_generar.pack(side="bottom", fill="x", padx=20, pady=(8, 10))

    # =====================================================================
    # SCROLL INFINITO - DETECCIÓN Y RENDERIZADO (misma lógica)
    # =====================================================================

    def _hook_scroll(self, first, last):
        """Detecta cuando la barra baja al final para cargar más datos."""
        self.scroll_tabla._scrollbar.set(first, last)

        if self.cargando_lock:
            return

        try:
            if float(last) > 0.90 and self.cantidad_mostrada < len(self.todos_los_alumnos):
                self.cargando_lock = True
                self.after(10, self._renderizar_siguiente_lote)
        except Exception:
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

    # =====================================================================
    # FILAS VISUALES (misma lógica, mejor estética)
    # =====================================================================

    def crear_fila(self, alu, index):
        bg_color = st.Colors.ROW_ODD if index % 2 == 0 else st.Colors.ROW_EVEN

        row = ctk.CTkFrame(
            self.scroll_tabla,
            fg_color=bg_color,
            corner_radius=6,
            height=38
        )
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)

        esta_seleccionado = alu.id in self.seleccionados
        var_check = ctk.BooleanVar(value=esta_seleccionado)

        chk = ctk.CTkCheckBox(
            row,
            text="",
            width=24,
            variable=var_check,
            command=lambda: self.toggle_seleccion(alu.id, var_check)
        )
        chk.pack(side="left", padx=(14, 6))

        ctk.CTkLabel(
            row,
            text=alu.codigo_matricula,
            width=90,
            text_color="silver",
            font=CTkFont(family="Roboto", size=11)
        ).pack(side="left", padx=4)

        ctk.CTkLabel(
            row,
            text=f"{alu.apell_paterno} {alu.apell_materno}, {alu.nombres}",
            text_color=TM.text(),
            anchor="w",
            font=CTkFont(family="Roboto", size=11)
        ).pack(side="left", padx=4, fill="x", expand=True)

        self.filas_visuales[alu.id] = {"var": var_check, "widget": row}

    def toggle_seleccion(self, id_alumno, var_check):
        if var_check.get():
            self.seleccionados.add(id_alumno)
        else:
            self.seleccionados.discard(id_alumno)
        self.actualizar_contador()

    # =====================================================================
    # THREADING - CARGA DE ALUMNOS (misma lógica)
    # =====================================================================

    def cargar_alumnos_thread(self):
        """Inicia la carga de alumnos en un hilo separado."""
        self.limpiar_tabla_visual()

        # Mostrar loader centrado
        self.lbl_loading.place(relx=0.5, rely=0.5, anchor="center")
        self.lbl_loading.lift()
        self.update_idletasks()

        self.btn_cargar.configure(state="disabled")
        self.lbl_vacio.pack_forget()

        grupo = self.cb_grupo.get()
        modalidad = self.cb_modalidad.get()
        horario = self.cb_horario.get()

        threading.Thread(
            target=self._proceso_busqueda,
            args=(grupo, modalidad, horario),
            daemon=True
        ).start()

    def _proceso_busqueda(self, g, m, h):
        """Worker Thread - Búsqueda en BD."""
        alumnos = self.controller.buscar_alumnos(g, m, h)
        self.after(0, lambda: self._finalizar_carga(alumnos))

    def _finalizar_carga(self, alumnos):
        """Main Thread - Actualiza UI con resultados."""
        self.lbl_loading.place_forget()
        self.btn_cargar.configure(state="normal")

        self.todos_los_alumnos = alumnos
        self.cantidad_mostrada = 0
        self.cargando_lock = False

        if not alumnos:
            self.lbl_vacio.pack(pady=20)
            self.lbl_vacio.configure(text="No se encontraron alumnos.")
            return

        # Renderizar primer lote y seleccionar todo
        self._renderizar_siguiente_lote()
        self.seleccionar_todo()

    # =====================================================================
    # THREADING - GENERACIÓN DE PDF (misma lógica)
    # =====================================================================

    def generar_reporte_thread(self):
        """Inicia la generación de PDF en un hilo separado."""
        if not self.seleccionados:
            messagebox.showwarning("Alerta", "Seleccione al menos un alumno.")
            return

        ids = list(self.seleccionados)
        tipo = self.var_tipo.get()
        titulo = self.entry_titulo.get()

        self.btn_generar.configure(state="disabled", text="Generando PDF...")

        threading.Thread(
            target=self._proceso_pdf,
            args=(ids, tipo, titulo),
            daemon=True
        ).start()

    def _proceso_pdf(self, ids, tipo, titulo):
        """Worker Thread - Generación del PDF."""
        exito, msg = self.controller.generar_reporte_pdf(ids, tipo, titulo)
        self.after(0, lambda: self._finalizar_pdf(exito, msg))

    def _finalizar_pdf(self, exito, msg):
        """Main Thread - Muestra resultado."""
        self.btn_generar.configure(state="normal", text="GENERAR PDF")

        if not exito:
            messagebox.showerror("Error", msg)

    # =====================================================================
    # LISTAS FAVORITAS (misma lógica)
    # =====================================================================

    def guardar_seleccion_actual(self):
        if not self.seleccionados:
            messagebox.showwarning("Aviso", "Selecciona alumnos primero.")
            return

        dialog = ctk.CTkInputDialog(
            text="Nombre para esta lista:",
            title="Guardar Lista"
        )
        nombre = dialog.get_input()
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

        self._finalizar_carga(alumnos)

        if alumnos:
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

    # =====================================================================
    # FILTROS Y HELPERS (misma lógica)
    # =====================================================================

    def al_cambiar_modalidad(self, seleccion):
        sel_lower = seleccion.lower()
        # Nota: en el original usabas cb_turno; aquí corresponde a cb_horario
        if "colegio" in sel_lower or "ordinario" in sel_lower:
            self.cb_horario.set("Todos")
            self.cb_horario.configure(state="disabled")
        else:
            self.cb_horario.configure(state="normal")

    def limpiar_tabla_visual(self):
        for w in self.scroll_tabla.winfo_children():
            if w is not self.lbl_vacio:
                w.destroy()

        self.filas_visuales = {}
        self.seleccionados = set()
        self.todos_los_alumnos = []
        self.cantidad_mostrada = 0
        self.actualizar_contador()
        self.lbl_vacio.configure(text="Use los filtros para cargar datos.")
        self.lbl_vacio.pack(pady=20)

    def seleccionar_todo(self):
        """Selecciona TODOS los alumnos (incluso los no visibles)."""
        for alu in self.todos_los_alumnos:
            self.seleccionados.add(alu.id)

        for _id, data in self.filas_visuales.items():
            data["var"].set(True)

        self.actualizar_contador()

    def limpiar_seleccion(self):
        self.seleccionados.clear()
        for _id, data in self.filas_visuales.items():
            data["var"].set(False)
        self.actualizar_contador()

    def actualizar_contador(self, event=None):
        count = len(self.seleccionados)
        self.lbl_contador.configure(
            text=f"{count} alumnos seleccionados",
            text_color=TM.success() if count > 0 else "gray"
        )
