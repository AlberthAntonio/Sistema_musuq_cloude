"""
Componentes KPI Card
Sistema Musuq Cloud
"""

import customtkinter as ctk
from core.theme_manager import ThemeManager as TM


class KPICard(ctk.CTkFrame):
    """
    Tarjeta KPI grande estilo Dashboard
    
    Uso:
        card = KPICard(
            parent=frame,
            titulo="👥 ALUMNOS ACTIVOS",
            valor="250",
            subtexto="Matriculados este periodo",
            color="#3498db",
            columna=0
        )
        card.actualizar_valor("275")
    """
    
    def __init__(
        self, 
        parent, 
        titulo: str, 
        valor: str, 
        subtexto: str, 
        color: str,
        columna: int = 0,
        **kwargs
    ):
        super().__init__(
            parent,
            fg_color=TM.bg_card(),
            corner_radius=15,
            border_width=2,
            border_color=color,
            **kwargs
        )
        self.grid(row=0, column=columna, padx=10, pady=10, sticky="nsew")
        
        # Barra superior de color
        self.color_bar = ctk.CTkFrame(
            self,
            height=5,
            fg_color=color,
            corner_radius=0
        )
        self.color_bar.pack(fill="x")
        
        # Contenido
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        self.lbl_titulo = ctk.CTkLabel(
            content,
            text=titulo,
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=color
        )
        self.lbl_titulo.pack(anchor="w")
        
        # Valor grande
        self.lbl_valor = ctk.CTkLabel(
            content,
            text=valor,
            font=ctk.CTkFont(family="Roboto", size=36, weight="bold"),
            text_color=TM.text()
        )
        self.lbl_valor.pack(anchor="w", pady=(5, 5))
        
        # Subtexto
        self.lbl_subtexto = ctk.CTkLabel(
            content,
            text=subtexto,
            font=ctk.CTkFont(family="Roboto", size=9),
            text_color=TM.text_secondary()
        )
        self.lbl_subtexto.pack(anchor="w")
    
    def actualizar_valor(self, nuevo_valor: str):
        """Actualizar el valor mostrado"""
        self.lbl_valor.configure(text=str(nuevo_valor))
    
    def actualizar_subtexto(self, nuevo_texto: str):
        """Actualizar el subtexto"""
        self.lbl_subtexto.configure(text=str(nuevo_texto))


class KPICardSmall(ctk.CTkFrame):
    """
    Tarjeta KPI pequeña para métricas secundarias
    
    Uso:
        card = KPICardSmall(
            parent=frame,
            titulo="INGRESOS",
            valor="S/. 12,500",
            color="#2ecc71",
            icono="💰"
        )
        card.pack(side="left", expand=True, fill="x")
    """
    
    def __init__(
        self,
        parent,
        titulo: str,
        valor: str,
        color: str,
        icono: str = "",
        **kwargs
    ):
        super().__init__(
            parent,
            fg_color=TM.bg_card(),
            corner_radius=10,
            height=80,
            **kwargs
        )
        self.pack_propagate(False)
        
        # Barra lateral de color
        ctk.CTkFrame(
            self,
            width=5,
            fg_color=color,
            corner_radius=0
        ).pack(side="left", fill="y", padx=(0, 10))
        
        # Contenido
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(side="left", fill="both", expand=True, pady=10)
        
        # Título
        ctk.CTkLabel(
            content,
            text=titulo,
            font=ctk.CTkFont(family="Roboto", size=10, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(anchor="w")
        
        # Valor
        self.lbl_valor = ctk.CTkLabel(
            content,
            text=valor,
            font=ctk.CTkFont(family="Roboto", size=20, weight="bold"),
            text_color=TM.text()
        )
        self.lbl_valor.pack(anchor="w")
        
        # Icono flotante
        if icono:
            ctk.CTkLabel(
                self,
                text=icono,
                font=ctk.CTkFont(size=25),
                text_color=TM.text_muted() if hasattr(TM, 'text_muted') else "#5A5A5A"
            ).pack(side="right", padx=15)
    
    def actualizar_valor(self, nuevo_valor: str):
        """Actualizar el valor"""
        self.lbl_valor.configure(text=str(nuevo_valor))
