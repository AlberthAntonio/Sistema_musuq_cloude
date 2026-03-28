"""
Vista de Gestión de Horarios – REDISEÑADA
Sistema Musuq Cloud
Flujo: Seleccionar Aula → Gestionar horario de esa aula por grupo
"""

import customtkinter as ctk
from tkinter import messagebox
from customtkinter import CTkFont

from controllers.academico_controller import AcademicoController
from controllers.docentes_controller import DocentesController
from controllers.aulas_controller import AulasController
from ui.views.docentes.dialogo_horario import DialogoHorario
from core.theme_manager import ThemeManager as TM

_COLOR_MODALIDAD = {
    "COLEGIO":   "#3498db",
    "VIRTUAL":   "#9b59b6",
    "MIXTA":     "#f39c12",
    "TALLER":    "#e67e22",
    "AUDITORIO": "#16a085",
}


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

        self.controller          = AcademicoController(auth_client.token if auth_client else "")
        self.docentes_controller = DocentesController(auth_client.token if auth_client else "")
        self.aulas_controller    = AulasController(auth_client.token if auth_client else "")

        # ── Estado ────────────────────────────────────────────
        self.aula_seleccionada: dict | None = None
        self.grupo_actual   = "A"
        self.turno_actual   = "MAÑANA"
        self.periodo_actual = "2026-I"
        self.horario_data: dict = {}
        self.todas_las_aulas: list = []

        # ── Layout 33 / 67 ────────────────────────────────────
        self.grid_columnconfigure(0, weight=15, minsize=280)
        self.grid_columnconfigure(1, weight=85)
        self.grid_rowconfigure(0, weight=1)

        self._crear_panel_aulas()
        self._crear_panel_horario()

        self.cargar_aulas()

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
        self.cb_turno.set(self.turno_actual)
        self.cb_turno.pack(side="left")

        # Derecha: actualizar
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

    def _crear_celda(self, parent, dia_num: int, h_ini: str, h_fin: str) -> ctk.CTkFrame:
        slot_key = f"{h_ini}-{h_fin}"
        clase = self.horario_data.get(dia_num, {}).get(slot_key)
        return (
            self._celda_con_clase(parent, clase)
            if clase else
            self._celda_vacia(parent, dia_num, h_ini, h_fin)
        )

    def _celda_con_clase(self, parent, clase: dict) -> ctk.CTkFrame:
        celda = ctk.CTkFrame(
            parent, fg_color="#1a4d2e", corner_radius=10,
            border_width=2, border_color=TM.success(), height=100
        )
        fc = ctk.CTkFrame(celda, fg_color="transparent")
        fc.pack(expand=True, fill="both", padx=10, pady=8)

        ctk.CTkLabel(
            fc, text=clase["nombre_curso"],
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            text_color="white", wraplength=145
        ).pack()

        doc_txt = clase.get("nombre_docente") or "Sin docente"
        ctk.CTkLabel(
            fc, text=f"👤 {doc_txt}",
            font=CTkFont(family="Roboto", size=9),
            text_color="#bdc3c7"
        ).pack(pady=(2, 0))

        fr_btns = ctk.CTkFrame(fc, fg_color="transparent")
        fr_btns.pack(pady=(4, 0))

        ctk.CTkButton(
            fr_btns, text="✏️", width=30, height=24,
            fg_color=TM.warning(), hover_color="#d35400", corner_radius=6,
            font=CTkFont(family="Arial", size=10),
            command=lambda c=clase: self._editar_bloque(c)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            fr_btns, text="❌", width=30, height=24,
            fg_color=TM.danger(), hover_color="#c0392b", corner_radius=6,
            font=CTkFont(family="Arial", size=10),
            command=lambda c=clase: self._eliminar_bloque(c)
        ).pack(side="left", padx=2)

        return celda

    def _celda_vacia(self, parent, dia_num: int, h_ini: str, h_fin: str) -> ctk.CTkFrame:
        celda = ctk.CTkFrame(
            parent, fg_color="#2d2d2d", corner_radius=10,
            border_width=1, border_color="#404040", height=100
        )
        ctk.CTkButton(
            celda, text="➕\nAgregar",
            fg_color="transparent", text_color="#7f8c8d", hover_color="#404040",
            font=CTkFont(family="Roboto", size=10),
            command=lambda: self._agregar_en_slot(dia_num, h_ini, h_fin)
        ).pack(expand=True, fill="both")
        return celda

    # ═══════════════════════════════════════════════════════════
    #  CARGA Y FILTRADO DE AULAS
    # ═══════════════════════════════════════════════════════════

    def cargar_aulas(self):
        """Carga todas las aulas activas desde la API."""
        self.todas_las_aulas = self.aulas_controller.listar(activo=True)
        self._filtrar_aulas()

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
        """Carga el horario del aula seleccionada y reconstruye el grid."""
        if not self.aula_seleccionada:
            self._mostrar_placeholder()
            return

        exito, msg, datos = self.controller.obtener_horario_aula(
            aula_id=self.aula_seleccionada["id"],
            grupo=self.grupo_actual,
            periodo=self.periodo_actual,
        )
        self.horario_data = datos if exito else {}
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

        slots = self.controller.obtener_slots_horarios(self.turno_actual)
        dias  = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

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
            es_recreo = h_ini in ("11:00", "17:00") and h_fin in ("11:30", "17:30")
            texto_hora = "☕\nRECREO" if es_recreo else f"{h_ini}\n{h_fin}"
            color_hora = "#34495e"   if es_recreo else TM.bg_card()

            ctk.CTkLabel(
                tabla, text=texto_hora,
                font=CTkFont(family="Roboto", size=10, weight="bold"),
                fg_color=color_hora, corner_radius=8, height=100
            ).grid(row=fila, column=0, sticky="nsew", padx=2, pady=2)

            for col, _ in enumerate(dias, start=1):
                if es_recreo:
                    ctk.CTkLabel(
                        tabla, text="☕",
                        font=CTkFont(family="Arial", size=28),
                        fg_color="#34495e", corner_radius=8, height=100
                    ).grid(row=fila, column=col, sticky="nsew", padx=2, pady=2)
                else:
                    celda = self._crear_celda(tabla, col, h_ini, h_fin)
                    celda.grid(row=fila, column=col, sticky="nsew", padx=2, pady=2)

    # ═══════════════════════════════════════════════════════════
    #  ACCIONES
    # ═══════════════════════════════════════════════════════════

    def _cambiar_filtro(self, event=None):
        self.grupo_actual = self.cb_grupo.get()
        self.turno_actual = self.cb_turno.get()
        self.cargar_horario()

    def _agregar_en_slot(self, dia: int, h_ini: str, h_fin: str):
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
        )
        self.wait_window(dialogo)
        if dialogo.guardado:
            # Actualización optimista: mostrar la clase al instante sin esperar la API
            slot_key = f"{h_ini}-{h_fin}"
            if dia not in self.horario_data:
                self.horario_data[dia] = {}
            self.horario_data[dia][slot_key] = {
                "id":             dialogo.nuevo_id,
                "nombre_curso":   dialogo.curso_nombre_guardado,
                "nombre_docente": dialogo.docente_nombre_guardado,
                "aula":           dialogo.aula_nombre,
                "grupo":          self.grupo_actual,
                "dia":            dia,
                "hora_inicio":    h_ini,
                "hora_fin":       h_fin,
            }
            self._construir_grid()

    def _editar_bloque(self, clase: dict):
        messagebox.showinfo(
            "Editar bloque",
            f"Edición de «{clase['nombre_curso']}» — próximamente."
        )

    def _eliminar_bloque(self, clase: dict):
        if not messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar «{clase['nombre_curso']}» del horario?\n"
            f"{clase.get('hora_inicio', '')} – {clase.get('hora_fin', '')}"
        ):
            return

        exito, msg = self.controller.eliminar_bloque_horario(clase["id"])
        if exito:
            messagebox.showinfo("Listo", "Bloque eliminado correctamente.")
            self.cargar_horario()
        else:
            messagebox.showerror("Error", msg)

    def refresh(self):
        """Llamado por main_window al mostrar esta vista."""
        self.cargar_aulas()
        if self.aula_seleccionada:
            self.cargar_horario()
