# app/ui/dialogo_horario.py

import customtkinter as ctk
from tkinter import messagebox

class DialogoHorario(ctk.CTkToplevel):
    """Ventana modal para agregar/editar bloques horarios"""
    
    def __init__(self, parent, cursos_ctrl, docentes_ctrl, horarios_ctrl,
                 grupo, dia, hora_inicio, hora_fin, turno, periodo):
        super().__init__(parent)
        
        self.cursos_ctrl = cursos_ctrl
        self.docentes_ctrl = docentes_ctrl
        self.horarios_ctrl = horarios_ctrl
        
        self.grupo = grupo
        self.dia = dia
        self.hora_inicio = hora_inicio
        self.hora_fin = hora_fin
        self.turno = turno
        self.periodo = periodo
        
        self.guardado = False
        
        # Configuración ventana
        self.title("Agregar Clase al Horario")
        self.geometry("450x400")
        self.resizable(False, False)
        
        # Centrar ventana
        self.transient(parent)
        self.grab_set()
        
        self.crear_ui()
    
    def crear_ui(self):
        """Crear interfaz del diálogo"""
        
        # Frame principal
        fr_main = ctk.CTkFrame(self, fg_color="#2d2d2d")
        fr_main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(
            fr_main,
            text=f"Agregar Clase - Grupo {self.grupo}",
            font=("Roboto", 16, "bold")
        ).pack(pady=(10, 20))
        
        # Info del slot
        dias_nombres = {1: 'Lunes', 2: 'Martes', 3: 'Miércoles', 
                       4: 'Jueves', 5: 'Viernes', 6: 'Sábado'}
        dia_nombre = dias_nombres.get(self.dia, 'Día desconocido')
        
        ctk.CTkLabel(
            fr_main,
            text=f"📅 {dia_nombre} | ⏰ {self.hora_inicio} - {self.hora_fin}",
            font=("Roboto", 11),
            text_color="#3498db"
        ).pack(pady=(0, 20))
        
        # CURSO
        ctk.CTkLabel(
            fr_main,
            text="Curso / Materia:",
            font=("Roboto", 11, "bold"),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(5, 2))
        
        self.cb_curso = ctk.CTkComboBox(
            fr_main,
            values=self.cursos_ctrl.obtener_nombres_para_combobox(),
            width=400
        )
        self.cb_curso.pack(padx=20, pady=(0, 15))
        self.cb_curso.set("Seleccione un curso")
        
        # DOCENTE
        ctk.CTkLabel(
            fr_main,
            text="Docente:",
            font=("Roboto", 11, "bold"),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(5, 2))
        
        docentes = ['Sin asignar'] + self.docentes_ctrl.obtener_nombres_para_combobox()
        self.cb_docente = ctk.CTkComboBox(
            fr_main,
            values=docentes,
            width=400
        )
        self.cb_docente.pack(padx=20, pady=(0, 15))
        self.cb_docente.set("Sin asignar")
        
        # AULA
        ctk.CTkLabel(
            fr_main,
            text="Aula:",
            font=("Roboto", 11, "bold"),
            anchor="w"
        ).pack(fill="x", padx=20, pady=(5, 2))
        
        self.entry_aula = ctk.CTkEntry(
            fr_main,
            placeholder_text="Ej: A-01, LAB-02, PATIO",
            width=400
        )
        self.entry_aula.pack(padx=20, pady=(0, 20))
        
        # Botones
        fr_botones = ctk.CTkFrame(fr_main, fg_color="transparent")
        fr_botones.pack(pady=(10, 10))
        
        ctk.CTkButton(
            fr_botones,
            text="Cancelar",
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            width=150,
            command=self.destroy
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            fr_botones,
            text="Guardar",
            fg_color="#2ecc71",
            hover_color="#27ae60",
            width=150,
            command=self.guardar
        ).pack(side="left", padx=10)
    
    def guardar(self):
        """Guardar el bloque horario"""
        
        # Validar curso
        curso_nombre = self.cb_curso.get()
        if curso_nombre == "Seleccione un curso":
            messagebox.showwarning("Validación", "Debe seleccionar un curso")
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
