"""
Vista de Gestión de Horarios - ESTILO PREMIUM MEJORADO
Sistema Musuq Cloud
Tabla horaria con grid responsive, filtros y asignación de clases
"""

import customtkinter as ctk
from tkinter import messagebox
from customtkinter import CTkFont

from styles import tabla_style as st
from controllers.academico_controller import AcademicoController
from controllers.docentes_controller import DocentesController
from ui.views.academico.dialogo_horario import DialogoHorario
from core.theme_manager import ThemeManager as TM


class HorariosView(ctk.CTkFrame):
    """
    Vista profesional para gestión de horarios escolares.
    Características: Tabla horaria grid, filtros, asignación de clases
    """

    def __init__(self, parent, auth_client=None):
        super().__init__(parent, fg_color="transparent")

        # Controllers
        self.controller = AcademicoController(auth_client.token if auth_client else "")
        self.docentes_controller = DocentesController(auth_client.token if auth_client else "")

        # Estado
        self.grupo_actual = 'A'
        self.turno_actual = 'MAÑANA'
        self.periodo_actual = '2026-I'
        self.horario_data = {}

        self.crear_ui()
        self.cargar_horario()

    def crear_ui(self):
        """Crear interfaz completa"""
        # Header con filtros
        self._crear_header()

        # Tabla horaria
        self._crear_tabla()

        # Panel de información
        self._crear_panel_info()

    def _crear_header(self):
        """Crear header con título y filtros"""
        fr_header = ctk.CTkFrame(
            self,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=90
        )
        fr_header.pack(fill="x", padx=20, pady=20)
        fr_header.pack_propagate(False)

        # Container interno
        header_content = ctk.CTkFrame(fr_header, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=25, pady=15)

        # Lado izquierdo: Título
        left_side = ctk.CTkFrame(header_content, fg_color="transparent")
        left_side.pack(side="left", fill="y")

        ctk.CTkLabel(
            left_side,
            text="⏰ GESTIÓN DE HORARIOS",
            font=CTkFont(family="Roboto", size=20, weight="bold"),
            text_color=TM.text()
        ).pack(anchor="w")

        ctk.CTkLabel(
            left_side,
            text="Organiza las clases por días y horarios",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(anchor="w", pady=(2, 0))

        # Centro: Filtros
        fr_filtros = ctk.CTkFrame(header_content, fg_color="transparent")
        fr_filtros.pack(side="left", padx=40)

        # Filtro Grupo
        ctk.CTkLabel(
            fr_filtros,
            text="Grupo:",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(0, 8))

        self.cb_grupo = ctk.CTkComboBox(
            fr_filtros,
            values=self.controller.obtener_grupos_disponibles(),
            width=90,
            fg_color=TM.bg_card(),
            border_width=1,
            border_color="#404040",
            button_color=TM.primary(),
            button_hover_color="#2980b9",
            dropdown_fg_color=TM.bg_card(),
            font=CTkFont(family="Roboto", size=11),
            command=self.cambiar_filtro
        )
        self.cb_grupo.set(self.grupo_actual)
        self.cb_grupo.pack(side="left", padx=(0, 20))

        # Filtro Turno
        ctk.CTkLabel(
            fr_filtros,
            text="Turno:",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(0, 8))

        self.cb_turno = ctk.CTkComboBox(
            fr_filtros,
            values=['MAÑANA', 'TARDE'],
            width=110,
            fg_color=TM.bg_card(),
            border_width=1,
            border_color="#404040",
            button_color=TM.primary(),
            button_hover_color="#2980b9",
            dropdown_fg_color=TM.bg_card(),
            font=CTkFont(family="Roboto", size=11),
            command=self.cambiar_filtro
        )
        self.cb_turno.set(self.turno_actual)
        self.cb_turno.pack(side="left")

        # Derecha: Botón Actualizar
        ctk.CTkButton(
            header_content,
            text="🔄 Actualizar",
            fg_color=TM.warning(),
            hover_color="#d35400",
            width=120,
            height=38,
            corner_radius=8,
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            command=self.cargar_horario
        ).pack(side="right")

    def _crear_tabla(self):
        """Crear tabla horaria scrollable"""
        self.fr_tabla = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.fr_tabla.pack(fill="both", expand=True, padx=20, pady=(0, 15))

    def _crear_panel_info(self):
        """Crear panel de información inferior"""
        fr_info = ctk.CTkFrame(
            self,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=65
        )
        fr_info.pack(fill="x", padx=20, pady=(0, 20))
        fr_info.pack_propagate(False)

        info_content = ctk.CTkFrame(fr_info, fg_color="transparent")
        info_content.pack(fill="both", expand=True, padx=20, pady=15)

        ctk.CTkLabel(
            info_content,
            text="💡 Ayuda:",
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.warning()
        ).pack(side="left")

        ctk.CTkLabel(
            info_content,
            text="  Click en ➕ para agregar clase  •  Click en ✏️ para editar  •  Click en ❌ para eliminar",
            font=CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(5, 0))

    def crear_grid_horario(self):
        """Crear la tabla grid de horarios"""
        # Limpiar frame
        for widget in self.fr_tabla.winfo_children():
            widget.destroy()

        # Obtener slots y días
        slots = self.controller.obtener_slots_horarios(self.turno_actual)
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']

        # Crear tabla
        tabla = ctk.CTkFrame(self.fr_tabla, fg_color="transparent")
        tabla.pack(fill="both", expand=True, padx=5, pady=5)

        # Configurar columnas
        tabla.columnconfigure(0, weight=0, minsize=100)
        for i in range(1, 7):
            tabla.columnconfigure(i, weight=1, minsize=180)

        # HEADER (Días de la semana)
        self._crear_header_tabla(tabla, dias)

        # FILAS (Bloques horarios)
        self._crear_filas_horario(tabla, slots, dias)

    def _crear_header_tabla(self, tabla, dias):
        """Crear header de la tabla con días de la semana"""
        # Celda "HORA"
        ctk.CTkLabel(
            tabla,
            text="⏰ HORA",
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            fg_color=TM.primary(),
            text_color="white",
            corner_radius=8,
            height=45
        ).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)

        # Días de la semana
        for col, dia in enumerate(dias, start=1):
            ctk.CTkLabel(
                tabla,
                text=dia.upper(),
                font=CTkFont(family="Roboto", size=11, weight="bold"),
                fg_color=TM.primary(),
                text_color="white",
                corner_radius=8,
                height=45
            ).grid(row=0, column=col, sticky="nsew", padx=2, pady=2)

    def _crear_filas_horario(self, tabla, slots, dias):
        """Crear filas de bloques horarios"""
        for fila, (hora_inicio, hora_fin) in enumerate(slots, start=1):
            # Detectar recreo
            es_recreo = (hora_inicio == '11:00' and hora_fin == '11:30') or \
                        (hora_inicio == '17:00' and hora_fin == '17:30')

            # Columna de hora
            self._crear_celda_hora(tabla, fila, hora_inicio, hora_fin, es_recreo)

            # Columnas de días
            for col, dia in enumerate(dias, start=1):
                if es_recreo:
                    self._crear_celda_recreo(tabla, fila, col)
                else:
                    celda = self.crear_celda_horario(tabla, col, hora_inicio, hora_fin)
                    celda.grid(row=fila, column=col, sticky="nsew", padx=2, pady=2)

    def _crear_celda_hora(self, tabla, fila, hora_inicio, hora_fin, es_recreo):
        """Crear celda de columna de hora"""
        if es_recreo:
            color_hora = "#34495e"
            texto_hora = "☕\nRECREO"
        else:
            color_hora = TM.bg_card()
            texto_hora = f"{hora_inicio}\n{hora_fin}"

        ctk.CTkLabel(
            tabla,
            text=texto_hora,
            font=CTkFont(family="Roboto", size=10, weight="bold"),
            fg_color=color_hora,
            corner_radius=8,
            height=105
        ).grid(row=fila, column=0, sticky="nsew", padx=2, pady=2)

    def _crear_celda_recreo(self, tabla, fila, col):
        """Crear celda de recreo"""
        ctk.CTkLabel(
            tabla,
            text="☕",
            font=CTkFont(family="Arial", size=35),
            fg_color="#34495e",
            corner_radius=8,
            height=105
        ).grid(row=fila, column=col, sticky="nsew", padx=2, pady=2)

    def crear_celda_horario(self, parent, dia_num, hora_inicio, hora_fin):
        """Crear una celda de horario (con clase o vacía)"""
        slot_key = f"{hora_inicio}-{hora_fin}"
        clase = self.horario_data.get(dia_num, {}).get(slot_key)

        if clase:
            return self._crear_celda_con_clase(parent, clase)
        else:
            return self._crear_celda_vacia(parent, dia_num, hora_inicio, hora_fin)

    def _crear_celda_con_clase(self, parent, clase):
        """Crear celda con clase asignada"""
        celda = ctk.CTkFrame(
            parent,
            fg_color="#1a4d2e",
            corner_radius=10,
            border_width=2,
            border_color=TM.success(),
            height=105
        )

        fr_content = ctk.CTkFrame(celda, fg_color="transparent")
        fr_content.pack(expand=True, fill="both", padx=12, pady=10)

        # Nombre del curso
        ctk.CTkLabel(
            fr_content,
            text=clase["nombre_curso"],
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color="white",
            wraplength=150
        ).pack()

        # Docente
        docente_texto = clase["nombre_docente"] if clase["nombre_docente"] else "Sin asignar"
        ctk.CTkLabel(
            fr_content,
            text=f"👤 {docente_texto}",
            font=CTkFont(family="Roboto", size=9),
            text_color="#bdc3c7"
        ).pack(pady=(3, 0))

        # Aula
        aula_texto = f"📍 {clase['aula']}" if clase["aula"] else "📍 Sin aula"
        ctk.CTkLabel(
            fr_content,
            text=aula_texto,
            font=CTkFont(family="Roboto", size=9, weight="bold"),
            text_color="#3498db"
        ).pack(pady=(3, 5))

        # Botones de acción
        fr_acciones = ctk.CTkFrame(fr_content, fg_color="transparent")
        fr_acciones.pack()

        ctk.CTkButton(
            fr_acciones,
            text="✏️",
            width=32,
            height=26,
            fg_color=TM.warning(),
            hover_color="#d35400",
            corner_radius=6,
            font=CTkFont(family="Arial", size=11),
            command=lambda: self.editar_bloque(clase)
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            fr_acciones,
            text="❌",
            width=32,
            height=26,
            fg_color=TM.danger(),
            hover_color="#c0392b",
            corner_radius=6,
            font=CTkFont(family="Arial", size=11),
            command=lambda: self.eliminar_bloque(clase)
        ).pack(side="left", padx=2)

        return celda

    def _crear_celda_vacia(self, parent, dia_num, hora_inicio, hora_fin):
        """Crear celda vacía con botón agregar"""
        celda = ctk.CTkFrame(
            parent,
            fg_color="#2d2d2d",
            corner_radius=10,
            border_width=1,
            border_color="#404040",
            height=105
        )

        btn_agregar = ctk.CTkButton(
            celda,
            text="➕\nAgregar",
            fg_color="transparent",
            text_color="#7f8c8d",
            hover_color="#404040",
            border_width=0,
            font=CTkFont(family="Roboto", size=11),
            command=lambda: self.agregar_en_slot(dia_num, hora_inicio, hora_fin)
        )
        btn_agregar.pack(expand=True, fill="both")

        return celda

    # ========================================================
    # ACCIONES
    # ========================================================

    def cargar_horario(self):
        """Cargar horario desde Controller"""
        exito, msg, datos = self.controller.obtener_horario_grupo(
            self.grupo_actual,
            self.periodo_actual
        )

        if exito:
            self.horario_data = datos
        else:
            self.horario_data = {}

        self.crear_grid_horario()

    def cambiar_filtro(self, event=None):
        """Cambiar grupo/turno"""
        self.grupo_actual = self.cb_grupo.get()
        self.turno_actual = self.cb_turno.get()
        self.cargar_horario()

    def agregar_en_slot(self, dia, hora_inicio, hora_fin):
        """Abrir diálogo para agregar clase"""
        dialogo = DialogoHorario(
            self,
            self.controller,
            self.docentes_controller,
            self.controller,
            grupo=self.grupo_actual,
            dia=dia,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            turno=self.turno_actual,
            periodo=self.periodo_actual
        )

        # Esperar a que cierre
        self.wait_window(dialogo)

        if dialogo.guardado:
            self.cargar_horario()

    def editar_bloque(self, clase):
        """Editar bloque (implementar según necesidad)"""
        messagebox.showinfo("Editar", f"Función de edición para {clase['nombre_curso']}")

    def eliminar_bloque(self, clase):
        """Eliminar bloque"""
        if messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar {clase['nombre_curso']} del horario?\n{clase['hora_inicio']} - {clase['hora_fin']}"
        ):
            exito, msg = self.controller.eliminar_bloque_horario(clase["id"])

            if exito:
                messagebox.showinfo("Éxito", "Horario eliminado correctamente")
                self.cargar_horario()
            else:
                messagebox.showerror("Error", msg)
