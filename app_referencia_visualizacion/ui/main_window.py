import customtkinter as ctk
import json
import os
import importlib

# [OPTIMIZACIÓN] Eliminamos las importaciones masivas para mejorar el tiempo de inicio
# y reducir el consumo de memoria inicial. Las vistas se cargarán bajo demanda.

class MainWindow(ctk.CTkFrame):
    def __init__(self, master, usuario_actual):
        super().__init__(master)
        self.usuario = usuario_actual
        
        # [OPTIMIZACIÓN] Eliminamos self.vistas_cache y self.vista_actual 
        # para forzar la recreación fresca de vistas (como en la referencia fluida)

        self.lista_submenus = []

        # Configuración del layout principal
        self.pack(fill="both", expand=True)

        # ============================================================
        #              BARRA LATERAL (SIDEBAR)
        # ============================================================
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.sidebar.pack(side="left", fill="y")
        
        self.lbl_app = ctk.CTkLabel(self.sidebar, text="SISTEMA\nMUSUQ", font=("Roboto", 22, "bold"))
        self.lbl_app.pack(pady=(30, 20), padx=20)
        
        self.lbl_user = ctk.CTkLabel(self.sidebar, text=f"Hola, {self.usuario.username}", text_color="gray")
        self.lbl_user.pack(pady=(0, 20))

        # --- MENÚS (Usando la nueva función de carga perezosa) ---

        # 1. CONTROL DIARIO
        self.btn_menu_diario = self.crear_boton_menu("✅ Control Diario", lambda: self.toggle_submenu(self.fr_sub_diario))
        self.fr_sub_diario = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.lista_submenus.append(self.fr_sub_diario)

        self.crear_boton_submenu(self.fr_sub_diario, "• Tomar Asistencia", lambda: self.mostrar_vista("app.ui.control_asistencia_view", "AsistenciaView"))
        self.crear_boton_submenu(self.fr_sub_diario, "• Justificar Faltas", lambda: self.mostrar_vista("app.ui.control_justificar_view", "JustificarView"))
        self.crear_boton_submenu(self.fr_sub_diario, "• Rep. Tardanzas", lambda: self.mostrar_vista("app.ui.control_rep_tardanza_view", "ReporteTardanzaView"))
        self.crear_boton_submenu(self.fr_sub_diario, "• Rep. Asistencia", lambda: self.mostrar_vista("app.ui.control_rep_asistencia_view", "ReporteAsistenciaView"))
        self.crear_boton_submenu(self.fr_sub_diario, "• Rep. Inasistencias", lambda: self.mostrar_vista("app.ui.control_rep_inasistencia_view", "ReporteInasistenciaView"))

        # 2. GESTIÓN ACADÉMICA
        self.btn_menu_academico = self.crear_boton_menu("🎓 Gestión Académica", lambda: self.toggle_submenu(self.fr_sub_academico))
        self.fr_sub_academico = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.lista_submenus.append(self.fr_sub_academico)

        self.crear_boton_submenu(self.fr_sub_academico, "• Registrar Notas", lambda: self.mostrar_vista("app.ui.gestion_registro_notas_view", "RegistrarNotasView"))
        self.crear_boton_submenu(self.fr_sub_academico, "• Boleta de Notas", lambda: self.mostrar_vista("app.ui.gestion_boleta_notas_view", "BoletaNotasView"))
        self.crear_boton_submenu(self.fr_sub_academico, "• Historial/Récord", lambda: self.mostrar_vista("app.ui.gestion_historial_academico_view", "HistorialAcademicoView"))

        # 3. ADMINISTRACIÓN
        self.btn_menu_admin = self.crear_boton_menu("📚 Administración", lambda: self.toggle_submenu(self.fr_sub_admin))
        self.fr_sub_admin = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.lista_submenus.append(self.fr_sub_admin)

        self.crear_boton_submenu(self.fr_sub_admin, "• Nueva Matrícula", lambda: self.mostrar_vista("app.ui.admin_registro_alumno_view", "RegistroAlumnoView"))
        self.crear_boton_submenu(self.fr_sub_admin, "• Ver Matriculas", lambda: self.mostrar_vista("app.ui.admin_ver_matriculas_view", "VerMatriculasView"))
        self.crear_boton_submenu(self.fr_sub_admin, "• Cursos", lambda: self.mostrar_vista("app.ui.admin_cursos_view", "GestionCursosView"))
        self.crear_boton_submenu(self.fr_sub_admin, "• Horarios", lambda: self.mostrar_vista("app.ui.admin_horarios_view", "GestionHorariosView"))
        self.crear_boton_submenu(self.fr_sub_admin, "• Gestión Docentes", lambda: self.mostrar_vista("app.ui.admin_gestion_docentes_view", "GestionDocentesView"))

        # 4. TESORERÍA
        self.btn_menu_tesoreria = self.crear_boton_menu("💰 Tesorería", lambda: self.toggle_submenu(self.fr_sub_tesoreria))
        self.fr_sub_tesoreria = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.lista_submenus.append(self.fr_sub_tesoreria)
        
        self.crear_boton_submenu(self.fr_sub_tesoreria, "• Caja y Pagos", lambda: self.mostrar_vista("app.ui.tesoreria_caja_view", "TesoreriaView"))
        self.crear_boton_submenu(self.fr_sub_tesoreria, "• Estado de Cuenta", lambda: self.mostrar_vista("app.ui.tesoreria_estado_cuenta_view", "EstadoCuentaView"))
        self.crear_boton_submenu(self.fr_sub_tesoreria, "• Rep. Deudores", lambda: self.mostrar_vista("app.ui.tesoreria_rep_deudores_view", "RepDeudoresView"))

        # 5. DOCUMENTOS
        self.btn_menu_docs = self.crear_boton_menu("🖨️ Documentos", lambda: self.toggle_submenu(self.fr_sub_docs))
        self.fr_sub_docs = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.lista_submenus.append(self.fr_sub_docs)

        self.crear_boton_submenu(self.fr_sub_docs, "• Listas de Clase", lambda: self.mostrar_vista("app.ui.doc_rep_listas_view", "ReporteView"))
        self.crear_boton_submenu(self.fr_sub_docs, "• Carnets", lambda: self.mostrar_vista("app.ui.doc_carnet_view", "CarnetView"))
        self.crear_boton_submenu(self.fr_sub_docs, "• Constancias", lambda: self.mostrar_vista("app.ui.doc_constancias_view", "ConstanciasView"))

        # 6. CONFIGURACIÓN
        self.btn_menu_config = self.crear_boton_menu("⚙️ Configuración", lambda: self.toggle_submenu(self.fr_sub_config))
        self.fr_sub_config = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.lista_submenus.append(self.fr_sub_config)

        self.crear_boton_submenu(self.fr_sub_config, "• Institución", lambda: self.mostrar_vista("app.ui.config_institucion_view", "ConfigInstitucionView"))
        self.crear_boton_submenu(self.fr_sub_config, "• Usuarios", lambda: self.mostrar_vista("app.ui.config_usuarios_view", "ConfigUsuariosView"))
        self.crear_boton_submenu(self.fr_sub_config, "• Periodo Lectivo", lambda: self.mostrar_vista("app.ui.config_periodo_lectivo_view", "ConfigPeriodoView"))
        self.crear_boton_submenu(self.fr_sub_config, "• SMS", lambda: self.mostrar_vista("app.ui.config_sms_view", "ConfigSMSView"))

        # SALIR
        self.btn_salir = ctk.CTkButton(self.sidebar, text="Cerrar Sesión", fg_color="#c0392b", hover_color="#e74c3c", 
                                       command=master.cerrar_sesion)
        self.btn_salir.pack(side="bottom", pady=30, padx=20, fill="x")

        # ============================================================
        #           ÁREA DE CONTENIDO PRINCIPAL
        # ============================================================
        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        # Restaurar sesión anterior (si existe)
        self.after(100, self.restaurar_estado)

    # ============================================================
    #                 NUEVA LÓGICA: CARGA PEREZOSA (LAZY LOADING)
    # ============================================================
    def mostrar_vista(self, module_name, class_name):
        """
        Carga una vista bajo demanda y elimina la anterior.
        Esto libera memoria y hace que la interfaz sea ligera y fluida al mover.
        """
        # 1. Limpiar área de contenido (DESTRUIR widget anterior)
        # Esto es clave para el rendimiento: no ocultamos, destruimos.
        for widget in self.content_area.winfo_children():
            widget.destroy()

        # 2. Cargar módulo dinámicamente
        try:
            # print(f"⏳ Cargando módulo: {module_name}...")
            module = importlib.import_module(module_name)
            view_class = getattr(module, class_name)
            
            # 3. Instanciar y mostrar vista
            # CASO ESPECIAL: DashboardView requiere usuario en el constructor
            if class_name == "DashboardView":
                 vista = view_class(self.content_area, self.usuario)
            else:
                 vista = view_class(self.content_area)
            
            # Inyectar usuario si la vista lo espera (para otras vistas que lo usen como atributo)
            if hasattr(vista, 'usuario') and not hasattr(vista, 'usuario_inyectado'): 
                 vista.usuario = self.usuario
            
            vista.pack(fill="both", expand=True)

            # 4. Guardar ubicación
            self.guardar_ubicacion(module_name, class_name)

            # 5. Inicializar datos si es necesario
            if hasattr(vista, 'actualizar'):
                 vista.actualizar()
            elif hasattr(vista, 'buscar'): 
                 vista.buscar()
            elif hasattr(vista, 'cargar_tabla_asistencias_hoy'):
                 vista.cargar_tabla_asistencias_hoy()

        except Exception as e:
            print(f"❌ Error cargando vista {class_name} desde {module_name}: {e}")
            import traceback
            traceback.print_exc()
            lbl_error = ctk.CTkLabel(self.content_area, text=f"Error cargando vista:\n{e}", text_color="red")
            lbl_error.pack(pady=50)

    # ============================================================
    #                 MÉTODOS AUXILIARES
    # ============================================================

    def limpiar_contenido(self):
        """Versión ligera: Solo oculta widgets, usada por bienvenida y pendientes"""
        for widget in self.content_area.winfo_children():
            widget.destroy() # Cambiamos a destroy también aquí

    def crear_boton_menu(self, texto, command):
        btn = ctk.CTkButton(self.sidebar, text=texto, font=("Roboto", 14, "bold"), anchor="w", 
                            fg_color="transparent", text_color=("gray10", "gray90"), 
                            hover_color=("gray70", "gray30"), height=40, command=command)
        btn.pack(fill="x", padx=10, pady=2)
        return btn

    def crear_boton_submenu(self, parent, texto, command):
        btn = ctk.CTkButton(parent, text=texto, font=("Roboto", 12), anchor="w", 
                            fg_color="transparent", text_color=("gray40", "gray60"), 
                            hover_color=("gray80", "gray25"), height=30, command=command)
        btn.pack(fill="x", padx=30, pady=0)
        return btn

    def toggle_submenu(self, frame_seleccionado):
        # Estado inicial
        ya_estaba_visible = frame_seleccionado.winfo_viewable()
        
        # Solo ocultamos los que esten visibles para evitar recálculos innecesarios
        for frame in self.lista_submenus:
            if frame.winfo_viewable():
                frame.pack_forget()
        
        # Si no estaba visible, lo mostramos
        if not ya_estaba_visible:
            mapa = {
                self.fr_sub_admin: self.btn_menu_admin,
                self.fr_sub_academico: self.btn_menu_academico,
                self.fr_sub_tesoreria: self.btn_menu_tesoreria,
                self.fr_sub_diario: self.btn_menu_diario,
                self.fr_sub_docs: self.btn_menu_docs,
                self.fr_sub_config: self.btn_menu_config
            }
            boton_padre = mapa.get(frame_seleccionado)
            if boton_padre:
                frame_seleccionado.pack(after=boton_padre, fill="x", pady=0)

    def guardar_ubicacion(self, module_name, class_name):
        try:
            with open("estado_sesion.json", "w") as f:
                json.dump({"module": module_name, "class": class_name}, f)
        except: pass

    def restaurar_estado(self):
        if os.path.exists("estado_sesion.json"):
            try:
                with open("estado_sesion.json", "r") as f:
                    data = json.load(f)
                    mod_name = data.get("module")
                    cls_name = data.get("class")
                    
                    if mod_name and cls_name:
                        print(f"🔄 Restaurando sesión en: {cls_name}")
                        self.mostrar_vista(mod_name, cls_name)
                    else:
                         self.mostrar_vista("app.ui.dashboard_view", "DashboardView")
            except Exception as e:
                print(f"Error restaurando sesión: {e}")
                self.mostrar_vista("app.ui.dashboard_view", "DashboardView")
        else:
            # Vista por defecto si no hay sesión guardada
            self.mostrar_vista("app.ui.dashboard_view", "DashboardView")
