"""
Diálogo para Agregar/Editar Bloques Horarios - ESTILO PREMIUM MEJORADO
Sistema Musuq Cloud
Ventana modal para asignación de clases al horario
"""

import customtkinter as ctk
from tkinter import messagebox
from customtkinter import CTkFont

from core.theme_manager import ThemeManager as TM


class DialogoHorario(ctk.CTkToplevel):
    """Ventana modal premium para agregar/editar bloques horarios"""

    def __init__(self, parent, cursos_ctrl, docentes_ctrl, horarios_ctrl,
                 grupo, dia, hora_inicio, hora_fin, turno, periodo):
        super().__init__(parent)

        # Controllers
        self.cursos_ctrl = cursos_ctrl
        self.docentes_ctrl = docentes_ctrl
        self.horarios_ctrl = horarios_ctrl

        # Datos
        self.grupo = grupo
        self.dia = dia
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.turno = turno
        self.periodo = periodo
        self.guardado = False

        # Configuración ventana
        self.title("Agregar Clase al Horario")
        self.geometry("480x550")
        self.resizable(False, False)

        # Centrar ventana y hacerla modal
        self.transient(parent)
        self.grab_set()

        self.crear_ui()

    def crear_ui(self):
        """Crear interfaz del diálogo"""
        # Frame principal scrollable (para que siempre se pueda acceder a los botones)
        fr_main = ctk.CTkScrollableFrame(
            self,
            fg_color=TM.bg_panel(),
            corner_radius=0
        )
        fr_main.pack(fill="both", expand=True)

        # Header
        self._crear_header(fr_main)

        # Separador
        ctk.CTkFrame(
            fr_main,
            height=2,
            fg_color="#404040"
        ).pack(fill="x", padx=25, pady=20)

        # Formulario
        self._crear_formulario(fr_main)

        # Botones
        self._crear_botones(fr_main)

    def _crear_header(self, parent):
        """Crear header del diálogo"""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.pack(fill="x", padx=25, pady=(25, 0))

        # Icono grande
        ctk.CTkLabel(
            header,
            text="📅",
            font=CTkFont(family="Arial", size=50)
        ).pack(pady=(0, 10))

        # Título
        ctk.CTkLabel(
            header,
            text=f"Agregar Clase - Grupo {self.grupo}",
            font=CTkFont(family="Roboto", size=18, weight="bold"),
            text_color=TM.text()
        ).pack()

        # Info del slot
        dias_nombres = {
            1: 'Lunes', 2: 'Martes', 3: 'Miércoles',
            4: 'Jueves', 5: 'Viernes', 6: 'Sábado'
        }
        dia_nombre = dias_nombres.get(self.dia, 'Día desconocido')

        info_frame = ctk.CTkFrame(header, fg_color=TM.bg_card(), corner_radius=8)
        info_frame.pack(fill="x", pady=(10, 0))

        ctk.CTkLabel(
            info_frame,
            text=f"📅 {dia_nombre}  •  ⏰ {self.hora_inicio} - {self.hora_fin}",
            font=CTkFont(family="Roboto", size=12),
            text_color=TM.primary()
        ).pack(pady=12)

    def _crear_formulario(self, parent):
        """Crear formulario con campos"""
        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=25)

        # CURSO
        ctk.CTkLabel(
            form,
            text="Curso / Materia:",
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        ).pack(fill="x", pady=(0, 8))

        self.cb_curso = ctk.CTkComboBox(
            form,
            values=self.cursos_ctrl.obtener_nombres_para_combobox(),
            width=430,
            height=40,
            fg_color=TM.bg_card(),
            border_width=1,
            border_color="#404040",
            button_color=TM.primary(),
            button_hover_color="#2980b9",
            dropdown_fg_color=TM.bg_card(),
            font=CTkFont(family="Roboto", size=11),
            command=self._on_curso_change,
        )
        self.cb_curso.pack(pady=(0, 20))
        self.cb_curso.set("Seleccione un curso")

        # DOCENTE
        ctk.CTkLabel(
            form,
            text="Docente:",
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        ).pack(fill="x", pady=(0, 8))

        # Inicialmente solo "Sin asignar"; al elegir curso se filtrarán docentes
        self.cb_docente = ctk.CTkComboBox(
            form,
            values=["Sin asignar"],
            width=430,
            height=40,
            fg_color=TM.bg_card(),
            border_width=1,
            border_color="#404040",
            button_color=TM.primary(),
            button_hover_color="#2980b9",
            dropdown_fg_color=TM.bg_card(),
            font=CTkFont(family="Roboto", size=11)
        )
        self.cb_docente.pack(pady=(0, 20))
        self.cb_docente.set("Sin asignar")

        # AULA
        ctk.CTkLabel(
            form,
            text="Aula:",
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        ).pack(fill="x", pady=(0, 8))

        self.entry_aula = ctk.CTkEntry(
            form,
            placeholder_text="Ej: A-01, LAB-02, PATIO",
            width=430,
            height=40,
            fg_color=TM.bg_card(),
            border_width=1,
            border_color="#404040",
            text_color=TM.text(),
            font=CTkFont(family="Roboto", size=11)
        )
        self.entry_aula.pack(pady=(0, 20))

    def _crear_botones(self, parent):
        """Crear botones de acción"""
        # Separador
        ctk.CTkFrame(
            parent,
            height=2,
            fg_color="#404040"
        ).pack(fill="x", padx=25, pady=(0, 20))

        # Frame botones
        fr_botones = ctk.CTkFrame(parent, fg_color="transparent")
        fr_botones.pack(pady=(0, 25))

        # Botón Cancelar
        ctk.CTkButton(
            fr_botones,
            text="Cancelar",
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            width=180,
            height=42,
            corner_radius=8,
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            command=self.destroy
        ).pack(side="left", padx=8)

        # Botón Guardar
        ctk.CTkButton(
            fr_botones,
            text="💾 Guardar Clase",
            fg_color=TM.success(),
            hover_color="#27ae60",
            width=180,
            height=42,
            corner_radius=8,
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            command=self.guardar
        ).pack(side="left", padx=8)

    def _on_curso_change(self, curso_nombre: str):
        """Actualizar la lista de docentes según el curso seleccionado."""
        if not curso_nombre or curso_nombre == "Seleccione un curso":
            # Volver a estado base
            self.cb_docente.configure(values=["Sin asignar"])
            self.cb_docente.set("Sin asignar")
            return

        curso = self.cursos_ctrl.buscar_por_nombre(curso_nombre)
        if not curso:
            self.cb_docente.configure(values=["Sin asignar"])
            self.cb_docente.set("Sin asignar")
            return

        nombres_docentes = self.docentes_ctrl.obtener_docentes_por_curso(curso.get("id"))
        valores = ["Sin asignar"] + nombres_docentes
        self.cb_docente.configure(values=valores)
        # Mantener selección si sigue siendo válida; si no, resetear
        actual = self.cb_docente.get()
        if actual not in valores:
            self.cb_docente.set("Sin asignar")

    def guardar(self):
        """Guardar el bloque horario"""
        # Validar curso
        curso_nombre = self.cb_curso.get()
        if curso_nombre == "Seleccione un curso":
            messagebox.showwarning("Validación", "Debe seleccionar un curso")
            self.lift()
            return

        # Buscar IDs
        curso = self.cursos_ctrl.buscar_por_nombre(curso_nombre)
        if not curso:
            messagebox.showerror("Error", "Curso no encontrado")
            return

        docente_nombre = self.cb_docente.get()
        docente_id = None
        if docente_nombre != "Sin asignar":
            docente = self.docentes_ctrl.buscar_por_nombre(docente_nombre)
            if docente:
                docente_id = docente['id']

        aula = self.entry_aula.get().strip() or None

        # Guardar
        exito, msg, nuevo_id = self.horarios_ctrl.agregar_bloque(
            curso_id=curso['id'],
            docente_id=docente_id,
            grupo=self.grupo,
            dia_semana=self.dia,
            hora_inicio=self.hora_inicio,
            hora_fin=self.hora_fin,
            aula=aula,
            turno=self.turno,
            periodo=self.periodo
        )

        if exito:
            self.guardado = True
            messagebox.showinfo("Éxito", "Horario agregado correctamente")
            self.destroy()
        else:
            messagebox.showerror("Error", msg)
            self.lift()
