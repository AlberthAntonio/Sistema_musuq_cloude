# app/ui/dashboard_view.py
import customtkinter as ctk
from datetime import date, datetime
import threading
import app.styles.tabla_style as st

class DashboardView(ctk.CTkFrame):
    def __init__(self, master, usuario):
        super().__init__(master)
        
        # self.controller = DashboardController()  # ← Después
        self.usuario = usuario  # Objeto usuario con rol
        
        self.configure(fg_color=st.Colors.BG_MAIN)
        
        # Container principal con scroll
        self.scroll_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )
        self.scroll_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # ============================
        # HEADER DE BIENVENIDA
        # ============================
        fr_header = ctk.CTkFrame(self.scroll_container, fg_color="transparent")
        fr_header.pack(fill="x", pady=(0, 20))
        
        # Saludo personalizado
        ahora = datetime.now()
        hora = ahora.hour
        saludo = "Buenos días" if hora < 12 else "Buenas tardes" if hora < 19 else "Buenas noches"
        
        ctk.CTkLabel(
            fr_header,
            text=f"🏠 {saludo}, {self.usuario.nombre_completo}",
            font=("Roboto", 22, "bold"),
            text_color="white"
        ).pack(side="left")
        
        # Fecha e info
        dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", 
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        
        hoy = date.today()
        fecha_texto = f"{dias_semana[hoy.weekday()]}, {hoy.day} de {meses[hoy.month-1]} de {hoy.year}"
        
        fr_info = ctk.CTkFrame(fr_header, fg_color="transparent")
        fr_info.pack(side="right")
        
        ctk.CTkLabel(
            fr_info,
            text=fecha_texto,
            font=("Roboto", 11),
            text_color="gray"
        ).pack(anchor="e")
        
        ctk.CTkLabel(
            fr_info,
            text="Periodo: 2026-I",  # ← Obtener de configuración
            font=("Roboto", 11),
            text_color="#3498db"
        ).pack(anchor="e")
        
        # ============================
        # SECCIÓN 1: KPIs GENERALES
        # ============================
        self.fr_kpis_generales = ctk.CTkFrame(
            self.scroll_container,
            fg_color="transparent"
        )
        self.fr_kpis_generales.pack(fill="x", pady=(0, 20))
        self.fr_kpis_generales.columnconfigure((0, 1, 2), weight=1)
        
        # KPIs que TODOS pueden ver
        self.card_alumnos = self.crear_kpi_card(
            self.fr_kpis_generales,
            "👥 ALUMNOS ACTIVOS",
            "250",
            "Matriculados este periodo",
            "#3498db",
            0
        )
        
        self.card_asistencia = self.crear_kpi_card(
            self.fr_kpis_generales,
            "📅 ASISTENCIA HOY",
            "87%",
            "217 de 250 alumnos presentes",
            "#2ecc71",
            1
        )
        
        self.card_grupos = self.crear_kpi_card(
            self.fr_kpis_generales,
            "📚 GRUPOS ACTIVOS",
            "6",
            "A, B, C, D, E, F",
            "#9b59b6",
            2
        )
        
        # ============================
        # SECCIÓN 2: INFORMACIÓN FINANCIERA
        # ============================
        # Solo visible para Admin, Secretaria, Contador
        if self.usuario.rol in ['Admin', 'Secretaria', 'Contador']:
            self.crear_seccion_financiera()
        
        # ============================
        # SECCIÓN 3: CALENDARIO DE EVENTOS
        # ============================
        fr_calendario = ctk.CTkFrame(
            self.scroll_container,
            fg_color="#2d2d2d",
            corner_radius=15,
            border_width=1,
            border_color="#3d3d3d"
        )
        fr_calendario.pack(fill="both", expand=True, pady=(0, 20))
        
        # Header
        fr_cal_header = ctk.CTkFrame(fr_calendario, fg_color="#34495e", corner_radius=15)
        fr_cal_header.pack(fill="x", padx=2, pady=2)
        
        ctk.CTkLabel(
            fr_cal_header,
            text="📅 PRÓXIMOS EVENTOS",
            font=("Roboto", 16, "bold"),
            text_color="white"
        ).pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(
            fr_cal_header,
            text="Eventos públicos visibles para todos",
            font=("Roboto", 9),
            text_color="gray"
        ).pack(side="left")
        
        # Contenido de eventos
        self.scroll_eventos = ctk.CTkScrollableFrame(
            fr_calendario,
            fg_color="transparent",
            height=200
        )
        self.scroll_eventos.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Cargar eventos (dummy por ahora)
        self.cargar_eventos_dummy()
        
        # Botón ver más
        ctk.CTkButton(
            fr_calendario,
            text="VER CALENDARIO COMPLETO →",
            fg_color="transparent",
            text_color="#3498db",
            hover_color="#404040",
            height=35,
            command=self.abrir_calendario
        ).pack(pady=(0, 15))
        
        # ============================
        # SECCIÓN 4: RESUMEN ACADÉMICO
        # ============================
        fr_resumen = ctk.CTkFrame(
            self.scroll_container,
            fg_color="#2d2d2d",
            corner_radius=15,
            border_width=1,
            border_color="#3d3d3d"
        )
        fr_resumen.pack(fill="x", pady=(0, 20))
        
        # Header
        ctk.CTkLabel(
            fr_resumen,
            text="📊 RESUMEN ACADÉMICO (Últimos 7 días)",
            font=("Roboto", 14, "bold"),
            text_color="white"
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        # Métricas en grid
        fr_metricas = ctk.CTkFrame(fr_resumen, fg_color="transparent")
        fr_metricas.pack(fill="x", padx=20, pady=(0, 15))
        fr_metricas.columnconfigure((0, 1, 2), weight=1)
        
        self.crear_metrica_simple(
            fr_metricas, "Asistencia promedio", "87% ✅", "#2ecc71", 0
        )
        self.crear_metrica_simple(
            fr_metricas, "Tardanzas registradas", "15", "#f39c12", 1
        )
        self.crear_metrica_simple(
            fr_metricas, "Inasistencias justificadas", "8", "#3498db", 2
        )
        
        # ============================
        # SECCIÓN 5: ALERTAS (Solo Admin/Secretaria)
        # ============================
        if self.usuario.rol in ['Admin', 'Secretaria']:
            self.crear_seccion_alertas()
        
        # Auto-actualización cada 5 minutos
        self._update_id = self.after(300000, self.actualizar_datos)

    def destroy(self):
        """Limpiar tareas pendientes al destruir"""
        if hasattr(self, '_update_id') and self._update_id:
            try:
                self.after_cancel(self._update_id)
            except:
                pass
        super().destroy()
    
    # =================== MÉTODOS PARA CREAR COMPONENTES ===================
    
    def crear_kpi_card(self, parent, titulo, valor, subtexto, color, col):
        """Crear tarjeta KPI grande"""
        card = ctk.CTkFrame(
            parent,
            fg_color="#2d2d2d",
            corner_radius=15,
            border_width=2,
            border_color=color
        )
        card.grid(row=0, column=col, padx=10, pady=10, sticky="nsew")
        
        # Barra superior de color
        ctk.CTkFrame(
            card,
            height=5,
            fg_color=color,
            corner_radius=0
        ).pack(fill="x")
        
        # Contenido
        fr_content = ctk.CTkFrame(card, fg_color="transparent")
        fr_content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        ctk.CTkLabel(
            fr_content,
            text=titulo,
            font=("Roboto", 11, "bold"),
            text_color=color
        ).pack(anchor="w")
        
        # Valor grande
        ctk.CTkLabel(
            fr_content,
            text=valor,
            font=("Roboto", 36, "bold"),
            text_color="white"
        ).pack(anchor="w", pady=(5, 5))
        
        # Subtexto
        ctk.CTkLabel(
            fr_content,
            text=subtexto,
            font=("Roboto", 9),
            text_color="gray"
        ).pack(anchor="w")
        
        return card
    
    def crear_seccion_financiera(self):
        """Sección financiera (solo Admin/Secretaria/Contador)"""
        fr_financiero = ctk.CTkFrame(
            self.scroll_container,
            fg_color="#922b21",  # Fondo rojo oscuro
            corner_radius=15,
            border_width=2,
            border_color="#c0392b"
        )
        fr_financiero.pack(fill="x", pady=(0, 20))
        
        # Header
        fr_fin_header = ctk.CTkFrame(fr_financiero, fg_color="transparent")
        fr_fin_header.pack(fill="x", padx=20, pady=(15, 10))
        
        ctk.CTkLabel(
            fr_fin_header,
            text="💰 INFORMACIÓN FINANCIERA",
            font=("Roboto", 14, "bold"),
            text_color="white"
        ).pack(side="left")
        
        ctk.CTkLabel(
            fr_fin_header,
            text="🔒 Acceso Restringido",
            font=("Roboto", 9),
            text_color="#ecf0f1",
            fg_color="#c0392b",
            corner_radius=5,
            padx=10,
            pady=3
        ).pack(side="right")
        
        # KPIs Financieros
        fr_kpis_fin = ctk.CTkFrame(fr_financiero, fg_color="transparent")
        fr_kpis_fin.pack(fill="x", padx=20, pady=(0, 15))
        fr_kpis_fin.columnconfigure((0, 1, 2), weight=1)
        
        # Solo muestra si el rol lo permite
        if self.usuario.rol in ['Admin', 'Contador']:
            # Contador y Admin ven montos reales
            self.crear_kpi_financiero(
                fr_kpis_fin, "INGRESO MES", "S/ 45,000", "68% de meta", 0
            )
            self.crear_kpi_financiero(
                fr_kpis_fin, "DEUDA TOTAL", "S/ 12,000", "26% del total", 1
            )
        else:
            # Secretaria solo ve resúmenes
            self.crear_kpi_financiero(
                fr_kpis_fin, "ESTADO COBRANZA", "68%", "Del mes actual", 0
            )
        
        self.crear_kpi_financiero(
            fr_kpis_fin, "MOROSOS", "12", "Requieren seguimiento", 2
        )
    
    def crear_kpi_financiero(self, parent, titulo, valor, detalle, col):
        """KPI financiero pequeño"""
        card = ctk.CTkFrame(parent, fg_color="#7b241c", corner_radius=10)
        card.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
        
        ctk.CTkLabel(
            card,
            text=titulo,
            font=("Roboto", 9, "bold"),
            text_color="#ecf0f1"
        ).pack(pady=(10, 2))
        
        ctk.CTkLabel(
            card,
            text=valor,
            font=("Roboto", 24, "bold"),
            text_color="white"
        ).pack()
        
        ctk.CTkLabel(
            card,
            text=detalle,
            font=("Roboto", 8),
            text_color="#bdc3c7"
        ).pack(pady=(2, 10))
    
    def crear_metrica_simple(self, parent, titulo, valor, color, col):
        """Métrica simple sin borde"""
        fr = ctk.CTkFrame(parent, fg_color="#1a1a1a", corner_radius=8)
        fr.grid(row=0, column=col, padx=5, pady=5, sticky="nsew")
        
        ctk.CTkLabel(
            fr,
            text=titulo,
            font=("Roboto", 10),
            text_color="gray"
        ).pack(pady=(10, 2))
        
        ctk.CTkLabel(
            fr,
            text=valor,
            font=("Roboto", 20, "bold"),
            text_color=color
        ).pack(pady=(0, 10))
    
    def cargar_eventos_dummy(self):
        """Cargar eventos de ejemplo"""
        eventos = [
            {
                'fecha': '25/01',
                'dia': 'Sábado',
                'titulo': 'Examen de Matemática',
                'detalle': 'Grupo A - 08:00 AM',
                'tipo': 'examen',
                'icono': '📝',
                'color': '#e74c3c'
            },
            {
                'fecha': '28/01',
                'dia': 'Martes',
                'titulo': 'Reunión de Apoderados',
                'detalle': 'Todos los grupos - 06:00 PM',
                'tipo': 'reunion',
                'icono': '👥',
                'color': '#3498db'
            },
            {
                'fecha': '30/01',
                'dia': 'Jueves',
                'titulo': 'Vencimiento Cuota Enero',
                'detalle': 'Recordar a apoderados',
                'tipo': 'pago',
                'icono': '💰',
                'color': '#f39c12'
            },
            {
                'fecha': '01/02',
                'dia': 'Sábado',
                'titulo': 'Aniversario de la Institución',
                'detalle': 'Evento especial - Todo el día',
                'tipo': 'evento',
                'icono': '🎉',
                'color': '#9b59b6'
            },
        ]
        
        for evento in eventos:
            self.crear_item_evento(evento)
    
    def crear_item_evento(self, evento):
        """Crear item de evento en la lista"""
        item = ctk.CTkFrame(
            self.scroll_eventos,
            fg_color="#1a1a1a",
            corner_radius=10,
            height=70
        )
        item.pack(fill="x", pady=5)
        item.pack_propagate(False)
        
        # Barra lateral de color
        ctk.CTkFrame(
            item,
            width=5,
            fg_color=evento['color'],
            corner_radius=0
        ).pack(side="left", fill="y")
        
        # Contenido
        fr_content = ctk.CTkFrame(item, fg_color="transparent")
        fr_content.pack(side="left", fill="both", expand=True, padx=15, pady=10)
        
        # Fila superior: Icono + Título
        fr_top = ctk.CTkFrame(fr_content, fg_color="transparent")
        fr_top.pack(fill="x")
        
        ctk.CTkLabel(
            fr_top,
            text=evento['icono'],
            font=("Arial", 20)
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            fr_top,
            text=evento['titulo'],
            font=("Roboto", 13, "bold"),
            text_color="white",
            anchor="w"
        ).pack(side="left", fill="x", expand=True)
        
        # Badge de fecha
        fr_fecha = ctk.CTkFrame(
            fr_top,
            fg_color=evento['color'],
            corner_radius=5
        )
        fr_fecha.pack(side="right")
        
        ctk.CTkLabel(
            fr_fecha,
            text=f"{evento['fecha']} • {evento['dia']}",
            font=("Roboto", 9, "bold"),
            text_color="white"
        ).pack(padx=10, pady=3)
        
        # Fila inferior: Detalle
        ctk.CTkLabel(
            fr_content,
            text=evento['detalle'],
            font=("Roboto", 10),
            text_color="gray",
            anchor="w"
        ).pack(fill="x", pady=(5, 0))
    
    def crear_seccion_alertas(self):
        """Sección de alertas (solo Admin/Secretaria)"""
        fr_alertas = ctk.CTkFrame(
            self.scroll_container,
            fg_color="#2d2d2d",
            corner_radius=15,
            border_width=1,
            border_color="#3d3d3d"
        )
        fr_alertas.pack(fill="x")
        
        # Header
        ctk.CTkLabel(
            fr_alertas,
            text="⚠️ ALERTAS ADMINISTRATIVAS",
            font=("Roboto", 14, "bold"),
            text_color="#e74c3c"
        ).pack(anchor="w", padx=20, pady=(15, 10))
        
        # Lista de alertas
        alertas = [
            {'nivel': 'critico', 'icono': '🔴', 'texto': '12 alumnos morosos >60 días'},
            {'nivel': 'advertencia', 'icono': '🟡', 'texto': 'Vence cuota mañana: 45 apoderados por contactar'},
            {'nivel': 'info', 'icono': '🔵', 'texto': '3 docentes sin registrar asistencia de hoy'},
        ]
        
        for alerta in alertas:
            self.crear_item_alerta(fr_alertas, alerta)
    
    def crear_item_alerta(self, parent, alerta):
        """Item individual de alerta"""
        color = {
            'critico': '#e74c3c',
            'advertencia': '#f39c12',
            'info': '#3498db'
        }[alerta['nivel']]
        
        item = ctk.CTkFrame(parent, fg_color="#1a1a1a", corner_radius=8)
        item.pack(fill="x", padx=15, pady=5)
        
        fr_content = ctk.CTkFrame(item, fg_color="transparent")
        fr_content.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(
            fr_content,
            text=alerta['icono'],
            font=("Arial", 16)
        ).pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            fr_content,
            text=alerta['texto'],
            font=("Roboto", 11),
            text_color="white",
            anchor="w"
        ).pack(side="left", fill="x", expand=True)
    
    # =================== MÉTODOS DE LÓGICA ===================
    
    def abrir_calendario(self):
        """Abrir vista de calendario completo"""
        print("Abrir vista Calendario (pendiente de implementar)")
    
    def actualizar_datos(self):
        """Actualizar datos del dashboard"""
        if not self.winfo_exists():
            return
        # Aquí llamarías a los controllers en un thread
        pass
