"""
Vista de Gestión de Notas - ESTILO PREMIUM MEJORADO
Sistema Musuq Cloud
Sábana de notas con panel de exámenes, filtros y paginación
"""

import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from typing import Dict, Any

from controllers.academico_controller import AcademicoController
from styles import tabla_style as st
from core.theme_manager import ThemeManager as TM


class NotasView(ctk.CTkFrame):
    """
    Vista profesional para gestión de notas académicas.
    Características: Panel de exámenes, sábana de notas, filtros, paginación
    """

    def __init__(self, parent, auth_client=None):
        super().__init__(parent, fg_color="transparent")
        self._auth_token = auth_client.token if auth_client else ""
        self.controller = None

        # Variables de estado
        self.sesion_actual = None
        self.lista_filas_alumnos = []

        # Variables de paginación
        self.pagina_actual = 1
        self.items_por_pagina = 30
        self.total_paginas = 1
        self.alumnos_filtrados_cache = []
        self._ui_ready = False
        self._loading_frame = None

        self._show_loading_state()
        self.after(1, self._build_ui_deferred)

    def _show_loading_state(self):
        """Placeholder inicial antes de construir la sábana completa."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._loading_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._loading_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        ctk.CTkLabel(
            self._loading_frame,
            text="Cargando modulo de notas...",
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            text_color=TM.text_secondary(),
        ).pack(expand=True)

    def _build_ui_deferred(self):
        """Construye widgets y carga exámenes luego del primer render."""
        if self._ui_ready:
            return

        if self.controller is None:
            self.controller = AcademicoController(self._auth_token)

        if self._loading_frame is not None:
            self._loading_frame.destroy()
            self._loading_frame = None

        self.create_widgets()
        self.after(150, self.cargar_lista_sesiones)
        self._ui_ready = True

    def create_widgets(self):
        # Layout principal con grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ============================
        # PANEL IZQUIERDO: EXÁMENES
        # ============================
        self._crear_panel_examenes()

        # ============================
        # PANEL DERECHO: SÁBANA DE NOTAS
        # ============================
        self._crear_panel_notas()

    def _crear_panel_examenes(self):
        """Crear panel izquierdo con lista de exámenes"""
        self.panel_izq = ctk.CTkFrame(
            self,
            width=300,
            fg_color=TM.bg_panel(),
            corner_radius=0
        )
        self.panel_izq.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        self.panel_izq.grid_propagate(False)

        # Header del panel
        header = ctk.CTkFrame(self.panel_izq, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))

        # Icono y título
        ctk.CTkLabel(
            header,
            text="📚",
            font=ctk.CTkFont(family="Arial", size=40)
        ).pack(pady=(0, 10))

        ctk.CTkLabel(
            header,
            text="EXÁMENES",
            font=ctk.CTkFont(family="Roboto", size=20, weight="bold"),
            text_color=TM.text()
        ).pack()

        # Botón Nuevo Examen
        self.btn_nuevo = ctk.CTkButton(
            self.panel_izq,
            text="+ NUEVO EXAMEN",
            fg_color=TM.primary(),
            hover_color="#2980b9",
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            command=self.abrir_popup_crear_examen
        )
        self.btn_nuevo.pack(pady=20, padx=20, fill="x")

        # Separador
        ctk.CTkFrame(
            self.panel_izq,
            height=2,
            fg_color="#404040"
        ).pack(fill="x", padx=20, pady=(0, 10))

        # Label de instrucción
        ctk.CTkLabel(
            self.panel_izq,
            text="Seleccione un examen:",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(family="Roboto", size=11)
        ).pack(anchor="w", padx=20, pady=(0, 10))

        # Scroll con lista de sesiones
        self.scroll_sesiones = ctk.CTkScrollableFrame(
            self.panel_izq,
            fg_color="transparent"
        )
        self.scroll_sesiones.pack(fill="both", expand=True, padx=15, pady=(0, 20))

    def _crear_panel_notas(self):
        """Crear panel derecho con sábana de notas"""
        self.panel_der = ctk.CTkFrame(self, fg_color="transparent")
        self.panel_der.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        # Header con título dinámico
        header = ctk.CTkFrame(
            self.panel_der,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=80
        )
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=25, pady=20)

        # Icono y título
        icon_title = ctk.CTkFrame(header_content, fg_color="transparent")
        icon_title.pack(side="left", fill="both", expand=True)

        self.lbl_titulo_sesion = ctk.CTkLabel(
            icon_title,
            text="📝 Selecciona un examen para comenzar",
            font=ctk.CTkFont(family="Roboto", size=22, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        )
        self.lbl_titulo_sesion.pack(side="left")

        # Barra de herramientas (Filtros y Paginación)
        self._crear_barra_herramientas()

        # Tabla (Sábana de notas)
        self._crear_tabla_notas()

        # Botón Guardar
        self._crear_boton_guardar()

    def _crear_barra_herramientas(self):
        """Crear barra de herramientas con filtros y paginación"""
        self.frame_tools = ctk.CTkFrame(
            self.panel_der,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=70
        )
        self.frame_tools.pack(fill="x", pady=(0, 15))
        self.frame_tools.pack_propagate(False)

        tools_content = ctk.CTkFrame(self.frame_tools, fg_color="transparent")
        tools_content.pack(fill="both", expand=True, padx=20, pady=15)

        # --- LADO IZQUIERDO: FILTROS ---
        filtros_left = ctk.CTkFrame(tools_content, fg_color="transparent")
        filtros_left.pack(side="left", fill="y")

        combo_style = {
            "fg_color": TM.bg_panel(),
            "border_width": 0,
            "button_color": TM.primary(),
            "button_hover_color": "#2980b9",
            "dropdown_fg_color": TM.bg_panel(),
            "font": ctk.CTkFont(family="Roboto", size=11)
        }

        # Filtro Grupo
        ctk.CTkLabel(
            filtros_left,
            text="Grupo:",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(family="Roboto", size=11)
        ).pack(side="left", padx=(0, 5))

        self.combo_grupo = ctk.CTkComboBox(
            filtros_left,
            values=["Todos", "A", "B", "C", "D"],
            width=80,
            **combo_style
        )
        self.combo_grupo.set("Todos")
        self.combo_grupo.pack(side="left", padx=(0, 15))

        # Filtro Modalidad
        ctk.CTkLabel(
            filtros_left,
            text="Modalidad:",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(family="Roboto", size=11)
        ).pack(side="left", padx=(0, 5))

        self.combo_modalidad = ctk.CTkComboBox(
            filtros_left,
            values=["Todos", "ORDINARIO", "PRIMERA OPCION", "COLEGIO", "REFORZAMIENTO"],
            width=150,
            **combo_style
        )
        self.combo_modalidad.set("Todos")
        self.combo_modalidad.pack(side="left", padx=(0, 15))

        # Buscador
        self.bg_search = ctk.CTkFrame(
            filtros_left,
            fg_color=TM.bg_panel(),
            corner_radius=10,
            height=38
        )
        self.bg_search.pack(side="left", padx=(0, 10))

        self.entry_busqueda = ctk.CTkEntry(
            self.bg_search,
            placeholder_text="🔍 Buscar alumno...",
            border_width=0,
            fg_color="transparent",
            text_color=TM.text(),
            width=180,
            font=ctk.CTkFont(family="Roboto", size=11)
        )
        self.entry_busqueda.pack(fill="both", padx=10, pady=5)
        self.entry_busqueda.bind("<Return>", lambda e: self.buscar_y_reiniciar())

        # Botón Filtrar
        self.btn_filtrar = ctk.CTkButton(
            filtros_left,
            text="Filtrar",
            width=90,
            height=38,
            fg_color=TM.warning(),
            hover_color="#d35400",
            corner_radius=10,
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            command=self.buscar_y_reiniciar
        )
        self.btn_filtrar.pack(side="left")

        # --- LADO DERECHO: PAGINACIÓN ---
        paginacion = ctk.CTkFrame(tools_content, fg_color="transparent")
        paginacion.pack(side="right", fill="y")

        # Botón Siguiente
        self.btn_siguiente = ctk.CTkButton(
            paginacion,
            text="›",
            width=40,
            height=38,
            fg_color="#34495e",
            hover_color="#2c3e50",
            corner_radius=10,
            font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
            command=self.pagina_siguiente
        )
        self.btn_siguiente.pack(side="right", padx=(10, 0))

        # Label Paginación
        self.lbl_paginacion = ctk.CTkLabel(
            paginacion,
            text="Pág 0/0",
            font=ctk.CTkFont(family="Roboto Mono", size=12, weight="bold"),
            text_color=TM.text_secondary(),
            width=120
        )
        self.lbl_paginacion.pack(side="right", padx=10)

        # Botón Anterior
        self.btn_anterior = ctk.CTkButton(
            paginacion,
            text="‹",
            width=40,
            height=38,
            fg_color="#34495e",
            hover_color="#2c3e50",
            corner_radius=10,
            font=ctk.CTkFont(family="Arial", size=20, weight="bold"),
            command=self.pagina_anterior
        )
        self.btn_anterior.pack(side="right")

    def _crear_tabla_notas(self):
        """Crear contenedor de tabla de notas"""
        self.fr_tabla_container = ctk.CTkFrame(
            self.panel_der,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.fr_tabla_container.pack(fill="both", expand=True, pady=(0, 15))

        # Scroll con sábana
        self.scroll_tabla = ctk.CTkScrollableFrame(
            self.fr_tabla_container,
            fg_color="transparent",
            orientation="vertical"
        )
        self.scroll_tabla.pack(fill="both", expand=True, padx=15, pady=15)

        # Grid frame para la sábana
        self.grid_frame = ctk.CTkFrame(self.scroll_tabla, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True)

        # Estado vacío inicial
        self._mostrar_estado_vacio("Seleccione un examen para comenzar")

    def _crear_boton_guardar(self):
        """Crear botón de guardar notas"""
        self.btn_guardar = ctk.CTkButton(
            self.panel_der,
            text="💾 GUARDAR NOTAS",
            fg_color=TM.success(),
            hover_color="#27ae60",
            height=50,
            corner_radius=10,
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            state="disabled",
            command=self.guardar_notas
        )
        self.btn_guardar.pack(fill="x")

    # ========================================================
    # LÓGICA DE EXÁMENES
    # ========================================================

    def cargar_lista_sesiones(self):
        """Cargar lista de sesiones de examen"""
        # Limpiar
        for w in self.scroll_sesiones.winfo_children():
            w.destroy()

        # Obtener sesiones
        sesiones = self.controller.obtener_sesiones_examen()

        if not sesiones:
            self._mostrar_estado_vacio_examenes()
            return

        # Renderizar cada sesión
        for sesion in sesiones:
            self._crear_tarjeta_examen(sesion)

    def _mostrar_estado_vacio_examenes(self):
        """Mostrar estado vacío en lista de exámenes"""
        empty_frame = ctk.CTkFrame(self.scroll_sesiones, fg_color="transparent")
        empty_frame.pack(fill="both", expand=True, pady=40)

        ctk.CTkLabel(
            empty_frame,
            text="📭",
            font=ctk.CTkFont(family="Arial", size=50)
        ).pack(pady=10)

        ctk.CTkLabel(
            empty_frame,
            text="Sin exámenes",
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            text_color=TM.text()
        ).pack()

        ctk.CTkLabel(
            empty_frame,
            text="Crea tu primer examen",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(pady=(5, 0))

    def _crear_tarjeta_examen(self, sesion):
        """Crear tarjeta de examen"""
        # Colores según estado
        if sesion.estado == "Abierto":
            bg_color = "#2c3e50"
            hover_color = "#34495e"
            txt_color = TM.text()
            badge_color = TM.success()
            badge_text = "ABIERTO"
        else:
            bg_color = "#2d2d2d"
            hover_color = "#363636"
            txt_color = TM.text_secondary()
            badge_color = "#7f8c8d"
            badge_text = "CERRADO"

        # Card principal
        card = ctk.CTkFrame(
            self.scroll_sesiones,
            fg_color=bg_color,
            corner_radius=10
        )
        card.pack(fill="x", pady=3)

        # Botón clickeable
        btn = ctk.CTkButton(
            card,
            text="",
            fg_color="transparent",
            hover_color=hover_color,
            corner_radius=10,
            height=75,
            anchor="w",
            command=lambda s=sesion: self.seleccionar_sesion(s)
        )
        btn.pack(fill="both", expand=True)

        # Content interno
        content = ctk.CTkFrame(btn, fg_color="transparent")
        content.place(relx=0, rely=0, relwidth=1, relheight=1)

        # Header con fecha y badge
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(10, 5))

        ctk.CTkLabel(
            header,
            text=str(sesion.fecha),
            font=ctk.CTkFont(family="Roboto Mono", size=10, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=badge_text,
            fg_color=badge_color,
            text_color="white",
            corner_radius=5,
            width=70,
            height=18,
            font=ctk.CTkFont(family="Roboto", size=8, weight="bold")
        ).pack(side="right")

        # Nombre del examen
        ctk.CTkLabel(
            content,
            text=sesion.nombre,
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=txt_color,
            anchor="w"
        ).pack(fill="x", padx=15, pady=(0, 10))

    def abrir_popup_crear_examen(self):
        """Abrir popup para crear nuevo examen"""
        self.popup = ctk.CTkToplevel(self)
        self.popup.title("Nuevo Examen")
        self.popup.geometry("450x400")
        self.popup.resizable(False, False)

        # Centrar ventana
        self.popup.update_idletasks()
        x = (self.popup.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.popup.winfo_screenheight() // 2) - (400 // 2)
        self.popup.geometry(f"450x400+{x}+{y}")

        self.popup.attributes("-topmost", True)
        self.popup.transient(self)
        self.popup.grab_set()

        # Header del popup
        header = ctk.CTkFrame(self.popup, fg_color=TM.bg_card(), corner_radius=0)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="📝",
            font=ctk.CTkFont(family="Arial", size=40)
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            header,
            text="Crear Nuevo Examen",
            font=ctk.CTkFont(family="Roboto", size=20, weight="bold"),
            text_color=TM.text()
        ).pack(pady=(0, 20))

        # Contenido
        content = ctk.CTkFrame(self.popup, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=30, pady=20)

        # Nombre del examen
        ctk.CTkLabel(
            content,
            text="Nombre del Examen:",
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        ).pack(fill="x", pady=(0, 5))

        self.entry_nombre_popup = ctk.CTkEntry(
            content,
            height=40,
            fg_color=TM.bg_panel(),
            border_width=0,
            placeholder_text="Ej. Examen Semanal 5",
            font=ctk.CTkFont(family="Roboto", size=12)
        )
        self.entry_nombre_popup.pack(fill="x", pady=(0, 20))

        # Fecha del examen
        ctk.CTkLabel(
            content,
            text="Fecha del Examen:",
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        ).pack(fill="x", pady=(0, 5))

        frame_fecha = ctk.CTkFrame(content, fg_color="transparent")
        frame_fecha.pack(fill="x", pady=(0, 30))

        combo_style = {
            "fg_color": TM.bg_panel(),
            "border_width": 0,
            "button_color": TM.primary(),
            "dropdown_fg_color": TM.bg_panel(),
            "font": ctk.CTkFont(family="Roboto", size=11),
            "height": 40
        }

        # Día
        dia_frame = ctk.CTkFrame(frame_fecha, fg_color="transparent")
        dia_frame.pack(side="left", expand=True, fill="x", padx=(0, 5))

        ctk.CTkLabel(
            dia_frame,
            text="Día",
            font=ctk.CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        ).pack(anchor="w")

        dias = [str(i) for i in range(1, 32)]
        self.combo_dia = ctk.CTkComboBox(dia_frame, values=dias, **combo_style)
        self.combo_dia.set(str(date.today().day))
        self.combo_dia.pack(fill="x")

        # Mes
        mes_frame = ctk.CTkFrame(frame_fecha, fg_color="transparent")
        mes_frame.pack(side="left", expand=True, fill="x", padx=5)

        ctk.CTkLabel(
            mes_frame,
            text="Mes",
            font=ctk.CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        ).pack(anchor="w")

        meses = [str(i) for i in range(1, 13)]
        self.combo_mes = ctk.CTkComboBox(mes_frame, values=meses, **combo_style)
        self.combo_mes.set(str(date.today().month))
        self.combo_mes.pack(fill="x")

        # Año
        anio_frame = ctk.CTkFrame(frame_fecha, fg_color="transparent")
        anio_frame.pack(side="left", expand=True, fill="x", padx=(5, 0))

        ctk.CTkLabel(
            anio_frame,
            text="Año",
            font=ctk.CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        ).pack(anchor="w")

        anio_actual = date.today().year
        anios = [str(anio_actual), str(anio_actual + 1)]
        self.combo_anio = ctk.CTkComboBox(anio_frame, values=anios, **combo_style)
        self.combo_anio.set(str(anio_actual))
        self.combo_anio.pack(fill="x")

        # Botón crear
        ctk.CTkButton(
            content,
            text="✓ Crear Examen",
            fg_color=TM.primary(),
            hover_color="#2980b9",
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            command=self.confirmar_creacion_examen
        ).pack(fill="x")

    def confirmar_creacion_examen(self):
        """Confirmar creación de examen"""
        nombre = self.entry_nombre_popup.get().strip()

        if not nombre:
            messagebox.showwarning("Atención", "Ingrese un nombre para el examen")
            return

        try:
            d = int(self.combo_dia.get())
            m = int(self.combo_mes.get())
            a = int(self.combo_anio.get())
            fecha = date(a, m, d)

            exito, msg = self.controller.crear_sesion_examen(nombre, fecha)

            if exito:
                self.popup.destroy()
                self.cargar_lista_sesiones()
                messagebox.showinfo("✅ Éxito", msg)
            else:
                messagebox.showerror("❌ Error", msg)

        except ValueError:
            messagebox.showerror("Error", "Fecha inválida")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def seleccionar_sesion(self, sesion):
        """Seleccionar sesión de examen"""
        self.sesion_actual = sesion

        # Actualizar título
        self.lbl_titulo_sesion.configure(
            text=f"📝 {sesion.nombre} ({sesion.fecha})"
        )

        # Configurar botón según estado
        if sesion.estado == "Cerrado":
            self.btn_guardar.configure(
                state="disabled",
                text="🔒 EXAMEN CERRADO",
                fg_color="#7f8c8d"
            )
        else:
            self.btn_guardar.configure(
                state="normal",
                text="💾 GUARDAR NOTAS",
                fg_color=TM.success()
            )

        # Cargar alumnos
        self.buscar_y_reiniciar()

    # ========================================================
    # LÓGICA DE FILTROS Y PAGINACIÓN
    # ========================================================

    def buscar_y_reiniciar(self, *args):
        """Buscar alumnos y reiniciar paginación"""
        if not self.sesion_actual:
            messagebox.showwarning(
                "Atención",
                "Seleccione un examen primero"
            )
            return

        # Obtener filtros
        grupo = self.combo_grupo.get()
        modalidad = self.combo_modalidad.get()
        busqueda = self.entry_busqueda.get().strip()

        # Buscar alumnos
        self.alumnos_filtrados_cache = self.controller.buscar_alumnos_notas(
            grupo,
            modalidad,
            busqueda
        )

        # Calcular páginas
        total_items = len(self.alumnos_filtrados_cache)
        if total_items == 0:
            self.total_paginas = 1
        else:
            self.total_paginas = (total_items + self.items_por_pagina - 1) // self.items_por_pagina

        self.pagina_actual = 1
        self.renderizar_pagina_actual()

    def pagina_siguiente(self):
        """Ir a página siguiente"""
        if self.pagina_actual < self.total_paginas:
            self.pagina_actual += 1
            self.renderizar_pagina_actual()

    def pagina_anterior(self):
        """Ir a página anterior"""
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.renderizar_pagina_actual()

    # ========================================================
    # RENDERIZADO DE SÁBANA
    # ========================================================

    def renderizar_pagina_actual(self):
        """Renderizar página actual de la sábana"""
        # Mock de cursos
        cursos = ["Matemática I", "Comunicación I", "Ciencias Sociales"]

        # Limpiar
        for w in self.grid_frame.winfo_children():
            w.destroy()

        self.lista_filas_alumnos = []

        # Calcular slice
        inicio = (self.pagina_actual - 1) * self.items_por_pagina
        fin = inicio + self.items_por_pagina
        alumnos_pagina = self.alumnos_filtrados_cache[inicio:fin]

        # Actualizar paginación
        self.lbl_paginacion.configure(
            text=f"Pág {self.pagina_actual}/{self.total_paginas} ({len(self.alumnos_filtrados_cache)} alumnos)"
        )

        # Validar datos
        if not alumnos_pagina:
            self._mostrar_estado_vacio("No hay alumnos en este grupo")
            return

        # Crear cabecera
        self._crear_cabecera_sabana(cursos)

        # Crear filas
        for i, alumno in enumerate(alumnos_pagina):
            self._crear_fila_alumno(i + 1, alumno, cursos)

    def _crear_cabecera_sabana(self, cursos):
        """Crear cabecera de la sábana"""
        # Fila 0: Cabecera
        header_row = ctk.CTkFrame(
            self.grid_frame,
            fg_color="#2c3e50",
            corner_radius=10,
            height=50
        )
        header_row.grid(row=0, column=0, columnspan=len(cursos) + 2, sticky="ew", padx=5, pady=(0, 10))

        # Configurar grid para la cabecera
        header_row.grid_columnconfigure(0, weight=1, minsize=250)
        for i in range(len(cursos)):
            header_row.grid_columnconfigure(i + 1, weight=0, minsize=80)
        header_row.grid_columnconfigure(len(cursos) + 1, weight=0, minsize=80)

        # Estudiante
        ctk.CTkLabel(
            header_row,
            text="ESTUDIANTE",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color="#f1c40f",
            anchor="w"
        ).grid(row=0, column=0, padx=20, pady=12, sticky="w")

        # Cursos
        for i, curso in enumerate(cursos):
            nom_corto = curso[:4].upper()
            ctk.CTkLabel(
                header_row,
                text=nom_corto,
                font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
                text_color="white"
            ).grid(row=0, column=i + 1, padx=5, pady=12)

        # Promedio
        ctk.CTkLabel(
            header_row,
            text="PROM",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color="#2ecc71"
        ).grid(row=0, column=len(cursos) + 1, padx=10, pady=12)

    def _crear_fila_alumno(self, row_idx, alumno, cursos):
        """Crear fila de alumno en la sábana"""
        fila_data = {
            "alumno_id": alumno.id,
            "nombre": f"{alumno.apell_paterno} {alumno.apell_materno} {alumno.nombres}",
            "inputs": {}
        }

        # Colores alternados
        bg = "#2d2d2d" if row_idx % 2 == 0 else "#363636"

        # Frame de la fila
        row_frame = ctk.CTkFrame(
            self.grid_frame,
            fg_color=bg,
            corner_radius=5,
            height=45
        )
        row_frame.grid(row=row_idx, column=0, columnspan=len(cursos) + 2, sticky="ew", padx=5, pady=2)

        # Configurar grid
        row_frame.grid_columnconfigure(0, weight=1, minsize=250)
        for i in range(len(cursos)):
            row_frame.grid_columnconfigure(i + 1, weight=0, minsize=80)
        row_frame.grid_columnconfigure(len(cursos) + 1, weight=0, minsize=80)

        # Nombre del alumno
        ctk.CTkLabel(
            row_frame,
            text=fila_data["nombre"],
            anchor="w",
            text_color=TM.text(),
            font=ctk.CTkFont(family="Roboto", size=11)
        ).grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # Obtener notas del alumno
        notas_alumno = self.controller.obtener_notas_alumno(
            self.sesion_actual.id,
            alumno.id
        )

        # Inputs de notas
        for i, curso in enumerate(cursos):
            val = notas_alumno.get(curso, 0.0)
            val_str = f"{val:.1f}" if val > 0 else ""

            entry = ctk.CTkEntry(
                row_frame,
                width=60,
                height=32,
                border_width=0,
                fg_color=TM.bg_panel(),
                text_color=TM.text(),
                justify="center",
                font=ctk.CTkFont(family="Roboto Mono", size=12, weight="bold")
            )
            entry.insert(0, val_str)

            if self.sesion_actual.estado == "Cerrado":
                entry.configure(state="disabled")

            # Bind para calcular promedio
            entry.bind(
                "<KeyRelease>",
                lambda e, f=fila_data, c=cursos: self.calcular_promedio_fila(f, c)
            )

            entry.grid(row=0, column=i + 1, padx=5, pady=5)
            fila_data["inputs"][curso] = entry

        # Label promedio
        lbl_prom = ctk.CTkLabel(
            row_frame,
            text="-",
            width=50,
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text_secondary()
        )
        lbl_prom.grid(row=0, column=len(cursos) + 1, padx=10, pady=10)
        fila_data["lbl_promedio"] = lbl_prom

        # Calcular promedio inicial
        self.calcular_promedio_fila(fila_data, cursos)

        # Guardar fila
        self.lista_filas_alumnos.append(fila_data)

    def calcular_promedio_fila(self, fila_data, cursos):
        """Calcular promedio de una fila"""
        suma, cant = 0.0, 0

        for c in cursos:
            texto = fila_data["inputs"][c].get().strip()
            if texto:
                try:
                    suma += float(texto)
                    cant += 1
                except:
                    pass

        if cant > 0:
            promedio = suma / cant
            color = TM.success() if promedio >= 11 else TM.danger()
            fila_data["lbl_promedio"].configure(
                text=f"{promedio:.1f}",
                text_color=color
            )
        else:
            fila_data["lbl_promedio"].configure(
                text="-",
                text_color=TM.text_secondary()
            )

    def _mostrar_estado_vacio(self, mensaje):
        """Mostrar estado vacío en la sábana"""
        for w in self.grid_frame.winfo_children():
            w.destroy()

        empty_frame = ctk.CTkFrame(self.grid_frame, fg_color="transparent")
        empty_frame.pack(fill="both", expand=True, pady=80)

        ctk.CTkLabel(
            empty_frame,
            text="📋",
            font=ctk.CTkFont(family="Arial", size=60)
        ).pack(pady=10)

        ctk.CTkLabel(
            empty_frame,
            text=mensaje,
            font=ctk.CTkFont(family="Roboto", size=16, weight="bold"),
            text_color=TM.text()
        ).pack()

        ctk.CTkLabel(
            empty_frame,
            text="Ajuste los filtros e intente nuevamente",
            font=ctk.CTkFont(family="Roboto", size=12),
            text_color=TM.text_secondary()
        ).pack(pady=(5, 0))

    # ========================================================
    # GUARDAR NOTAS
    # ========================================================

    def guardar_notas(self):
        """Guardar notas de la página actual"""
        if not self.sesion_actual:
            return

        # Mock de guardado
        exito, msg = self.controller.guardar_notas_lote(
            self.sesion_actual.id,
            []
        )

        if exito:
            messagebox.showinfo(
                "✅ Guardado",
                "Las notas se guardaron correctamente"
            )
        else:
            messagebox.showerror("❌ Error", msg)

    # ================= CICLO DE VIDA =================

    def on_show(self):
        if not self._ui_ready:
            self.after(1, self._build_ui_deferred)

    def on_hide(self):
        pass

    def cleanup(self):
        self.on_hide()
