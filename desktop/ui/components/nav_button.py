"""
Botón de Navegación para Sidebar
Sistema Musuq Cloud
"""

import customtkinter as ctk
from typing import Callable, Optional
from core.theme_manager import ThemeManager as TM


class NavButton(ctk.CTkButton):
    """
    Botón de navegación estilizado para sidebar
    
    Uso:
        btn = NavButton(
            parent=sidebar,
            text="📊 Dashboard",
            command=self.show_dashboard,
            active=True
        )
    """
    
    def __init__(
        self,
        parent,
        text: str,
        command: Optional[Callable] = None,
        active: bool = False,
        **kwargs
    ):
        # Colores según estado
        self.active_color = (TM.primary(), "#1F538D")
        self.inactive_color = "transparent"
        self.hover_color = ("#3B8ED0", "#1F538D")
        
        super().__init__(
            parent,
            text=text,
            command=command,
            width=200,
            height=40,
            font=ctk.CTkFont(family="Roboto", size=14),
            anchor="w",
            corner_radius=8,
            fg_color=self.active_color if active else self.inactive_color,
            hover_color=self.hover_color,
            text_color=TM.text(),
            **kwargs
        )
        
        self._is_active = active
    
    def set_active(self, active: bool):
        """Cambiar estado activo/inactivo"""
        self._is_active = active
        self.configure(
            fg_color=self.active_color if active else self.inactive_color
        )
    
    @property
    def is_active(self) -> bool:
        return self._is_active


class SubMenuButton(ctk.CTkButton):
    """
    Botón de submenú (más pequeño, indentado)
    
    Uso:
        btn = SubMenuButton(
            parent=submenu_frame,
            text="• Tomar Asistencia",
            command=self.show_asistencia
        )
    """
    
    def __init__(
        self,
        parent,
        text: str,
        command: Optional[Callable] = None,
        **kwargs
    ):
        super().__init__(
            parent,
            text=text,
            command=command,
            width=180,
            height=30,
            font=ctk.CTkFont(family="Roboto", size=12),
            anchor="w",
            corner_radius=5,
            fg_color="transparent",
            hover_color=("#404040", "#353535"),
            text_color=TM.text_secondary(),
            **kwargs
        )
