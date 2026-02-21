# app/ui/gestion_horarios_view.py

import customtkinter as ctk
from tkinter import messagebox
import app.styles.tabla_style as st
from app.controllers.horarios_controller import HorariosController
from app.controllers.cursos_controller import CursosController
from app.controllers.docentes_controller import DocentesController

class GestionHorariosView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        self.controller = HorariosController()
        self.cursos_controller = CursosController()
        self.docentes_controller = DocentesController()
        
        self.configure(fg_color=st.Colors.BG_MAIN)
        
        self.grupo_actual = 'A'
        self.turno_actual = 'MAÑANA'
        self.periodo_actual = '2026-I'
        self.horario_data = {}
        
        self.crear_ui()
        self.cargar_horario()
    
    def crear_ui(self):
        """Crear interfaz completa"""
        
        # ============================
        # HEADER CON FILTROS
        # ============================
        fr_header = ctk.CTkFrame(self, fg_color=st.Colors.BG_PANEL, height=80)
        fr_header.pack(fill="x", padx=20, pady=20)
        fr_header.pack_propagate(False)
        
        # Título
        ctk.CTkLabel(
            fr_header,
            text="⏰ GESTIÓN DE HORARIOS",
            font=("Roboto", 18, "bold"),
            text_color="white"
        ).pack(side="left", padx=20)
        
        # Filtros
        fr_filtros = ctk.CTkFrame(fr_header, fg_color="transparent")
        fr_filtros.pack(side="left", padx=20)
        
        ctk.CTkLabel(fr_filtros, text="Grupo:", text_color="gray").pack(side="left", padx=5)
        self.cb_grupo = ctk.CTkComboBox(
            fr_filtros,
            values=self.controller.obtener_grupos_disponibles(),
            width=80,
            command=self.cambiar_filtro
        )
        self.cb_grupo.set(self.grupo_actual)
        self.cb_grupo.pack(side="left", padx=5)
        
        ctk.CTkLabel(fr_filtros, text="Turno:", text_color="gray").pack(side="left", padx=(15, 5))
        self.cb_turno = ctk.CTkComboBox(
            fr_filtros,
            values=['MAÑANA', 'TARDE'],
            width=100,
            command=self.cambiar_filtro
        )
        self.cb_turno.set(self.turno_actual)
        self.cb_turno.pack(side="left", padx=5)
        
        # Botón Actualizar
        ctk.CTkButton(
            fr_header,
            text="🔄 Actualizar",
            fg_color="#34495e",
            hover_color="#2c3e50",
            width=100,
            command=self.cargar_horario
        ).pack(side="right", padx=(5, 20))
        
        # ============================
        # TABLA HORARIA (SCROLLABLE)
        # ============================
        self.fr_tabla = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.fr_tabla.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Crear grid de horarios
        self.crear_grid_horario()
        
        # ============================
        # PANEL INFERIOR - INFO
        # ============================
        fr_info = ctk.CTkFrame(self, fg_color="#2d2d2d", height=60)
        fr_info.pack(fill="x", padx=20, pady=(0, 20))
        fr_info.pack_propagate(False)
        
        ctk.CTkLabel(
            fr_info,
            text="💡 Click en '+' para agregar una clase | Click en ✏️ para editar | Click en ❌ para eliminar",
            font=("Roboto", 10),
            text_color="gray"
        ).pack(pady=20)
    
    def crear_grid_horario(self):
        """Crear la tabla grid de horarios"""
        
        # Limpiar frame
        for widget in self.fr_tabla.winfo_children():
            widget.destroy()
        
        # Si no hay datos, mostrar mensaje
        if not self.horario_data:
            fr_empty = ctk.CTkFrame(self.fr_tabla, fg_color="transparent")
            fr_empty.pack(expand=True, fill="both", pady=100)
            
            ctk.CTkLabel(
                fr_empty,
                text="📅 No hay horarios registrados para este grupo",
                font=("Roboto", 16, "bold"),
                text_color="gray"
            ).pack(pady=10)
            
            ctk.CTkLabel(
                fr_empty,
                text="Haga click en los espacios para agregar clases",
                font=("Roboto", 12),
                text_color="gray"
            ).pack()
            
            # Mostrar grid vacío igualmente
        
        # Slots de tiempo según turno
        slots = self.controller.obtener_slots_horarios(self.turno_actual)
        dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
        
        # Crear tabla
        tabla = ctk.CTkFrame(self.fr_tabla, fg_color="transparent")
        tabla.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Configurar columnas
        tabla.columnconfigure(0, weight=0, minsize=100)  # Columna de horas
        for i in range(1, 7):
            tabla.columnconfigure(i, weight=1, minsize=180)
        
        # HEADER (Días de la semana)
        ctk.CTkLabel(
            tabla,
            text="HORA",
            font=("Roboto", 11, "bold"),
            fg_color=st.Colors.TABLE_HEADER,
            corner_radius=5,
            height=40
        ).grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        for col, dia in enumerate(dias, start=1):
            ctk.CTkLabel(
                tabla,
                text=dia.upper(),
                font=("Roboto", 11, "bold"),
                fg_color=st.Colors.TABLE_HEADER,
                corner_radius=5,
                height=40
            ).grid(row=0, column=col, sticky="nsew", padx=2, pady=2)
        
        # FILAS (Bloques horarios)
        for fila, (hora_inicio, hora_fin) in enumerate(slots, start=1):
            
            # Detectar recreo
            es_recreo = (hora_inicio == '11:00' and hora_fin == '11:30') or \
                        (hora_inicio == '17:00' and hora_fin == '17:30')
            
            # Columna de hora
            color_hora = "#34495e" if es_recreo else st.Colors.BG_PANEL
            texto_hora = "RECREO" if es_recreo else f"{hora_inicio}\n{hora_fin}"
            
            ctk.CTkLabel(
                tabla,
                text=texto_hora,
                font=("Roboto", 10, "bold"),
                fg_color=color_hora,
                corner_radius=5,
                height=100
            ).grid(row=fila, column=0, sticky="nsew", padx=2, pady=2)
            
            # Columnas de días
            for col, dia in enumerate(dias, start=1):
                if es_recreo:
                    # Celda de recreo
                    ctk.CTkLabel(
                        tabla,
                        text="☕",
                        font=("Arial", 30),
                        fg_color="#34495e",
                        corner_radius=5,
                        height=100
                    ).grid(row=fila, column=col, sticky="nsew", padx=2, pady=2)
                else:
                    # Celda normal
                    celda = self.crear_celda_horario(
                        tabla, col, hora_inicio, hora_fin
                    )
                    celda.grid(row=fila, column=col, sticky="nsew", padx=2, pady=2)
    
    def crear_celda_horario(self, parent, dia_num, hora_inicio, hora_fin):
        """Crea una celda de horario"""
        
        slot_key = f"{hora_inicio}-{hora_fin}"
        clase = self.horario_data.get(dia_num, {}).get(slot_key)
        
        if clase:
            # Celda CON CLASE
            celda = ctk.CTkFrame(
                parent,
                fg_color="#1a4d2e",  # Verde oscuro
                corner_radius=8,
                border_width=2,
                border_color="#2ecc71",
                height=100
            )
            
            fr_content = ctk.CTkFrame(celda, fg_color="transparent")
            fr_content.pack(expand=True, fill="both", padx=10, pady=8)
            
            # Curso
            ctk.CTkLabel(
                fr_content,
                text=clase.nombre_curso,
                font=("Roboto", 12, "bold"),
                text_color="white",
                wraplength=150
            ).pack()
            
            # Docente
            docente_texto = clase.nombre_docente if clase.nombre_docente else "Sin asignar"
            ctk.CTkLabel(
                fr_content,
                text=docente_texto,
                font=("Roboto", 9),
                text_color="#bdc3c7"
            ).pack(pady=(2, 0))
            
            # Aula
            aula_texto = f"[{clase.aula}]" if clase.aula else "[Sin aula]"
            ctk.CTkLabel(
                fr_content,
                text=aula_texto,
                font=("Roboto", 9, "bold"),
                text_color="#3498db"
            ).pack(pady=(2, 5))
            
            # Botones de acción
            fr_acciones = ctk.CTkFrame(fr_content, fg_color="transparent")
            fr_acciones.pack()
            
            ctk.CTkButton(
                fr_acciones,
                text="✏️",
                width=30,
                height=25,
                fg_color="#f39c12",
                hover_color="#e67e22",
                command=lambda: self.editar_bloque(clase)
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                fr_acciones,
                text="❌",
                width=30,
                height=25,
                fg_color="#e74c3c",
                hover_color="#c0392b",
                command=lambda: self.eliminar_bloque(clase)
            ).pack(side="left", padx=2)
        
        else:
            # Celda VACÍA
            celda = ctk.CTkFrame(
                parent,
                fg_color="#2d2d2d",
                corner_radius=8,
                border_width=1,
                border_color="#404040",
                height=100
            )
            
            btn_agregar = ctk.CTkButton(
                celda,
                text="+ Agregar clase",
                fg_color="transparent",
                text_color="gray",
                hover_color="#404040",
                border_width=0,
                command=lambda: self.agregar_en_slot(dia_num, hora_inicio, hora_fin)
            )
            btn_agregar.pack(expand=True, fill="both", padx=10, pady=10)
        
        return celda
    
    def cargar_horario(self):
        """Cargar horario desde BD"""
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
        from app.ui.dialogo_horario import DialogoHorario
        
        dialogo = DialogoHorario(
            self,
            self.cursos_controller,
            self.docentes_controller,
            self.controller,
            grupo=self.grupo_actual,
            dia=dia,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            turno=self.turno_actual,
            periodo=self.periodo_actual
        )
        
        # Si se guardó, recargar
        if dialogo.guardado:
            self.cargar_horario()
    
    def editar_bloque(self, clase):
        """Editar bloque existente"""
        messagebox.showinfo("Editar", f"Editar: {clase.nombre_curso}\n(Implementar diálogo de edición)")
    
    def eliminar_bloque(self, clase):
        """Eliminar bloque"""
        if messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar {clase.nombre_curso} del horario?\n\n" +
            f"Día: {clase.dia_nombre if hasattr(clase, 'dia_nombre') else 'N/A'}\n" +
            f"Hora: {clase.hora_inicio} - {clase.hora_fin}"
        ):
            exito, msg = self.controller.eliminar_bloque(clase.id)
            
            if exito:
                messagebox.showinfo("Éxito", "Horario eliminado correctamente")
                self.cargar_horario()
            else:
                messagebox.showerror("Error", msg)
