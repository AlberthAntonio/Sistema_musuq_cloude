"""
Vista de Generador de Boletas - ESTILO PREMIUM MEJORADO
Sistema Musuq Cloud
Panel dual: Controles + Vista previa de boleta
"""

import customtkinter as ctk
from tkinter import messagebox

from controllers.academico_controller import AcademicoController
from styles import tabla_style as st
from core.theme_manager import ThemeManager as TM


class BoletasView(ctk.CTkFrame):
    """
    Vista profesional para generación de boletas académicas.
    Características: Panel de controles, búsqueda de alumnos, vista previa, exportación
    """

    def __init__(self, parent, auth_client=None):
        super().__init__(parent, fg_color="transparent")
        self.controller = AcademicoController(auth_client.token if auth_client else "")
        self.alumno_seleccionado = None

        self.create_widgets()

    def create_widgets(self):
        # Layout principal con grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # ============================
        # PANEL IZQUIERDO: CONTROLES
        # ============================
        self._crear_panel_controles()

        # ============================
        # PANEL DERECHO: VISTA PREVIA
        # ============================
        self._crear_panel_preview()

    def _crear_panel_controles(self):
        """Crear panel izquierdo con controles"""
        self.panel_izq = ctk.CTkScrollableFrame(
            self,
            width=350,
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
            text="📄",
            font=ctk.CTkFont(family="Arial", size=50)
        ).pack(pady=(0, 10))

        # Título
        ctk.CTkLabel(
            header,
            text="GENERADOR DE BOLETAS",
            font=ctk.CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=TM.text()
        ).pack()

        # Separador
        ctk.CTkFrame(
            self.panel_izq,
            height=2,
            fg_color="#404040"
        ).pack(fill="x", padx=20, pady=20)

        # Sección filtros
        self._crear_seccion_filtros()

        # Sección búsqueda
        self._crear_seccion_busqueda()

        # Sección resultados
        self._crear_seccion_resultados()

        # Sección configuración
        self._crear_seccion_configuracion()

        # Separador
        ctk.CTkFrame(
            self.panel_izq,
            height=2,
            fg_color="#404040"
        ).pack(fill="x", padx=20, pady=20)

        # Botones de acción
        self._crear_botones_accion()

    def _crear_seccion_filtros(self):
        """Crear sección de filtros"""
        # Label sección
        ctk.CTkLabel(
            self.panel_izq,
            text="Filtros",
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 10))

        # Frame filtros
        frame_filtros = ctk.CTkFrame(self.panel_izq, fg_color="transparent")
        frame_filtros.pack(fill="x", padx=20, pady=(0, 15))

        # Label Grupo
        ctk.CTkLabel(
            frame_filtros,
            text="Grupo:",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(family="Roboto", size=11)
        ).pack(side="left", padx=(0, 10))

        # ComboBox Grupo
        self.combo_grupo = ctk.CTkComboBox(
            frame_filtros,
            values=["A", "B", "C", "D"],
            width=100,
            fg_color=TM.bg_card(),
            border_width=0,
            button_color=TM.primary(),
            button_hover_color="#2980b9",
            dropdown_fg_color=TM.bg_card(),
            font=ctk.CTkFont(family="Roboto", size=11)
        )
        self.combo_grupo.set("A")
        self.combo_grupo.pack(side="left")

    def _crear_seccion_busqueda(self):
        """Crear sección de búsqueda"""
        # Label sección
        ctk.CTkLabel(
            self.panel_izq,
            text="Buscar Alumno",
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 10))

        # Frame del buscador
        self.fr_search = ctk.CTkFrame(
            self.panel_izq,
            fg_color=TM.bg_card(),
            height=45,
            corner_radius=10
        )
        self.fr_search.pack(fill="x", padx=20, pady=(0, 10))
        self.fr_search.pack_propagate(False)

        # Icono de búsqueda
        ctk.CTkLabel(
            self.fr_search,
            text="🔍",
            font=ctk.CTkFont(family="Arial", size=16),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(15, 5))

        # Entry de búsqueda
        self.entry_buscar = ctk.CTkEntry(
            self.fr_search,
            placeholder_text="Apellido o Nombre...",
            border_width=0,
            fg_color="transparent",
            text_color=TM.text(),
            font=ctk.CTkFont(family="Roboto", size=12)
        )
        self.entry_buscar.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.entry_buscar.bind("<Return>", lambda e: self.buscar_alumno())

        # Botón buscar
        ctk.CTkButton(
            self.panel_izq,
            text="BUSCAR ALUMNO",
            fg_color=TM.primary(),
            hover_color="#2980b9",
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            command=self.buscar_alumno
        ).pack(fill="x", padx=20, pady=(0, 15))

    def _crear_seccion_resultados(self):
        """Crear sección de resultados"""
        # Label sección
        ctk.CTkLabel(
            self.panel_izq,
            text="Resultados de Búsqueda",
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 10))

        # Frame resultados
        self.scroll_resultados = ctk.CTkScrollableFrame(
            self.panel_izq,
            height=220,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.scroll_resultados.pack(fill="x", padx=20, pady=(0, 15))

        # Estado inicial vacío
        self._mostrar_estado_vacio_resultados()

    def _crear_seccion_configuracion(self):
        """Crear sección de configuración"""
        # Label sección
        ctk.CTkLabel(
            self.panel_izq,
            text="Configuración del Reporte",
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.warning(),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 15))

        # Frame para checkboxes
        config_frame = ctk.CTkFrame(self.panel_izq, fg_color="transparent")
        config_frame.pack(fill="x", padx=25, pady=(0, 10))

        # Checkbox Asistencia
        self.check_asistencia = ctk.CTkCheckBox(
            config_frame,
            text="Incluir Control de Asistencia",
            onvalue=True,
            offvalue=False,
            text_color=TM.text(),
            font=ctk.CTkFont(family="Roboto", size=11),
            fg_color=TM.primary(),
            hover_color="#2980b9"
        )
        self.check_asistencia.select()
        self.check_asistencia.pack(anchor="w", pady=5)

        # Checkbox Ranking
        self.check_ranking = ctk.CTkCheckBox(
            config_frame,
            text="Incluir Orden de Mérito (Ranking)",
            onvalue=True,
            offvalue=False,
            text_color=TM.text(),
            font=ctk.CTkFont(family="Roboto", size=11),
            fg_color=TM.primary(),
            hover_color="#2980b9"
        )
        self.check_ranking.select()
        self.check_ranking.pack(anchor="w", pady=5)

    def _crear_botones_accion(self):
        """Crear botones de acción"""
        # Botón actualizar vista
        ctk.CTkButton(
            self.panel_izq,
            text="🔄 ACTUALIZAR VISTA",
            fg_color=TM.warning(),
            hover_color="#d35400",
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            command=self.generar_vista_previa
        ).pack(fill="x", padx=20, pady=(0, 10))

        # Botón exportar PDF
        self.btn_export = ctk.CTkButton(
            self.panel_izq,
            text="📄 EXPORTAR PDF",
            fg_color=TM.danger(),
            hover_color="#c0392b",
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            state="disabled"
        )
        self.btn_export.pack(fill="x", padx=20, pady=(0, 10))

        # Botón imprimir
        self.btn_print = ctk.CTkButton(
            self.panel_izq,
            text="🖨️ IMPRIMIR",
            fg_color=TM.success(),
            hover_color="#27ae60",
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            state="disabled"
        )
        self.btn_print.pack(fill="x", padx=20, pady=(0, 20))

    def _crear_panel_preview(self):
        """Crear panel derecho con vista previa"""
        self.panel_der = ctk.CTkFrame(
            self,
            fg_color=TM.bg_panel(),
            corner_radius=10
        )
        self.panel_der.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        # Header del preview
        header = ctk.CTkFrame(
            self.panel_der,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=70
        )
        header.pack(fill="x", padx=20, pady=(20, 15))
        header.pack_propagate(False)

        header_content = ctk.CTkFrame(header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=25, pady=15)

        ctk.CTkLabel(
            header_content,
            text="📋 Vista Previa de Boleta",
            font=ctk.CTkFont(family="Roboto", size=20, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        ).pack(side="left")

        # Área de scroll para la hoja
        self.scroll_preview = ctk.CTkScrollableFrame(
            self.panel_der,
            fg_color="transparent"
        )
        self.scroll_preview.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # La "Hoja de Papel" blanca
        self.hoja_papel = ctk.CTkFrame(
            self.scroll_preview,
            fg_color="white",
            width=650,
            height=850,
            corner_radius=8,
            border_width=1,
            border_color="#bdc3c7"
        )
        self.hoja_papel.pack(pady=20, padx=10)

        # Estado inicial vacío
        self._mostrar_estado_vacio_preview()

    # ========================================================
    # LÓGICA DE BÚSQUEDA
    # ========================================================

    def buscar_alumno(self):
        """Buscar alumnos según filtros"""
        texto = self.entry_buscar.get().strip()
        grupo = self.combo_grupo.get()

        # Limpiar resultados
        for w in self.scroll_resultados.winfo_children():
            w.destroy()

        # Buscar
        resultados = self.controller.buscar_alumno_boleta(texto, grupo)

        if not resultados:
            self._mostrar_estado_vacio_resultados("No se encontraron alumnos")
            return

        # Mostrar resultados
        for alum in resultados:
            self._crear_item_resultado(alum)

    def _crear_item_resultado(self, alumno):
        """Crear item de resultado"""
        # Frame para hover
        item_frame = ctk.CTkFrame(
            self.scroll_resultados,
            fg_color="transparent"
        )
        item_frame.pack(fill="x", pady=1)

        # Botón del alumno
        btn = ctk.CTkButton(
            item_frame,
            text=f"{alumno.apell_paterno} {alumno.apell_materno}, {alumno.nombres}",
            fg_color="transparent",
            hover_color="#34495e",
            anchor="w",
            text_color=TM.text(),
            font=ctk.CTkFont(family="Roboto", size=11),
            height=35,
            corner_radius=5,
            command=lambda a=alumno: self.seleccionar_alumno(a)
        )
        btn.pack(fill="x")

    def seleccionar_alumno(self, alumno):
        """Seleccionar alumno y generar boleta"""
        self.alumno_seleccionado = alumno
        self.generar_vista_previa()

        # Habilitar botones
        self.btn_export.configure(state="normal")
        self.btn_print.configure(state="normal")

    def _mostrar_estado_vacio_resultados(self, mensaje="Realiza una búsqueda"):
        """Mostrar estado vacío en resultados"""
        for w in self.scroll_resultados.winfo_children():
            w.destroy()

        empty_frame = ctk.CTkFrame(self.scroll_resultados, fg_color="transparent")
        empty_frame.pack(fill="both", expand=True, pady=40)

        ctk.CTkLabel(
            empty_frame,
            text="👤",
            font=ctk.CTkFont(family="Arial", size=40)
        ).pack(pady=10)

        ctk.CTkLabel(
            empty_frame,
            text=mensaje,
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text()
        ).pack()

        ctk.CTkLabel(
            empty_frame,
            text="Usa el buscador para encontrar alumnos",
            font=ctk.CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        ).pack(pady=(5, 0))

    def _mostrar_estado_vacio_preview(self):
        """Mostrar estado vacío en preview"""
        empty_frame = ctk.CTkFrame(self.hoja_papel, fg_color="transparent")
        empty_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(
            empty_frame,
            text="📄",
            font=ctk.CTkFont(family="Arial", size=80)
        ).pack(pady=20)

        ctk.CTkLabel(
            empty_frame,
            text="Selecciona un alumno",
            font=ctk.CTkFont(family="Roboto", size=16, weight="bold"),
            text_color="#2c3e50"
        ).pack()

        ctk.CTkLabel(
            empty_frame,
            text="La boleta se generará aquí",
            font=ctk.CTkFont(family="Roboto", size=12),
            text_color="#7f8c8d"
        ).pack(pady=(5, 0))

    # ========================================================
    # GENERACIÓN DE BOLETA
    # ========================================================

    def generar_vista_previa(self):
        """Generar vista previa de la boleta"""
        if not self.alumno_seleccionado:
            messagebox.showwarning("Atención", "Seleccione un alumno primero")
            return

        # Limpiar hoja
        for w in self.hoja_papel.winfo_children():
            w.destroy()

        # Obtener data completa
        data = self.controller.obtener_data_boleta(self.alumno_seleccionado.id)
        alum = self.alumno_seleccionado

        # --- 1. ENCABEZADO ---
        self._crear_encabezado_boleta()

        # --- 2. DATOS DEL ALUMNO ---
        self._crear_datos_alumno(alum, data)

        # --- 3. TABLA DE NOTAS ---
        self._crear_tabla_notas(data)

        # --- 4. RESUMEN ASISTENCIA ---
        if self.check_asistencia.get():
            self._crear_resumen_asistencia(data['asistencia'])

        # --- 5. PIE DE PÁGINA ---
        self._crear_pie_boleta()

    def _crear_encabezado_boleta(self):
        """Crear encabezado de la boleta"""
        header_frame = ctk.CTkFrame(self.hoja_papel, fg_color="transparent")
        header_frame.pack(fill="x", padx=40, pady=30)

        # Datos del colegio
        datos_cole = ctk.CTkFrame(header_frame, fg_color="transparent")
        datos_cole.pack(side="left")

        ctk.CTkLabel(
            datos_cole,
            text="COLEGIO PRIVADO",
            font=ctk.CTkFont(family="Times New Roman", size=20, weight="bold"),
            text_color="black"
        ).pack(anchor="w")

        ctk.CTkLabel(
            datos_cole,
            text='"MUSUQ CLOUD SYSTEM"',
            font=ctk.CTkFont(family="Times New Roman", size=16),
            text_color="black"
        ).pack(anchor="w")

        ctk.CTkLabel(
            datos_cole,
            text="INFORME DE PROGRESO ACADÉMICO 2025",
            font=ctk.CTkFont(family="Arial", size=11, weight="bold"),
            text_color="gray"
        ).pack(anchor="w", pady=(5, 0))

    def _crear_datos_alumno(self, alum, data):
        """Crear sección de datos del alumno"""
        # Línea separadora
        ctk.CTkFrame(
            self.hoja_papel,
            height=2,
            fg_color="#2c3e50"
        ).pack(fill="x", padx=40, pady=(0, 20))

        # Frame de información
        info_frame = ctk.CTkFrame(
            self.hoja_papel,
            fg_color="#f8f9fa",
            corner_radius=0
        )
        info_frame.pack(fill="x", padx=40)

        # Datos en grid
        meta = [
            ("Estudiante:", f"{alum.apell_paterno} {alum.apell_materno}, {alum.nombres}"),
            ("Código:", alum.codigo_matricula),
            ("Grado/Grupo:", f"Secundaria - {alum.grupo}"),
            ("Promedio Gral:", f"{data['promedio_gral']:.2f}"),
            ("Orden de Mérito:", f"{data['puesto']}° de {data['total_alumnos']}")
        ]

        for i, (key, val) in enumerate(meta):
            row = i // 2
            col = (i % 2) * 2

            ctk.CTkLabel(
                info_frame,
                text=key,
                font=ctk.CTkFont(family="Arial", size=11, weight="bold"),
                text_color="#2c3e50"
            ).grid(row=row, column=col, sticky="w", padx=10, pady=5)

            ctk.CTkLabel(
                info_frame,
                text=val,
                font=ctk.CTkFont(family="Arial", size=11),
                text_color="black"
            ).grid(row=row, column=col + 1, sticky="w", padx=0, pady=5)

    def _crear_tabla_notas(self, data):
        """Crear tabla de notas"""
        # Container de la tabla
        tabla_container = ctk.CTkFrame(
            self.hoja_papel,
            fg_color="white",
            border_width=1,
            border_color="black",
            corner_radius=0
        )
        tabla_container.pack(fill="x", padx=40, pady=20)

        # Header de la tabla
        h_frame = ctk.CTkFrame(
            tabla_container,
            fg_color="#ecf0f1",
            corner_radius=0,
            height=30
        )
        h_frame.pack(fill="x")

        ctk.CTkLabel(
            h_frame,
            text="CURSO / ÁREA",
            font=ctk.CTkFont(family="Arial", size=10, weight="bold"),
            width=150,
            anchor="w",
            text_color="black"
        ).pack(side="left", padx=5)

        # Headers de sesiones
        right_header = ctk.CTkFrame(h_frame, fg_color="transparent")
        right_header.pack(side="right", padx=5)

        for sesion in data['sesiones']:
            nom_corto = sesion[:6] + ".." if len(sesion) > 6 else sesion
            ctk.CTkLabel(
                right_header,
                text=nom_corto,
                font=ctk.CTkFont(family="Arial", size=9, weight="bold"),
                width=50,
                text_color="black"
            ).pack(side="left", padx=2)

        ctk.CTkLabel(
            right_header,
            text="PROM",
            font=ctk.CTkFont(family="Arial", size=10, weight="bold"),
            width=50,
            text_color="black"
        ).pack(side="left", padx=5)

        # Filas de cursos
        for curso in data['cursos']:
            f_row = ctk.CTkFrame(tabla_container, fg_color="transparent", height=25)
            f_row.pack(fill="x", pady=1)

            ctk.CTkLabel(
                f_row,
                text=curso,
                font=ctk.CTkFont(family="Arial", size=10),
                anchor="w",
                text_color="black",
                width=150
            ).pack(side="left", padx=5)

            f_notas = ctk.CTkFrame(f_row, fg_color="transparent")
            f_notas.pack(side="right", padx=5)

            notas_curso = data['notas'][curso]

            # Notas por sesión
            for ses in data['sesiones']:
                val = notas_curso.get(ses, 0)
                txt = f"{val:.1f}" if val > 0 else "-"
                color = "#c0392b" if val > 0 and val < 11 else "black"

                ctk.CTkLabel(
                    f_notas,
                    text=txt,
                    font=ctk.CTkFont(family="Arial", size=10),
                    text_color=color,
                    width=50
                ).pack(side="left", padx=2)

            # Promedio de la fila
            vals = [v for v in notas_curso.values() if v > 0]
            prom = sum(vals) / len(vals) if vals else 0
            color_prom = "#c0392b" if prom < 11 else "#2980b9"

            ctk.CTkLabel(
                f_notas,
                text=f"{prom:.1f}",
                font=ctk.CTkFont(family="Arial", size=10, weight="bold"),
                text_color=color_prom,
                width=50
            ).pack(side="left", padx=5)

            # Separador
            ctk.CTkFrame(
                tabla_container,
                height=1,
                fg_color="#bdc3c7"
            ).pack(fill="x")

    def _crear_resumen_asistencia(self, asistencia):
        """Crear resumen de asistencia"""
        asist_frame = ctk.CTkFrame(
            self.hoja_papel,
            fg_color="#f4f6f7",
            border_width=1,
            border_color="#ccc",
            corner_radius=5
        )
        asist_frame.pack(fill="x", padx=40, pady=15)

        ctk.CTkLabel(
            asist_frame,
            text="CONTROL DE ASISTENCIA",
            font=ctk.CTkFont(family="Arial", size=10, weight="bold"),
            text_color="black"
        ).pack(anchor="w", padx=10, pady=(5, 0))

        resumen = (
            f"Total Días: {asistencia['total']} | "
            f"Puntual: {asistencia['puntual']} | "
            f"Tardanzas: {asistencia['tarde']} | "
            f"Faltas: {asistencia['falta']}"
        )

        ctk.CTkLabel(
            asist_frame,
            text=resumen,
            font=ctk.CTkFont(family="Arial", size=10),
            text_color="#555"
        ).pack(anchor="w", padx=10, pady=(0, 5))

    def _crear_pie_boleta(self):
        """Crear pie de página de la boleta"""
        pie_frame = ctk.CTkFrame(self.hoja_papel, fg_color="transparent")
        pie_frame.pack(fill="x", padx=40, pady=(20, 30))

        ctk.CTkLabel(
            pie_frame,
            text="Generado por Musuq Cloud System",
            font=ctk.CTkFont(family="Arial", size=9, slant="italic"),
            text_color="#7f8c8d"
        ).pack(anchor="center")
