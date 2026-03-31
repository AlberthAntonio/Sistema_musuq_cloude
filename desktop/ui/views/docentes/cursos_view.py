"""
Vista de Gestión de Cursos - ESTILO PREMIUM MEJORADO
Sistema Musuq Cloud
Panel dual: Catálogo de cursos + Malla curricular por grupos
"""

import customtkinter as ctk
from tkinter import messagebox
from customtkinter import CTkFont
import threading
import time

from controllers.academico_controller import AcademicoController
from styles import tabla_style as st
from core.theme_manager import ThemeManager as TM
from utils.perf_utils import get_logger

logger = get_logger(__name__)


class CursosView(ctk.CTkFrame):
    """
    Vista profesional para gestión de cursos y malla curricular.
    Características: Catálogo de cursos, asignación por grupos, vista tipo chips
    """

    def __init__(self, parent, auth_client=None):
        super().__init__(parent, fg_color="transparent")
        self._auth_token = auth_client.token if auth_client else ""
        self.controller = None
        self.grupos_base = ["A", "B", "C", "D"]
        self.grupo_todos = "TODOS"

        # Cache de datos para filtrado rápido
        self.todos_los_cursos = []
        self._malla_cache = {}  # {grupo: [items]}
        self._cache_ts = 0  # Timestamp del último fetch
        self._cache_ttl = 60  # Segundos de validez del cache
        self._request_id = 0
        self._ui_ready = False
        self._loading_frame = None

        self._show_loading_state()
        self.after(1, self._build_ui_deferred)

    def _show_loading_state(self):
        """Placeholder inicial mientras se crea la vista."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._loading_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._loading_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        ctk.CTkLabel(
            self._loading_frame,
            text="Cargando gestion de cursos...",
            font=CTkFont(family="Roboto", size=14, weight="bold"),
            text_color=TM.text_secondary(),
        ).pack(expand=True)

    def _build_ui_deferred(self):
        """Construye widgets y dispara carga inicial fuera del constructor."""
        if self._ui_ready:
            return

        if self.controller is None:
            self.controller = AcademicoController(self._auth_token)

        if self._loading_frame is not None:
            self._loading_frame.destroy()
            self._loading_frame = None

        self.create_widgets()
        self._cargar_todo_async()
        self._ui_ready = True

    def create_widgets(self):
        # Layout principal con grid
        # 30% catálogo, 70% malla
        self.grid_columnconfigure(0, weight=3, minsize=350)
        self.grid_columnconfigure(1, weight=7)
        self.grid_rowconfigure(0, weight=1)

        # ============================
        # PANEL IZQUIERDO: CATÁLOGO
        # ============================
        self._crear_panel_catalogo()

        # ============================
        # PANEL DERECHO: MALLA CURRICULAR
        # ============================
        self._crear_panel_malla()

    def _crear_panel_catalogo(self):
        """Crear panel izquierdo con catálogo de cursos"""
        self.panel_izq = ctk.CTkFrame(
            self,
            fg_color=TM.bg_panel(),
            corner_radius=0
        )
        self.panel_izq.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)

        # Header del panel
        header = ctk.CTkFrame(self.panel_izq, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))

        # Icono grande
        ctk.CTkLabel(
            header,
            text="📚",
            font=CTkFont(family="Arial", size=50)
        ).pack(pady=(0, 10))

        # Título
        ctk.CTkLabel(
            header,
            text="CATÁLOGO DE CURSOS",
            font=CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=TM.text()
        ).pack()

        # Separador
        ctk.CTkFrame(
            self.panel_izq,
            height=2,
            fg_color="#404040"
        ).pack(fill="x", padx=20, pady=20)

        # Sección crear curso
        self._crear_seccion_nuevo_curso()

        # Sección buscador
        self._crear_seccion_buscador()

        # Sección lista de cursos
        self._crear_seccion_lista()

    def _crear_seccion_nuevo_curso(self):
        """Crear sección para nuevo curso"""
        # Label sección
        ctk.CTkLabel(
            self.panel_izq,
            text="Crear Nuevo Curso",
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 10))

        # Frame de creación
        self.frame_nuevo = ctk.CTkFrame(
            self.panel_izq,
            fg_color=TM.bg_card(),
            height=45,
            corner_radius=10
        )
        self.frame_nuevo.pack(fill="x", padx=20, pady=(0, 15))
        self.frame_nuevo.pack_propagate(False)

        # Entry
        self.entry_nuevo_curso = ctk.CTkEntry(
            self.frame_nuevo,
            placeholder_text="Nombre del curso...",
            border_width=0,
            fg_color="transparent",
            text_color=TM.text(),
            font=CTkFont(family="Roboto", size=12),
            height=45
        )
        self.entry_nuevo_curso.pack(side="left", fill="both", expand=True, padx=(15, 5))
        self.entry_nuevo_curso.bind("<Return>", lambda e: self.crear_curso_global())

        # Botón crear
        btn_add = ctk.CTkButton(
            self.frame_nuevo,
            text="CREAR",
            width=70,
            height=32,
            fg_color=TM.primary(),
            hover_color="#2980b9",
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            corner_radius=8,
            command=self.crear_curso_global
        )
        btn_add.pack(side="right", padx=8)

    def _crear_seccion_buscador(self):
        """Crear sección de búsqueda"""
        # Label sección
        ctk.CTkLabel(
            self.panel_izq,
            text="Buscar en Catálogo",
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 10))

        # Frame buscador
        frame_search = ctk.CTkFrame(
            self.panel_izq,
            fg_color=TM.bg_card(),
            height=45,
            corner_radius=10
        )
        frame_search.pack(fill="x", padx=20, pady=(0, 15))
        frame_search.pack_propagate(False)

        # Icono
        ctk.CTkLabel(
            frame_search,
            text="🔍",
            font=CTkFont(family="Arial", size=16),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(15, 5))

        # Entry
        self.entry_buscar = ctk.CTkEntry(
            frame_search,
            placeholder_text="Filtrar lista de cursos...",
            border_width=0,
            fg_color="transparent",
            text_color=TM.text(),
            font=CTkFont(family="Roboto", size=12)
        )
        self.entry_buscar.pack(side="left", fill="both", expand=True, padx=(0, 15))
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_catalogo)

    def _crear_seccion_lista(self):
        """Crear sección de lista de cursos"""
        # Label sección
        ctk.CTkLabel(
            self.panel_izq,
            text="Lista de Cursos Disponibles",
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 10))

        # Scroll de cursos
        self.scroll_cursos = ctk.CTkScrollableFrame(
            self.panel_izq,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.scroll_cursos.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Estado inicial vacío
        self._mostrar_estado_vacio_catalogo()

    def _crear_panel_malla(self):
        """Crear panel derecho con malla curricular"""
        self.panel_der = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )
        self.panel_der.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        # Header del panel
        header = ctk.CTkFrame(
            self.panel_der,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=90
        )
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=25, pady=15)

        # Título principal
        ctk.CTkLabel(
            header_content,
            text="🎓 MALLA CURRICULAR",
            font=CTkFont(family="Roboto", size=22, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        ).pack(anchor="w")

        # Subtítulo
        ctk.CTkLabel(
            header_content,
            text="Selecciona un grupo para gestionar sus materias",
            font=CTkFont(family="Roboto", size=12),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(anchor="w", pady=(5, 0))

        # Pestañas de grupos
        self.tab_grupos = ctk.CTkTabview(
            self.panel_der,
            fg_color=TM.bg_panel(),
            segmented_button_fg_color="#2b2b2b",
            segmented_button_selected_color=TM.warning(),
            segmented_button_selected_hover_color="#d35400",
            segmented_button_unselected_color="#2b2b2b",
            segmented_button_unselected_hover_color="#34495e",
            text_color=TM.text(),
            corner_radius=10
        )
        self.tab_grupos.pack(fill="both", expand=True)

        # Crear tabs para cada grupo
        self.tabs_data = {}
        for grupo in [*self.grupos_base, self.grupo_todos]:
            tab = self.tab_grupos.add(grupo)

            # Scroll container para los CHIPS
            scroll = ctk.CTkScrollableFrame(
                tab,
                fg_color="transparent"
            )
            scroll.pack(fill="both", expand=True, padx=10, pady=10)

            # Guardamos la referencia
            self.tabs_data[grupo] = scroll

    # ========================================================
    # LÓGICA DEL CATÁLOGO
    # ========================================================

    def crear_curso_global(self):
        """Crear un nuevo curso en el catálogo"""
        nombre = self.entry_nuevo_curso.get().strip()

        if not nombre:
            messagebox.showwarning("Atención", "Ingrese el nombre del curso")
            return

        exito, msg = self.controller.crear_curso(nombre)

        if exito:
            self.entry_nuevo_curso.delete(0, 'end')
            self.cargar_catalogo_bd()
            messagebox.showinfo("Éxito", msg)
        else:
            messagebox.showerror("Error", msg)

    def cargar_catalogo_bd(self):
        """Cargar catálogo desde base de datos (background thread)"""
        self._request_id += 1
        req_id = self._request_id

        # Mostrar loading en lista de cursos
        for w in self.scroll_cursos.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.scroll_cursos,
            text="⏳ Cargando catálogo...",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(pady=20)

        def _hilo():
            cursos = self.controller.obtener_catalogo()
            if self.winfo_exists() and req_id == self._request_id:
                self.after(0, lambda: self._aplicar_catalogo(cursos))

        threading.Thread(target=_hilo, daemon=True).start()

    def _aplicar_catalogo(self, cursos):
        """Aplicar catálogo a la UI (hilo principal)"""
        if not self.winfo_exists():
            return
        self.todos_los_cursos = cursos
        self._cache_ts = time.time()
        self.filtrar_catalogo()

    def filtrar_catalogo(self, event=None):
        """Filtrar lista de cursos visualmente"""
        texto = self.entry_buscar.get().lower()

        # Limpiar UI
        for w in self.scroll_cursos.winfo_children():
            w.destroy()

        # Filtrar
        filtrados = [c for c in self.todos_los_cursos if texto in c['nombre'].lower()]

        if not filtrados:
            self._mostrar_estado_vacio_catalogo("No se encontraron cursos")
            return

        # Dibujar items
        for curso in filtrados:
            self._dibujar_item_catalogo(curso)

    def _dibujar_item_catalogo(self, curso):
        """Dibujar un item del catálogo"""
        # Frame del item
        item_frame = ctk.CTkFrame(
            self.scroll_cursos,
            fg_color="transparent"
        )
        item_frame.pack(fill="x", pady=1)

        # Frame interno con hover
        inner_frame = ctk.CTkFrame(
            item_frame,
            fg_color="#2b2b2b",
            corner_radius=8,
            height=45
        )
        inner_frame.pack(fill="x", pady=1)
        inner_frame.pack_propagate(False)

        # Nombre del curso
        ctk.CTkLabel(
            inner_frame,
            text=curso['nombre'],
            anchor="w",
            text_color=TM.text(),
            font=CTkFont(family="Roboto", size=12)
        ).pack(side="left", padx=15, fill="both", expand=True)

        # Botón agregar
        btn = ctk.CTkButton(
            inner_frame,
            text="➕",
            width=35,
            height=28,
            fg_color=TM.success(),
            hover_color="#27ae60",
            font=CTkFont(family="Arial", size=14),
            corner_radius=6,
            command=lambda c=curso: self.agregar_al_grupo_actual(c)
        )
        btn.pack(side="right", padx=(4, 8))

        # Botón eliminar del catálogo
        btn_del_catalogo = ctk.CTkButton(
            inner_frame,
            text="🗑",
            width=35,
            height=28,
            fg_color="transparent",
            hover_color=TM.danger(),
            text_color="#e74c3c",
            font=CTkFont(family="Arial", size=13),
            corner_radius=6,
            command=lambda c=curso: self.eliminar_curso_catalogo(c)
        )
        btn_del_catalogo.pack(side="right", padx=(0, 4))

    def eliminar_curso_catalogo(self, curso):
        """Eliminar curso del catálogo general"""
        if not isinstance(curso, dict):
            messagebox.showerror("Error", "No se pudo leer el curso seleccionado")
            return

        curso_id = curso.get("id")
        nombre = curso.get("nombre", "este curso")

        if not curso_id:
            messagebox.showerror("Error", "No se encontró el identificador del curso")
            return

        confirmado = messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar '{nombre}' del catálogo?\n\n"
            "Esta acción también quitará sus asignaciones de malla donde corresponda."
        )
        if not confirmado:
            return

        exito, msg = self.controller.eliminar_curso(curso_id)
        if exito:
            self.cargar_catalogo_bd()
            self.cargar_mallas()
            messagebox.showinfo("Éxito", msg)
        else:
            messagebox.showerror("Error", msg)

    def _mostrar_estado_vacio_catalogo(self, mensaje="Sin cursos registrados"):
        """Mostrar estado vacío en catálogo"""
        for w in self.scroll_cursos.winfo_children():
            w.destroy()

        empty_frame = ctk.CTkFrame(self.scroll_cursos, fg_color="transparent")
        empty_frame.pack(fill="both", expand=True, pady=40)

        ctk.CTkLabel(
            empty_frame,
            text="📚",
            font=CTkFont(family="Arial", size=50)
        ).pack(pady=10)

        ctk.CTkLabel(
            empty_frame,
            text=mensaje,
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text()
        ).pack()

        ctk.CTkLabel(
            empty_frame,
            text="Crea tu primer curso arriba",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(pady=(5, 0))

    # ========================================================
    # LÓGICA DE MALLAS (CHIPS)
    # ========================================================

    def cargar_mallas(self):
        """Recargar chips de todos los grupos (background thread)"""
        self._request_id += 1
        req_id = self._request_id

        # Mostrar loading en cada tab
        for grupo, scroll_widget in self.tabs_data.items():
            for w in scroll_widget.winfo_children():
                w.destroy()
            ctk.CTkLabel(
                scroll_widget,
                text="⏳ Cargando malla...",
                font=CTkFont(family="Roboto", size=11),
                text_color=TM.text_secondary()
            ).pack(pady=20)

        def _hilo():
            # Cargar malla de cada grupo base
            malla_data = {}
            for grupo in self.grupos_base:
                malla_data[grupo] = self.controller.obtener_malla_grupo(grupo)

            # Construir TODOS desde cache local (sin roundtrips extra)
            malla_data[self.grupo_todos] = self._build_todos_from_cache(malla_data)

            if self.winfo_exists() and req_id == self._request_id:
                self.after(0, lambda: self._aplicar_mallas(malla_data))

        threading.Thread(target=_hilo, daemon=True).start()

    def _build_todos_from_cache(self, malla_data):
        """Construir vista TODOS desde datos ya cargados (sin roundtrips extra)"""
        claves_por_grupo = []
        nombres_por_clave = {}

        for grupo in self.grupos_base:
            claves_grupo = set()
            for item in malla_data.get(grupo, []):
                curso_id = item.get("curso_id")
                if curso_id is None:
                    curso_id = item.get("id")
                clave = curso_id if curso_id is not None else item.get("nombre", "").strip().lower()

                if clave is None:
                    continue

                claves_grupo.add(clave)
                if clave not in nombres_por_clave:
                    nombres_por_clave[clave] = item.get("nombre", "Curso sin nombre")

            claves_por_grupo.append(claves_grupo)

        if not claves_por_grupo:
            return []

        claves_comunes = set.intersection(*claves_por_grupo)
        return [
            {"nombre": nombres_por_clave.get(clave, "Curso sin nombre"), "solo_lectura": True}
            for clave in claves_comunes
        ]

    def _aplicar_mallas(self, malla_data):
        """Aplicar datos de malla a los tabs (hilo principal)"""
        if not self.winfo_exists():
            return

        self._malla_cache = malla_data

        for grupo, scroll_widget in self.tabs_data.items():
            # Limpiar
            for w in scroll_widget.winfo_children():
                w.destroy()

            asignaciones = malla_data.get(grupo, [])

            if not asignaciones:
                self._mostrar_estado_vacio_malla(scroll_widget, grupo)
                continue

            self._dibujar_chips_grid(scroll_widget, asignaciones)

    def _cargar_todo_async(self):
        """Carga inicial: catálogo y mallas en paralelo"""
        self._request_id += 1
        req_id = self._request_id

        # Loading en catálogo
        for w in self.scroll_cursos.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.scroll_cursos,
            text="⏳ Cargando...",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(pady=20)

        def _hilo():
            cursos = self.controller.obtener_catalogo()
            malla_data = {}
            for grupo in self.grupos_base:
                malla_data[grupo] = self.controller.obtener_malla_grupo(grupo)
            malla_data[self.grupo_todos] = self._build_todos_from_cache(malla_data)

            if self.winfo_exists() and req_id == self._request_id:
                self.after(0, lambda: self._aplicar_carga_inicial(cursos, malla_data))

        threading.Thread(target=_hilo, daemon=True).start()

    def _aplicar_carga_inicial(self, cursos, malla_data):
        """Aplicar carga inicial completa"""
        if not self.winfo_exists():
            return
        self.todos_los_cursos = cursos
        self._cache_ts = time.time()
        self.filtrar_catalogo()
        self._aplicar_mallas(malla_data)

    def _dibujar_chips_grid(self, parent, asignaciones):
        """Dibujar chips en layout grid"""
        # Frame interno para el grid
        grid_frame = ctk.CTkFrame(parent, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, pady=10)

        # 3 columnas
        col_count = 3

        for i, item in enumerate(asignaciones):
            row = i // col_count
            col = i % col_count
            self._dibujar_chip(grid_frame, item, row, col)

        # Configurar peso de columnas
        for i in range(col_count):
            grid_frame.grid_columnconfigure(i, weight=1)

    def _dibujar_chip(self, parent, curso_item, r, c):
        """Crear una tarjeta chip para el curso"""
        # Chip frame
        chip = ctk.CTkFrame(
            parent,
            fg_color="#34495e",
            corner_radius=12,
            border_width=2,
            border_color=TM.primary()
        )
        chip.grid(row=r, column=c, padx=8, pady=8, sticky="ew")

        # Container interno
        content = ctk.CTkFrame(chip, fg_color="transparent")
        content.pack(fill="x", padx=12, pady=10)

        # Nombre del curso
        nombre = curso_item['nombre']
        nom_display = (nombre[:22] + '...') if len(nombre) > 25 else nombre

        ctk.CTkLabel(
            content,
            text=nom_display,
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color="white",
            anchor="w"
        ).pack(side="left", fill="x", expand=True)

        # Botón eliminar
        if not curso_item.get("solo_lectura", False):
            malla_id = self._obtener_malla_id(curso_item)
            if malla_id is None:
                return

            btn_del = ctk.CTkButton(
                content,
                text="✕",
                width=28,
                height=28,
                fg_color="transparent",
                hover_color=TM.danger(),
                text_color="#e74c3c",
                corner_radius=8,
                font=CTkFont(family="Arial", size=14, weight="bold"),
                command=lambda m=malla_id: self.quitar_curso(m)
            )
            btn_del.pack(side="right")

    def _obtener_malla_id(self, curso_item):
        """Retornar id de asignación de malla con tolerancia de claves."""
        return (
            curso_item.get("malla_id")
            or curso_item.get("id_malla")
            or curso_item.get("asignacion_id")
            or curso_item.get("id")
        )


    def _mostrar_estado_vacio_malla(self, parent, grupo):
        """Mostrar estado vacío en malla"""
        empty_frame = ctk.CTkFrame(parent, fg_color="transparent")
        empty_frame.pack(fill="both", expand=True, pady=80)

        if grupo == self.grupo_todos:
            ctk.CTkLabel(
                empty_frame,
                text="📋",
                font=CTkFont(family="Arial", size=70)
            ).pack(pady=15)

            ctk.CTkLabel(
                empty_frame,
                text="Sin cursos en la vista TODOS",
                font=CTkFont(family="Roboto", size=15, weight="bold"),
                text_color=TM.text()
            ).pack()

            ctk.CTkLabel(
                empty_frame,
                text="Agrega cursos aquí para asignarlos en A, B, C y D automáticamente",
                font=CTkFont(family="Roboto", size=12),
                text_color=TM.text_secondary()
            ).pack(pady=(8, 0))
            return

        ctk.CTkLabel(
            empty_frame,
            text="📋",
            font=CTkFont(family="Arial", size=70)
        ).pack(pady=15)

        ctk.CTkLabel(
            empty_frame,
            text=f"Sin cursos asignados al Grupo {grupo}",
            font=CTkFont(family="Roboto", size=15, weight="bold"),
            text_color=TM.text()
        ).pack()

        ctk.CTkLabel(
            empty_frame,
            text="Usa el botón ➕ del catálogo para agregar cursos",
            font=CTkFont(family="Roboto", size=12),
            text_color=TM.text_secondary()
        ).pack(pady=(8, 0))

    # ========================================================
    # ACCIONES
    # ========================================================

    def agregar_al_grupo_actual(self, curso):
        """Añadir curso al grupo activo"""
        grupo_activo = self.tab_grupos.get()
        curso_id = curso.get("id") if isinstance(curso, dict) else curso

        if not curso_id:
            messagebox.showerror("Error", "No se pudo identificar el curso seleccionado")
            return

        if grupo_activo == self.grupo_todos:
            errores = []
            hubo_exito = False

            for grupo in self.grupos_base:
                exito, msg = self.controller.agregar_curso_a_grupo(grupo, curso_id)
                if exito:
                    hubo_exito = True
                else:
                    errores.append(f"{grupo}: {msg}")

            if hubo_exito:
                self.cargar_mallas()

            if errores:
                messagebox.showwarning("Aviso", "No se pudo asignar en todos los grupos:\n" + "\n".join(errores))
            else:
                messagebox.showinfo("Éxito", "Curso asignado en A, B, C y D")
            return

        exito, msg = self.controller.agregar_curso_a_grupo(grupo_activo, curso_id)

        if exito:
            self.cargar_mallas()
        else:
            messagebox.showwarning("Aviso", msg)

    def quitar_curso(self, malla_id):
        """Quitar curso del grupo"""
        if not messagebox.askyesno("Confirmar", "¿Quitar esta materia del grupo?"):
            return

        exito, msg = self.controller.quitar_curso_de_grupo(malla_id)

        if exito:
            self.cargar_mallas()
        else:
            messagebox.showerror("Error", msg)

    # ── Lifecycle ──
    def on_show(self):
        if not self._ui_ready:
            self.after(1, self._build_ui_deferred)

    def on_hide(self):
        pass

    def cleanup(self):
        pass
