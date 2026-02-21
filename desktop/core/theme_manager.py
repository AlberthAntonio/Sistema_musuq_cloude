"""
Gestor de temas visuales
Sistema Musuq Cloud
"""

import customtkinter as ctk
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class Theme:
    """Definición de un tema"""
    name: str
    
    # Fondos
    bg_main: str
    bg_panel: str
    bg_card: str
    bg_sidebar: str
    
    # Bordes y hover
    border: str
    hover: str
    
    # Colores principales
    primary: str
    success: str
    warning: str
    danger: str
    info: str
    
    # Texto
    text_primary: str
    text_secondary: str
    text_muted: str
    
    # Modo CTK
    appearance_mode: str = "dark"


# ==================== TEMAS DISPONIBLES ====================

THEME_DARK = Theme(
    name="Oscuro",
    bg_main="#1a1a1a",
    bg_panel="#2b2b2b",
    bg_card="#2d2d2d",
    bg_sidebar="#242424",
    border="#3d3d3d",
    hover="#3d5a75",
    primary="#3498db",
    success="#2ecc71",
    warning="#f39c12",
    danger="#e74c3c",
    info="#9b59b6",
    text_primary="#ffffff",
    text_secondary="#b0b0b0",
    text_muted="#707070",
    appearance_mode="dark"
)

THEME_LIGHT = Theme(
    name="Claro",
    bg_main="#f5f5f5",
    bg_panel="#ffffff",
    bg_card="#ffffff",
    bg_sidebar="#e8e8e8",
    border="#d0d0d0",
    hover="#e3f2fd",
    primary="#2980b9",
    success="#27ae60",
    warning="#e67e22",
    danger="#c0392b",
    info="#8e44ad",
    text_primary="#1a1a1a",
    text_secondary="#505050",
    text_muted="#909090",
    appearance_mode="light"
)

THEME_BLUE_PRO = Theme(
    name="Azul Pro",
    bg_main="#1a2634",
    bg_panel="#243447",
    bg_card="#2d3e50",
    bg_sidebar="#1e2d3d",
    border="#3d5a80",
    hover="#4a6fa5",
    primary="#4fc3f7",
    success="#66bb6a",
    warning="#ffb74d",
    danger="#ef5350",
    info="#ba68c8",
    text_primary="#ffffff",
    text_secondary="#b0bec5",
    text_muted="#78909c",
    appearance_mode="dark"
)

THEME_GREEN_EDU = Theme(
    name="Verde Edu",
    bg_main="#1a2e1a",
    bg_panel="#243d24",
    bg_card="#2d4a2d",
    bg_sidebar="#1e3a1e",
    border="#4a7c4a",
    hover="#5a9a5a",
    primary="#66bb6a",
    success="#81c784",
    warning="#ffb74d",
    danger="#e57373",
    info="#4dd0e1",
    text_primary="#ffffff",
    text_secondary="#a5d6a7",
    text_muted="#81c784",
    appearance_mode="dark"
)

# Diccionario de temas
THEMES: Dict[str, Theme] = {
    "dark": THEME_DARK,
    "light": THEME_LIGHT,
    "blue_pro": THEME_BLUE_PRO,
    "green_edu": THEME_GREEN_EDU
}


class ThemeManager:
    """Gestor de temas de la aplicación"""
    
    _instance: Optional['ThemeManager'] = None
    _current_theme: Theme = THEME_DARK
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_theme(cls) -> Theme:
        """Obtener tema actual"""
        return cls._current_theme
    
    @classmethod
    def set_theme(cls, theme_key: str):
        """Cambiar tema"""
        if theme_key in THEMES:
            cls._current_theme = THEMES[theme_key]
            ctk.set_appearance_mode(cls._current_theme.appearance_mode)
    
    @classmethod
    def get_available_themes(cls) -> Dict[str, str]:
        """Obtener temas disponibles"""
        return {key: theme.name for key, theme in THEMES.items()}
    
    # ==================== ATAJOS DE COLORES ====================
    
    @classmethod
    def bg_main(cls) -> str:
        return cls._current_theme.bg_main
    
    @classmethod
    def bg_panel(cls) -> str:
        return cls._current_theme.bg_panel
    
    @classmethod
    def bg_card(cls) -> str:
        return cls._current_theme.bg_card
    
    @classmethod
    def bg_sidebar(cls) -> str:
        return cls._current_theme.bg_sidebar
    
    @classmethod
    def primary(cls) -> str:
        return cls._current_theme.primary
    
    @classmethod
    def success(cls) -> str:
        return cls._current_theme.success
    
    @classmethod
    def warning(cls) -> str:
        return cls._current_theme.warning
    
    @classmethod
    def danger(cls) -> str:
        return cls._current_theme.danger
    
    @classmethod
    def text(cls) -> str:
        return cls._current_theme.text_primary
    
    @classmethod
    def text_secondary(cls) -> str:
        return cls._current_theme.text_secondary

    @classmethod
    def text_muted(cls) -> str:
        return cls._current_theme.text_muted

    @classmethod
    def hover(cls) -> str:
        return cls._current_theme.hover

    @classmethod
    def info(cls) -> str:
        return cls._current_theme.info


# Alias para acceso rápido
TM = ThemeManager
