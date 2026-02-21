"""
Panel de Dashboard
Sistema Musuq Cloud
"""

import customtkinter as ctk
from datetime import date, datetime
import threading
from typing import Dict, Optional

from core.api_client import APIClient, DashboardClient
from core.theme_manager import ThemeManager as TM

from ui.components.kpi_card import KPICard, KPICardSmall


class DashboardPanel(ctk.CTkFrame):
    """Panel de dashboard con estadísticas y resumen"""
    
    def __init__(self, parent, auth_client: APIClient):
        super().__init__(parent, fg_color="transparent")
        
        self.auth_client = auth_client
        self.dashboard_client = DashboardClient()
        self.dashboard_client.token = auth_client.token
        
        self.create_widgets()
        self.load_data()
    
    def create_widgets(self):
        """Crear widgets del dashboard"""
        
        # Container scrollable
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.scroll.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ==================== HEADER ====================
        self.create_header()
        
        # ==================== KPIs PRINCIPALES ====================
        self.create_kpi_section()
        
        # ==================== EVENTOS PRÓXIMOS ====================
        self.create_events_section()
        
        # ==================== RESUMEN ACADÉMICO ====================
        self.create_summary_section()
    
    def create_header(self):
        """Crear header con saludo"""
        header = ctk.CTkFrame(self.scroll, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        
        # Saludo personalizado
        hora = datetime.now().hour
        if hora < 12:
            saludo = "Buenos días"
        elif hora < 19:
            saludo = "Buenas tardes"
        else:
            saludo = "Buenas noches"
        
        ctk.CTkLabel(
            header,
            text=f"🏠 {saludo}",
            font=ctk.CTkFont(family="Roboto", size=24, weight="bold"),
            text_color=TM.text()
        ).pack(side="left")
        
        # Fecha actual
        info_frame = ctk.CTkFrame(header, fg_color="transparent")
        info_frame.pack(side="right")
        
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        hoy = date.today()
        fecha_str = f"{dias[hoy.weekday()]}, {hoy.day} de {meses[hoy.month-1]} de {hoy.year}"
        
        ctk.CTkLabel(
            info_frame,
            text=fecha_str,
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        ).pack(anchor="e")
        
        ctk.CTkLabel(
            info_frame,
            text="Periodo: 2026-I",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.primary()
        ).pack(anchor="e")
    
    def create_kpi_section(self):
        """Crear sección de KPIs"""
        kpi_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        kpi_frame.pack(fill="x", pady=(0, 20))
        kpi_frame.columnconfigure((0, 1, 2), weight=1)
        
        # KPI 1: Alumnos
        self.kpi_alumnos = KPICard(
            kpi_frame,
            titulo="👥 ALUMNOS ACTIVOS",
            valor="---",
            subtexto="Cargando...",
            color=TM.primary(),
            columna=0
        )
        
        # KPI 2: Asistencia
        self.kpi_asistencia = KPICard(
            kpi_frame,
            titulo="📅 ASISTENCIA HOY",
            valor="---",
            subtexto="Cargando...",
            color=TM.success(),
            columna=1
        )
        
        # KPI 3: Grupos
        self.kpi_grupos = KPICard(
            kpi_frame,
            titulo="📚 GRUPOS ACTIVOS",
            valor="---",
            subtexto="Cargando...",
            color="#9b59b6",
            columna=2
        )
    
    def create_events_section(self):
        """Crear sección de eventos"""
        events_frame = ctk.CTkFrame(
            self.scroll,
            fg_color=TM.bg_card(),
            corner_radius=15,
            border_width=1,
            border_color=TM.get_theme().border
        )
        events_frame.pack(fill="x", pady=(0, 20))
        
        # Header
        header = ctk.CTkFrame(
            events_frame,
            fg_color="#34495e",
            corner_radius=15
        )
        header.pack(fill="x", padx=2, pady=2)
        
        ctk.CTkLabel(
            header,
            text="📅 PRÓXIMOS EVENTOS",
            font=ctk.CTkFont(family="Roboto", size=16, weight="bold"),
            text_color=TM.text()
        ).pack(side="left", padx=20, pady=15)
        
        # Contenido
        self.events_container = ctk.CTkFrame(events_frame, fg_color="transparent")
        self.events_container.pack(fill="x", padx=15, pady=15)
        
        # Eventos de ejemplo
        eventos = [
            {"fecha": "10/02", "dia": "Lunes", "titulo": "Inicio de clases", "icono": "📚", "color": TM.primary()},
            {"fecha": "14/02", "dia": "Viernes", "titulo": "Evaluación diagnóstica", "icono": "📝", "color": TM.warning()},
            {"fecha": "28/02", "dia": "Viernes", "titulo": "Vencimiento primera cuota", "icono": "💰", "color": TM.danger()},
        ]
        
        for evento in eventos:
            self.create_event_item(evento)
        
        # Botón ver más
        ctk.CTkButton(
            events_frame,
            text="VER CALENDARIO COMPLETO →",
            fg_color="transparent",
            text_color=TM.primary(),
            hover_color=TM.get_theme().hover,
            height=35,
            font=ctk.CTkFont(family="Roboto", size=12)
        ).pack(pady=(0, 15))
    
    def create_event_item(self, evento: Dict):
        """Crear item de evento"""
        item = ctk.CTkFrame(
            self.events_container,
            fg_color=TM.bg_panel(),
            corner_radius=10,
            height=60
        )
        item.pack(fill="x", pady=5)
        item.pack_propagate(False)
        
        # Barra de color
        ctk.CTkFrame(
            item,
            width=5,
            fg_color=evento["color"],
            corner_radius=0
        ).pack(side="left", fill="y")
        
        # Contenido
        content = ctk.CTkFrame(item, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        
        # Icono + Título
        top_row = ctk.CTkFrame(content, fg_color="transparent")
        top_row.pack(fill="x")
        
        ctk.CTkLabel(
            top_row,
            text=evento["icono"],
            font=ctk.CTkFont(size=18)
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            top_row,
            text=evento["titulo"],
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            text_color=TM.text()
        ).pack(side="left")
        
        # Badge fecha
        badge = ctk.CTkFrame(top_row, fg_color=evento["color"], corner_radius=5)
        badge.pack(side="right")
        
        ctk.CTkLabel(
            badge,
            text=f"{evento['fecha']} • {evento['dia']}",
            font=ctk.CTkFont(family="Roboto", size=9, weight="bold"),
            text_color="white"
        ).pack(padx=10, pady=3)
    
    def create_summary_section(self):
        """Crear sección de resumen"""
        summary_frame = ctk.CTkFrame(
            self.scroll,
            fg_color=TM.bg_card(),
            corner_radius=15,
            border_width=1,
            border_color=TM.get_theme().border
        )
        summary_frame.pack(fill="x")
        
        # Header
        ctk.CTkLabel(
            summary_frame,
            text="📊 RESUMEN ACADÉMICO (Últimos 7 días)",
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            text_color=TM.text()
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        # Métricas
        metrics_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Asistencia promedio
        self.create_metric(
            metrics_frame,
            "Asistencia promedio",
            "87% ✅",
            TM.success()
        )
        
        # Tardanzas
        self.create_metric(
            metrics_frame,
            "Tardanzas registradas",
            "15",
            TM.warning()
        )
        
        # Justificadas
        self.create_metric(
            metrics_frame,
            "Inasistencias justificadas",
            "8",
            TM.primary()
        )
    
    def create_metric(self, parent, titulo: str, valor: str, color: str):
        """Crear métrica simple"""
        metric = ctk.CTkFrame(parent, fg_color=TM.bg_panel(), corner_radius=8)
        metric.pack(side="left", expand=True, fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(
            metric,
            text=titulo,
            font=ctk.CTkFont(family="Roboto", size=10),
            text_color=TM.text_secondary()
        ).pack(pady=(10, 2))
        
        ctk.CTkLabel(
            metric,
            text=valor,
            font=ctk.CTkFont(family="Roboto", size=20, weight="bold"),
            text_color=color
        ).pack(pady=(0, 10))
    
    def load_data(self):
        """Cargar datos del backend"""
        def fetch():
            success, data = self.dashboard_client.get_stats()
            if success:
                self.after(0, lambda: self.update_kpis(data))
            else:
                self.after(0, lambda: self.show_error(data.get("error", "Error desconocido")))
        
        thread = threading.Thread(target=fetch, daemon=True)
        thread.start()
    
    def update_kpis(self, data: Dict):
        """Actualizar KPIs con datos"""
        total = data.get("total_alumnos", 0)
        activos = data.get("alumnos_activos", 0)
        grupos = data.get("grupos", 0)
        asistencia = data.get("asistencia_hoy", "N/A")
        
        self.kpi_alumnos.actualizar_valor(str(activos))
        self.kpi_alumnos.actualizar_subtexto(f"De {total} matriculados")
        
        self.kpi_asistencia.actualizar_valor(str(asistencia))
        self.kpi_asistencia.actualizar_subtexto("Promedio del día")
        
        self.kpi_grupos.actualizar_valor(str(grupos))
        self.kpi_grupos.actualizar_subtexto("Grupos diferentes")
    
    def show_error(self, message: str):
        """Mostrar error en KPIs"""
        self.kpi_alumnos.actualizar_valor("!")
        self.kpi_alumnos.actualizar_subtexto(message[:30])
    
    def refresh(self):
        """Refrescar datos"""
        self.load_data()
