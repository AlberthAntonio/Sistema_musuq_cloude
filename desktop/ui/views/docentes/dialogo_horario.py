"""
Diálogo para Agregar/Editar Bloques Horarios - ESTILO PREMIUM MEJORADO
Sistema Musuq Cloud
Ventana modal para asignación de clases al horario
"""

import customtkinter as ctk
from tkinter import messagebox
from customtkinter import CTkFont
from typing import Optional

from core.theme_manager import ThemeManager as TM


class DialogoHorario(ctk.CTkToplevel):
    """Ventana modal premium para agregar/editar bloques horarios"""

    _DIAS = {
        "Lunes": 1,
        "Martes": 2,
        "Miercoles": 3,
        "Jueves": 4,
        "Viernes": 5,
        "Sabado": 6,
    }

    @staticmethod
    def _generar_opciones_hora(intervalo_min: int = 15) -> list[str]:
        """Genera horas del dia en formato HH:MM para selectores."""
        opciones: list[str] = []
        for total_min in range(0, 24 * 60, intervalo_min):
            hh = total_min // 60
            mm = total_min % 60
            opciones.append(f"{hh:02d}:{mm:02d}")
        return opciones

    @staticmethod
    def _minutos_hora(hora_hhmm: str) -> int:
        hh, mm = hora_hhmm.split(":")
        return int(hh) * 60 + int(mm)

    def _hora_por_defecto(self, valor: str, fallback: str) -> str:
        if valor in self._opciones_hora:
            return valor
        return fallback

    def __init__(self, parent, cursos_ctrl, docentes_ctrl, horarios_ctrl,
                 grupo, dia, hora_inicio, hora_fin, turno, periodo,
                 aula_nombre: str = "", aula_id: int = None,
                 modo_plantilla: bool = False,
                 plantilla_bloque_id: Optional[int] = None):
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
        self.aula_nombre = aula_nombre
        self.aula_id = aula_id
        self.modo_plantilla = modo_plantilla
        self.plantilla_bloque_id = plantilla_bloque_id
        self._opciones_hora = self._generar_opciones_hora(intervalo_min=15)
        self.guardado = False
        # Datos del bloque guardado (disponibles tras guardar exitosamente)
        self.nuevo_id: int | None = None
        self.curso_nombre_guardado: str = ""
        self.docente_nombre_guardado: str = ""

        # Configuración ventana
        self.title("Gestion de Bloque" if self.modo_plantilla else "Agregar Clase al Horario")
        self.geometry("500x620" if self.modo_plantilla else "480x550")
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
        if self.modo_plantilla:
            self._crear_formulario_plantilla(fr_main)
        else:
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
            text=(
                f"Bloque Personalizado - Grupo {self.grupo}"
                if self.modo_plantilla
                else f"Agregar Clase - Grupo {self.grupo}"
            ),
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
            text=(
                f"📍 {self.aula_nombre or 'Sin aula'}  •  Grupo {self.grupo}  •  Turno {self.turno}"
                if self.modo_plantilla
                else f"📅 {dia_nombre}  •  ⏰ {self.hora_inicio} - {self.hora_fin}"
            ),
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

        # AULA (solo lectura – se pasa desde HorariosView)
        ctk.CTkLabel(
            form,
            text="Aula:",
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        ).pack(fill="x", pady=(0, 8))

        fr_aula = ctk.CTkFrame(
            form,
            fg_color=TM.bg_card(),
            corner_radius=8,
            height=42,
            border_width=1,
            border_color="#404040"
        )
        fr_aula.pack(fill="x", pady=(0, 20))
        fr_aula.pack_propagate(False)

        ctk.CTkLabel(
            fr_aula,
            text=f"📍  {self.aula_nombre}" if self.aula_nombre else "📍  (sin aula seleccionada)",
            font=CTkFont(family="Roboto", size=11),
            text_color=TM.primary() if self.aula_nombre else TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", expand=True, padx=14, pady=10)

    def _crear_formulario_plantilla(self, parent):
        """Formulario para crear bloque personalizado por día/hora/tipo."""
        form = ctk.CTkFrame(parent, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=25)

        ctk.CTkLabel(
            form,
            text="Dia:",
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text(),
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        dia_por_num = {v: k for k, v in self._DIAS.items()}
        dia_default = dia_por_num.get(self.dia, "Lunes")
        self.cb_dia = ctk.CTkComboBox(
            form,
            values=list(self._DIAS.keys()),
            width=430,
            height=40,
            fg_color=TM.bg_card(),
            border_width=1,
            border_color="#404040",
            button_color=TM.primary(),
            button_hover_color="#2980b9",
            dropdown_fg_color=TM.bg_card(),
            font=CTkFont(family="Roboto", size=11),
        )
        self.cb_dia.pack(pady=(0, 16))
        self.cb_dia.set(dia_default)

        horas_row = ctk.CTkFrame(form, fg_color="transparent")
        horas_row.pack(fill="x", pady=(0, 16))
        horas_row.grid_columnconfigure(0, weight=1)
        horas_row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            horas_row,
            text="Hora inicio (HH:MM):",
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.text(),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=(0, 8), pady=(0, 6))
        ctk.CTkLabel(
            horas_row,
            text="Hora fin (HH:MM):",
            font=CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.text(),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", padx=(8, 0), pady=(0, 6))

        self.cb_hora_inicio = ctk.CTkComboBox(
            horas_row,
            values=self._opciones_hora,
            height=38,
            fg_color=TM.bg_card(),
            border_width=1,
            border_color="#404040",
            button_color=TM.primary(),
            button_hover_color="#2980b9",
            dropdown_fg_color=TM.bg_card(),
            font=CTkFont(family="Roboto", size=11),
            command=self._on_hora_inicio_change,
        )
        self.cb_hora_inicio.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.cb_hora_inicio.set(self._hora_por_defecto(self.hora_inicio or "", "08:00"))

        self.cb_hora_fin = ctk.CTkComboBox(
            horas_row,
            values=self._opciones_hora,
            height=38,
            fg_color=TM.bg_card(),
            border_width=1,
            border_color="#404040",
            button_color=TM.primary(),
            button_hover_color="#2980b9",
            dropdown_fg_color=TM.bg_card(),
            font=CTkFont(family="Roboto", size=11),
        )
        self.cb_hora_fin.grid(row=1, column=1, sticky="ew", padx=(8, 0))
        self.cb_hora_fin.set(self._hora_por_defecto(self.hora_fin or "", "08:45"))
        self._on_hora_inicio_change(self.cb_hora_inicio.get())

        ctk.CTkLabel(
            form,
            text="Tipo de bloque:",
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text(),
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        self.cb_tipo_bloque = ctk.CTkComboBox(
            form,
            values=["CLASE", "RECREO", "LIBRE"],
            width=430,
            height=40,
            fg_color=TM.bg_card(),
            border_width=1,
            border_color="#404040",
            button_color=TM.primary(),
            button_hover_color="#2980b9",
            dropdown_fg_color=TM.bg_card(),
            font=CTkFont(family="Roboto", size=11),
        )
        self.cb_tipo_bloque.pack(pady=(0, 16))
        self.cb_tipo_bloque.set("CLASE")

        ctk.CTkLabel(
            form,
            text="Etiqueta (opcional):",
            font=CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text(),
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        self.ent_etiqueta = ctk.CTkEntry(
            form,
            height=38,
            fg_color=TM.bg_card(),
            border_width=1,
            border_color="#404040",
            font=CTkFont(family="Roboto", size=11),
            placeholder_text="Ejemplo: Recreo largo o Laboratorio",
        )
        self.ent_etiqueta.pack(fill="x", pady=(0, 8))

        nota = ctk.CTkFrame(form, fg_color=TM.bg_card(), corner_radius=8)
        nota.pack(fill="x", pady=(8, 0))
        ctk.CTkLabel(
            nota,
            text="Los bloques CLASE podran recibir curso/docente desde la grilla.",
            font=CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary(),
            justify="left",
            wraplength=400,
            anchor="w",
        ).pack(fill="x", padx=12, pady=10)

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
            text="💾 Guardar Bloque" if self.modo_plantilla else "💾 Guardar Clase",
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

    def _on_hora_inicio_change(self, hora_inicio: str):
        """Ajusta opciones de hora fin para que siempre sea mayor al inicio."""
        if not hora_inicio or hora_inicio not in self._opciones_hora:
            return

        inicio_min = self._minutos_hora(hora_inicio)
        opciones_fin = [h for h in self._opciones_hora if self._minutos_hora(h) > inicio_min]

        if not opciones_fin:
            opciones_fin = ["23:59"]

        actual_fin = self.cb_hora_fin.get()
        self.cb_hora_fin.configure(values=opciones_fin)
        if actual_fin in opciones_fin:
            self.cb_hora_fin.set(actual_fin)
        else:
            self.cb_hora_fin.set(opciones_fin[0])

    def guardar(self):
        """Guardar el bloque horario"""
        if self.modo_plantilla:
            self._guardar_bloque_personalizado()
            return

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

        aula = self.aula_nombre or None

        # Guardar
        exito, msg, nuevo_id = self.horarios_ctrl.agregar_bloque(
            curso_id=curso['id'],
            docente_id=docente_id,
            grupo=self.grupo,
            dia_semana=self.dia,
            hora_inicio=self.hora_inicio,
            hora_fin=self.hora_fin,
            aula=aula,
            aula_id=self.aula_id,
            turno=self.turno,
            periodo=self.periodo,
            plantilla_bloque_id=self.plantilla_bloque_id,
        )

        if exito:
            self.guardado = True
            self.nuevo_id = nuevo_id
            self.curso_nombre_guardado = curso_nombre
            self.docente_nombre_guardado = docente_nombre if docente_nombre != "Sin asignar" else ""
            messagebox.showinfo("Éxito", "Horario agregado correctamente")
            self.destroy()
        else:
            messagebox.showerror("Error", msg)
            self.lift()

    def _guardar_bloque_personalizado(self):
        """Crear bloque de plantilla por día/hora/tipo."""
        if not self.aula_id:
            messagebox.showwarning("Validación", "Debe seleccionar un aula antes de crear bloques")
            self.lift()
            return

        dia_label = self.cb_dia.get()
        dia_semana = self._DIAS.get(dia_label)
        hora_inicio = (self.cb_hora_inicio.get() or "").strip()
        hora_fin = (self.cb_hora_fin.get() or "").strip()
        tipo_bloque = (self.cb_tipo_bloque.get() or "CLASE").strip().upper()
        etiqueta = (self.ent_etiqueta.get() or "").strip()

        if dia_semana is None:
            messagebox.showwarning("Validación", "Seleccione un día válido")
            self.lift()
            return

        if len(hora_inicio) != 5 or len(hora_fin) != 5 or ":" not in hora_inicio or ":" not in hora_fin:
            messagebox.showwarning("Validación", "Use formato HH:MM para hora inicio y fin")
            self.lift()
            return

        if hora_inicio >= hora_fin:
            messagebox.showwarning("Validación", "La hora de inicio debe ser menor a la hora fin")
            self.lift()
            return

        exito, msg, bloque_id = self.horarios_ctrl.crear_bloque_plantilla_personalizado(
            aula_id=self.aula_id,
            grupo=self.grupo,
            periodo=self.periodo,
            turno=self.turno,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            tipo_bloque=tipo_bloque,
            etiqueta=etiqueta or None,
        )

        if exito:
            self.guardado = True
            self.nuevo_id = bloque_id
            self.curso_nombre_guardado = ""
            self.docente_nombre_guardado = ""
            messagebox.showinfo("Éxito", "Bloque personalizado creado correctamente")
            self.destroy()
        else:
            messagebox.showerror("Error", msg)
            self.lift()
