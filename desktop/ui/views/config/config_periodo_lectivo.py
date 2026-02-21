"""
ConfigPeriodoView - VERSIÓN VISUAL PREMIUM (Musuq Cloud)
Refactor visual usando ThemeManager (TM), lógica intacta.
"""

import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import date, datetime

import styles.tabla_style as st
from core.theme_manager import TM


class ConfigPeriodoView(ctk.CTkFrame):
    def __init__(self, master, auth_client=None):
        super().__init__(master, fg_color=TM.bg_main())

        # self.controller = PeriodoController() # ← Después

        # Variables de estado
        self.periodo_seleccionado = None
        self.periodo_activo_actual = "2026-I"

        # Layout: 40% lista, 60% formulario/acciones
        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=6)
        self.grid_rowconfigure(0, weight=1)

        # Paneles
        self._crear_panel_lista()
        self._crear_panel_derecho()

        # Calcular duración inicial
        self.calcular_duracion()

    # ============================
    # PANEL IZQUIERDO: TIMELINE
    # ============================

    def _crear_panel_lista(self):
        self.panel_lista = ctk.CTkFrame(
            self,
            fg_color=TM.bg_panel(),
            corner_radius=15,
            border_width=1,
            border_color=TM.bg_card(),
        )
        self.panel_lista.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Header
        ctk.CTkLabel(
            self.panel_lista,
            text="📊 PERIODOS",
            font=("Roboto", 16, "bold"),
            text_color=TM.text(),
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self.panel_lista,
            text="Gestión de ciclos académicos",
            font=("Roboto", 10),
            text_color=TM.text_secondary(),
        ).pack(pady=(0, 10))

        # Periodo actual destacado
        fr_actual = ctk.CTkFrame(
            self.panel_lista, fg_color=TM.primary(), corner_radius=10
        )
        fr_actual.pack(fill="x", padx=15, pady=(5, 15))

        ctk.CTkLabel(
            fr_actual,
            text="📌 PERIODO ACTUAL",
            font=("Roboto", 9, "bold"),
            text_color="white",
        ).pack(pady=(8, 2))

        ctk.CTkLabel(
            fr_actual,
            text=self.periodo_activo_actual,
            font=("Roboto", 20, "bold"),
            text_color="white",
        ).pack(pady=(0, 8))

        # Lista de periodos (scrollable)
        self.scroll_periodos = ctk.CTkScrollableFrame(
            self.panel_lista, fg_color="transparent"
        )
        self.scroll_periodos.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Cargar periodos dummy
        self.cargar_periodos_dummy()

        # Botón nuevo periodo
        self.btn_nuevo = ctk.CTkButton(
            self.panel_lista,
            text="➕ NUEVO PERIODO",
            fg_color=TM.success(),
            hover_color="#27ae60",
            height=40,
            command=self.activar_formulario_nuevo,
        )
        self.btn_nuevo.pack(fill="x", padx=15, pady=(0, 15))

    # ============================
    # PANEL DERECHO: TABVIEW
    # ============================

    def _crear_panel_derecho(self):
        self.panel_derecho = ctk.CTkFrame(self, fg_color="transparent")
        self.panel_derecho.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")

        # Tabview (pestañas)
        self.tabview = ctk.CTkTabview(
            self.panel_derecho,
            fg_color=TM.bg_panel(),
            segmented_button_fg_color=TM.bg_card(),
            segmented_button_selected_color=TM.primary(),
            segmented_button_selected_hover_color=TM.hover(),
        )
        self.tabview.pack(fill="both", expand=True)

        # Crear pestañas
        self.tabview.add("➕ Crear Nuevo")
        self.tabview.add("📊 Estadísticas")
        self.tabview.add("⚙️ Acciones")

        # Construir contenido de cada pestaña
        self._crear_tab_crear_nuevo()
        self._crear_tab_estadisticas()
        self._crear_tab_acciones()

    def _crear_tab_crear_nuevo(self):
        """PESTAÑA 1: CREAR NUEVO"""
        tab1 = self.tabview.tab("➕ Crear Nuevo")
        fr_form = ctk.CTkFrame(tab1, fg_color="transparent")
        fr_form.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            fr_form,
            text="📝 NUEVO PERIODO ACADÉMICO",
            font=("Roboto", 16, "bold"),
            text_color=TM.text(),
        ).pack(pady=(0, 20))

        # Año
        ctk.CTkLabel(
            fr_form,
            text="Año *",
            anchor="w",
            text_color=TM.text_secondary(),
            font=("Roboto", 11),
        ).pack(fill="x", pady=(5, 2))

        self.entry_anio = ctk.CTkEntry(
            fr_form,
            placeholder_text="2026",
            height=40,
            font=("Roboto", 14),
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_anio.pack(fill="x", pady=(0, 15))
        self.entry_anio.insert(0, str(date.today().year))

        # Ciclo/Periodo
        ctk.CTkLabel(
            fr_form,
            text="Periodo/Ciclo *",
            anchor="w",
            text_color=TM.text_secondary(),
            font=("Roboto", 11),
        ).pack(fill="x", pady=(5, 2))

        self.combo_ciclo = ctk.CTkComboBox(
            fr_form,
            values=[
                "I (Primer Semestre)",
                "II (Segundo Semestre)",
                "ANUAL (Año Completo)",
                "VERANO (Ciclo de Verano)",
                "TRIMESTRE-1",
                "TRIMESTRE-2",
                "TRIMESTRE-3",
            ],
            height=40,
            fg_color=TM.bg_card(),
            dropdown_fg_color=TM.bg_panel(),
            button_color=TM.primary(),
            button_hover_color=TM.hover(),
            text_color=TM.text(),
            state="readonly",
        )
        self.combo_ciclo.set("I (Primer Semestre)")
        self.combo_ciclo.pack(fill="x", pady=(0, 15))

        # Separador
        ctk.CTkFrame(fr_form, height=2, fg_color=TM.bg_card()).pack(fill="x", pady=15)

        # Fechas
        ctk.CTkLabel(
            fr_form,
            text="📅 DURACIÓN DEL PERIODO",
            font=("Roboto", 12, "bold"),
            text_color=TM.primary(),
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        # Fecha inicio
        fr_fecha_inicio = ctk.CTkFrame(fr_form, fg_color="transparent")
        fr_fecha_inicio.pack(fill="x", pady=5)

        ctk.CTkLabel(
            fr_fecha_inicio,
            text="Fecha de Inicio *",
            width=150,
            anchor="w",
            text_color=TM.text_secondary(),
        ).pack(side="left", padx=(0, 10))

        self.cal_inicio = DateEntry(
            fr_fecha_inicio,
            width=20,
            background="darkblue",
            foreground="white",
            borderwidth=2,
            date_pattern="dd/mm/yyyy",
            font=("Roboto", 11),
        )
        self.cal_inicio.pack(side="left", fill="x", expand=True)

        # Fecha fin
        fr_fecha_fin = ctk.CTkFrame(fr_form, fg_color="transparent")
        fr_fecha_fin.pack(fill="x", pady=5)

        ctk.CTkLabel(
            fr_fecha_fin,
            text="Fecha de Fin *",
            width=150,
            anchor="w",
            text_color=TM.text_secondary(),
        ).pack(side="left", padx=(0, 10))

        self.cal_fin = DateEntry(
            fr_fecha_fin,
            width=20,
            background="darkblue",
            foreground="white",
            borderwidth=2,
            date_pattern="dd/mm/yyyy",
            font=("Roboto", 11),
        )
        self.cal_fin.pack(side="left", fill="x", expand=True)

        # Info de duración
        self.lbl_duracion = ctk.CTkLabel(
            fr_form,
            text="📊 Duración: 0 días",
            text_color=TM.text_muted(),
            font=("Roboto", 10),
        )
        self.lbl_duracion.pack(anchor="w", pady=(5, 15))

        self.cal_inicio.bind("<<DateEntrySelected>>", self.calcular_duracion)
        self.cal_fin.bind("<<DateEntrySelected>>", self.calcular_duracion)

        # Separador
        ctk.CTkFrame(fr_form, height=2, fg_color=TM.bg_card()).pack(fill="x", pady=15)

        # Opciones
        self.chk_establecer_activo = ctk.CTkCheckBox(
            fr_form,
            text="✅ Establecer como periodo activo",
            fg_color=TM.success(),
            hover_color="#2ecc71",
            font=("Roboto", 11),
            text_color=TM.text(),
        )
        self.chk_establecer_activo.pack(anchor="w", pady=5)
        self.chk_establecer_activo.select()

        ctk.CTkLabel(
            fr_form,
            text="⚠️ Al activar, el periodo actual pasará a histórico",
            text_color=TM.warning(),
            font=("Roboto", 9),
        ).pack(anchor="w", pady=(0, 20))

        # Botón crear
        self.btn_crear = ctk.CTkButton(
            fr_form,
            text="💾 CREAR PERIODO",
            height=50,
            font=("Roboto", 14, "bold"),
            fg_color=TM.success(),
            hover_color="#2ecc71",
            command=self.crear_periodo,
        )
        self.btn_crear.pack(fill="x", pady=(10, 0))

    def _crear_tab_estadisticas(self):
        """PESTAÑA 2: ESTADÍSTICAS"""
        tab2 = self.tabview.tab("📊 Estadísticas")
        fr_stats = ctk.CTkFrame(tab2, fg_color="transparent")
        fr_stats.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            fr_stats,
            text=f"📊 ESTADÍSTICAS DEL PERIODO {self.periodo_activo_actual}",
            font=("Roboto", 16, "bold"),
            text_color=TM.text(),
        ).pack(pady=(0, 20))

        # Cards de estadísticas
        stats_data = [
            ("👥 Alumnos Matriculados", "250", TM.primary()),
            ("📚 Cursos Activos", "15", TM.success()),
            ("👨‍🏫 Docentes Asignados", "12", TM.warning()),
            ("💰 Ingresos Totales", "S/ 125,000", TM.success()),
        ]

        for titulo, valor, color in stats_data:
            self.crear_card_estadistica(fr_stats, titulo, valor, color)

        # Separador
        ctk.CTkFrame(fr_stats, height=2, fg_color=TM.bg_card()).pack(fill="x", pady=20)

        # Progreso del periodo
        ctk.CTkLabel(
            fr_stats,
            text="📅 PROGRESO DEL PERIODO",
            font=("Roboto", 12, "bold"),
            text_color=TM.primary(),
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        fr_progreso = ctk.CTkFrame(fr_stats, fg_color=TM.bg_card(), corner_radius=10)
        fr_progreso.pack(fill="x", pady=10)

        fr_progreso_content = ctk.CTkFrame(fr_progreso, fg_color="transparent")
        fr_progreso_content.pack(fill="x", padx=20, pady=15)

        self.progress_periodo = ctk.CTkProgressBar(
            fr_progreso_content, height=20, corner_radius=10, progress_color=TM.primary()
        )
        self.progress_periodo.pack(fill="x", pady=(0, 5))
        self.progress_periodo.set(0.45)

        ctk.CTkLabel(
            fr_progreso_content,
            text="Días transcurridos: 68 de 150 (45%)",
            text_color=TM.text_secondary(),
            font=("Roboto", 10),
        ).pack(anchor="w")

        ctk.CTkLabel(
            fr_progreso_content,
            text="Días restantes: 82 días",
            text_color=TM.text_secondary(),
            font=("Roboto", 10),
        ).pack(anchor="w")

    def _crear_tab_acciones(self):
        """PESTAÑA 3: ACCIONES"""
        tab3 = self.tabview.tab("⚙️ Acciones")
        fr_acciones = ctk.CTkFrame(tab3, fg_color="transparent")
        fr_acciones.pack(fill="both", expand=True, padx=30, pady=20)

        ctk.CTkLabel(
            fr_acciones,
            text=f"⚙️ GESTIÓN DEL PERIODO {self.periodo_activo_actual}",
            font=("Roboto", 16, "bold"),
            text_color=TM.text(),
        ).pack(pady=(0, 20))

        # Acción 1: Generar reporte
        fr_accion1 = ctk.CTkFrame(fr_acciones, fg_color=TM.bg_card(), corner_radius=10)
        fr_accion1.pack(fill="x", pady=10)

        fr_accion1_content = ctk.CTkFrame(fr_accion1, fg_color="transparent")
        fr_accion1_content.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            fr_accion1_content,
            text="📄 GENERAR REPORTE COMPLETO",
            font=("Roboto", 12, "bold"),
            text_color=TM.text(),
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            fr_accion1_content,
            text="Exporta estadísticas, asistencias y notas del periodo",
            text_color=TM.text_secondary(),
            font=("Roboto", 9),
            anchor="w",
        ).pack(fill="x", pady=(2, 10))

        ctk.CTkButton(
            fr_accion1_content,
            text="📊 Generar Reporte PDF",
            fg_color=TM.primary(),
            hover_color=TM.hover(),
            command=self.generar_reporte,
        ).pack(fill="x")

        # Acción 2: Cerrar periodo
        fr_accion2 = ctk.CTkFrame(fr_acciones, fg_color=TM.bg_card(), corner_radius=10)
        fr_accion2.pack(fill="x", pady=10)

        fr_accion2_content = ctk.CTkFrame(fr_accion2, fg_color="transparent")
        fr_accion2_content.pack(fill="x", padx=20, pady=15)

        ctk.CTkLabel(
            fr_accion2_content,
            text="🔒 CERRAR PERIODO",
            font=("Roboto", 12, "bold"),
            text_color=TM.warning(),
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            fr_accion2_content,
            text="Marca el periodo como finalizado y archiva datos",
            text_color=TM.text_secondary(),
            font=("Roboto", 9),
            anchor="w",
        ).pack(fill="x", pady=(2, 10))

        ctk.CTkButton(
            fr_accion2_content,
            text="🔒 Cerrar Periodo Actual",
            fg_color=TM.warning(),
            hover_color="#d35400",
            command=self.cerrar_periodo,
        ).pack(fill="x")

        # Advertencia
        fr_warning = ctk.CTkFrame(fr_acciones, fg_color=TM.danger(), corner_radius=10)
        fr_warning.pack(fill="x", pady=(20, 0))

        ctk.CTkLabel(
            fr_warning,
            text="⚠️ ADVERTENCIA IMPORTANTE",
            font=("Roboto", 11, "bold"),
            text_color="white",
        ).pack(padx=15, pady=(10, 5))

        warning_text = """Al cerrar un periodo:
• No se podrán registrar más asistencias
• No se podrán modificar notas
• Los datos quedarán como históricos
• Esta acción NO se puede deshacer"""

        ctk.CTkLabel(
            fr_warning,
            text=warning_text,
            text_color="white",
            font=("Roboto", 9),
            justify="left",
        ).pack(padx=25, pady=(0, 10))

    # =================== MÉTODOS UI HELPERS ===================

    def crear_item_periodo(self, anio, ciclo, fecha_inicio, fecha_fin, alumnos, estado, activo):
        """Crear item de periodo en timeline"""
        bg = TM.bg_card() if not activo else TM.hover()
        fr_periodo = ctk.CTkFrame(self.scroll_periodos, fg_color=bg, corner_radius=10)
        fr_periodo.pack(fill="x", pady=5)

        # Barra lateral indicadora
        color_barra = TM.success() if activo else TM.text_muted()
        ctk.CTkFrame(
            fr_periodo, width=5, fg_color=color_barra, corner_radius=0
        ).pack(side="left", fill="y")

        # Contenido
        fr_content = ctk.CTkFrame(fr_periodo, fg_color="transparent")
        fr_content.pack(side="left", fill="both", expand=True, padx=15, pady=12)

        # Fila 1: Nombre + badge
        fr_row1 = ctk.CTkFrame(fr_content, fg_color="transparent")
        fr_row1.pack(fill="x")

        icono = "●" if activo else "○"
        ctk.CTkLabel(
            fr_row1,
            text=f"{icono} {anio}-{ciclo}",
            font=("Roboto", 14, "bold"),
            text_color=TM.text(),
            anchor="w",
        ).pack(side="left")

        # Badge de estado
        color_badge = {
            "ACTIVO": TM.success(),
            "CERRADO": "#95a5a6",
            "PROGRAMADO": TM.warning(),
        }.get(estado, "#7f8c8d")

        lbl_badge = ctk.CTkLabel(
            fr_row1,
            text=estado,
            font=("Arial", 8, "bold"),
            text_color="white",
            fg_color=color_badge,
            corner_radius=5,
            width=70,
            height=18,
        )
        lbl_badge.pack(side="right")

        # Fila 2: Fechas
        ctk.CTkLabel(
            fr_content,
            text=f"📅 {fecha_inicio} → {fecha_fin}",
            font=("Roboto", 9),
            text_color=TM.text_secondary(),
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # Fila 3: Alumnos
        ctk.CTkLabel(
            fr_content,
            text=f"👥 {alumnos} alumnos matriculados",
            font=("Roboto", 9),
            text_color=TM.text_secondary(),
            anchor="w",
        ).pack(fill="x")

    def crear_card_estadistica(self, parent, titulo, valor, color):
        """Crear card de estadística"""
        fr_card = ctk.CTkFrame(parent, fg_color=TM.bg_card(), corner_radius=10)
        fr_card.pack(fill="x", pady=5)

        # Barra lateral
        ctk.CTkFrame(fr_card, width=5, fg_color=color, corner_radius=0).pack(
            side="left", fill="y"
        )

        # Contenido
        fr_content = ctk.CTkFrame(fr_card, fg_color="transparent")
        fr_content.pack(side="left", fill="both", expand=True, padx=15, pady=12)

        ctk.CTkLabel(
            fr_content,
            text=titulo,
            font=("Roboto", 10),
            text_color=TM.text_secondary(),
            anchor="w",
        ).pack(fill="x")

        ctk.CTkLabel(
            fr_content,
            text=valor,
            font=("Roboto", 20, "bold"),
            text_color=TM.text(),
            anchor="w",
        ).pack(fill="x")

    def cargar_periodos_dummy(self):
        """Cargar periodos de ejemplo"""
        periodos_ejemplo = [
            ("2026", "I", "01/03", "31/07", 250, "ACTIVO", True),
            ("2025", "II", "01/08", "31/12", 230, "CERRADO", False),
            ("2025", "I", "01/03", "31/07", 220, "CERRADO", False),
            ("2024", "II", "01/08", "31/12", 210, "CERRADO", False),
        ]

        for anio, ciclo, inicio, fin, alumnos, estado, activo in periodos_ejemplo:
            self.crear_item_periodo(anio, ciclo, inicio, fin, alumnos, estado, activo)

    # =================== MÉTODOS DE LÓGICA ===================

    def calcular_duracion(self, event=None):
        """Calcular duración entre fechas"""
        try:
            fecha_inicio = self.cal_inicio.get_date()
            fecha_fin = self.cal_fin.get_date()

            if fecha_fin < fecha_inicio:
                self.lbl_duracion.configure(
                    text="⚠️ La fecha de fin debe ser posterior al inicio",
                    text_color=TM.danger(),
                )
                return

            dias = (fecha_fin - fecha_inicio).days
            meses = dias // 30
            texto = f"📊 Duración: {dias} días"
            if meses > 0:
                texto += f" (~{meses} meses)"

            self.lbl_duracion.configure(text=texto, text_color=TM.text_muted())
        except:
            self.lbl_duracion.configure(
                text="📊 Duración: --", text_color=TM.text_muted()
            )

    def activar_formulario_nuevo(self):
        """Cambiar a pestaña de crear nuevo"""
        self.tabview.set("➕ Crear Nuevo")

    def crear_periodo(self):
        """Validar y crear nuevo periodo"""
        anio = self.entry_anio.get().strip()
        ciclo = self.combo_ciclo.get().split()[0]
        fecha_inicio = self.cal_inicio.get_date()
        fecha_fin = self.cal_fin.get_date()
        establecer_activo = self.chk_establecer_activo.get() == 1

        # Validaciones
        errores = []

        if not anio or not anio.isdigit():
            errores.append("- El año debe ser un número válido")
        elif int(anio) < 2020 or int(anio) > 2050:
            errores.append("- El año debe estar entre 2020 y 2050")

        if fecha_fin <= fecha_inicio:
            errores.append("- La fecha de fin debe ser posterior al inicio")

        duracion = (fecha_fin - fecha_inicio).days
        if duracion < 30:
            errores.append("- El periodo debe durar al menos 30 días")

        if errores:
            messagebox.showwarning("Validación", "\n".join(errores))
            return

        # Confirmación
        nombre_periodo = f"{anio}-{ciclo}"
        mensaje_confirmacion = f"¿Crear periodo '{nombre_periodo}'?\n\n"
        mensaje_confirmacion += f"Inicio: {fecha_inicio.strftime('%d/%m/%Y')}\n"
        mensaje_confirmacion += f"Fin: {fecha_fin.strftime('%d/%m/%Y')}\n"
        mensaje_confirmacion += f"Duración: {duracion} días\n"
        if establecer_activo:
            mensaje_confirmacion += f"\n⚠️ Se establecerá como periodo ACTIVO"

        if not messagebox.askyesno("Confirmar", mensaje_confirmacion):
            return

        periodo_data = {
            "anio": anio,
            "ciclo": ciclo,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "activo": establecer_activo,
        }

        messagebox.showinfo(
            "✅ Periodo Creado",
            f"Periodo académico '{nombre_periodo}' creado correctamente\n\n"
            f"Duración: {duracion} días\n"
            f"Estado: {'ACTIVO' if establecer_activo else 'PROGRAMADO'}\n\n"
            f"(Funcionalidad de guardado pendiente)",
        )

        self.tabview.set("📊 Estadísticas")

    def generar_reporte(self):
        """Generar reporte del periodo"""
        messagebox.showinfo(
            "Reporte",
            f"Generando reporte completo del periodo {self.periodo_activo_actual}:\n\n"
            f"• Resumen de asistencias\n"
            f"• Estadísticas de notas\n"
            f"• Resumen financiero\n"
            f"• Lista de alumnos\n\n"
            f"(Funcionalidad pendiente)",
        )

    def cerrar_periodo(self):
        """Cerrar periodo actual"""
        confirmacion = messagebox.askyesno(
            "⚠️ Cerrar Periodo",
            f"¿Está seguro de cerrar el periodo {self.periodo_activo_actual}?\n\n"
            f"Al cerrar el periodo:\n"
            f"• No se podrán registrar más asistencias\n"
            f"• No se podrán modificar notas\n"
            f"• Los datos quedarán como históricos\n"
            f"• Esta acción NO se puede deshacer\n\n"
            f"¿Continuar?",
        )

        if not confirmacion:
            return

        confirmacion2 = messagebox.askyesno(
            "⚠️ CONFIRMACIÓN FINAL",
            f"Esta es su última oportunidad.\n\n"
            f"¿Realmente desea CERRAR el periodo {self.periodo_activo_actual}?",
        )

        if confirmacion2:
            messagebox.showinfo(
                "Periodo Cerrado",
                f"Periodo {self.periodo_activo_actual} cerrado correctamente\n\n"
                f"Los datos han sido archivados.\n"
                f"Cree un nuevo periodo para continuar operando.\n\n"
                f"(Funcionalidad pendiente)",
            )
