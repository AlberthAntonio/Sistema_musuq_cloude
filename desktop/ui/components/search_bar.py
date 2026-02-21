"""
Barra de búsqueda
Sistema Musuq Cloud
"""

import customtkinter as ctk
from typing import Callable, Optional
from core.theme_manager import ThemeManager as TM


class SearchBar(ctk.CTkFrame):
    """
    Barra de búsqueda estilizada
    
    Uso:
        search = SearchBar(
            parent=frame,
            placeholder="Buscar alumnos...",
            on_search=self.handle_search
        )
    """
    
    def __init__(
        self,
        parent,
        placeholder: str = "Buscar...",
        on_search: Optional[Callable[[str], None]] = None,
        width: int = 300,
        **kwargs
    ):
        super().__init__(parent, fg_color="transparent", **kwargs)
        
        self.on_search = on_search
        
        # Frame contenedor
        container = ctk.CTkFrame(
            self,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        container.pack(fill="x")
        
        # Icono de búsqueda
        ctk.CTkLabel(
            container,
            text="🔍",
            font=ctk.CTkFont(size=14),
            width=30
        ).pack(side="left", padx=(10, 0))
        
        # Entry
        self.entry = ctk.CTkEntry(
            container,
            placeholder_text=placeholder,
            width=width,
            height=35,
            font=ctk.CTkFont(family="Roboto", size=12),
            fg_color="transparent",
            border_width=0
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)
        
        # Bind Enter key
        self.entry.bind("<Return>", self._on_enter)
        
        # Botón buscar (opcional)
        self.btn_search = ctk.CTkButton(
            container,
            text="Buscar",
            width=70,
            height=30,
            font=ctk.CTkFont(family="Roboto", size=12),
            fg_color=TM.primary(),
            command=self._do_search
        )
        self.btn_search.pack(side="right", padx=5, pady=5)
    
    def _on_enter(self, event):
        """Manejar tecla Enter"""
        self._do_search()
    
    def _do_search(self):
        """Ejecutar búsqueda"""
        if self.on_search:
            self.on_search(self.entry.get())
    
    def get_value(self) -> str:
        """Obtener texto actual"""
        return self.entry.get()
    
    def clear(self):
        """Limpiar búsqueda"""
        self.entry.delete(0, "end")
