"""
CrearAulasView – ESTILO PREMIUM
Sistema Musuq Cloud
Panel dual: Lista de aulas registradas + Formulario de creación / detalle
"""

import customtkinter as ctk
from tkinter import messagebox
from customtkinter import CTkFont
import threading

from core.theme_manager import ThemeManager as TM
from controllers.aulas_controller import AulasController
from utils.perf_utils import get_logger

logger = get_logger(__name__)

MODALIDADES = [
    "COLEGIO",
    "ORDINARIO",
    "PRIMERA OPCION",
    "REFORZAMIENTO",
    "VIRTUAL",
    "MIXTA",
    "TALLER",
    "AUDITORIO",
]
GRUPOS_DISPONIBLES = ["A", "B", "C", "D", "Único"]


class CrearAulasView(ctk.CTkFrame):
    """
    Vista profesional para gestión y creación de aulas.
    Diseño: Lista lateral + formulario tabbed a la derecha.
    """

    def __init__(self, parent, auth_client=None):
        super().__init__(parent, fg_color="transparent")

        self.controller = AulasController(auth_client.token if auth_client else "")
        self.auth_client = auth_client
        self.aulas: list = []
        self.aula_seleccionada: dict | None = None

        # Variables del formulario
        self.var_nombre      = ctk.StringVar()
        self.var_modalidad   = ctk.StringVar(value=MODALIDADES[0])
        self.var_descripcion = ctk.StringVar()
        self.var_activo      = ctk.BooleanVar(value=True)
        self.vars_grupos: dict[str, ctk.BooleanVar] = {
            g: ctk.BooleanVar(value=False) for g in GRUPOS_DISPONIBLES
        }

        # Layout 35 / 65
        self.grid_columnconfigure(0, weight=35, minsize=320)
        self.grid_columnconfigure(1, weight=65)
        self.grid_rowconfigure(0, weight=1)

        self._crear_panel_izquierdo()
        self._crear_panel_derecho()

        self._cargar_aulas_async()

    # ═══════════════════════════════════════════════════════════
    #  PANEL IZQUIERDO – LISTA DE AULAS
    # ═══════════════════════════════════════════════════════════

    def _crear_panel_izquierdo(self):
        self.panel_izq = ctk.CTkFrame(
            self,
            fg_color=TM.bg_panel(),
            corner_radius=0
        )
        self.panel_izq.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)

        # ── Icono + título ───────────────────────────────────
        header = ctk.CTkFrame(self.panel_izq, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 0))

        ctk.CTkLabel(
            header,
            text="🏫",
            font=CTkFont(family="Arial", size=50)
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            header,
            text="GESTIÓN DE AULAS",
            font=CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=TM.text()
        ).pack()

        ctk.CTkLabel(
            header,
            text="Registro y administración de espacios",
            font=CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        ).pack(pady=(3, 0))

        # ── Separador ────────────────────────────────────────
        ctk.CTkFrame(
            self.panel_izq,
            height=2,
            fg_color="#404040"
        ).pack(fill="x", padx=20, pady=18)

        # ── Buscador ─────────────────────────────────────────
        ctk.CTkLabel(
            self.panel_izq,
            text="Buscar Aula",
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 8))

        frame_search = ctk.CTkFrame(
            self.panel_izq,
            fg_color=TM.bg_card(),
            height=42,
            corner_radius=10
        )
        frame_search.pack(fill="x", padx=20, pady=(0, 15))
        frame_search.pack_propagate(False)

        ctk.CTkLabel(
            frame_search,
            text="🔍",
            font=CTkFont(family="Arial", size=15),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(12, 4))

        self.entry_buscar = ctk.CTkEntry(
            frame_search,
            placeholder_text="Filtrar aulas...",
            border_width=0,
            fg_color="transparent",
            text_color=TM.text(),
            font=CTkFont(family="Roboto", size=12)
        )
        self.entry_buscar.pack(side="left", fill="both", expand=True, padx=(0, 12))
        self.entry_buscar.bind("<KeyRelease>", self._filtrar_lista)

        # ── Lista scrollable ──────────────────────────────────
        ctk.CTkLabel(
            self.panel_izq,
            text="Aulas Registradas",
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 8))

        self.scroll_aulas = ctk.CTkScrollableFrame(
            self.panel_izq,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.scroll_aulas.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # ── Botón Nueva Aula ──────────────────────────────────
        ctk.CTkButton(
            self.panel_izq,
            text="➕  NUEVA AULA",
            height=42,
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            fg_color=TM.success(),
            hover_color="#27ae60",
            corner_radius=10,
            command=self._activar_form_nuevo
        ).pack(fill="x", padx=20, pady=(0, 20))

    # ═══════════════════════════════════════════════════════════
    #  PANEL DERECHO – TABVIEW
    # ═══════════════════════════════════════════════════════════

    def _crear_panel_derecho(self):
        self.panel_der = ctk.CTkFrame(self, fg_color="transparent")
        self.panel_der.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        self.tabview = ctk.CTkTabview(
            self.panel_der,
            fg_color=TM.bg_panel(),
            segmented_button_fg_color=TM.bg_card(),
            segmented_button_selected_color=TM.primary(),
            segmented_button_selected_hover_color=TM.hover(),
            segmented_button_unselected_color=TM.bg_card(),
            segmented_button_unselected_hover_color="#34495e",
            text_color=TM.text(),
            corner_radius=12
        )
        self.tabview.pack(fill="both", expand=True)

        self.tabview.add("➕  Nueva Aula")
        self.tabview.add("📋  Detalle")
        self.tabview.add("📊  Resumen")

        self._crear_tab_nueva_aula()
        self._crear_tab_detalle()
        self._crear_tab_resumen()

    # ───────────────────────────────────────────────────────────
    #  TAB 1 – NUEVA AULA
    # ───────────────────────────────────────────────────────────

    def _crear_tab_nueva_aula(self):
        tab = self.tabview.tab("➕  Nueva Aula")

        scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        fr = ctk.CTkFrame(scroll, fg_color="transparent")
        fr.pack(fill="both", expand=True, padx=35, pady=20)

        # Título del formulario
        ctk.CTkLabel(
            fr,
            text="🏫  REGISTRAR NUEVA AULA",
            font=CTkFont(family="Roboto", size=17, weight="bold"),
            text_color=TM.text()
        ).pack(pady=(0, 5))

        ctk.CTkLabel(
            fr,
            text="Completa los datos del espacio académico",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(pady=(0, 22))

        # ── Sección datos básicos ────────────────────────────
        self._seccion_titulo(fr, "📝  DATOS BÁSICOS")

        # Nombre
        self._campo_label(fr, "Nombre del Aula  *")
        self.entry_nombre = ctk.CTkEntry(
            fr,
            textvariable=self.var_nombre,
            placeholder_text="Ej: Aula 201, Lab. Física...",
            height=42,
            font=CTkFont(family="Roboto", size=13),
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text()
        )
        self.entry_nombre.pack(fill="x", pady=(0, 15))

        # Modalidad
        self._campo_label(fr, "Modalidad  *")
        self.combo_modalidad = ctk.CTkComboBox(
            fr,
            values=MODALIDADES,
            variable=self.var_modalidad,
            height=42,
            font=CTkFont(family="Roboto", size=13),
            fg_color=TM.bg_card(),
            dropdown_fg_color=TM.bg_panel(),
            button_color=TM.primary(),
            button_hover_color=TM.hover(),
            text_color=TM.text(),
            state="readonly"
        )
        self.combo_modalidad.pack(fill="x", pady=(0, 15))

        # Descripción
        self._campo_label(fr, "Descripción  (opcional)")
        self.entry_descripcion = ctk.CTkEntry(
            fr,
            textvariable=self.var_descripcion,
            placeholder_text="Ej: Segundo piso, ala norte...",
            height=42,
            font=CTkFont(family="Roboto", size=13),
            fg_color=TM.bg_main(),
            border_color=TM.bg_card(),
            text_color=TM.text()
        )
        self.entry_descripcion.pack(fill="x", pady=(0, 20))

        # ── Separador ────────────────────────────────────────
        ctk.CTkFrame(fr, height=2, fg_color=TM.bg_card()).pack(fill="x", pady=5)

        # ── Sección grupos ───────────────────────────────────
        self._seccion_titulo(fr, "👥  GRUPOS QUE USARÁN EL AULA")

        ctk.CTkLabel(
            fr,
            text="Selecciona uno o más grupos",
            font=CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", pady=(0, 10))

        frm_grupos = ctk.CTkFrame(fr, fg_color=TM.bg_card(), corner_radius=10)
        frm_grupos.pack(fill="x", pady=(0, 20))

        fila_grupos = ctk.CTkFrame(frm_grupos, fg_color="transparent")
        fila_grupos.pack(fill="x", padx=20, pady=15)

        for grupo in GRUPOS_DISPONIBLES:
            ctk.CTkCheckBox(
                fila_grupos,
                text=f"  {grupo}",
                variable=self.vars_grupos[grupo],
                font=CTkFont(family="Roboto", size=12),
                fg_color=TM.primary(),
                hover_color=TM.hover(),
                text_color=TM.text(),
                checkmark_color="white",
                corner_radius=5,
                width=80
            ).pack(side="left", padx=10)

        # ── Separador ────────────────────────────────────────
        ctk.CTkFrame(fr, height=2, fg_color=TM.bg_card()).pack(fill="x", pady=5)

        # ── Opciones adicionales ──────────────────────────────
        self._seccion_titulo(fr, "⚙️  OPCIONES")

        fr_opts = ctk.CTkFrame(fr, fg_color=TM.bg_card(), corner_radius=10)
        fr_opts.pack(fill="x", pady=(0, 20))

        fr_opts_content = ctk.CTkFrame(fr_opts, fg_color="transparent")
        fr_opts_content.pack(fill="x", padx=20, pady=15)

        ctk.CTkCheckBox(
            fr_opts_content,
            text="  Habilitada desde el inicio",
            variable=self.var_activo,
            font=CTkFont(family="Roboto", size=12),
            fg_color=TM.success(),
            hover_color="#2ecc71",
            text_color=TM.text(),
            checkmark_color="white",
            corner_radius=5
        ).pack(anchor="w")

        ctk.CTkLabel(
            fr_opts_content,
            text="Las aulas deshabilitadas no aparecen en la asignación de horarios",
            font=CTkFont(family="Roboto", size=9),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(anchor="w", pady=(5, 0))

        # ── Botón crear ───────────────────────────────────────
        ctk.CTkFrame(fr, height=2, fg_color=TM.bg_card()).pack(fill="x", pady=10)

        self.btn_crear = ctk.CTkButton(
            fr,
            text="💾  REGISTRAR AULA",
            height=52,
            font=CTkFont(family="Roboto", size=15, weight="bold"),
            fg_color=TM.success(),
            hover_color="#2ecc71",
            corner_radius=10,
            command=self._crear_aula
        )
        self.btn_crear.pack(fill="x", pady=(5, 5))

        ctk.CTkButton(
            fr,
            text="🗑  Limpiar Formulario",
            height=36,
            font=CTkFont(family="Roboto", size=11),
            fg_color="transparent",
            hover_color=TM.bg_card(),
            border_width=1,
            border_color=TM.bg_card(),
            text_color=TM.text_secondary(),
            corner_radius=8,
            command=self._limpiar_formulario
        ).pack(fill="x", pady=(0, 20))

    # ───────────────────────────────────────────────────────────
    #  TAB 2 – DETALLE DEL AULA SELECCIONADA
    # ───────────────────────────────────────────────────────────

    def _crear_tab_detalle(self):
        tab = self.tabview.tab("📋  Detalle")
        self.frame_detalle_contenido = ctk.CTkScrollableFrame(
            tab, fg_color="transparent"
        )
        self.frame_detalle_contenido.pack(fill="both", expand=True)
        self._mostrar_sin_seleccion()

    def _mostrar_sin_seleccion(self):
        """Estado: ningún aula seleccionada"""
        for w in self.frame_detalle_contenido.winfo_children():
            w.destroy()

        vacio = ctk.CTkFrame(self.frame_detalle_contenido, fg_color="transparent")
        vacio.pack(fill="both", expand=True, pady=80)

        ctk.CTkLabel(
            vacio, text="👆",
            font=CTkFont(family="Arial", size=60)
        ).pack(pady=10)

        ctk.CTkLabel(
            vacio,
            text="Selecciona un aula de la lista",
            font=CTkFont(family="Roboto", size=15, weight="bold"),
            text_color=TM.text()
        ).pack()

        ctk.CTkLabel(
            vacio,
            text="Haz clic en cualquier aula del panel izquierdo para ver su detalle",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(pady=(8, 0))

    def _mostrar_detalle_aula(self, aula: dict):
        """Renderizar detalle del aula seleccionada"""
        for w in self.frame_detalle_contenido.winfo_children():
            w.destroy()

        fr = ctk.CTkFrame(self.frame_detalle_contenido, fg_color="transparent")
        fr.pack(fill="both", expand=True, padx=35, pady=20)

        # Badge estado
        activo = aula.get("activo", True)
        color_badge = TM.success() if activo else "#95a5a6"
        texto_badge = "● ACTIVA" if activo else "● INACTIVA"

        fr_badge = ctk.CTkFrame(fr, fg_color=color_badge, corner_radius=8)
        fr_badge.pack(anchor="w", pady=(0, 15))
        ctk.CTkLabel(
            fr_badge,
            text=texto_badge,
            font=CTkFont(family="Roboto", size=10, weight="bold"),
            text_color="white"
        ).pack(padx=12, pady=5)

        # Nombre
        ctk.CTkLabel(
            fr,
            text=aula.get("nombre", "—"),
            font=CTkFont(family="Roboto", size=22, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            fr,
            text=f"Modalidad: {aula.get('modalidad', '—')}",
            font=CTkFont(family="Roboto", size=12),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", pady=(3, 0))

        desc = aula.get("descripcion") or "Sin descripción"
        ctk.CTkLabel(
            fr,
            text=f"📎 {desc}",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", pady=(2, 15))

        ctk.CTkFrame(fr, height=2, fg_color=TM.bg_card()).pack(fill="x", pady=10)

        # Grupos
        self._seccion_titulo(fr, "👥  GRUPOS ASIGNADOS")
        grupos = aula.get("grupos", [])
        if grupos:
            fr_chips = ctk.CTkFrame(fr, fg_color="transparent")
            fr_chips.pack(fill="x", pady=(5, 15))
            for g in grupos:
                chip = ctk.CTkFrame(
                    fr_chips,
                    fg_color=TM.primary(),
                    corner_radius=8
                )
                chip.pack(side="left", padx=(0, 8))
                ctk.CTkLabel(
                    chip,
                    text=f"  Grupo {g}  ",
                    font=CTkFont(family="Roboto", size=12, weight="bold"),
                    text_color="white"
                ).pack(pady=6)
        else:
            ctk.CTkLabel(
                fr,
                text="Sin grupos asignados",
                font=CTkFont(family="Roboto", size=11),
                text_color=TM.text_secondary(),
                anchor="w"
            ).pack(fill="x", pady=(0, 15))

        ctk.CTkFrame(fr, height=2, fg_color=TM.bg_card()).pack(fill="x", pady=10)

        # Acciones
        self._seccion_titulo(fr, "⚙️  ACCIONES")

        texto_toggle = "🔴  Desactivar Aula" if activo else "🟢  Activar Aula"
        color_toggle = TM.danger() if activo else TM.success()
        hover_toggle = "#b71c1c" if activo else "#27ae60"

        ctk.CTkButton(
            fr,
            text=texto_toggle,
            height=42,
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            fg_color=color_toggle,
            hover_color=hover_toggle,
            corner_radius=8,
            command=lambda: self._toggle_estado_aula(aula)
        ).pack(fill="x", pady=(8, 5))

        ctk.CTkButton(
            fr,
            text="✏️  Editar Nombre / Descripción",
            height=42,
            font=CTkFont(family="Roboto", size=12),
            fg_color=TM.primary(),
            hover_color=TM.hover(),
            corner_radius=8,
            command=lambda: self._abrir_editar_aula(aula)
        ).pack(fill="x", pady=5)

        ctk.CTkButton(
            fr,
            text="🗑  Eliminar Aula",
            height=42,
            font=CTkFont(family="Roboto", size=12),
            fg_color="transparent",
            hover_color="#b71c1c",
            border_width=1,
            border_color=TM.danger(),
            text_color=TM.danger(),
            corner_radius=8,
            command=lambda: self._eliminar_aula(aula)
        ).pack(fill="x", pady=(5, 20))

    # ───────────────────────────────────────────────────────────
    #  TAB 3 – RESUMEN ESTADÍSTICO
    # ───────────────────────────────────────────────────────────

    def _crear_tab_resumen(self):
        tab = self.tabview.tab("📊  Resumen")
        self.fr_resumen = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        self.fr_resumen.pack(fill="both", expand=True, padx=30, pady=20)
        self._renderizar_resumen()

    def _renderizar_resumen(self):
        for w in self.fr_resumen.winfo_children():
            w.destroy()

        ctk.CTkLabel(
            self.fr_resumen,
            text="📊  RESUMEN GENERAL DE AULAS",
            font=CTkFont(family="Roboto", size=16, weight="bold"),
            text_color=TM.text()
        ).pack(pady=(0, 20))

        total     = len(self.aulas)
        activas   = sum(1 for a in self.aulas if a.get("activo"))
        inactivas = total - activas
        presencial = sum(1 for a in self.aulas if a.get("modalidad") == "COLEGIO")
        virtual   = sum(1 for a in self.aulas if a.get("modalidad") == "VIRTUAL")

        stats = [
            ("🏫  Total de Aulas",          str(total),     TM.primary()),
            ("✅  Aulas Activas",            str(activas),   TM.success()),
            ("⛔  Aulas Inactivas",          str(inactivas), "#95a5a6"),
            ("🏢  Presenciales (COLEGIO)",   str(presencial),TM.warning()),
            ("💻  Virtuales",               str(virtual),   "#9b59b6"),
        ]

        for titulo, valor, color in stats:
            self._crear_card_stat(titulo, valor, color)

        # Barra de proporción activas / total
        if total > 0:
            ctk.CTkFrame(
                self.fr_resumen, height=2, fg_color=TM.bg_card()
            ).pack(fill="x", pady=20)

            ctk.CTkLabel(
                self.fr_resumen,
                text="📈  PROPORCIÓN ACTIVAS / TOTAL",
                font=CTkFont(family="Roboto", size=12, weight="bold"),
                text_color=TM.primary(),
                anchor="w"
            ).pack(fill="x", pady=(0, 10))

            fr_bar = ctk.CTkFrame(
                self.fr_resumen, fg_color=TM.bg_card(), corner_radius=10
            )
            fr_bar.pack(fill="x")

            fr_bar_content = ctk.CTkFrame(fr_bar, fg_color="transparent")
            fr_bar_content.pack(fill="x", padx=20, pady=15)

            barra = ctk.CTkProgressBar(
                fr_bar_content,
                height=18,
                corner_radius=8,
                progress_color=TM.success()
            )
            barra.pack(fill="x", pady=(0, 6))
            barra.set(activas / total)

            ctk.CTkLabel(
                fr_bar_content,
                text=f"{activas} de {total} aulas activas  ({int(activas/total*100)}%)",
                font=CTkFont(family="Roboto", size=10),
                text_color=TM.text_secondary()
            ).pack(anchor="w")

    def _crear_card_stat(self, titulo: str, valor: str, color: str):
        fr = ctk.CTkFrame(self.fr_resumen, fg_color=TM.bg_card(), corner_radius=10)
        fr.pack(fill="x", pady=5)

        ctk.CTkFrame(fr, width=5, fg_color=color, corner_radius=0).pack(
            side="left", fill="y"
        )

        fc = ctk.CTkFrame(fr, fg_color="transparent")
        fc.pack(side="left", fill="both", expand=True, padx=15, pady=12)

        ctk.CTkLabel(
            fc,
            text=titulo,
            font=CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x")

        ctk.CTkLabel(
            fc,
            text=valor,
            font=CTkFont(family="Roboto", size=22, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        ).pack(fill="x")

    # ═══════════════════════════════════════════════════════════
    #  HELPERS DE UI
    # ═══════════════════════════════════════════════════════════

    def _seccion_titulo(self, parent, texto: str):
        ctk.CTkLabel(
            parent,
            text=texto,
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.primary(),
            anchor="w"
        ).pack(fill="x", pady=(12, 6))

    def _campo_label(self, parent, texto: str):
        ctk.CTkLabel(
            parent,
            text=texto,
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", pady=(0, 4))

    # ═══════════════════════════════════════════════════════════
    #  RENDERIZADO DE LA LISTA
    # ═══════════════════════════════════════════════════════════

    def _cargar_aulas_async(self):
        """Carga la lista de aulas en background."""
        # Loading placeholder
        for w in self.scroll_aulas.winfo_children():
            w.destroy()
        ctk.CTkLabel(
            self.scroll_aulas,
            text="⏳ Cargando aulas...",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(pady=20)

        def _hilo():
            activas = self.controller.listar(activo=True)
            inactivas = self.controller.listar(activo=False)
            # Deduplicar por ID
            visto = set()
            combinadas = []
            for a in activas + inactivas:
                if a["id"] not in visto:
                    visto.add(a["id"])
                    combinadas.append(a)
            if self.winfo_exists():
                self.after(0, lambda: self._aplicar_aulas(combinadas))

        threading.Thread(target=_hilo, daemon=True).start()

    def _aplicar_aulas(self, aulas):
        if not self.winfo_exists():
            return
        self.aulas = aulas
        self._filtrar_lista()
        self._renderizar_resumen()

    def cargar_aulas(self):
        """Public method - delegates to async."""
        self._cargar_aulas_async()

    def _filtrar_lista(self, event=None):
        texto = self.entry_buscar.get().lower()
        for w in self.scroll_aulas.winfo_children():
            w.destroy()

        filtradas = [
            a for a in self.aulas
            if texto in a["nombre"].lower()
            or texto in a["modalidad"].lower()
        ]

        if not filtradas:
            self._estado_vacio_lista()
            return

        for aula in filtradas:
            self._dibujar_item_aula(aula)

    def _dibujar_item_aula(self, aula: dict):
        activo = aula.get("activo", True)
        color_barra = TM.success() if activo else "#95a5a6"

        # Contenedor exterior
        item = ctk.CTkFrame(
            self.scroll_aulas,
            fg_color="transparent"
        )
        item.pack(fill="x", pady=1)

        # Card interna
        card = ctk.CTkFrame(
            item,
            fg_color="#2b2b2b",
            corner_radius=10,
            height=64
        )
        card.pack(fill="x", pady=1)
        card.pack_propagate(False)

        # Barra lateral de estado
        ctk.CTkFrame(
            card, width=5, fg_color=color_barra, corner_radius=0
        ).pack(side="left", fill="y")

        # Contenido del card
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=10, pady=6)

        # Fila 1: nombre + modalidad badge
        fr1 = ctk.CTkFrame(content, fg_color="transparent")
        fr1.pack(fill="x", pady=(0, 2))

        ctk.CTkLabel(
            fr1,
            text=aula["nombre"],
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        ).pack(side="left", fill="x", expand=True)

        color_mod = {
            "COLEGIO":        TM.primary(),
            "ORDINARIO":      "#1abc9c",
            "PRIMERA OPCION": "#c56f36",
            "REFORZAMIENTO":  "#e74c3c",
            "VIRTUAL":        "#9b59b6",
            "MIXTA":          TM.warning(),
            "TALLER":         "#e67e22",
            "AUDITORIO":      "#16a085",
        }.get(aula.get("modalidad", "COLEGIO"), TM.primary())

        lbl_mod = ctk.CTkLabel(
            fr1,
            text=aula.get("modalidad", ""),
            font=CTkFont(family="Arial", size=8, weight="bold"),
            text_color="white",
            fg_color=color_mod,
            corner_radius=5,
            height=16,
            padx=6
        )
        lbl_mod.pack(side="right", padx=(6, 0))

        # Fila 2: grupos
        grupos_txt = "Grupos: " + ", ".join(aula.get("grupos", [])) if aula.get("grupos") else "Sin grupos"
        ctk.CTkLabel(
            content,
            text=f"👥 {grupos_txt}",
            font=CTkFont(family="Roboto", size=9),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", pady=(0, 0))

        # Desc
        desc = aula.get("descripcion") or ""
        if desc:
            ctk.CTkLabel(
                content,
                text=f"📎 {desc[:45]}{'...' if len(desc) > 45 else ''}",
                font=CTkFont(family="Roboto", size=9),
                text_color=TM.text_secondary(),
                anchor="w"
            ).pack(fill="x")

        # Botón seleccionar
        ctk.CTkButton(
            card,
            text="›",
            width=32,
            height=28,
            font=CTkFont(family="Roboto", size=16, weight="bold"),
            fg_color=TM.primary(),
            hover_color=TM.hover(),
            corner_radius=8,
            command=lambda a=aula: self._seleccionar_aula(a)
        ).pack(side="right", padx=10)

    def _estado_vacio_lista(self):
        vacio = ctk.CTkFrame(self.scroll_aulas, fg_color="transparent")
        vacio.pack(fill="both", expand=True, pady=50)

        ctk.CTkLabel(
            vacio, text="🏫",
            font=CTkFont(family="Arial", size=45)
        ).pack(pady=8)

        ctk.CTkLabel(
            vacio,
            text="Sin aulas registradas",
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text()
        ).pack()

        ctk.CTkLabel(
            vacio,
            text="Usa el botón ➕ para crear la primera",
            font=CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        ).pack(pady=(4, 0))

    # ═══════════════════════════════════════════════════════════
    #  LÓGICA / ACCIONES
    # ═══════════════════════════════════════════════════════════

    def refresh(self):
        """Llamado automáticamente por main_window al mostrar la vista."""
        self._cargar_aulas_async()

    # ── Lifecycle ──
    def on_show(self):
        pass

    def on_hide(self):
        pass

    def cleanup(self):
        pass

    def _seleccionar_aula(self, aula: dict):
        self.aula_seleccionada = aula
        self._mostrar_detalle_aula(aula)
        self.tabview.set("📋  Detalle")

    def _activar_form_nuevo(self):
        self._limpiar_formulario()
        self.tabview.set("➕  Nueva Aula")

    def _limpiar_formulario(self):
        self.var_nombre.set("")
        self.var_modalidad.set(MODALIDADES[0])
        self.var_descripcion.set("")
        self.var_activo.set(True)
        for var in self.vars_grupos.values():
            var.set(False)

    def _crear_aula(self):
        nombre    = self.var_nombre.get().strip()
        modalidad = self.var_modalidad.get().strip()
        desc      = self.var_descripcion.get().strip()
        activo    = self.var_activo.get()
        grupos    = [g for g, v in self.vars_grupos.items() if v.get()]

        # ── Validaciones ──────────────────────────────────────
        errores = []

        if not nombre:
            errores.append("• El nombre del aula es obligatorio")
        elif any(a["nombre"].lower() == nombre.lower() for a in self.aulas):
            errores.append("• Ya existe un aula con ese nombre")

        if not modalidad:
            errores.append("• Selecciona una modalidad")

        if errores:
            messagebox.showwarning(
                "Datos incompletos",
                "Corrige los siguientes errores:\n\n" + "\n".join(errores)
            )
            return

        # ── Confirmación ──────────────────────────────────────
        grupos_txt = ", ".join(grupos) if grupos else "Ninguno aún"
        confirmar = messagebox.askyesno(
            "Confirmar Registro",
            f"¿Registrar el siguiente aula?\n\n"
            f"  Nombre    : {nombre}\n"
            f"  Modalidad : {modalidad}\n"
            f"  Grupos    : {grupos_txt}\n"
            f"  Estado    : {'Activa' if activo else 'Inactiva'}\n"
        )
        if not confirmar:
            return

        # ── Deshabilitar botón mientras se guarda ────────────
        self.btn_crear.configure(state="disabled", text="⏳  Guardando...")
        self.update_idletasks()

        exito, resultado = self.controller.crear(
            nombre=nombre,
            modalidad=modalidad,
            descripcion=desc or None,
            grupos=grupos,
            activo=activo,
        )

        self.btn_crear.configure(state="normal", text="💾  REGISTRAR AULA")

        if not exito:
            messagebox.showerror(
                "Error al crear aula",
                f"No se pudo registrar el aula:\n\n{resultado}"
            )
            return

        nueva_aula = resultado   # AulaResponse del backend

        self._limpiar_formulario()
        self.cargar_aulas()      # recarga fresca desde la API

        messagebox.showinfo(
            "✅ Aula Registrada",
            f"El aula «{nueva_aula.get('nombre', nombre)}» fue registrada correctamente.\n\n"
            f"Ya está disponible para asignación en horarios."
        )

        # Buscar el objeto actualizado en la lista recargada y seleccionarlo
        aula_actualizada = next(
            (a for a in self.aulas if a["id"] == nueva_aula.get("id")), nueva_aula
        )
        self._seleccionar_aula(aula_actualizada)

    def _toggle_estado_aula(self, aula: dict):
        nueva_estado = not aula.get("activo", True)
        accion = "desactivar" if not nueva_estado else "activar"

        if not messagebox.askyesno(
            "Confirmar",
            f"¿Deseas {accion} el aula «{aula['nombre']}»?"
        ):
            return

        exito, resultado = self.controller.actualizar(aula["id"], activo=nueva_estado)

        if not exito:
            messagebox.showerror(
                "Error",
                f"No se pudo cambiar el estado del aula:\n\n{resultado}"
            )
            return

        # Actualizar el dict local con los datos frescos del backend
        aula.update(resultado)

        self.cargar_aulas()
        # Re-buscar el objeto actualizado
        aula_actualizada = next((a for a in self.aulas if a["id"] == aula["id"]), aula)
        self._mostrar_detalle_aula(aula_actualizada)

        estado_txt = "activada" if nueva_estado else "desactivada"
        messagebox.showinfo(
            "Estado actualizado",
            f"El aula «{aula_actualizada['nombre']}» fue {estado_txt} correctamente."
        )

    def _abrir_editar_aula(self, aula: dict):
        """Diálogo simplificado de edición"""
        dialogo = ctk.CTkToplevel(self)
        dialogo.title(f"Editar – {aula['nombre']}")
        dialogo.geometry("440x320")
        dialogo.resizable(False, False)
        dialogo.configure(fg_color=TM.bg_main())
        dialogo.grab_set()

        fr = ctk.CTkFrame(dialogo, fg_color="transparent")
        fr.pack(fill="both", expand=True, padx=30, pady=25)

        ctk.CTkLabel(
            fr,
            text=f"✏️  Editar «{aula['nombre']}»",
            font=CTkFont(family="Roboto", size=15, weight="bold"),
            text_color=TM.text()
        ).pack(pady=(0, 20))

        var_n = ctk.StringVar(value=aula["nombre"])
        var_d = ctk.StringVar(value=aula.get("descripcion") or "")

        ctk.CTkLabel(fr, text="Nombre", anchor="w",
                     text_color=TM.text_secondary(),
                     font=CTkFont(family="Roboto", size=11)).pack(fill="x")
        ctk.CTkEntry(fr, textvariable=var_n, height=40,
                     fg_color=TM.bg_card(), text_color=TM.text(),
                     border_color=TM.primary()).pack(fill="x", pady=(2, 15))

        ctk.CTkLabel(fr, text="Descripción", anchor="w",
                     text_color=TM.text_secondary(),
                     font=CTkFont(family="Roboto", size=11)).pack(fill="x")
        ctk.CTkEntry(fr, textvariable=var_d, height=40,
                     fg_color=TM.bg_card(), text_color=TM.text(),
                     border_color=TM.bg_card()).pack(fill="x", pady=(2, 20))

        def guardar():
            nuevo_nombre = var_n.get().strip()
            nueva_desc   = var_d.get().strip()
            if not nuevo_nombre:
                messagebox.showwarning("Error", "El nombre no puede estar vacío", parent=dialogo)
                return

            btn_guardar.configure(state="disabled", text="⏳  Guardando...")
            dialogo.update_idletasks()

            exito, resultado = self.controller.actualizar(
                aula["id"],
                nombre=nuevo_nombre,
                descripcion=nueva_desc or None,
            )

            if not exito:
                btn_guardar.configure(state="normal", text="💾  Guardar Cambios")
                messagebox.showerror("Error", f"No se pudo guardar:\n\n{resultado}", parent=dialogo)
                return

            aula.update(resultado)  # datos frescos del backend
            dialogo.destroy()
            self.cargar_aulas()
            aula_actualizada = next((a for a in self.aulas if a["id"] == aula["id"]), aula)
            self._mostrar_detalle_aula(aula_actualizada)

        btn_guardar = ctk.CTkButton(
            fr,
            text="💾  Guardar Cambios",
            height=44,
            fg_color=TM.primary(),
            hover_color=TM.hover(),
            font=CTkFont(family="Roboto", size=13, weight="bold"),
            command=guardar
        )
        btn_guardar.pack(fill="x")

    def _eliminar_aula(self, aula: dict):
        if not messagebox.askyesno(
            "⚠️ Confirmar Eliminación",
            f"¿Eliminar definitivamente el aula «{aula['nombre']}»?\n\n"
            f"Esta acción no se puede deshacer."
        ):
            return

        exito, mensaje = self.controller.eliminar(aula["id"])

        if not exito:
            messagebox.showerror(
                "Error al eliminar",
                f"No se pudo eliminar el aula:\n\n{mensaje}"
            )
            return

        nombre_borrado = aula["nombre"]
        self.aula_seleccionada = None
        self.cargar_aulas()
        self._mostrar_sin_seleccion()

        messagebox.showinfo(
            "Eliminada",
            f"El aula «{nombre_borrado}» fue eliminada del registro."
        )
