"""
Ventana Principal con Sidebar Reorganizado
Sistema Musuq Cloud
"""

import customtkinter as ctk
from typing import Dict, Optional, Type
from datetime import datetime

from core.config import Config
from core.api_client import APIClient
from core.auth_manager import AuthManager
from core.theme_manager import ThemeManager as TM

from ui.components.nav_button import NavButton, SubMenuButton


class MainWindow(ctk.CTkFrame):
    """Ventana principal con sidebar y área de contenido"""
    
    def __init__(self, parent, auth_client: APIClient, user_data: Dict):
        super().__init__(parent)
        
        self.parent = parent
        self.auth_client = auth_client
        self.user_data = user_data
        self.auth_manager = AuthManager()
        
        # Cache de vistas
        self.views_cache: Dict[str, ctk.CTkFrame] = {}
        self.current_view: Optional[ctk.CTkFrame] = None
        self.nav_buttons: Dict[str, NavButton] = {}
        self.submenus: Dict[str, ctk.CTkFrame] = {}
        
        # Configurar ventana principal
        parent.title(f"{Config.APP_NAME} - {user_data.get('nombre_completo', 'Usuario')}")
        parent.geometry(Config.MAIN_SIZE)
        parent.minsize(*Config.MIN_SIZE)
        
        # Configurar layout
        self.configure(fg_color=TM.bg_main())
        self.pack(fill="both", expand=True)
        
        # Crear UI
        self.create_sidebar()
        self.create_content_area()
        
        # Mostrar dashboard por defecto
        self.show_dashboard()
    
    def create_sidebar(self):
        """Crear barra lateral con nueva organización"""
        
        # ==================== SIDEBAR CONTAINER ====================
        self.sidebar = ctk.CTkFrame(
            self,
            width=240,
            corner_radius=0,
            fg_color=TM.bg_sidebar()
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        
        # ==================== LOGO ====================
        logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(25, 10))
        
        ctk.CTkLabel(
            logo_frame,
            text="🎓 MUSUQ",
            font=ctk.CTkFont(family="Roboto", size=22, weight="bold"),
            text_color=TM.text()
        ).pack()
        
        ctk.CTkLabel(
            logo_frame,
            text="CLOUD",
            font=ctk.CTkFont(family="Roboto", size=12),
            text_color=TM.primary()
        ).pack()
        
        # Línea divisoria
        ctk.CTkFrame(
            self.sidebar,
            height=1,
            fg_color=TM.get_theme().border
        ).pack(fill="x", padx=20, pady=15)
        
        # ==================== MENÚ NAVEGACIÓN ====================
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.pack(fill="x", padx=10)
        
        # 1. 🏠 DASHBOARD ============================================================================================
        self.nav_buttons["dashboard"] = NavButton(
            nav_frame,
            text="🏠 Dashboard",
            command=self.show_dashboard,
            active=True
        )
        self.nav_buttons["dashboard"].pack(pady=3, fill="x")
        
        # 2. 👨‍🎓 ALUMNOS (con submenú) ================================================================================
        self.nav_buttons["alumnos"] = NavButton(
            nav_frame,
            text="👨‍🎓 Alumnos",
            command=lambda: self.toggle_submenu("alumnos")
        )
        self.nav_buttons["alumnos"].pack(pady=3, fill="x")
        
        self.submenus["alumnos"] = ctk.CTkFrame(nav_frame, fg_color="transparent")
        SubMenuButton(self.submenus["alumnos"], text="   • Ver Matrículas", 
                     command=self.show_alumnos_lista).pack(fill="x", pady=1)
        SubMenuButton(self.submenus["alumnos"], text="   • Nueva Matrícula", 
                     command=self.show_alumnos_nuevo).pack(fill="x", pady=1)
        SubMenuButton(self.submenus["alumnos"], text="   • Historial ", 
                     command=self.show_alumnos_nuevo).pack(fill="x", pady=1)
        
        # 3. 👨‍🏫 DOCENTES ============================================================================================ 
        self.nav_buttons["docentes"] = NavButton(
            nav_frame,
            text="👨‍🏫 Docentes",
            command=lambda: self.toggle_submenu("docentes")
        )
        self.nav_buttons["docentes"].pack(pady=3, fill="x")
        
        self.submenus["docentes"] = ctk.CTkFrame(nav_frame, fg_color="transparent")
        SubMenuButton(self.submenus["docentes"], text="   • Gestión Docentes", 
                     command=self.show_docentes_gestion).pack(fill="x", pady=1)
        SubMenuButton(self.submenus["docentes"], text="   • Asignar Cursos", 
                     command=self.show_docentes_asignar_cursos).pack(fill="x", pady=1)
        SubMenuButton(self.submenus["docentes"], text="   • Cursos", 
                     command=self.show_docentes_cursos).pack(fill="x", pady=1)
        SubMenuButton(self.submenus["docentes"], text="   • Horarios", 
                     command=self.show_docentes_horarios).pack(fill="x", pady=1)
        
        # 4. 📅 ASISTENCIA ============================================================================================ 
        self.nav_buttons["asistencia"] = NavButton(
            nav_frame,
            text="📅 Asistencia",
            command=lambda: self.toggle_submenu("asistencia")
        )
        self.nav_buttons["asistencia"].pack(pady=3, fill="x")
        
        self.submenus["asistencia"] = ctk.CTkFrame(nav_frame, fg_color="transparent")
        SubMenuButton(self.submenus["asistencia"], text="   • Tomar Asistencia", 
                     command=self.show_asistencia_toma).pack(fill="x", pady=1)
        SubMenuButton(self.submenus["asistencia"], text="   • Justificar Faltas", 
                     command=self.show_asistencia_justificar).pack(fill="x", pady=1)
        SubMenuButton(self.submenus["asistencia"], text="   • Rep. Tardanzas", 
                     command=self.show_asistencia_tardanzas).pack(fill="x", pady=1)
        SubMenuButton(self.submenus["asistencia"], text="   • Rep. Inasistencias", 
                     command=self.show_asistencia_inasistencias).pack(fill="x", pady=1)
        SubMenuButton(self.submenus["asistencia"], text="   • Rep. Asistencia", 
                     command=self.show_asistencia_reporte).pack(fill="x", pady=1)

        # 5. 📝 ACADÉMICO ============================================================================================ 
        self.nav_buttons["academico"] = NavButton(
            nav_frame,
            text="📝 Académico",
            command=lambda: self.toggle_submenu("academico")
        )
        self.nav_buttons["academico"].pack(pady=3, fill="x")
        
        self.submenus["academico"] = ctk.CTkFrame(nav_frame, fg_color="transparent")
        SubMenuButton(self.submenus["academico"], text="   • Registrar Notas", 
                     command=self.show_academico_notas).pack(fill="x", pady=1)
        SubMenuButton(self.submenus["academico"], text="   • Boletas", 
                     command=self.show_academico_boletas).pack(fill="x", pady=1)
        SubMenuButton(self.submenus["academico"], text="   • Constancias", 
                     command=self.show_academico_constancias).pack(fill="x", pady=1)
        
        
        # 6. 💰 PAGOS ============================================================================================ 
        self.nav_buttons["pagos"] = NavButton(
            nav_frame,
            text="💰 Pagos",
            command=lambda: self.toggle_submenu("pagos")
        )
        self.nav_buttons["pagos"].pack(pady=3, fill="x")
        
        self.submenus["pagos"] = ctk.CTkFrame(nav_frame, fg_color="transparent")
        SubMenuButton(self.submenus["pagos"], text="   • Caja", 
                     command=self.show_pagos_caja).pack(fill="x", pady=1)
        SubMenuButton(self.submenus["pagos"], text="   • Estado de Cuenta", 
                     command=self.show_pagos_estado_cuenta).pack(fill="x", pady=1)
        SubMenuButton(self.submenus["pagos"], text="   • Deudores", 
                     command=self.show_pagos_deudores).pack(fill="x", pady=1)
        
        # 7. 📄 REPORTES ============================================================================================ 
        self.nav_buttons["reportes"] = NavButton(
            nav_frame,
            text="📄 Reportes",
            command=lambda: self.toggle_submenu("reportes")
        )
        self.nav_buttons["reportes"].pack(pady=3, fill="x")
        
        self.submenus["reportes"] = ctk.CTkFrame(nav_frame, fg_color="transparent")
        SubMenuButton(self.submenus["reportes"], text="   • Listas de Clase", 
                     command=self.show_reportes_listas).pack(fill="x", pady=1)
        SubMenuButton(self.submenus["reportes"], text="   • Carnets", 
                     command=self.show_reportes_carnets).pack(fill="x", pady=1)
        
        
        # 8. ⚙️ CONFIGURACIÓN (solo admin) ============================================================================================ 
        if self.user_data.get("rol", "").lower() in ["admin", "administrador"]:
            self.nav_buttons["config"] = NavButton(
                nav_frame,
                text="⚙️ Configuración",
                command=lambda: self.toggle_submenu("config")
            )
            self.nav_buttons["config"].pack(pady=3, fill="x")
            
            self.submenus["config"] = ctk.CTkFrame(nav_frame, fg_color="transparent")
            SubMenuButton(self.submenus["config"], text="   • Institución", 
                         command=self.show_config_institucion).pack(fill="x", pady=1)
            SubMenuButton(self.submenus["config"], text="   • Usuarios", 
                         command=self.show_config_usuarios).pack(fill="x", pady=1)
            SubMenuButton(self.submenus["config"], text="   • Periodo Lectivo", 
                         command=self.show_config_periodo).pack(fill="x", pady=1)
            SubMenuButton(self.submenus["config"], text="   • SMS", 
                         command=self.show_config_sms).pack(fill="x", pady=1)
        
        # ==================== SPACER ====================
        spacer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        spacer.pack(fill="both", expand=True)
        
        # ==================== USER INFO ====================
        user_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        user_frame.pack(side="bottom", fill="x", padx=15, pady=20)
        
        # Línea divisoria
        ctk.CTkFrame(
            user_frame,
            height=1,
            fg_color=TM.get_theme().border
        ).pack(fill="x", pady=(0, 15))
        
        # Info del usuario
        user_info = ctk.CTkFrame(user_frame, fg_color="transparent")
        user_info.pack(fill="x")
        
        ctk.CTkLabel(
            user_info,
            text=f"👤 {self.user_data.get('username', 'Usuario')}",
            font=ctk.CTkFont(family="Roboto", size=12),
            text_color=TM.text()
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            user_info,
            text=self.user_data.get("rol", "Usuario"),
            font=ctk.CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        ).pack(anchor="w")
        
        # Botón logout
        ctk.CTkButton(
            user_frame,
            text="🚪 Cerrar Sesión",
            width=200,
            height=35,
            font=ctk.CTkFont(family="Roboto", size=12),
            fg_color=TM.danger(),
            hover_color="#b71c1c",
            corner_radius=8,
            command=self.handle_logout
        ).pack(pady=(15, 0))
    
    def create_content_area(self):
        """Crear área de contenido principal"""
        self.content_area = ctk.CTkFrame(
            self,
            corner_radius=0,
            fg_color=TM.bg_main()
        )
        self.content_area.pack(side="right", fill="both", expand=True)
    
    def toggle_submenu(self, key: str):
        """Mostrar/ocultar submenú"""
        # Cerrar todos los submenús
        for menu_key, submenu in self.submenus.items():
            if menu_key != key:
                submenu.pack_forget()
        
        # Toggle del submenú seleccionado
        if key in self.submenus:
            submenu = self.submenus[key]
            if submenu.winfo_ismapped():
                submenu.pack_forget()
            else:
                # Insertar después del botón correspondiente
                btn = self.nav_buttons.get(key)
                if btn:
                    submenu.pack(after=btn, fill="x", pady=(0, 5))
    
    def set_active_nav(self, key: str):
        """Establecer botón de navegación activo"""
        for nav_key, btn in self.nav_buttons.items():
            btn.set_active(nav_key == key)
    
    def clear_content(self):
        """Limpiar área de contenido"""
        for widget in self.content_area.winfo_children():
            widget.pack_forget()
    
    def show_view(self, view_class: Type, view_key: str, *args, **kwargs):
        """Mostrar una vista (con caché)"""
        self.clear_content()
        
        if view_key not in self.views_cache:
            try:
                self.views_cache[view_key] = view_class(
                    self.content_area,
                    self.auth_client,
                    *args,
                    **kwargs
                )
            except Exception as e:
                print(f"Error cargando vista {view_key}: {e}")
                import traceback
                traceback.print_exc()
                self.show_placeholder(f"Error: {e}")
                return
        
        self.current_view = self.views_cache[view_key]
        self.current_view.pack(fill="both", expand=True)
        
        # Refrescar si tiene método
        if hasattr(self.current_view, 'refresh'):
            self.current_view.refresh()
    
    def show_placeholder(self, text: str):
        """Mostrar placeholder para vistas no implementadas"""
        self.clear_content()
        
        placeholder = ctk.CTkFrame(self.content_area, fg_color="transparent")
        placeholder.pack(fill="both", expand=True)
        
        ctk.CTkLabel(
            placeholder,
            text="🚧",
            font=ctk.CTkFont(size=60)
        ).pack(expand=True, pady=(100, 10))
        
        ctk.CTkLabel(
            placeholder,
            text=text,
            font=ctk.CTkFont(family="Roboto", size=20),
            text_color=TM.text_secondary()
        ).pack()
        
        ctk.CTkLabel(
            placeholder,
            text="Esta funcionalidad estará disponible próximamente",
            font=ctk.CTkFont(family="Roboto", size=12),
            text_color=TM.text_secondary()
        ).pack(pady=10)
    
    # ==================== NAVEGACIÓN ====================
    
    # -------------Dashboard-------------
    def show_dashboard(self):
        """Mostrar dashboard"""
        self.set_active_nav("dashboard")
        from ui.panels.dashboard_panel import DashboardPanel
        self.show_view(DashboardPanel, "dashboard")
    

    # -------------Alumnos-------------
    def show_alumnos_lista(self):
        """Mostrar lista de alumnos"""
        self.set_active_nav("alumnos")
        from ui.views.alumnos import AlumnosListPanel
        self.show_view(AlumnosListPanel, "alumnos_lista")
    
    def show_alumnos_nuevo(self):
        """Mostrar formulario de nuevo alumno"""
        self.set_active_nav("alumnos")
        from ui.views.alumnos.nuevo_alumno_view import NuevoAlumnoPanel
        self.show_view(NuevoAlumnoPanel, "alumnos_nuevo")
    

    # -------------Docentes-------------
    def show_docentes_gestion(self):
        """Mostrar gestión de docentes"""
        self.set_active_nav("docentes")
        from ui.views.docentes.gestion_docentes_view import GestionDocentesView
        self.show_view(GestionDocentesView, "docentes_gestion")

    def show_docentes_asignar_cursos(self):
        """Mostrar asignación de cursos a docentes"""
        self.set_active_nav("docentes")
        from ui.views.docentes.asignar_curso_view import AsignarCursoView
        self.show_view(AsignarCursoView, "docentes_asignar_cursos")

    def show_docentes_cursos(self):
        """Mostrar catálogo de cursos/malla"""
        self.set_active_nav("docentes")
        from ui.views.docentes.cursos_view import CursosView
        self.show_view(CursosView, "docentes_cursos")

    def show_docentes_horarios(self):
        """Mostrar gestión de horarios"""
        self.set_active_nav("docentes")
        from ui.views.docentes.horarios_view import HorariosView
        self.show_view(HorariosView, "docentes_horarios")


    # -------------Asistencia-------------
    def show_asistencia_toma(self):
        """Mostrar vista de toma de asistencia"""
        self.set_active_nav("asistencia")
        from ui.views.asistencia.asistencia_view import AsistenciaView
        self.show_view(AsistenciaView, "asistencia_toma")

    def show_asistencia_justificar(self):
        """Mostrar vista de justificación"""
        self.set_active_nav("asistencia")
        from ui.views.asistencia.justificar_view import JustificarView
        self.show_view(JustificarView, "asistencia_justificar")

    def show_asistencia_reporte(self):
        """Mostrar reporte de asistencia"""
        self.set_active_nav("asistencia")
        from ui.views.asistencia.reporte_asistencia_view import ReporteAsistenciaView
        self.show_view(ReporteAsistenciaView, "asistencia_reporte")

    def show_asistencia_tardanzas(self):
        """Mostrar reporte de tardanzas"""
        self.set_active_nav("asistencia")
        from ui.views.asistencia.reporte_tardanza_view import ReporteTardanzaView
        self.show_view(ReporteTardanzaView, "asistencia_tardanzas")

    def show_asistencia_inasistencias(self):
        """Mostrar reporte de inasistencias"""
        self.set_active_nav("asistencia")
        from ui.views.asistencia.reporte_inasistencia_view import ReporteInasistenciaView
        self.show_view(ReporteInasistenciaView, "asistencia_inasistencias")
    

    # -------------Academico-------------
    def show_academico_notas(self):
        """Mostrar registro de notas"""
        self.set_active_nav("academico")
        from ui.views.academico.notas_view import NotasView
        self.show_view(NotasView, "academico_notas")

    def show_academico_boletas(self):
        """Mostrar generación de boletas"""
        self.set_active_nav("academico")
        from ui.views.academico.boletas_view import BoletasView
        self.show_view(BoletasView, "academico_boletas")

    def show_academico_constancias(self):
        """Mostrar generador de constancias"""
        self.set_active_nav("academico")
        from desktop.ui.views.academico.doc_constancias import ConstanciasView
        self.show_view(ConstanciasView, "academico_constancias")

    


    # -------------Pagos-------------
    def show_pagos_caja(self):
        """Mostrar vista de Caja"""
        self.set_active_nav("pagos")
        from ui.views.pagos.caja_view import CajaView
        self.show_view(CajaView, "pagos_caja")

    def show_pagos_estado_cuenta(self):
        """Mostrar estado de cuenta"""
        self.set_active_nav("pagos")
        from ui.views.pagos.estado_cuenta_view import EstadoCuentaView
        self.show_view(EstadoCuentaView, "pagos_estado_cuenta")

    def show_pagos_deudores(self):
        """Mostrar reporte de deudores"""
        self.set_active_nav("pagos")
        from ui.views.pagos.deudores_view import DeudoresView
        self.show_view(DeudoresView, "pagos_deudores")
    

    # -------------Reportes-------------    
    def show_reportes_listas(self):
        """Mostrar reportes de asistencia"""
        self.set_active_nav("reportes")
        from ui.views.reportes.rep_listas import ReporteListasView
        self.show_view(ReporteListasView, "reportes_listas")

    def show_reportes_carnets(self):
        """Mostrar generador de carnets"""
        self.set_active_nav("reportes")
        from ui.views.reportes.gen_carnet import CarnetView
        self.show_view(CarnetView, "reportes_carnet")

    

    #----------configuracion----------------
    def show_config_usuarios(self):
        """Mostrar gestión de usuarios"""
        self.set_active_nav("configuracion")
        from ui.views.config.config_usuarios import ConfigUsuariosView
        self.show_view(ConfigUsuariosView, "config_usuarios")   

    def show_config_institucion(self):
        """Mostrar gestión de institucion"""
        self.set_active_nav("configuracion")
        from ui.views.config.config_institucion import ConfigInstitucionView
        self.show_view(ConfigInstitucionView, "config_institucion")     

    def show_config_periodo(self):
        """Mostrar gestión de periodo"""
        self.set_active_nav("configuracion")
        from ui.views.config.config_periodo_lectivo import ConfigPeriodoView
        self.show_view(ConfigPeriodoView, "config_periodo")     
    
    def show_config_sms(self):
        """Mostrar gestión de sms"""
        self.set_active_nav("configuracion")
        from ui.views.config.config_sms import ConfigSMSView
        self.show_view(ConfigSMSView, "config_sms")
    

    
    
    # ==================== LOGOUT ====================
    
    def handle_logout(self):
        """Manejar cierre de sesión"""
        from tkinter import messagebox
        
        result = messagebox.askyesno(
            "Cerrar Sesión",
            "¿Está seguro que desea cerrar sesión?"
        )
        
        if result:
            self.auth_manager.clear_session()
            self.destroy()
            
            # Reabrir login
            from ui.login_window import LoginWindow
            
            def on_login_success(client, user_data):
                MainWindow(self.parent, client, user_data)
            
            LoginWindow(self.parent, on_login_success)
