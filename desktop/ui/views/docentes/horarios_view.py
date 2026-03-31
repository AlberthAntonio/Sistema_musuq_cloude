"""
Vista de Gestión de Horarios – REDISEÑADA
Sistema Musuq Cloud
Flujo: Seleccionar Aula → Gestionar horario de esa aula por grupo
"""

import customtkinter as ctk
from tkinter import messagebox
from customtkinter import CTkFont
import threading

from controllers.academico_controller import AcademicoController
from controllers.docentes_controller import DocentesController
from controllers.aulas_controller import AulasController
from ui.views.docentes.dialogo_horario import DialogoHorario
from core.theme_manager import ThemeManager as TM
from utils.perf_utils import get_logger

logger = get_logger(__name__)

_COLOR_MODALIDAD = {
    "COLEGIO":   "#3498db",
    "VIRTUAL":   "#9b59b6",
    "MIXTA":     "#f39c12",
    "TALLER":    "#e67e22",
    "AUDITORIO": "#16a085",
}

_SLOT_ROW_HEIGHT = 60


class HorariosView(ctk.CTkFrame):
    """
    Vista de horarios con selector de aula.

    Flujo:
      1. Panel izquierdo → el usuario elige un aula.
      2. Panel derecho  → muestra la tabla horaria de esa aula
         filtrada por grupo y turno.
      3. Celda vacía    → abre DialogoHorario con el aula pre-cargada.
    """

    def __init__(self, parent, auth_client=None):
        super().__init__(parent, fg_color="transparent")

        self._auth_token = auth_client.token if auth_client else ""
        self.controller = None
        self.docentes_controller = None
        self.aulas_controller = None

        # ── Estado ────────────────────────────────────────────
        self.aula_seleccionada: dict | None = None
        self.grupo_actual   = "A"
        self.turno_actual   = "MANANA"
        self.periodo_actual = "2026-I"
        self.horario_data: dict = {}
        self.bloques_dinamicos: list = []
        self.todas_las_aulas: list = []
        self._aulas_request_id = 0
        self._horario_request_id = 0
        self._ui_ready = False
        self._loading_frame = None

        # ── Layout 33 / 67 ────────────────────────────────────
        self.grid_columnconfigure(0, weight=15, minsize=280)
        self.grid_columnconfigure(1, weight=85)
        self.grid_rowconfigure(0, weight=1)

        self._show_loading_state()
        self.after(1, self._build_ui_deferred)

    def _show_loading_state(self):
        """Renderiza un placeholder liviano antes de construir toda la vista."""
        self._loading_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._loading_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=20, pady=20)
        ctk.CTkLabel(
            self._loading_frame,
            text="Cargando gestion de horarios...",
            font=CTkFont(family="Roboto", size=14, weight="bold"),
            text_color=TM.text_secondary(),
        ).pack(expand=True)

    def _build_ui_deferred(self):
        """Construye la UI y dispara cargas remotas fuera del constructor."""
        if self._ui_ready:
            return

        # Inicializacion perezosa: evita costo de crear clientes HTTP en show_view.
        if self.controller is None:
            self.controller = AcademicoController(self._auth_token)
        if self.docentes_controller is None:
            self.docentes_controller = DocentesController(self._auth_token)
        if self.aulas_controller is None:
            self.aulas_controller = AulasController(self._auth_token)

        if self._loading_frame is not None:
            self._loading_frame.destroy()
            self._loading_frame = None

        self._crear_panel_aulas()
        self._crear_panel_horario()
        self._cargar_aulas_async()
        self._ui_ready = True

    # ═══════════════════════════════════════════════════════════
    #  PANEL IZQUIERDO – SELECTOR DE AULAS
    # ═══════════════════════════════════════════════════════════

    def _crear_panel_aulas(self):
        self.panel_aulas = ctk.CTkFrame(
            self, fg_color=TM.bg_panel(), corner_radius=0
        )
        self.panel_aulas.grid(row=0, column=0, sticky="nsew", padx=(20, 8), pady=20)

        # ── Encabezado ────────────────────────────────────────
        ctk.CTkLabel(
            self.panel_aulas, text="🏫",
            font=CTkFont(family="Arial", size=44)
        ).pack(pady=(18, 4))

        ctk.CTkLabel(
            self.panel_aulas,
            text="SELECCIONAR AULA",
            font=CTkFont(family="Roboto", size=15, weight="bold"),
            text_color=TM.text()
        ).pack()

        ctk.CTkLabel(
            self.panel_aulas,
            text="Elige el aula para gestionar su horario",
            font=CTkFont(family="Roboto", size=9),
            text_color=TM.text_secondary()
        ).pack(pady=(2, 14))

        # ── Buscador ──────────────────────────────────────────
        fr_search = ctk.CTkFrame(
            self.panel_aulas, fg_color=TM.bg_card(), height=38, corner_radius=8
        )
        fr_search.pack(fill="x", padx=15, pady=(0, 10))
        fr_search.pack_propagate(False)

        ctk.CTkLabel(
            fr_search, text="🔍",
            font=CTkFont(family="Arial", size=13),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(10, 3))

        self.entry_buscar_aula = ctk.CTkEntry(
            fr_search,
            placeholder_text="Buscar aula...",
            border_width=0,
            fg_color="transparent",
            text_color=TM.text(),
            font=CTkFont(family="Roboto", size=11)
        )
        self.entry_buscar_aula.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self.entry_buscar_aula.bind("<KeyRelease>", self._filtrar_aulas)

        # ── Lista scrollable ──────────────────────────────────
        self.scroll_aulas = ctk.CTkScrollableFrame(
            self.panel_aulas, fg_color="transparent"
        )
        self.scroll_aulas.pack(fill="both", expand=True, padx=5, pady=(0, 8))

        # ── Botón recargar ────────────────────────────────────
        ctk.CTkButton(
            self.panel_aulas,
            text="🔄  Recargar Aulas",
            height=34,
            font=CTkFont(family="Roboto", size=11),
            fg_color=TM.bg_card(),
            hover_color="#34495e",
            text_color=TM.text_secondary(),
            corner_radius=8,
            command=self.cargar_aulas
        ).pack(fill="x", padx=15, pady=(0, 15))

    # ═══════════════════════════════════════════════════════════
    #  PANEL DERECHO – TABLA DE HORARIOS
    # ═══════════════════════════════════════════════════════════

    def _crear_panel_horario(self):
        self.panel_horario = ctk.CTkFrame(self, fg_color="transparent")
        self.panel_horario.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        self._crear_header_horario()

        # Tabla scrollable
        self.fr_tabla = ctk.CTkScrollableFrame(
            self.panel_horario, fg_color="transparent"
        )
        self.fr_tabla.pack(fill="both", expand=True, pady=(0, 8))

        # Barra de ayuda inferior
        self._crear_barra_ayuda()

        # Placeholder inicial
        self._mostrar_placeholder()

    def _crear_header_horario(self):
        fr = ctk.CTkFrame(
            self.panel_horario, fg_color=TM.bg_card(), corner_radius=10, height=88
        )
        fr.pack(fill="x", pady=(0, 10))
        fr.pack_propagate(False)

        cnt = ctk.CTkFrame(fr, fg_color="transparent")
        cnt.pack(fill="both", expand=True, padx=20, pady=12)

        # Izquierda: título dinámico
        left = ctk.CTkFrame(cnt, fg_color="transparent")
        left.pack(side="left", fill="y")

        self.lbl_titulo = ctk.CTkLabel(
            left,
            text="⏰  HORARIOS",
            font=CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=TM.text()
        )
        self.lbl_titulo.pack(anchor="w")

        self.lbl_subtitulo = ctk.CTkLabel(
            left,
            text="← Selecciona un aula del panel izquierdo",
            font=CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        )
        self.lbl_subtitulo.pack(anchor="w", pady=(2, 0))

        # Centro: filtros Grupo / Turno
        fr_filtros = ctk.CTkFrame(cnt, fg_color="transparent")
        fr_filtros.pack(side="left", padx=30)

        ctk.CTkLabel(
            fr_filtros, text="Grupo:",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(0, 6))

        self.cb_grupo = ctk.CTkComboBox(
            fr_filtros,
            values=["A", "B", "C", "D"],
            width=80,
            fg_color=TM.bg_card(),
            border_color="#404040",
            button_color=TM.primary(),
            button_hover_color="#2980b9",
            dropdown_fg_color=TM.bg_card(),
            font=CTkFont(family="Roboto", size=11),
            command=self._cambiar_filtro,
            state="disabled"
        )
        self.cb_grupo.set(self.grupo_actual)
        self.cb_grupo.pack(side="left", padx=(0, 18))

        ctk.CTkLabel(
            fr_filtros, text="Turno:",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(0, 6))

        self.cb_turno = ctk.CTkComboBox(
            fr_filtros,
            values=["MAÑANA", "TARDE"],
            width=110,
            fg_color=TM.bg_card(),
            border_color="#404040",
            button_color=TM.primary(),
            button_hover_color="#2980b9",
            dropdown_fg_color=TM.bg_card(),
            font=CTkFont(family="Roboto", size=11),
            command=self._cambiar_filtro,
            state="disabled"
        )
        self.cb_turno.set("MAÑANA")
        self.cb_turno.pack(side="left")

        # Derecha: acciones
        ctk.CTkButton(
            cnt,
            text="🧩 Nuevo Bloque",
            fg_color=TM.primary(),
            hover_color="#2980b9",
            width=130, height=36,
            corner_radius=8,
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            command=self._abrir_dialogo_bloque_personalizado,
        ).pack(side="right", padx=(0, 8))

        ctk.CTkButton(
            cnt,
            text="🔄 Actualizar",
            fg_color=TM.warning(),
            hover_color="#d35400",
            width=120, height=36,
            corner_radius=8,
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            command=self.cargar_horario
        ).pack(side="right")

    def _crear_barra_ayuda(self):
        fr = ctk.CTkFrame(
            self.panel_horario, fg_color=TM.bg_card(), corner_radius=10, height=50
        )
        fr.pack(fill="x")
        fr.pack_propagate(False)

        cnt = ctk.CTkFrame(fr, fg_color="transparent")
        cnt.pack(fill="both", expand=True, padx=18, pady=14)

        ctk.CTkLabel(
            cnt, text="💡  Ayuda:",
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.warning()
        ).pack(side="left")

        ctk.CTkLabel(
            cnt,
            text="  ➕ Agregar clase en celda vacía  •  ✏️ Editar  •  ❌ Eliminar",
            font=CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(5, 0))

    def _crear_celda(self, parent, bloque: dict | None, dia_num: int, h_ini: str, h_fin: str) -> ctk.CTkFrame:
        if not bloque:
            return self._celda_vacia(parent, dia_num, h_ini, h_fin)

        tipo = (bloque.get("tipo_bloque") or "CLASE").upper()
        if tipo == "CLASE":
            if bloque.get("id") or bloque.get("curso_id") or bloque.get("curso_nombre"):
                return self._celda_con_clase(parent, bloque)
            return self._celda_clase_sin_asignar(parent, bloque)
        if tipo == "RECREO":
            return self._celda_tipo_bloque(parent, bloque, "☕", "RECREO", "#7f5a00")
        return self._celda_tipo_bloque(parent, bloque, "🟫", "LIBRE", "#4a4a4a")

    def _materia_color(self, nombre_curso: str) -> str:
        palette = [
            "#4F8CFF", "#00B894", "#F4B400", "#E17055", "#A66CFF", "#00A8CC", "#D63031",
        ]
        base = (nombre_curso or "Clase").strip().lower()
        idx = sum(ord(ch) for ch in base) % len(palette)
        return palette[idx]

    def _is_descendant_widget(self, widget, ancestor) -> bool:
        if widget is None or ancestor is None:
            return False
        current = widget
        while current is not None:
            if current == ancestor:
                return True
            try:
                parent_name = current.winfo_parent()
                if not parent_name:
                    break
                current = current.nametowidget(parent_name)
            except Exception:
                break
        return False

    def _wire_hover_actions(self, celda, actions_frame) -> None:
        state = {"hide_job": None}

        def show_actions(_event=None):
            if state["hide_job"] is not None:
                try:
                    celda.after_cancel(state["hide_job"])
                except Exception:
                    pass
                state["hide_job"] = None
            actions_frame.place(in_=celda, relx=1.0, x=-8, y=8, anchor="ne")

        def hide_actions(_event=None):
            def _do_hide():
                x = celda.winfo_pointerx()
                y = celda.winfo_pointery()
                hovered = celda.winfo_containing(x, y)
                if not self._is_descendant_widget(hovered, celda):
                    actions_frame.place_forget()

            state["hide_job"] = celda.after(120, _do_hide)

        def _bind_recursive(widget):
            widget.bind("<Enter>", show_actions)
            widget.bind("<Leave>", hide_actions)
            for child in widget.winfo_children():
                _bind_recursive(child)

        _bind_recursive(celda)
        _bind_recursive(actions_frame)

    def _celda_con_clase(self, parent, clase: dict) -> ctk.CTkFrame:
        nombre_curso = clase.get("nombre_curso") or clase.get("curso_nombre") or "Clase"
        nombre_docente = clase.get("nombre_docente") or clase.get("docente_nombre") or "Sin docente"
        color_acento = self._materia_color(nombre_curso)

        celda = ctk.CTkFrame(
            parent,
            fg_color="#161B22",
            corner_radius=10,
            border_width=1,
            border_color="#2D333B",
            height=_SLOT_ROW_HEIGHT,
        )
        celda.grid_propagate(False)
        celda.pack_propagate(False)

        # Borde izquierdo grueso con color representativo de la materia
        barra = ctk.CTkFrame(celda, fg_color=color_acento, width=4, corner_radius=0)
        barra.pack(side="left", fill="y")

        cuerpo = ctk.CTkFrame(celda, fg_color="#1C2128", corner_radius=8)
        cuerpo.pack(side="left", fill="both", expand=True, padx=(0, 0), pady=0)
        cuerpo.pack_propagate(False)

        # Contenido alineado arriba con padding uniforme
        fc = ctk.CTkFrame(cuerpo, fg_color="transparent")
        fc.pack(fill="both", expand=True, padx=5, pady=5, anchor="n")

        ctk.CTkLabel(
            fc, text=nombre_curso,
            font=CTkFont(family="Roboto", size=10, weight="bold"),
            text_color="#F0F6FC", wraplength=145,
            justify="left", anchor="w"
        ).pack(fill="x", anchor="nw")

        ctk.CTkLabel(
            fc, text=f"👤 {nombre_docente}",
            font=CTkFont(family="Roboto", size=7),
            text_color="#9DA7B3",
            justify="left", anchor="w"
        ).pack(fill="x", anchor="nw", pady=(0, 0))

        # Acciones pequeñas, solo visibles en hover
        fr_btns = ctk.CTkFrame(celda, fg_color="transparent")
        fr_btns.place_forget()

        ctk.CTkButton(
            fr_btns,
            text="✏",
            width=20,
            height=20,
            fg_color="#2D333B",
            hover_color="#3A414A",
            corner_radius=5,
            border_width=1,
            border_color="#4A525C",
            font=CTkFont(family="Roboto", size=9),
            text_color="#D0D7DE",
            command=lambda c=clase: self._editar_bloque(c)
        ).pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            fr_btns,
            text="🗑",
            width=20,
            height=20,
            fg_color="#2D333B",
            hover_color="#4A2A2A",
            corner_radius=5,
            border_width=1,
            border_color="#5A3636",
            font=CTkFont(family="Roboto", size=8),
            text_color="#FFB3B3",
            command=lambda c=clase: self._eliminar_bloque(c)
        ).pack(side="left")

        self._wire_hover_actions(celda, fr_btns)

        return celda

    def _celda_clase_sin_asignar(self, parent, bloque: dict) -> ctk.CTkFrame:
        celda = ctk.CTkFrame(
            parent, fg_color="#2d3e50", corner_radius=10,
            border_width=1, border_color="#4a6b8a", height=_SLOT_ROW_HEIGHT
        )
        celda.grid_propagate(False)
        celda.pack_propagate(False)

        ctk.CTkLabel(
            celda,
            text="📘 CLASE\nSin asignar", 
            font=CTkFont(family="Roboto", size=8, weight="bold"),
            text_color="#d6eaf8",
            justify="center",
        ).pack(pady=(5, 1))

        fr_btns = ctk.CTkFrame(celda, fg_color="transparent")
        fr_btns.pack(pady=(0, 4))

        ctk.CTkButton(
            fr_btns,
            text="➕ Clase",
            width=78,
            height=20,
            fg_color=TM.primary(),
            hover_color="#2980b9",
            corner_radius=6,
            font=CTkFont(family="Roboto", size=8, weight="bold"),
            command=lambda b=bloque: self._asignar_clase_en_bloque(b),
        ).pack(side="left", padx=2)

        if bloque.get("plantilla_bloque_id"):
            ctk.CTkButton(
                fr_btns,
                text="❌",
                width=28,
                height=24,
                fg_color=TM.danger(),
                hover_color="#c0392b",
                corner_radius=6,
                font=CTkFont(family="Arial", size=10),
                command=lambda b=bloque: self._eliminar_bloque_plantilla(b),
            ).pack(side="left", padx=2)

        return celda

    def _celda_tipo_bloque(self, parent, bloque: dict, icono: str, titulo: str, color: str) -> ctk.CTkFrame:
        celda = ctk.CTkFrame(
            parent,
            fg_color=color,
            corner_radius=10,
            border_width=1,
            border_color="#707070",
            height=_SLOT_ROW_HEIGHT,
        )
        etiqueta = (bloque.get("etiqueta") or "").strip()
        texto = f"{icono} {titulo}" if not etiqueta else f"{icono} {titulo}\n{etiqueta}"
        ctk.CTkLabel(
            celda,
            text=texto,
            font=CTkFont(family="Roboto", size=8, weight="bold"),
            text_color="white",
            justify="center",
            wraplength=120,
        ).pack(expand=True, fill="both", padx=5, pady=(4, 1))

        if bloque.get("plantilla_bloque_id"):
            ctk.CTkButton(
                celda,
                text="❌",
                width=28,
                height=22,
                fg_color="#8b1a1a",
                hover_color="#aa2a2a",
                corner_radius=6,
                font=CTkFont(family="Arial", size=10),
                command=lambda b=bloque: self._eliminar_bloque_plantilla(b),
            ).pack(pady=(0, 6))
        return celda

    def _celda_vacia(self, parent, dia_num: int, h_ini: str, h_fin: str) -> ctk.CTkFrame:
        celda = ctk.CTkFrame(
            parent,
            fg_color="#161B22",
            corner_radius=10,
            border_width=1,
            border_color="#2D333B",
            height=_SLOT_ROW_HEIGHT,
        )

        btn = ctk.CTkButton(
            celda,
            text="",
            fg_color="transparent",
            hover_color="#1C2128",
            corner_radius=10,
            command=lambda: self._agregar_en_slot(dia_num, h_ini, h_fin),
        )
        btn.pack(expand=True, fill="both")

        lbl_plus = ctk.CTkLabel(
            celda,
            text="",
            font=CTkFont(family="Roboto", size=14, weight="bold"),
            text_color="#6E7681",
        )
        lbl_plus.place(relx=0.5, rely=0.5, anchor="center")

        def _hover_on(_event=None):
            celda.configure(border_color="#4B5563")
            lbl_plus.configure(text="+")

        def _hover_off(_event=None):
            celda.configure(border_color="#2D333B")
            lbl_plus.configure(text="")

        for w in (celda, btn):
            w.bind("<Enter>", _hover_on)
            w.bind("<Leave>", _hover_off)

        return celda

    def _parse_hhmm_to_minutes(self, hhmm: str) -> int:
        try:
            parts = (hhmm or "").strip().split(":")
            if len(parts) < 2:
                return 0
            hh, mm = parts[0], parts[1]
            return int(hh) * 60 + int(mm)
        except Exception:
            return 0

    def _calcular_row_span(self, start_min: int, end_min: int, interval_minutes: int) -> int:
        """
        Evita que pequeñas desviaciones (ej. 61-65 min) se rendericen como 2 filas.
        Una clase de 1 hora debe verse como 1 bloque.
        """
        duracion = max(1, end_min - start_min)
        tolerancia_min = 5
        if duracion <= interval_minutes + tolerancia_min:
            return 1
        return max(1, (duracion + interval_minutes - 1) // interval_minutes)

    def _format_minutes_to_hhmm(self, total_minutes: int) -> str:
        hh = max(total_minutes, 0) // 60
        mm = max(total_minutes, 0) % 60
        return f"{hh:02d}:{mm:02d}"

    def _build_fixed_time_axis(self, bloques: list[dict], interval_minutes: int = 60) -> list[tuple[str, str]]:
        """
        Genera eje de tiempo fijo e inmutable.
        Si hay datos, usa min/max de bloques redondeados al intervalo.
        Si no hay datos, usa un rango por defecto de 07:00 a 19:00.
        """
        if not bloques:
            start_min = 7 * 60
            end_min = 19 * 60
        else:
            starts = [self._parse_hhmm_to_minutes(b.get("hora_inicio", "")) for b in bloques if b.get("hora_inicio")]
            ends = [self._parse_hhmm_to_minutes(b.get("hora_fin", "")) for b in bloques if b.get("hora_fin")]
            if not starts or not ends:
                start_min = 7 * 60
                end_min = 19 * 60
            else:
                raw_start = min(starts)
                raw_end = max(ends)
                start_min = (raw_start // interval_minutes) * interval_minutes
                end_min = ((raw_end + interval_minutes - 1) // interval_minutes) * interval_minutes
                if end_min <= start_min:
                    end_min = start_min + interval_minutes

        slots: list[tuple[str, str]] = []
        for t in range(start_min, end_min, interval_minutes):
            slots.append((self._format_minutes_to_hhmm(t), self._format_minutes_to_hhmm(t + interval_minutes)))
        return slots

    # ═══════════════════════════════════════════════════════════
    #  CARGA Y FILTRADO DE AULAS
    # ═══════════════════════════════════════════════════════════

    def _cargar_aulas_async(self):
        """Carga aulas en background thread."""
        self._aulas_request_id += 1
        req_id = self._aulas_request_id

        for w in self.scroll_aulas.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.scroll_aulas,
            text="⏳ Cargando aulas...",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(pady=20)

        def _hilo():
            try:
                aulas = self.aulas_controller.listar(activo=True)
            except Exception as exc:
                if self.winfo_exists() and req_id == self._aulas_request_id:
                    self.after(0, lambda: self._aplicar_aulas([]))
                logger.error(f"Error cargando aulas: {exc}")
                return

            if self.winfo_exists() and req_id == self._aulas_request_id:
                self.after(0, lambda: self._aplicar_aulas(aulas))

        threading.Thread(target=_hilo, daemon=True).start()

    def _aplicar_aulas(self, aulas):
        if not self.winfo_exists():
            return
        self.todas_las_aulas = aulas
        self._filtrar_aulas()

    def cargar_aulas(self):
        """Public method - delegates to async."""
        self._cargar_aulas_async()

    def _filtrar_aulas(self, event=None):
        txt = self.entry_buscar_aula.get().lower()

        for w in self.scroll_aulas.winfo_children():
            w.destroy()

        filtradas = [
            a for a in self.todas_las_aulas
            if txt in a["nombre"].lower() or txt in a.get("modalidad", "").lower()
        ]

        if not filtradas:
            self._estado_vacio_aulas()
            return

        for aula in filtradas:
            self._dibujar_card_aula(aula)

    def _dibujar_card_aula(self, aula: dict):
        es_seleccionada = (
            self.aula_seleccionada is not None
            and self.aula_seleccionada.get("id") == aula["id"]
        )
        bg = TM.primary() if es_seleccionada else "#2b2b2b"
        bc = TM.primary() if es_seleccionada else "#3d3d3d"

        card = ctk.CTkFrame(
            self.scroll_aulas, fg_color=bg, corner_radius=10,
            border_width=2, border_color=bc, cursor="hand2", height=72
        )
        card.pack(fill="x", padx=5, pady=3)
        card.pack_propagate(False)

        # Barra de estado
        activo = aula.get("activo", True)
        barra_estado = ctk.CTkFrame(
            card, width=4,
            fg_color=TM.success() if activo else "#95a5a6",
            corner_radius=0
        )
        barra_estado.pack(side="left", fill="y")

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=10, pady=6)

        fr1 = ctk.CTkFrame(content, fg_color="transparent")
        fr1.pack(fill="x", pady=(0, 2))

        lbl_nombre = ctk.CTkLabel(
            fr1, text=aula["nombre"],
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color="white", anchor="w", wraplength=190, justify="left"
        )
        lbl_nombre.pack(side="left", fill="x", expand=True)

        color_mod = _COLOR_MODALIDAD.get(aula.get("modalidad", ""), TM.primary())
        lbl_modalidad = ctk.CTkLabel(
            fr1, text=aula.get("modalidad", ""),
            font=CTkFont(family="Arial", size=8, weight="bold"),
            text_color="white", fg_color=color_mod,
            corner_radius=4, height=16, padx=6
        )
        lbl_modalidad.pack(side="right", padx=(6, 0))

        grupos = aula.get("grupos", [])
        grupos_txt = "  ".join([f"Grp {g}" for g in grupos]) if grupos else "Sin grupos"
        lbl_grupos = ctk.CTkLabel(
            content, text=f"👥 {grupos_txt}",
            font=CTkFont(family="Roboto", size=9),
            text_color="#bdc3c7", anchor="w", wraplength=210, justify="left"
        )
        lbl_grupos.pack(fill="x", pady=(0, 0))

        lbl_indicador = ctk.CTkLabel(
            card, text="✓" if es_seleccionada else "›",
            font=CTkFont(family="Roboto", size=18, weight="bold"),
            text_color="white", width=24
        )
        lbl_indicador.pack(side="right", padx=10)

        cmd = lambda e, a=aula: self._seleccionar_aula(a)
        for w in [
            card, barra_estado, content, fr1, lbl_nombre,
            lbl_modalidad, lbl_grupos, lbl_indicador
        ]:
            w.configure(cursor="hand2")
            w.bind("<Button-1>", cmd)

    def _estado_vacio_aulas(self):
        vacio = ctk.CTkFrame(self.scroll_aulas, fg_color="transparent")
        vacio.pack(fill="both", expand=True, pady=40)

        ctk.CTkLabel(vacio, text="🏫", font=CTkFont(family="Arial", size=38)).pack(pady=8)
        ctk.CTkLabel(
            vacio, text="Sin aulas disponibles",
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text()
        ).pack()
        ctk.CTkLabel(
            vacio, text="Crea aulas en Docentes › Aulas",
            font=CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        ).pack(pady=(3, 0))

    # ═══════════════════════════════════════════════════════════
    #  SELECCIÓN DE AULA
    # ═══════════════════════════════════════════════════════════

    def _seleccionar_aula(self, aula: dict):
        self.aula_seleccionada = aula

        grupos = aula.get("grupos") or ["A", "B", "C", "D"]
        self.cb_grupo.configure(values=grupos, state="normal")
        self.cb_turno.configure(state="normal")
        self.cb_turno.set("MAÑANA" if self.turno_actual == "MANANA" else "TARDE")

        if grupos:
            self.grupo_actual = grupos[0]
            self.cb_grupo.set(self.grupo_actual)

        self.lbl_titulo.configure(text=f"⏰  {aula['nombre'].upper()}")
        self.lbl_subtitulo.configure(
            text=f"{aula.get('modalidad', '')}  •  Grupos: {', '.join(grupos)}"
        )

        self._filtrar_aulas()
        self.cargar_horario()

    # ═══════════════════════════════════════════════════════════
    #  CARGA Y RENDERIZADO DEL GRID
    # ═══════════════════════════════════════════════════════════

    def cargar_horario(self):
        """Carga el horario del aula seleccionada en background."""
        if not self.aula_seleccionada:
            self._mostrar_placeholder()
            return

        self._horario_request_id += 1
        req_id = self._horario_request_id
        aula_id = self.aula_seleccionada["id"]
        grupo = self.grupo_actual
        periodo = self.periodo_actual
        turno = self.turno_actual

        # Loading
        for w in self.fr_tabla.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.fr_tabla,
            text="⏳ Cargando horario...",
            font=CTkFont(family="Roboto", size=13),
            text_color=TM.text_secondary()
        ).pack(pady=60)

        def _hilo():
            exito, msg, datos = self.controller.obtener_bloques_horario_aula(
                aula_id=aula_id,
                grupo=grupo,
                periodo=periodo,
                turno=turno,
            )
            if self.winfo_exists() and req_id == self._horario_request_id:
                self.after(0, lambda: self._aplicar_horario(exito, datos))

        threading.Thread(target=_hilo, daemon=True).start()

    def _aplicar_horario(self, exito, datos):
        if not self.winfo_exists():
            return
        self.bloques_dinamicos = datos if exito else []
        self._construir_grid()

    def _mostrar_placeholder(self):
        for w in self.fr_tabla.winfo_children():
            w.destroy()

        ph = ctk.CTkFrame(self.fr_tabla, fg_color="transparent")
        ph.pack(fill="both", expand=True, pady=100)

        ctk.CTkLabel(ph, text="👈", font=CTkFont(family="Arial", size=60)).pack(pady=10)
        ctk.CTkLabel(
            ph, text="Selecciona un aula",
            font=CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=TM.text()
        ).pack()
        ctk.CTkLabel(
            ph,
            text="Haz clic en cualquier aula del panel izquierdo\npara ver y gestionar su horario",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary(), justify="center"
        ).pack(pady=(8, 0))

    def _construir_grid(self):
        for w in self.fr_tabla.winfo_children():
            w.destroy()

        if not self.bloques_dinamicos:
            vacio = ctk.CTkFrame(self.fr_tabla, fg_color="transparent")
            vacio.pack(fill="both", expand=True, pady=60)
            ctk.CTkLabel(
                vacio,
                text="🧩",
                font=CTkFont(family="Arial", size=42),
            ).pack(pady=(0, 8))
            ctk.CTkLabel(
                vacio,
                text="No hay bloques configurados para este grupo/turno",
                font=CTkFont(family="Roboto", size=13, weight="bold"),
                text_color=TM.text(),
            ).pack()
            ctk.CTkButton(
                vacio,
                text="➕ Crear primer bloque",
                fg_color=TM.primary(),
                hover_color="#2980b9",
                font=CTkFont(family="Roboto", size=12, weight="bold"),
                command=self._abrir_dialogo_bloque_personalizado,
            ).pack(pady=(14, 0))
            return

        # Eje fijo de tiempo: filas regulares de 1 hora
        interval_minutes = 60
        slots = self._build_fixed_time_axis(self.bloques_dinamicos, interval_minutes=interval_minutes)
        dias  = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

        if not slots:
            self._mostrar_placeholder()
            return

        axis_start_min = self._parse_hhmm_to_minutes(slots[0][0])
        total_rows = len(slots)

        tabla = ctk.CTkFrame(self.fr_tabla, fg_color="transparent")
        tabla.pack(fill="both", expand=True, padx=5, pady=5)

        tabla.columnconfigure(0, weight=0, minsize=95)
        for i in range(1, 7):
            tabla.columnconfigure(i, weight=1, minsize=165)

        ctk.CTkLabel(
            tabla, text="⏰ HORA",
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            fg_color=TM.primary(), text_color="white",
            corner_radius=8, height=44
        ).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        for col, dia in enumerate(dias, start=1):
            ctk.CTkLabel(
                tabla, text=dia.upper(),
                font=CTkFont(family="Roboto", size=11, weight="bold"),
                fg_color=TM.primary(), text_color="white",
                corner_radius=8, height=44
            ).grid(row=0, column=col, sticky="nsew", padx=2, pady=2)

        for fila, (h_ini, h_fin) in enumerate(slots, start=1):
            texto_hora = f"{h_ini}\n{h_fin}"
            color_hora = TM.bg_card()

            ctk.CTkLabel(
                tabla, text=texto_hora,
                font=CTkFont(family="Roboto", size=10, weight="bold"),
                fg_color=color_hora, corner_radius=8, height=_SLOT_ROW_HEIGHT
            ).grid(row=fila, column=0, sticky="nsew", padx=2, pady=2)

            for col, _ in enumerate(dias, start=1):
                # Fondo inmutable de la cuadrícula por slot horario
                celda = self._celda_vacia(tabla, col, h_ini, h_fin)
                celda.grid(row=fila, column=col, sticky="nsew", padx=2, pady=2)

        # Overlay de bloques con spanning vertical (rowspan)
        bloques_sorted = sorted(
            self.bloques_dinamicos,
            key=lambda b: (
                b.get("dia_semana", 0),
                self._parse_hhmm_to_minutes(b.get("hora_inicio", "")),
                self._parse_hhmm_to_minutes(b.get("hora_fin", "")),
            ),
        )

        for bloque in bloques_sorted:
            dia = int(bloque.get("dia_semana") or 0)
            if dia < 1 or dia > 6:
                continue

            start_min = self._parse_hhmm_to_minutes(bloque.get("hora_inicio", ""))
            end_min = self._parse_hhmm_to_minutes(bloque.get("hora_fin", ""))
            if end_min <= start_min:
                continue

            row_index = max(0, (start_min - axis_start_min) // interval_minutes)
            row_span = self._calcular_row_span(start_min, end_min, interval_minutes)

            if row_index >= total_rows:
                continue
            if row_index + row_span > total_rows:
                row_span = total_rows - row_index
            if row_span <= 0:
                continue

            celda_bloque = self._crear_celda(
                tabla,
                bloque,
                dia,
                bloque.get("hora_inicio", ""),
                bloque.get("hora_fin", ""),
            )
            celda_bloque.grid(
                row=row_index + 1,
                column=dia,
                rowspan=row_span,
                sticky="nsew",
                padx=2,
                pady=2,
            )

    # ═══════════════════════════════════════════════════════════
    #  ACCIONES
    # ═══════════════════════════════════════════════════════════

    def _cambiar_filtro(self, event=None):
        self.grupo_actual = self.cb_grupo.get()
        turno_ui = self.cb_turno.get()
        self.turno_actual = "MANANA" if turno_ui == "MAÑANA" else "TARDE"
        self.cargar_horario()

    def _abrir_dialogo_bloque_personalizado(self, dia: int = 1, h_ini: str = "08:00", h_fin: str = "08:45"):
        if not self.aula_seleccionada:
            messagebox.showwarning("Sin aula", "Selecciona un aula primero.")
            return

        dialogo = DialogoHorario(
            self,
            self.controller,
            self.docentes_controller,
            self.controller,
            grupo=self.grupo_actual,
            dia=dia,
            hora_inicio=h_ini,
            hora_fin=h_fin,
            turno=self.turno_actual,
            periodo=self.periodo_actual,
            aula_nombre=self.aula_seleccionada["nombre"],
            aula_id=self.aula_seleccionada["id"],
            modo_plantilla=True,
        )
        self.wait_window(dialogo)
        if dialogo.guardado:
            self.cargar_horario()

    def _agregar_en_slot(self, dia: int, h_ini: str, h_fin: str):
        self._abrir_dialogo_bloque_personalizado(dia=dia, h_ini=h_ini, h_fin=h_fin)

    def _asignar_clase_en_bloque(self, bloque: dict):
        if not self.aula_seleccionada:
            messagebox.showwarning("Sin aula", "Selecciona un aula primero.")
            return

        dialogo = DialogoHorario(
            self,
            self.controller,
            self.docentes_controller,
            self.controller,
            grupo=self.grupo_actual,
            dia=bloque.get("dia_semana", 1),
            hora_inicio=bloque.get("hora_inicio", ""),
            hora_fin=bloque.get("hora_fin", ""),
            turno=self.turno_actual,
            periodo=self.periodo_actual,
            aula_nombre=self.aula_seleccionada["nombre"],
            aula_id=self.aula_seleccionada["id"],
            plantilla_bloque_id=bloque.get("plantilla_bloque_id"),
        )
        self.wait_window(dialogo)
        if dialogo.guardado:
            self.cargar_horario()

    def _editar_bloque(self, clase: dict):
        nombre_curso = clase.get("nombre_curso") or clase.get("curso_nombre") or "Clase"
        messagebox.showinfo(
            "Editar bloque",
            f"Edición de «{nombre_curso}» — próximamente."
        )

    def _eliminar_bloque(self, clase: dict):
        nombre_curso = clase.get("nombre_curso") or clase.get("curso_nombre") or "Clase"
        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar «{nombre_curso}» del horario?\n"
            f"{clase.get('hora_inicio', '')} – {clase.get('hora_fin', '')}"
        ):
            return

        exito, msg = self.controller.eliminar_bloque_horario(clase["id"])
        if exito:
            messagebox.showinfo("Listo", "Bloque eliminado correctamente.")
            self.cargar_horario()
        else:
            messagebox.showerror("Error", msg)

    def _eliminar_bloque_plantilla(self, bloque: dict):
        bloque_id = bloque.get("plantilla_bloque_id")
        if not bloque_id:
            messagebox.showwarning("Accion no valida", "Este bloque no pertenece a una plantilla editable.")
            return

        tipo = bloque.get("tipo_bloque", "BLOQUE")
        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar bloque {tipo} {bloque.get('hora_inicio', '')}-{bloque.get('hora_fin', '')}?",
        ):
            return

        exito, msg = self.controller.eliminar_bloque_plantilla(bloque_id)
        if exito:
            messagebox.showinfo("Listo", "Bloque de plantilla eliminado.")
            self.cargar_horario()
        else:
            messagebox.showerror("Error", msg)

    def refresh(self):
        """Llamado por main_window al mostrar esta vista."""
        if not self._ui_ready:
            self.after(1, self._build_ui_deferred)
            return

        self._cargar_aulas_async()
        if self.aula_seleccionada:
            self.cargar_horario()

    def on_show(self):
        if not self._ui_ready:
            self.after(1, self._build_ui_deferred)

    def on_hide(self):
        pass

    def cleanup(self):
        pass
