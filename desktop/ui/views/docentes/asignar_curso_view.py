"""
Vista de Asignación de Cursos a Docentes
Sistema Musuq Cloud

Flujo:
  1. Panel izquierdo  → lista de docentes registrados
  2. Panel derecho    → selector dual (Disponibles / Asignados) con chips
  Los cursos se obtienen de la API (misma fuente que cursos_view.py)
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import List, Dict, Optional

from controllers.docentes_controller import DocentesController
from controllers.academico_controller import AcademicoController
from styles import tabla_style as st
from core.theme_manager import ThemeManager as TM


# ── Colores por nombre de curso ──────────────────────────────────────────────
PALETA = [
    "#2980b9", "#8e44ad", "#27ae60", "#e67e22", "#c0392b",
    "#16a085", "#d35400", "#2c3e50", "#1abc9c", "#7f8c8d",
    "#f39c12", "#2ecc71", "#9b59b6", "#e74c3c", "#3498db",
]

def _color_curso(nombre: str, cache: Dict[str, str]) -> str:
    """Asigna un color consistente a cada nombre de curso."""
    if nombre not in cache:
        cache[nombre] = PALETA[len(cache) % len(PALETA)]
    return cache[nombre]


# ── Vista principal ──────────────────────────────────────────────────────────
class AsignarCursoView(ctk.CTkFrame):
    """
    Vista de asignación de cursos a docentes.
    Izquierda: lista de docentes  |  Derecha: panel de asignación
    """

    def __init__(self, parent, auth_client=None):
        super().__init__(parent, fg_color="transparent")

        token = auth_client.token if auth_client else ""
        self.docentes_ctrl  = DocentesController(token)
        self.academico_ctrl = AcademicoController(token)

        # Estado
        self.docente_activo: Optional[Dict] = None      # docente seleccionado
        self.cursos_api:     List[Dict] = []              # todos los cursos de la BD
        self.cursos_asig:    List[Dict] = []              # cursos ya asignados al docente
        self._color_cache:   Dict[str, str] = {}          # cache colores por nombre
        self._item_disp:     Optional[Dict] = None        # ítem selec. en lista Disponibles
        self._item_asig:     Optional[Dict] = None        # ítem selec. en lista Asignados

        # Layout: 30% docentes | 70% asignador
        self.grid_columnconfigure(0, weight=3, minsize=300)
        self.grid_columnconfigure(1, weight=7)
        self.grid_rowconfigure(0, weight=1)

        self._build_panel_docentes()
        self._build_panel_asignador()

        # Carga inicial
        self._cargar_cursos_api()
        self._cargar_docentes()

    # =========================================================================
    # PANEL IZQUIERDO: LISTA DE DOCENTES
    # =========================================================================
    def _build_panel_docentes(self):
        self.panel_doc = ctk.CTkFrame(self, fg_color=TM.bg_panel(), corner_radius=0)
        self.panel_doc.grid(row=0, column=0, sticky="nsew", padx=(20, 8), pady=20)

        # ── Header ──
        header = ctk.CTkFrame(self.panel_doc, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(18, 8))

        ctk.CTkLabel(
            header,
            text="👨‍🏫",
            font=ctk.CTkFont(family="Arial", size=36)
        ).pack()

        ctk.CTkLabel(
            header,
            text="DOCENTES",
            font=ctk.CTkFont(family="Roboto", size=15, weight="bold"),
            text_color=TM.text()
        ).pack(pady=(4, 0))

        ctk.CTkFrame(header, height=2, fg_color=TM.primary()).pack(
            fill="x", pady=(10, 0)
        )

        # ── Buscador ──
        fr_search = ctk.CTkFrame(self.panel_doc, fg_color="transparent")
        fr_search.pack(fill="x", padx=12, pady=(8, 6))

        self.entry_buscar = ctk.CTkEntry(
            fr_search,
            placeholder_text="🔍  Buscar docente...",
            fg_color=TM.bg_card(),
            border_width=0,
            height=34,
            corner_radius=8,
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text()
        )
        self.entry_buscar.pack(fill="x")
        self.entry_buscar.bind("<KeyRelease>", lambda e: self._filtrar_docentes())

        # ── Lista scrollable ──
        self.scroll_doc = ctk.CTkScrollableFrame(
            self.panel_doc,
            fg_color="transparent"
        )
        self.scroll_doc.pack(fill="both", expand=True, padx=6, pady=(0, 10))

        # ── Pie: contador ──
        self.lbl_total_doc = ctk.CTkLabel(
            self.panel_doc,
            text="0 docentes",
            font=ctk.CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        )
        self.lbl_total_doc.pack(pady=(0, 10))

    # =========================================================================
    # PANEL DERECHO: ASIGNADOR
    # =========================================================================
    def _build_panel_asignador(self):
        self.panel_asign = ctk.CTkFrame(self, fg_color="transparent")
        self.panel_asign.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        # ── Estado vacío inicial ──
        self._mostrar_placeholder()

    def _mostrar_placeholder(self):
        """Pantalla cuando no hay docente seleccionado."""
        for w in self.panel_asign.winfo_children():
            w.destroy()

        fr = ctk.CTkFrame(self.panel_asign, fg_color=TM.bg_card(), corner_radius=12)
        fr.pack(fill="both", expand=True)

        ctk.CTkLabel(
            fr, text="📋",
            font=ctk.CTkFont(family="Arial", size=64)
        ).pack(expand=True, pady=(0, 10))

        ctk.CTkLabel(
            fr,
            text="Selecciona un docente",
            font=ctk.CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=TM.text()
        ).pack()

        ctk.CTkLabel(
            fr,
            text="Elige un docente de la lista para asignarle cursos",
            font=ctk.CTkFont(family="Roboto", size=12),
            text_color=TM.text_secondary()
        ).pack(pady=(6, 0))

    def _build_asignador(self):
        """Construye el panel derecho para el docente activo."""
        for w in self.panel_asign.winfo_children():
            w.destroy()

        d = self.docente_activo

        # ── Header docente ──────────────────────────────────────────────────
        hdr = ctk.CTkFrame(
            self.panel_asign,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=72
        )
        hdr.pack(fill="x", pady=(0, 12))
        hdr.pack_propagate(False)

        hdr_inner = ctk.CTkFrame(hdr, fg_color="transparent")
        hdr_inner.pack(fill="both", expand=True, padx=20, pady=14)

        ctk.CTkLabel(
            hdr_inner,
            text=f"👨‍🏫  {d.get('nombre', '')}",
            font=ctk.CTkFont(family="Roboto", size=16, weight="bold"),
            text_color=TM.text()
        ).pack(side="left")

        esp = d.get("especialidad", "")
        if esp and esp not in ("--", "-- Seleccione --", ""):
            ctk.CTkLabel(
                hdr_inner,
                text=f"  ·  {esp}",
                font=ctk.CTkFont(family="Roboto", size=12),
                text_color=TM.text_secondary()
            ).pack(side="left")

        # Estado del docente
        activo = d.get("activo", True)
        ctk.CTkLabel(
            hdr_inner,
            text="● Activo" if activo else "● Inactivo",
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.success() if activo else TM.danger()
        ).pack(side="right")

        # ── Título sección ──────────────────────────────────────────────────
        self._seccion_label("ASIGNACIÓN DE CURSOS")

        # ── Panel dual: Disponibles ◀▶ Asignados ───────────────────────────
        dual = ctk.CTkFrame(self.panel_asign, fg_color="transparent")
        dual.pack(fill="both", expand=True, pady=(0, 10))
        dual.grid_columnconfigure(0, weight=1)
        dual.grid_columnconfigure(1, minsize=52)
        dual.grid_columnconfigure(2, weight=1)
        dual.grid_rowconfigure(0, weight=1)

        # ─ Col izquierda: Disponibles
        col_disp = ctk.CTkFrame(dual, fg_color=TM.bg_card(), corner_radius=10)
        col_disp.grid(row=0, column=0, sticky="nsew")

        ctk.CTkLabel(
            col_disp,
            text="📚  Cursos Disponibles",
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(pady=(10, 4), padx=12, anchor="w")

        ctk.CTkFrame(col_disp, height=1, fg_color=TM.bg_panel()).pack(
            fill="x", padx=10, pady=(0, 4)
        )

        self.lista_disp = ctk.CTkScrollableFrame(
            col_disp, fg_color="transparent"
        )
        self.lista_disp.pack(fill="both", expand=True, padx=6, pady=(0, 8))

        # ─ Col central: botones
        col_btns = ctk.CTkFrame(dual, fg_color="transparent")
        col_btns.grid(row=0, column=1, padx=4)

        ctk.CTkLabel(col_btns, text="", height=40).pack()

        self.btn_asignar = ctk.CTkButton(
            col_btns,
            text="▶",
            width=40, height=36,
            corner_radius=8,
            fg_color=TM.primary(),
            hover_color="#2471a3",
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
            command=self._asignar
        )
        self.btn_asignar.pack(pady=(0, 8))

        self.btn_quitar = ctk.CTkButton(
            col_btns,
            text="◀",
            width=40, height=36,
            corner_radius=8,
            fg_color="#c0392b",
            hover_color="#922b21",
            font=ctk.CTkFont(family="Arial", size=14, weight="bold"),
            command=self._quitar
        )
        self.btn_quitar.pack()

        ctk.CTkLabel(col_btns, text="", height=20).pack()

        # ─ Col derecha: Asignados
        col_asig = ctk.CTkFrame(dual, fg_color=TM.bg_card(), corner_radius=10)
        col_asig.grid(row=0, column=2, sticky="nsew")

        ctk.CTkLabel(
            col_asig,
            text="✅  Cursos Asignados",
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.success()
        ).pack(pady=(10, 4), padx=12, anchor="w")

        ctk.CTkFrame(col_asig, height=1, fg_color=TM.bg_panel()).pack(
            fill="x", padx=10, pady=(0, 4)
        )

        self.lista_asig = ctk.CTkScrollableFrame(
            col_asig, fg_color="transparent"
        )
        self.lista_asig.pack(fill="both", expand=True, padx=6, pady=(0, 8))

        # ── Chips de cursos asignados ───────────────────────────────────────
        self._seccion_label("RESUMEN")

        self.lbl_n_cursos = ctk.CTkLabel(
            self.panel_asign,
            text="",
            font=ctk.CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        )
        self.lbl_n_cursos.pack(anchor="w", padx=4)

        self.frame_chips = ctk.CTkFrame(
            self.panel_asign,
            fg_color=TM.bg_card(),
            corner_radius=8,
            height=52
        )
        self.frame_chips.pack(fill="x", pady=(4, 10))

        # ── Botón guardar ───────────────────────────────────────────────────
        self.btn_guardar = ctk.CTkButton(
            self.panel_asign,
            text="💾  GUARDAR ASIGNACIÓN",
            height=44,
            corner_radius=10,
            fg_color=TM.success(),
            hover_color="#27ae60",
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            command=self._guardar
        )
        self.btn_guardar.pack(fill="x", pady=(0, 4))

        # ── Poblar listas ───────────────────────────────────────────────────
        self._rebuild_listas()

    # =========================================================================
    # CARGA DE DATOS DESDE API
    # =========================================================================
    def _cargar_cursos_api(self):
        """Obtiene todos los cursos desde la API (misma fuente que cursos_view)."""
        self.cursos_api = self.academico_ctrl.obtener_catalogo()

    def _cargar_docentes(self):
        """Carga y pinta la lista de docentes."""
        for w in self.scroll_doc.winfo_children():
            w.destroy()

        criterio = self.entry_buscar.get().strip()
        docentes = self.docentes_ctrl.obtener_docentes(criterio, "activos")

        if not docentes:
            ctk.CTkLabel(
                self.scroll_doc,
                text="Sin docentes registrados",
                font=ctk.CTkFont(family="Roboto", size=11),
                text_color=TM.text_secondary()
            ).pack(pady=20)
        else:
            for d in docentes:
                self._crear_card_docente(d)

        self.lbl_total_doc.configure(text=f"{len(docentes)} docente(s)")

    def _filtrar_docentes(self):
        self._cargar_docentes()

    # =========================================================================
    # CARD DE DOCENTE EN LA LISTA IZQUIERDA
    # =========================================================================
    def _crear_card_docente(self, data: Dict):
        """Tarjeta clickeable de un docente."""
        es_seleccionado = (
            self.docente_activo is not None and
            self.docente_activo.get("id") == data.get("id")
        )
        bg_card = TM.primary() if es_seleccionado else TM.bg_card()

        card = ctk.CTkFrame(
            self.scroll_doc,
            fg_color=bg_card,
            corner_radius=8,
            height=56
        )
        card.pack(fill="x", pady=3, padx=2)
        card.pack_propagate(False)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=10, pady=8)

        # Avatar circular con inicial
        inicial = (data.get("nombre", "?") or "?")[0].upper()
        avatar = ctk.CTkLabel(
            inner,
            text=inicial,
            width=36, height=36,
            fg_color=TM.primary() if not es_seleccionado else "#1a5276",
            corner_radius=18,
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            text_color="white"
        )
        avatar.pack(side="left", padx=(0, 8))

        info = ctk.CTkFrame(inner, fg_color="transparent")
        info.pack(side="left", fill="x", expand=True)

        ctk.CTkLabel(
            info,
            text=data.get("nombre", ""),
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color="white" if es_seleccionado else TM.text(),
            anchor="w"
        ).pack(fill="x")

        esp = data.get("especialidad", "") or ""
        ctk.CTkLabel(
            info,
            text=esp if esp not in ("--", "-- Seleccione --") else "Sin especialidad",
            font=ctk.CTkFont(family="Roboto", size=9),
            text_color="white" if es_seleccionado else TM.text_secondary(),
            anchor="w"
        ).pack(fill="x")

        # Hover / click
        def on_enter(e, c=card, sel=es_seleccionado):
            if not sel:
                c.configure(fg_color="#34495e")
        def on_leave(e, c=card, sel=es_seleccionado):
            if not sel:
                c.configure(fg_color=TM.bg_card())
        def on_click(e, d=data):
            self._seleccionar_docente(d)

        for w in [card, inner, avatar, info] + info.winfo_children():
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)

    # =========================================================================
    # SELECCIÓN DE DOCENTE
    # =========================================================================
    def _seleccionar_docente(self, data: Dict):
        """Activa el docente seleccionado y construye el panel derecho."""
        self.docente_activo  = data
        self._item_disp      = None
        self._item_asig      = None

        # Cargar cursos ya asignados al docente
        self.cursos_asig = self._obtener_cursos_docente(data)

        # Reconstruir panel derecho
        self._build_asignador()

        # Refrescar lista izquierda para marcar seleccionado
        self._cargar_docentes()

    def _obtener_cursos_docente(self, data: Dict) -> List[Dict]:
        """
        Devuelve los cursos actualmente asignados al docente.
        Cuando el backend esté listo usará la llamada real;
        de momento lee el campo 'cursos' del dict si existe.
        """
        cursos_txt = data.get("cursos", "") or ""
        if not cursos_txt.strip():
            return []

        nombres = [n.strip() for n in cursos_txt.split(",") if n.strip()]
        # Mapear a objetos del catálogo de la API
        result = []
        for nombre in nombres:
            match = next(
                (c for c in self.cursos_api
                 if c.get("nombre", "").strip().lower() == nombre.lower()),
                None
            )
            if match:
                result.append(match)
            else:
                # Curso asignado pero no en catálogo; lo incluimos igualmente
                result.append({"id": None, "nombre": nombre})
        return result

    # =========================================================================
    # LISTAS DISPONIBLES / ASIGNADOS
    # =========================================================================
    def _rebuild_listas(self):
        """Repinta ambas columnas desde el estado interno."""
        if not hasattr(self, "lista_disp"):
            return

        for w in self.lista_disp.winfo_children():
            w.destroy()
        for w in self.lista_asig.winfo_children():
            w.destroy()

        ids_asig = {c.get("id") for c in self.cursos_asig if c.get("id")}
        nombres_asig = {c.get("nombre", "").lower() for c in self.cursos_asig}

        # Disponibles = todos los de la API que NO estén asignados
        disponibles = [
            c for c in self.cursos_api
            if c.get("id") not in ids_asig
            and c.get("nombre", "").lower() not in nombres_asig
        ]

        for curso in disponibles:
            self._item_lista(self.lista_disp, curso, lado="disp")

        for curso in self.cursos_asig:
            self._item_lista(self.lista_asig, curso, lado="asig")

        self._actualizar_chips()

    def _item_lista(self, parent, curso: Dict, lado: str):
        """Crea un ítem clickeable en una lista."""
        nombre = curso.get("nombre", "")
        color  = _color_curso(nombre, self._color_cache)

        fr = ctk.CTkFrame(parent, fg_color="#3a3a3a", corner_radius=6, height=30)
        fr.pack(fill="x", pady=2, padx=2)
        fr.pack_propagate(False)

        ctk.CTkLabel(
            fr, text="●", width=18,
            font=ctk.CTkFont(family="Arial", size=10),
            text_color=color
        ).pack(side="left", padx=(6, 0))

        lbl = ctk.CTkLabel(
            fr, text=nombre,
            font=ctk.CTkFont(family="Roboto", size=10),
            text_color=TM.text(), anchor="w"
        )
        lbl.pack(side="left", fill="x", expand=True, padx=4)

        def on_click(e, c=curso, l=lado, f=fr):
            self._seleccionar_item(c, l, f, parent)

        def on_dbl(e, l=lado):
            self._asignar() if l == "disp" else self._quitar()

        for w in [fr, lbl]:
            w.bind("<Button-1>", on_click)
            w.bind("<Double-Button-1>", on_dbl)

    def _seleccionar_item(self, curso: Dict, lado: str,
                          frame: ctk.CTkFrame, parent):
        """Resalta el ítem seleccionado."""
        for w in parent.winfo_children():
            w.configure(fg_color="#3a3a3a")
        frame.configure(fg_color="#1a6fa8")

        if lado == "disp":
            self._item_disp = curso
        else:
            self._item_asig = curso

    def _asignar(self):
        """Mover de Disponibles → Asignados."""
        if not self._item_disp:
            return
        curso = self._item_disp
        if not any(c.get("id") == curso.get("id") and
                   c.get("nombre") == curso.get("nombre")
                   for c in self.cursos_asig):
            self.cursos_asig.append(curso)
        self._item_disp = None
        self._rebuild_listas()

    def _quitar(self):
        """Mover de Asignados → Disponibles."""
        if not self._item_asig:
            return
        curso = self._item_asig
        self.cursos_asig = [
            c for c in self.cursos_asig
            if not (c.get("id") == curso.get("id") and
                    c.get("nombre") == curso.get("nombre"))
        ]
        self._item_asig = None
        self._rebuild_listas()

    # =========================================================================
    # CHIPS DE RESUMEN
    # =========================================================================
    def _actualizar_chips(self):
        if not hasattr(self, "frame_chips"):
            return

        for w in self.frame_chips.winfo_children():
            w.destroy()

        n = len(self.cursos_asig)
        self.lbl_n_cursos.configure(
            text=f"{n} curso{'s' if n != 1 else ''} asignado{'s' if n != 1 else ''}"
        )

        if not self.cursos_asig:
            ctk.CTkLabel(
                self.frame_chips,
                text="Sin cursos asignados",
                font=ctk.CTkFont(family="Roboto", size=10),
                text_color=TM.text_secondary()
            ).pack(padx=12, pady=14)
            return

        wrap = ctk.CTkFrame(self.frame_chips, fg_color="transparent")
        wrap.pack(fill="x", padx=8, pady=8)

        for curso in self.cursos_asig:
            nombre = curso.get("nombre", "")
            color  = _color_curso(nombre, self._color_cache)

            chip = ctk.CTkFrame(wrap, fg_color=color, corner_radius=12)
            chip.pack(side="left", padx=3, pady=2)

            ctk.CTkLabel(
                chip, text=nombre,
                font=ctk.CTkFont(family="Roboto", size=9, weight="bold"),
                text_color="white"
            ).pack(side="left", padx=(8, 2), pady=4)

            ctk.CTkButton(
                chip,
                text="×",
                width=16, height=16,
                corner_radius=8,
                fg_color="transparent",
                hover_color="#00000033",
                text_color="white",
                font=ctk.CTkFont(family="Arial", size=11, weight="bold"),
                command=lambda c=curso: self._quitar_chip(c)
            ).pack(side="left", padx=(0, 4))

    def _quitar_chip(self, curso: Dict):
        """Quitar curso desde el chip directamente."""
        self.cursos_asig = [
            c for c in self.cursos_asig
            if not (c.get("id") == curso.get("id") and
                    c.get("nombre") == curso.get("nombre"))
        ]
        self._rebuild_listas()

    # =========================================================================
    # GUARDAR
    # =========================================================================
    def _guardar(self):
        """Guarda la asignación de cursos al docente activo."""
        if not self.docente_activo:
            return

        if not self.cursos_asig:
            messagebox.showwarning(
                "Sin cursos",
                "Asigna al menos un curso antes de guardar."
            )
            return

        nombres = [c.get("nombre", "") for c in self.cursos_asig]
        ids     = [c.get("id") for c in self.cursos_asig if c.get("id")]

        exito, msg = self.docentes_ctrl.asignar_cursos(
            docente_id=self.docente_activo.get("id"),
            curso_ids=ids,
            nombres=nombres
        )

        if exito:
            messagebox.showinfo("✅ Guardado", msg)
            # Refrescar
            self._cargar_cursos_api()
            self._cargar_docentes()
            self._build_asignador()
        else:
            messagebox.showerror("❌ Error", msg)

    # =========================================================================
    # HELPERS VISUALES
    # =========================================================================
    def _seccion_label(self, titulo: str):
        fr = ctk.CTkFrame(self.panel_asign, fg_color="transparent")
        fr.pack(fill="x", pady=(8, 4))

        ctk.CTkLabel(
            fr, text=titulo,
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.primary()
        ).pack(side="left")

        ctk.CTkFrame(fr, height=2, fg_color=TM.primary()).pack(
            side="left", fill="x", expand=True, padx=(8, 0)
        )
