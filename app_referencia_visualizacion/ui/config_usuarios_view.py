# app/ui/config_usuarios_view.py
import customtkinter as ctk
from tkinter import messagebox
import app.styles.tabla_style as st

class ConfigUsuariosView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        # self.controller = UsuarioController()  # ← Después
        
        # Variables de estado
        self.usuario_seleccionado_id = None
        self.modo_edicion = False
        
        self.configure(fg_color=st.Colors.BG_MAIN)
        
        # Layout: 40% lista, 60% formulario
        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=6)
        self.grid_rowconfigure(0, weight=1)
        
        # ============================
        # PANEL IZQUIERDO: LISTA
        # ============================
        self.panel_lista = ctk.CTkFrame(
            self,
            fg_color="#2d2d2d",
            corner_radius=15,
            border_width=1,
            border_color="#3d3d3d"
        )
        self.panel_lista.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Header
        ctk.CTkLabel(
            self.panel_lista,
            text="👥 USUARIOS REGISTRADOS",
            font=("Roboto", 14, "bold"),
            text_color="white"
        ).pack(pady=(20, 10))
        
        # Buscador
        fr_search = ctk.CTkFrame(self.panel_lista, fg_color="transparent")
        fr_search.pack(fill="x", padx=15, pady=(0, 10))
        
        self.bg_search = ctk.CTkFrame(
            fr_search,
            fg_color="#383838",
            corner_radius=20,
            height=40
        )
        self.bg_search.pack(fill="x")
        self.bg_search.pack_propagate(False)
        
        ctk.CTkLabel(
            self.bg_search,
            text="🔍",
            font=("Arial", 14),
            text_color="gray"
        ).pack(side="left", padx=10)
        
        self.entry_buscar = ctk.CTkEntry(
            self.bg_search,
            placeholder_text="Buscar usuario...",
            border_width=0,
            fg_color="transparent",
            text_color="white"
        )
        self.entry_buscar.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_buscar.bind("<KeyRelease>", self.buscar_usuario)
        
        # Lista de usuarios
        self.scroll_usuarios = ctk.CTkScrollableFrame(
            self.panel_lista,
            fg_color="#2b2b2b"
        )
        self.scroll_usuarios.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Cargar usuarios dummy
        self.cargar_usuarios_dummy()
        
        # Footer con estadísticas
        fr_stats = ctk.CTkFrame(self.panel_lista, fg_color="#1a1a1a", corner_radius=10)
        fr_stats.pack(fill="x", padx=15, pady=(0, 15))
        
        ctk.CTkLabel(
            fr_stats,
            text="Total: 4 usuarios",
            text_color="gray",
            font=("Roboto", 10)
        ).pack(pady=5)
        
        fr_stats_detail = ctk.CTkFrame(fr_stats, fg_color="transparent")
        fr_stats_detail.pack(pady=(0, 5))
        
        ctk.CTkLabel(
            fr_stats_detail,
            text="✅ Activos: 3",
            text_color=st.Colors.PUNTUAL,
            font=("Roboto", 9)
        ).pack(side="left", padx=10)
        
        ctk.CTkLabel(
            fr_stats_detail,
            text="❌ Inactivos: 1",
            text_color=st.Colors.FALTA,
            font=("Roboto", 9)
        ).pack(side="left", padx=10)
        
        # Botón nuevo usuario
        self.btn_nuevo = ctk.CTkButton(
            self.panel_lista,
            text="➕ NUEVO USUARIO",
            fg_color=st.Colors.ASISTENCIA,
            hover_color="#2980b9",
            height=40,
            command=self.nuevo_usuario
        )
        self.btn_nuevo.pack(fill="x", padx=15, pady=(0, 15))
        
        # ============================
        # PANEL DERECHO: FORMULARIO
        # ============================
        self.panel_form = ctk.CTkFrame(
            self,
            fg_color="#2d2d2d",
            corner_radius=15,
            border_width=1,
            border_color="#3d3d3d"
        )
        self.panel_form.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        
        # Scroll para el formulario
        self.scroll_form = ctk.CTkScrollableFrame(
            self.panel_form,
            fg_color="transparent"
        )
        self.scroll_form.pack(fill="both", expand=True, padx=30, pady=20)
        
        # Header dinámico
        self.lbl_titulo_form = ctk.CTkLabel(
            self.scroll_form,
            text="✏️ DATOS DEL USUARIO",
            font=("Roboto", 16, "bold"),
            text_color="white"
        )
        self.lbl_titulo_form.pack(pady=(0, 20))
        
        # --- SECCIÓN 1: DATOS BÁSICOS ---
        ctk.CTkLabel(
            self.scroll_form,
            text="📄 INFORMACIÓN BÁSICA",
            font=("Roboto", 12, "bold"),
            text_color=st.Colors.ASISTENCIA,
            anchor="w"
        ).pack(fill="x", pady=(0, 10))
        
        # Username
        self.entry_username = self.campo(
            self.scroll_form,
            "Usuario *",
            "Ej: jperez, secretaria1"
        )
        
        # Nombre completo
        self.entry_nombre = self.campo(
            self.scroll_form,
            "Nombre Completo *",
            "Nombres y apellidos"
        )
        
        # Email
        self.entry_email = self.campo(
            self.scroll_form,
            "Email",
            "usuario@correo.com"
        )
        
        # Rol
        ctk.CTkLabel(
            self.scroll_form,
            text="Rol *",
            anchor="w",
            text_color="gray",
            font=("Roboto", 11)
        ).pack(fill="x", pady=(5, 2))
        
        self.combo_rol = ctk.CTkComboBox(
            self.scroll_form,
            values=[
                "Admin (Acceso Total)",
                "Secretaria (Admin + Control + Tesorería)",
                "Docente (Control Diario + Notas)",
                "Contador (Solo Tesorería)",
                "Visualizador (Solo Lectura)"
            ],
            height=40,
            fg_color="#34495e",
            dropdown_fg_color="#2d2d2d",
            button_color=st.Colors.ASISTENCIA,
            state="readonly"
        )
        self.combo_rol.set("Secretaria (Admin + Control + Tesorería)")
        self.combo_rol.pack(fill="x", pady=(0, 10))
        
        # Info de permisos
        self.fr_permisos_info = ctk.CTkFrame(
            self.scroll_form,
            fg_color="#1a1a1a",
            corner_radius=10
        )
        self.fr_permisos_info.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            self.fr_permisos_info,
            text="ℹ️ Permisos del rol seleccionado:",
            text_color="#3498db",
            font=("Roboto", 10, "bold")
        ).pack(anchor="w", padx=15, pady=(10, 5))
        
        self.lbl_permisos = ctk.CTkLabel(
            self.fr_permisos_info,
            text="• Gestión de alumnos\n• Control de asistencia\n• Tesorería y pagos",
            text_color="gray",
            font=("Roboto", 9),
            justify="left",
            anchor="w"
        )
        self.lbl_permisos.pack(anchor="w", padx=25, pady=(0, 10))
        
        self.combo_rol.configure(command=self.actualizar_permisos)
        
        # --- SEPARADOR ---
        ctk.CTkFrame(self.scroll_form, height=2, fg_color="#404040").pack(fill="x", pady=15)
        
        # --- SECCIÓN 2: CONTRASEÑA ---
        self.lbl_seccion_pass = ctk.CTkLabel(
            self.scroll_form,
            text="🔐 CONTRASEÑA",
            font=("Roboto", 12, "bold"),
            text_color=st.Colors.ASISTENCIA,
            anchor="w"
        )
        self.lbl_seccion_pass.pack(fill="x", pady=(0, 10))
        
        # Contraseña
        ctk.CTkLabel(
            self.scroll_form,
            text="Nueva Contraseña",
            anchor="w",
            text_color="gray",
            font=("Roboto", 11)
        ).pack(fill="x", pady=(5, 2))
        
        self.entry_password = ctk.CTkEntry(
            self.scroll_form,
            placeholder_text="Mínimo 6 caracteres",
            show="*",
            height=40
        )
        self.entry_password.pack(fill="x", pady=(0, 10))
        
        # Confirmar contraseña
        ctk.CTkLabel(
            self.scroll_form,
            text="Confirmar Contraseña",
            anchor="w",
            text_color="gray",
            font=("Roboto", 11)
        ).pack(fill="x", pady=(5, 2))
        
        self.entry_password_confirm = ctk.CTkEntry(
            self.scroll_form,
            placeholder_text="Repetir contraseña",
            show="*",
            height=40
        )
        self.entry_password_confirm.pack(fill="x", pady=(0, 10))
        
        # Info de seguridad
        ctk.CTkLabel(
            self.scroll_form,
            text="💡 Tip: Use contraseñas seguras con letras, números y símbolos",
            text_color="#7f8c8d",
            font=("Roboto", 9)
        ).pack(anchor="w", pady=(0, 10))
        
        # --- SEPARADOR ---
        ctk.CTkFrame(self.scroll_form, height=2, fg_color="#404040").pack(fill="x", pady=15)
        
        # --- SECCIÓN 3: ESTADO ---
        ctk.CTkLabel(
            self.scroll_form,
            text="⚙️ ESTADO",
            font=("Roboto", 12, "bold"),
            text_color=st.Colors.ASISTENCIA,
            anchor="w"
        ).pack(fill="x", pady=(0, 10))
        
        self.switch_activo = ctk.CTkSwitch(
            self.scroll_form,
            text="Usuario Activo",
            progress_color=st.Colors.PUNTUAL,
            font=("Roboto", 11)
        )
        self.switch_activo.pack(anchor="w", pady=5)
        self.switch_activo.select()
        
        ctk.CTkLabel(
            self.scroll_form,
            text="⚠️ Si desactiva el usuario, no podrá iniciar sesión",
            text_color="#e67e22",
            font=("Roboto", 9)
        ).pack(anchor="w", pady=(0, 15))
        
        # --- BOTONES DE ACCIÓN ---
        fr_botones = ctk.CTkFrame(self.scroll_form, fg_color="transparent")
        fr_botones.pack(fill="x", pady=(20, 0))
        
        self.btn_guardar = ctk.CTkButton(
            fr_botones,
            text="💾 GUARDAR",
            height=45,
            font=("Roboto", 13, "bold"),
            fg_color=st.Colors.PUNTUAL,
            hover_color="#2ecc71",
            command=self.guardar_usuario
        )
        self.btn_guardar.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.btn_eliminar = ctk.CTkButton(
            fr_botones,
            text="🗑️ ELIMINAR",
            height=45,
            font=("Roboto", 13, "bold"),
            fg_color=st.Colors.FALTA,
            hover_color="#e74c3c",
            command=self.eliminar_usuario,
            state="disabled"  # Activar solo en modo edición
        )
        self.btn_eliminar.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        self.btn_cancelar = ctk.CTkButton(
            self.scroll_form,
            text="❌ Cancelar",
            height=35,
            fg_color="#404040",
            hover_color="#505050",
            command=self.limpiar_formulario
        )
        self.btn_cancelar.pack(fill="x", pady=(5, 0))
        
        # Inicializar en modo nuevo usuario
        self.actualizar_permisos("Secretaria (Admin + Control + Tesorería)")
    
    # =================== MÉTODOS UI HELPERS ===================
    
    def campo(self, parent, label, placeholder=""):
        """Campo de entrada estándar"""
        ctk.CTkLabel(
            parent,
            text=label,
            anchor="w",
            text_color="gray",
            font=("Roboto", 11)
        ).pack(fill="x", pady=(5, 2))
        
        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=40
        )
        entry.pack(fill="x", pady=(0, 10))
        
        return entry
    
    def crear_item_usuario(self, username, nombre, rol, activo):
        """Crear item de usuario en la lista"""
        bg = "#2b2b2b"
        
        fr_usuario = ctk.CTkFrame(
            self.scroll_usuarios,
            fg_color=bg,
            corner_radius=8,
            height=60
        )
        fr_usuario.pack(fill="x", pady=2)
        fr_usuario.pack_propagate(False)
        
        # Badge de estado
        icono = "✅" if activo else "❌"
        color_badge = st.Colors.PUNTUAL if activo else st.Colors.FALTA
        
        fr_badge = ctk.CTkFrame(fr_usuario, width=5, fg_color=color_badge, corner_radius=0)
        fr_badge.pack(side="left", fill="y")
        
        # Contenido
        fr_content = ctk.CTkFrame(fr_usuario, fg_color="transparent")
        fr_content.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        
        # Fila 1: Username + estado
        fr_row1 = ctk.CTkFrame(fr_content, fg_color="transparent")
        fr_row1.pack(fill="x")
        
        ctk.CTkLabel(
            fr_row1,
            text=f"{icono} {username}",
            font=("Roboto", 12, "bold"),
            text_color="white",
            anchor="w"
        ).pack(side="left")
        
        # Fila 2: Nombre + rol
        fr_row2 = ctk.CTkFrame(fr_content, fg_color="transparent")
        fr_row2.pack(fill="x")
        
        ctk.CTkLabel(
            fr_row2,
            text=nombre if nombre else "Sin nombre",
            font=("Roboto", 9),
            text_color="gray",
            anchor="w"
        ).pack(side="left")
        
        # Badge de rol
        rol_corto = rol.split()[0]  # "Admin", "Secretaria", etc.
        color_rol = {
            "Admin": "#e74c3c",
            "Secretaria": "#3498db",
            "Docente": "#2ecc71",
            "Contador": "#f39c12",
            "Visualizador": "#95a5a6"
        }.get(rol_corto, "#7f8c8d")
        
        lbl_rol = ctk.CTkLabel(
            fr_row2,
            text=rol_corto.upper(),
            font=("Arial", 8, "bold"),
            text_color="white",
            fg_color=color_rol,
            corner_radius=3,
            width=60,
            height=16
        )
        lbl_rol.pack(side="right")
        
        # Interactividad
        def on_click(e):
            self.seleccionar_usuario(username, nombre, rol, activo)
        
        def on_enter(e):
            fr_usuario.configure(fg_color="#3a3a3a")
        
        def on_leave(e):
            fr_usuario.configure(fg_color=bg)
        
        fr_usuario.bind("<Button-1>", on_click)
        fr_usuario.bind("<Enter>", on_enter)
        fr_usuario.bind("<Leave>", on_leave)
        
        for widget in fr_usuario.winfo_children():
            widget.bind("<Button-1>", on_click)
    
    def actualizar_permisos(self, rol_seleccionado):
        """Actualizar descripción de permisos según rol"""
        permisos = {
            "Admin (Acceso Total)": 
                "• Acceso completo al sistema\n• Gestión de usuarios\n• Configuración general\n• Todos los módulos",
            
            "Secretaria (Admin + Control + Tesorería)":
                "• Gestión de alumnos y matrículas\n• Control de asistencia\n• Tesorería y pagos\n• Generación de documentos",
            
            "Docente (Control Diario + Notas)":
                "• Registro de asistencia\n• Registro y consulta de notas\n• Visualización de alumnos\n• Reportes académicos",
            
            "Contador (Solo Tesorería)":
                "• Gestión de pagos\n• Consulta de estados de cuenta\n• Reportes financieros\n• Sin acceso a otros módulos",
            
            "Visualizador (Solo Lectura)":
                "• Solo consulta de información\n• Sin permisos de edición\n• Acceso a reportes\n• Sin acceso a configuración"
        }
        
        texto_permisos = permisos.get(rol_seleccionado, "Seleccione un rol")
        self.lbl_permisos.configure(text=texto_permisos)
    
    def cargar_usuarios_dummy(self):
        """Cargar usuarios de ejemplo"""
        usuarios_ejemplo = [
            ("admin", "Juan Pérez García", "Admin", True),
            ("secretaria", "María López Ramos", "Secretaria", True),
            ("docente1", "Carlos Torres Silva", "Docente", False),
            ("contador", "Ana Gómez Vargas", "Contador", True),
        ]
        
        for username, nombre, rol, activo in usuarios_ejemplo:
            self.crear_item_usuario(username, nombre, rol, activo)
    
    # =================== MÉTODOS DE LÓGICA ===================
    
    def nuevo_usuario(self):
        """Activar modo creación de nuevo usuario"""
        self.modo_edicion = False
        self.usuario_seleccionado_id = None
        self.limpiar_formulario()
        
        self.lbl_titulo_form.configure(text="➕ NUEVO USUARIO")
        self.lbl_seccion_pass.configure(text="🔐 CONTRASEÑA *")
        self.btn_eliminar.configure(state="disabled")
        
        # En modo nuevo, la contraseña es obligatoria
        self.entry_password.configure(placeholder_text="Contraseña obligatoria")
    
    def seleccionar_usuario(self, username, nombre, rol, activo):
        """Cargar datos de usuario en formulario para edición"""
        self.modo_edicion = True
        self.usuario_seleccionado_id = username
        
        # Actualizar título
        self.lbl_titulo_form.configure(text=f"✏️ EDITAR: {username}")
        self.lbl_seccion_pass.configure(text="🔐 CAMBIAR CONTRASEÑA (Opcional)")
        self.btn_eliminar.configure(state="normal")
        
        # Cargar datos
        self.entry_username.delete(0, 'end')
        self.entry_username.insert(0, username)
        self.entry_username.configure(state="disabled")  # No editable
        
        self.entry_nombre.delete(0, 'end')
        self.entry_nombre.insert(0, nombre)
        
        # Seleccionar rol
        rol_map = {
            "Admin": "Admin (Acceso Total)",
            "Secretaria": "Secretaria (Admin + Control + Tesorería)",
            "Docente": "Docente (Control Diario + Notas)",
            "Contador": "Contador (Solo Tesorería)",
            "Visualizador": "Visualizador (Solo Lectura)"
        }
        self.combo_rol.set(rol_map.get(rol, "Secretaria (Admin + Control + Tesorería)"))
        self.actualizar_permisos(self.combo_rol.get())
        
        # Estado
        if activo:
            self.switch_activo.select()
        else:
            self.switch_activo.deselect()
        
        # Limpiar contraseñas (opcional en edición)
        self.entry_password.delete(0, 'end')
        self.entry_password_confirm.delete(0, 'end')
        self.entry_password.configure(placeholder_text="Dejar vacío para mantener actual")
        
        # Scroll al inicio
        self.scroll_form._parent_canvas.yview_moveto(0)
    
    def limpiar_formulario(self):
        """Limpiar todos los campos"""
        self.entry_username.configure(state="normal")
        self.entry_username.delete(0, 'end')
        self.entry_nombre.delete(0, 'end')
        self.entry_email.delete(0, 'end')
        self.entry_password.delete(0, 'end')
        self.entry_password_confirm.delete(0, 'end')
        
        self.combo_rol.set("Secretaria (Admin + Control + Tesorería)")
        self.actualizar_permisos(self.combo_rol.get())
        self.switch_activo.select()
        
        self.lbl_titulo_form.configure(text="✏️ DATOS DEL USUARIO")
        self.lbl_seccion_pass.configure(text="🔐 CONTRASEÑA")
        self.btn_eliminar.configure(state="disabled")
        
        self.modo_edicion = False
        self.usuario_seleccionado_id = None
    
    def guardar_usuario(self):
        """Validar y guardar usuario"""
        # Obtener datos
        username = self.entry_username.get().strip()
        nombre = self.entry_nombre.get().strip()
        email = self.entry_email.get().strip()
        rol = self.combo_rol.get().split()[0]  # Extraer "Admin", "Secretaria", etc.
        password = self.entry_password.get()
        password_confirm = self.entry_password_confirm.get()
        activo = self.switch_activo.get() == 1
        
        # Validaciones
        errores = []
        
        if not username:
            errores.append("- El usuario es obligatorio")
        elif len(username) < 3:
            errores.append("- El usuario debe tener al menos 3 caracteres")
        
        if not nombre:
            errores.append("- El nombre completo es obligatorio")
        
        # Validar contraseña solo si es nuevo usuario o si está llenando el campo
        if not self.modo_edicion:  # Nuevo usuario
            if not password:
                errores.append("- La contraseña es obligatoria para usuarios nuevos")
            elif len(password) < 6:
                errores.append("- La contraseña debe tener al menos 6 caracteres")
            elif password != password_confirm:
                errores.append("- Las contraseñas no coinciden")
        
        else:  # Edición
            if password:  # Solo validar si está cambiando contraseña
                if len(password) < 6:
                    errores.append("- La nueva contraseña debe tener al menos 6 caracteres")
                elif password != password_confirm:
                    errores.append("- Las contraseñas no coinciden")
        
        if errores:
            messagebox.showwarning("Validación", "\n".join(errores))
            return
        
        # Confirmación
        accion = "actualizar" if self.modo_edicion else "crear"
        if not messagebox.askyesno("Confirmar", f"¿{accion.capitalize()} usuario '{username}'?"):
            return
        
        # Aquí llamarías al controller
        usuario_data = {
            "username": username,
            "nombre_completo": nombre,
            "email": email,
            "rol": rol,
            "activo": activo,
            "password": password if password else None
        }
        
        messagebox.showinfo(
            "✅ Guardado",
            f"Usuario {'actualizado' if self.modo_edicion else 'creado'} correctamente:\n\n"
            f"Usuario: {username}\n"
            f"Rol: {rol}\n"
            f"Estado: {'Activo' if activo else 'Inactivo'}\n\n"
            f"(Funcionalidad de guardado pendiente)"
        )
        
        self.limpiar_formulario()
    
    def eliminar_usuario(self):
        """Eliminar usuario actual"""
        if not self.usuario_seleccionado_id:
            return
        
        if self.usuario_seleccionado_id == "admin":
            messagebox.showwarning(
                "Advertencia",
                "No se puede eliminar el usuario administrador principal"
            )
            return
        
        if messagebox.askyesno(
            "⚠️ Confirmar Eliminación",
            f"¿Está seguro de eliminar el usuario '{self.usuario_seleccionado_id}'?\n\n"
            f"Esta acción NO se puede deshacer."
        ):
            messagebox.showinfo(
                "Eliminado",
                f"Usuario '{self.usuario_seleccionado_id}' eliminado\n(Funcionalidad pendiente)"
            )
            self.limpiar_formulario()
    
    def buscar_usuario(self, event):
        """Filtrar lista de usuarios"""
        criterio = self.entry_buscar.get().lower()
        # Aquí implementarías el filtrado real
        pass
