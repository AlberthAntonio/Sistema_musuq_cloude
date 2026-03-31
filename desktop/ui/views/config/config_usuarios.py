"""
ConfigUsuariosView - VERSIÓN VISUAL PREMIUM (Musuq Cloud)
Refactor visual usando ThemeManager (TM), conectado a la API del backend.
"""

import customtkinter as ctk
from tkinter import messagebox
import threading

import styles.tabla_style as st
from core.theme_manager import TM
from core.api_client import UsuariosClient
from utils.perf_utils import get_logger

logger = get_logger(__name__)


class ConfigUsuariosView(ctk.CTkFrame):
    def __init__(self, master, auth_client=None):
        super().__init__(master, fg_color=TM.bg_main())

        # Cliente API para gestión de usuarios
        self.client = UsuariosClient()

        # Variables de estado
        self.usuario_seleccionado_id = None   # ID numérico del usuario en el backend
        self.modo_edicion = False
        self._usuarios_cache: list = []       # Caché de usuarios cargados desde la API
        self._request_id = 0
        self._debounce_id = None

        # Layout: 40% lista, 60% formulario
        self.grid_columnconfigure(0, weight=4)
        self.grid_columnconfigure(1, weight=6)
        self.grid_rowconfigure(0, weight=1)

        # Paneles
        self._crear_panel_lista()
        self._crear_panel_formulario()

    # ============================================================
    # PANEL IZQUIERDO: LISTA DE USUARIOS
    # ============================================================

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
            text="👥 USUARIOS",
            font=("Roboto", 16, "bold"),
            text_color=TM.text(),
        ).pack(pady=(20, 5))

        ctk.CTkLabel(
            self.panel_lista,
            text="Gestión de cuentas del sistema",
            font=("Roboto", 10),
            text_color=TM.text_secondary(),
        ).pack(pady=(0, 15))

        # Buscador
        fr_search = ctk.CTkFrame(self.panel_lista, fg_color="transparent")
        fr_search.pack(fill="x", padx=15, pady=(0, 10))

        self.bg_search = ctk.CTkFrame(
            fr_search,
            fg_color=TM.bg_card(),
            corner_radius=20,
            height=40,
        )
        self.bg_search.pack(fill="x")
        self.bg_search.pack_propagate(False)

        ctk.CTkLabel(
            self.bg_search,
            text="🔍",
            font=("Arial", 14),
            text_color=TM.text_muted(),
        ).pack(side="left", padx=10)

        self.entry_buscar = ctk.CTkEntry(
            self.bg_search,
            placeholder_text="Buscar usuario...",
            border_width=0,
            fg_color="transparent",
            text_color=TM.text(),
        )
        self.entry_buscar.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_buscar.bind("<KeyRelease>", self.buscar_usuario)

        # Lista de usuarios
        self.scroll_usuarios = ctk.CTkScrollableFrame(
            self.panel_lista, fg_color=TM.bg_card()
        )
        self.scroll_usuarios.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Cargar usuarios desde la API (async)
        self._cargar_usuarios_async()

        # Footer con estadísticas
        fr_stats = ctk.CTkFrame(
            self.panel_lista, fg_color=TM.bg_main(), corner_radius=10
        )
        fr_stats.pack(fill="x", padx=15, pady=(0, 15))

        ctk.CTkLabel(
            fr_stats,
            text="",
            text_color=TM.text_secondary(),
            font=("Roboto", 10),
        ).pack(pady=5)
        self.lbl_total_usuarios = fr_stats.winfo_children()[-1]

        fr_stats_detail = ctk.CTkFrame(fr_stats, fg_color="transparent")
        fr_stats_detail.pack(pady=(0, 5))

        ctk.CTkLabel(
            fr_stats_detail,
            text="",
            text_color=TM.success(),
            font=("Roboto", 9),
        ).pack(side="left", padx=10)
        self.lbl_activos = fr_stats_detail.winfo_children()[-1]

        ctk.CTkLabel(
            fr_stats_detail,
            text="",
            text_color=TM.danger(),
            font=("Roboto", 9),
        ).pack(side="left", padx=10)
        self.lbl_inactivos = fr_stats_detail.winfo_children()[-1]

        # Botón nuevo usuario
        self.btn_nuevo = ctk.CTkButton(
            self.panel_lista,
            text="➕ NUEVO USUARIO",
            fg_color=TM.primary(),
            hover_color=TM.hover(),
            height=40,
            command=self.nuevo_usuario,
        )
        self.btn_nuevo.pack(fill="x", padx=15, pady=(0, 15))

    # ============================================================
    # PANEL DERECHO: FORMULARIO
    # ============================================================

    def _crear_panel_formulario(self):
        self.panel_form = ctk.CTkFrame(
            self,
            fg_color=TM.bg_panel(),
            corner_radius=15,
            border_width=1,
            border_color=TM.bg_card(),
        )
        self.panel_form.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")

        # Scroll para el formulario
        self.scroll_form = ctk.CTkScrollableFrame(
            self.panel_form, fg_color="transparent"
        )
        self.scroll_form.pack(fill="both", expand=True, padx=30, pady=20)

        # Header dinámico
        self.lbl_titulo_form = ctk.CTkLabel(
            self.scroll_form,
            text="✏️ DATOS DEL USUARIO",
            font=("Roboto", 16, "bold"),
            text_color=TM.text(),
        )
        self.lbl_titulo_form.pack(pady=(0, 20))

        # --- SECCIÓN 1: DATOS BÁSICOS ---
        ctk.CTkLabel(
            self.scroll_form,
            text="📄 INFORMACIÓN BÁSICA",
            font=("Roboto", 12, "bold"),
            text_color=TM.primary(),
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        # Username
        self.entry_username = self.campo(
            self.scroll_form, "Usuario *", "Ej: jperez, secretaria1"
        )

        # Nombre completo
        self.entry_nombre = self.campo(
            self.scroll_form, "Nombre Completo *", "Nombres y apellidos"
        )

        # Email
        self.entry_email = self.campo(
            self.scroll_form, "Email", "usuario@correo.com"
        )

        # Rol
        ctk.CTkLabel(
            self.scroll_form,
            text="Rol *",
            anchor="w",
            text_color=TM.text_secondary(),
            font=("Roboto", 11),
        ).pack(fill="x", pady=(5, 2))

        self.combo_rol = ctk.CTkComboBox(
            self.scroll_form,
            values=[
                "Admin (Acceso Total)",
                "Secretaria (Admin + Control + Tesorería)",
                "Docente (Control Diario + Notas)",
                "Contador (Solo Tesorería)",
                "Visualizador (Solo Lectura)",
            ],
            height=40,
            fg_color=TM.bg_card(),
            dropdown_fg_color=TM.bg_panel(),
            button_color=TM.primary(),
            button_hover_color=TM.hover(),
            text_color=TM.text(),
            state="readonly",
        )
        self.combo_rol.set("Secretaria (Admin + Control + Tesorería)")
        self.combo_rol.pack(fill="x", pady=(0, 10))

        # Info de permisos
        self.fr_permisos_info = ctk.CTkFrame(
            self.scroll_form, fg_color=TM.bg_main(), corner_radius=10
        )
        self.fr_permisos_info.pack(fill="x", pady=(0, 15))

        ctk.CTkLabel(
            self.fr_permisos_info,
            text="ℹ️ Permisos del rol seleccionado:",
            text_color=TM.primary(),
            font=("Roboto", 10, "bold"),
        ).pack(anchor="w", padx=15, pady=(10, 5))

        self.lbl_permisos = ctk.CTkLabel(
            self.fr_permisos_info,
            text="• Gestión de alumnos\n• Control de asistencia\n• Tesorería y pagos",
            text_color=TM.text_secondary(),
            font=("Roboto", 9),
            justify="left",
            anchor="w",
        )
        self.lbl_permisos.pack(anchor="w", padx=25, pady=(0, 10))

        self.combo_rol.configure(command=self.actualizar_permisos)

        # --- SEPARADOR ---
        ctk.CTkFrame(self.scroll_form, height=2, fg_color=TM.bg_card()).pack(
            fill="x", pady=15
        )

        # --- SECCIÓN 2: CONTRASEÑA ---
        self.lbl_seccion_pass = ctk.CTkLabel(
            self.scroll_form,
            text="🔐 CONTRASEÑA",
            font=("Roboto", 12, "bold"),
            text_color=TM.primary(),
            anchor="w",
        )
        self.lbl_seccion_pass.pack(fill="x", pady=(0, 10))

        # Contraseña
        ctk.CTkLabel(
            self.scroll_form,
            text="Nueva Contraseña",
            anchor="w",
            text_color=TM.text_secondary(),
            font=("Roboto", 11),
        ).pack(fill="x", pady=(5, 2))

        self.entry_password = ctk.CTkEntry(
            self.scroll_form,
            placeholder_text="Mínimo 6 caracteres",
            show="*",
            height=40,
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_password.pack(fill="x", pady=(0, 10))

        # Confirmar contraseña
        ctk.CTkLabel(
            self.scroll_form,
            text="Confirmar Contraseña",
            anchor="w",
            text_color=TM.text_secondary(),
            font=("Roboto", 11),
        ).pack(fill="x", pady=(5, 2))

        self.entry_password_confirm = ctk.CTkEntry(
            self.scroll_form,
            placeholder_text="Repetir contraseña",
            show="*",
            height=40,
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        self.entry_password_confirm.pack(fill="x", pady=(0, 10))

        # Info de seguridad
        ctk.CTkLabel(
            self.scroll_form,
            text="💡 Tip: Use contraseñas seguras con letras, números y símbolos",
            text_color=TM.text_muted(),
            font=("Roboto", 9),
        ).pack(anchor="w", pady=(0, 10))

        # --- SEPARADOR ---
        ctk.CTkFrame(self.scroll_form, height=2, fg_color=TM.bg_card()).pack(
            fill="x", pady=15
        )

        # --- SECCIÓN 3: ESTADO ---
        ctk.CTkLabel(
            self.scroll_form,
            text="⚙️ ESTADO",
            font=("Roboto", 12, "bold"),
            text_color=TM.primary(),
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

        self.switch_activo = ctk.CTkSwitch(
            self.scroll_form,
            text="Usuario Activo",
            progress_color=TM.success(),
            font=("Roboto", 11),
            text_color=TM.text(),
        )
        self.switch_activo.pack(anchor="w", pady=5)
        self.switch_activo.select()

        ctk.CTkLabel(
            self.scroll_form,
            text="⚠️ Si desactiva el usuario, no podrá iniciar sesión",
            text_color=TM.warning(),
            font=("Roboto", 9),
        ).pack(anchor="w", pady=(0, 15))

        # --- BOTONES DE ACCIÓN ---
        fr_botones = ctk.CTkFrame(self.scroll_form, fg_color="transparent")
        fr_botones.pack(fill="x", pady=(20, 0))

        self.btn_guardar = ctk.CTkButton(
            fr_botones,
            text="💾 GUARDAR",
            height=45,
            font=("Roboto", 13, "bold"),
            fg_color=TM.success(),
            hover_color="#2ecc71",
            command=self.guardar_usuario,
        )
        self.btn_guardar.pack(side="left", fill="x", expand=True, padx=(0, 5))

        self.btn_eliminar = ctk.CTkButton(
            fr_botones,
            text="🗑️ ELIMINAR",
            height=45,
            font=("Roboto", 13, "bold"),
            fg_color=TM.danger(),
            hover_color="#e74c3c",
            command=self.eliminar_usuario,
            state="disabled",  # Activar solo en modo edición
        )
        self.btn_eliminar.pack(side="left", fill="x", expand=True, padx=(5, 0))

        self.btn_cancelar = ctk.CTkButton(
            self.scroll_form,
            text="❌ Cancelar",
            height=35,
            fg_color=TM.bg_card(),
            hover_color=TM.hover(),
            text_color=TM.text(),
            command=self.limpiar_formulario,
        )
        self.btn_cancelar.pack(fill="x", pady=(5, 0))

        # Inicializar
        self.actualizar_permisos("Secretaria (Admin + Control + Tesorería)")

    # =================== MÉTODOS UI HELPERS ===================

    def campo(self, parent, label, placeholder=""):
        """Campo de entrada estándar"""
        ctk.CTkLabel(
            parent,
            text=label,
            anchor="w",
            text_color=TM.text_secondary(),
            font=("Roboto", 11),
        ).pack(fill="x", pady=(5, 2))

        entry = ctk.CTkEntry(
            parent,
            placeholder_text=placeholder,
            height=40,
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
        )
        entry.pack(fill="x", pady=(0, 10))
        return entry

    def crear_item_usuario(self, usuario_id, username, nombre, rol, activo):
        """Crear item de usuario en la lista"""
        bg = TM.bg_card()
        fr_usuario = ctk.CTkFrame(
            self.scroll_usuarios, fg_color=bg, corner_radius=8, height=60
        )
        fr_usuario.pack(fill="x", pady=2)
        fr_usuario.pack_propagate(False)

        # Badge de estado
        icono = "✅" if activo else "❌"
        color_badge = TM.success() if activo else TM.danger()
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
            text_color=TM.text(),
            anchor="w",
        ).pack(side="left")

        # Fila 2: Nombre + rol
        fr_row2 = ctk.CTkFrame(fr_content, fg_color="transparent")
        fr_row2.pack(fill="x")

        ctk.CTkLabel(
            fr_row2,
            text=nombre if nombre else "Sin nombre",
            font=("Roboto", 9),
            text_color=TM.text_secondary(),
            anchor="w",
        ).pack(side="left")

        # Badge de rol
        rol_corto = rol.split()[0]
        color_rol = {
            "Admin": "#e74c3c",
            "Secretaria": TM.primary(),
            "Docente": TM.success(),
            "Contador": TM.warning(),
            "Visualizador": "#95a5a6",
        }.get(rol_corto, "#7f8c8d")

        lbl_rol = ctk.CTkLabel(
            fr_row2,
            text=rol_corto.upper(),
            font=("Arial", 8, "bold"),
            text_color="white",
            fg_color=color_rol,
            corner_radius=3,
            width=60,
            height=16,
        )
        lbl_rol.pack(side="right")

        # Interactividad
        def on_click(e, uid=usuario_id, un=username, nm=nombre, r=rol, ac=activo):
            self.seleccionar_usuario(uid, un, nm, r, ac)

        def on_enter(e):
            fr_usuario.configure(fg_color=TM.hover())

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
            "Admin (Acceso Total)": "• Acceso completo al sistema\n• Gestión de usuarios\n• Configuración general\n• Todos los módulos",
            "Secretaria (Admin + Control + Tesorería)": "• Gestión de alumnos y matrículas\n• Control de asistencia\n• Tesorería y pagos\n• Generación de documentos",
            "Docente (Control Diario + Notas)": "• Registro de asistencia\n• Registro y consulta de notas\n• Visualización de alumnos\n• Reportes académicos",
            "Contador (Solo Tesorería)": "• Gestión de pagos\n• Consulta de estados de cuenta\n• Reportes financieros\n• Sin acceso a otros módulos",
            "Visualizador (Solo Lectura)": "• Solo consulta de información\n• Sin permisos de edición\n• Acceso a reportes\n• Sin acceso a configuración",
        }

        texto_permisos = permisos.get(rol_seleccionado, "Seleccione un rol")
        self.lbl_permisos.configure(text=texto_permisos)

    def _cargar_usuarios_async(self, criterio: str = ""):
        """Carga usuarios en background thread."""
        self._request_id += 1
        req_id = self._request_id

        # Limpiar y mostrar loading
        for widget in self.scroll_usuarios.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self.scroll_usuarios,
            text="⏳ Cargando usuarios...",
            font=("Roboto", 11),
            text_color=TM.text_secondary()
        ).pack(pady=20)

        def _hilo():
            success, result = self.client.obtener_todos(limit=500)
            if self.winfo_exists() and req_id == self._request_id:
                self.after(0, lambda: self._aplicar_usuarios(success, result, criterio))

        threading.Thread(target=_hilo, daemon=True).start()

    def _aplicar_usuarios(self, success, result, criterio):
        if not self.winfo_exists():
            return

        for widget in self.scroll_usuarios.winfo_children():
            widget.destroy()

        if not success:
            ctk.CTkLabel(
                self.scroll_usuarios,
                text="⚠️ No se pudo conectar al servidor",
                text_color=TM.warning(),
            ).pack(pady=20)
            return

        usuarios = result if isinstance(result, list) else result.get("items", [])
        self._usuarios_cache = usuarios

        if criterio:
            c = criterio.lower()
            usuarios = [
                u for u in usuarios
                if c in u.get("username", "").lower()
                or c in (u.get("nombre_completo") or u.get("username", "")).lower()
            ]

        total = len(self._usuarios_cache)
        activos = sum(1 for u in self._usuarios_cache if u.get("activo", True))
        inactivos = total - activos

        try:
            self.lbl_total_usuarios.configure(text=f"Total: {total} usuarios")
            self.lbl_activos.configure(text=f"✅ Activos: {activos}")
            self.lbl_inactivos.configure(text=f"❌ Inactivos: {inactivos}")
        except Exception:
            pass

        ROL_MAP = {
            "admin": "Admin", "secretaria": "Secretaria",
            "docente": "Docente", "contador": "Contador",
            "visualizador": "Visualizador",
        }

        for u in usuarios:
            uid = u.get("id")
            username = u.get("username", "")
            nombre = u.get("nombre_completo") or username
            rol = ROL_MAP.get(u.get("rol", "").lower(), u.get("rol", "?"))
            activo = u.get("activo", True)
            self.crear_item_usuario(uid, username, nombre, rol, activo)

    def cargar_usuarios_desde_api(self, criterio: str = ""):
        """Public method - delegates to async."""
        self._cargar_usuarios_async(criterio)

    def cargar_usuarios_dummy(self):
        """[Compatibilidad] Llama a la carga real desde API"""
        self._cargar_usuarios_async()

    # =================== MÉTODOS DE LÓGICA ===================

    def nuevo_usuario(self):
        """Activar modo creación de nuevo usuario"""
        self.modo_edicion = False
        self.usuario_seleccionado_id = None
        self.limpiar_formulario()
        self.lbl_titulo_form.configure(text="➕ NUEVO USUARIO")
        self.lbl_seccion_pass.configure(text="🔐 CONTRASEÑA *")
        self.btn_eliminar.configure(state="disabled")
        self.entry_password.configure(placeholder_text="Contraseña obligatoria")

    def seleccionar_usuario(self, usuario_id, username, nombre, rol, activo):
        """Cargar datos de usuario en formulario para edición"""
        self.modo_edicion = True
        self.usuario_seleccionado_id = usuario_id  # ID numérico del backend

        self.lbl_titulo_form.configure(text=f"✏️ EDITAR: {username}")
        self.lbl_seccion_pass.configure(text="🔐 CAMBIAR CONTRASEÑA (Opcional)")
        self.btn_eliminar.configure(state="normal")

        # Cargar datos
        self.entry_username.delete(0, "end")
        self.entry_username.insert(0, username)
        self.entry_username.configure(state="disabled")

        self.entry_nombre.delete(0, "end")
        self.entry_nombre.insert(0, nombre)

        # Seleccionar rol
        rol_map = {
            "Admin": "Admin (Acceso Total)",
            "Secretaria": "Secretaria (Admin + Control + Tesorería)",
            "Docente": "Docente (Control Diario + Notas)",
            "Contador": "Contador (Solo Tesorería)",
            "Visualizador": "Visualizador (Solo Lectura)",
        }
        self.combo_rol.set(rol_map.get(rol, "Secretaria (Admin + Control + Tesorería)"))
        self.actualizar_permisos(self.combo_rol.get())

        # Estado
        if activo:
            self.switch_activo.select()
        else:
            self.switch_activo.deselect()

        # Limpiar contraseñas
        self.entry_password.delete(0, "end")
        self.entry_password_confirm.delete(0, "end")
        self.entry_password.configure(placeholder_text="Dejar vacío para mantener actual")

        # Scroll al inicio
        self.scroll_form._parent_canvas.yview_moveto(0)

    def limpiar_formulario(self):
        """Limpiar todos los campos"""
        self.entry_username.configure(state="normal")
        self.entry_username.delete(0, "end")
        self.entry_nombre.delete(0, "end")
        self.entry_email.delete(0, "end")
        self.entry_password.delete(0, "end")
        self.entry_password_confirm.delete(0, "end")
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
        username = self.entry_username.get().strip()
        nombre = self.entry_nombre.get().strip()
        email = self.entry_email.get().strip()
        rol = self.combo_rol.get().split()[0]
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

        if not self.modo_edicion:
            if not password:
                errores.append("- La contraseña es obligatoria para usuarios nuevos")
            elif len(password) < 6:
                errores.append("- La contraseña debe tener al menos 6 caracteres")
            elif password != password_confirm:
                errores.append("- Las contraseñas no coinciden")
        else:
            if password:
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

        usuario_data = {
            "username": username,
            "nombre_completo": nombre,
            "email": email,
            "rol": rol.lower(),
            "activo": activo,
        }
        if password:
            usuario_data["password"] = password

        if self.modo_edicion and self.usuario_seleccionado_id:
            success, result = self.client.actualizar(self.usuario_seleccionado_id, usuario_data)
            mensaje_ok = f"Usuario '{username}' actualizado correctamente."
        else:
            success, result = self.client.crear(usuario_data)
            mensaje_ok = f"Usuario '{username}' creado correctamente."

        if success:
            messagebox.showinfo("✅ Guardado", mensaje_ok)
            self.limpiar_formulario()
            self.cargar_usuarios_desde_api()
        else:
            error = result.get("error", "Error desconocido") if isinstance(result, dict) else str(result)
            messagebox.showerror("❌ Error", f"No se pudo guardar el usuario:\n{error}")

    def eliminar_usuario(self):
        """Eliminar usuario actual llamando a la API"""
        if not self.usuario_seleccionado_id:
            return

        # Buscar en caché si es el admin principal (id=1 o username="admin")
        usuario_actual = next(
            (u for u in self._usuarios_cache if u.get("id") == self.usuario_seleccionado_id), {}
        )
        if usuario_actual.get("username") == "admin":
            messagebox.showwarning(
                "Advertencia",
                "No se puede eliminar el usuario administrador principal",
            )
            return

        nombre_display = usuario_actual.get("username", str(self.usuario_seleccionado_id))
        if messagebox.askyesno(
            "⚠️ Confirmar Eliminación",
            f"¿Está seguro de eliminar el usuario '{nombre_display}'?\n\n"
            f"Esta acción NO se puede deshacer.",
        ):
            success, result = self.client.eliminar(self.usuario_seleccionado_id)
            if success:
                messagebox.showinfo("Eliminado", f"Usuario '{nombre_display}' eliminado correctamente")
                self.limpiar_formulario()
                self.cargar_usuarios_desde_api()
            else:
                error = result.get("error", "Error desconocido") if isinstance(result, dict) else str(result)
                messagebox.showerror("❌ Error", f"No se pudo eliminar:\n{error}")

    def buscar_usuario(self, event):
        """Filtrar lista de usuarios con debounce."""
        if self._debounce_id:
            self.after_cancel(self._debounce_id)

        def _buscar():
            criterio = self.entry_buscar.get().strip()
            # Filtrar desde cache local sin roundtrip
            if self._usuarios_cache:
                for widget in self.scroll_usuarios.winfo_children():
                    widget.destroy()

                c = criterio.lower()
                usuarios = [
                    u for u in self._usuarios_cache
                    if not c or c in u.get("username", "").lower()
                    or c in (u.get("nombre_completo") or u.get("username", "")).lower()
                ]

                ROL_MAP = {
                    "admin": "Admin", "secretaria": "Secretaria",
                    "docente": "Docente", "contador": "Contador",
                    "visualizador": "Visualizador",
                }

                for u in usuarios:
                    uid = u.get("id")
                    username = u.get("username", "")
                    nombre = u.get("nombre_completo") or username
                    rol = ROL_MAP.get(u.get("rol", "").lower(), u.get("rol", "?"))
                    activo = u.get("activo", True)
                    self.crear_item_usuario(uid, username, nombre, rol, activo)
            else:
                self._cargar_usuarios_async(criterio)

        self._debounce_id = self.after(300, _buscar)

    # ── Lifecycle ──
    def on_show(self):
        pass

    def on_hide(self):
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
            self._debounce_id = None

    def cleanup(self):
        self.on_hide()
