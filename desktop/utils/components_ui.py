import customtkinter as ctk
from styles import tabla_style as st

def crear_tarjeta_metrica(parent, titulo, valor, icono, color_acento, grid_col, is_progress=False):
    """
    Crea una tarjeta de métrica estandarizada.
    
    Args:
        parent: Widget padre (usualmente un frame con grid)
        titulo: Título de la métrica
        valor: Valor a mostrar (texto o número)
        icono: Emoji o texto corto para el icono de fondo
        color_acento: Color para el título y decoración
        grid_col: Columna en el grid del padre
        is_progress: Si es True, muestra una barra de progreso en lugar de una línea decorativa
    """
    card = ctk.CTkFrame(parent, fg_color=st.Colors.BG_CARD, corner_radius=10)
    card.grid(row=0, column=grid_col, sticky="ew", padx=5)
    
    # Icono de fondo
    ctk.CTkLabel(
        card, 
        text=icono, 
        font=("Arial", 40), 
        text_color="#404040"
    ).place(relx=0.85, rely=0.5, anchor="center")

    # Contenido
    content = ctk.CTkFrame(card, fg_color="transparent")
    content.pack(fill="both", padx=15, pady=15)

    # Título
    ctk.CTkLabel(
        content, 
        text=titulo, 
        font=st.Fonts.HEADER, 
        text_color=color_acento
    ).pack(anchor="w")
    
    # Valor
    ctk.CTkLabel(
        content, 
        text=valor, 
        font=st.Fonts.NUMBER_BIG, 
        text_color=st.Colors.TEXT_WHITE
    ).pack(anchor="w", pady=(0, 5))
    
    # Decoración inferior
    if is_progress:
        try:
            # Intentar parsear porcentaje tipo "85%"
            val_float = float(str(valor).replace("%", "")) / 100
        except:
            val_float = 0
            
        prog = ctk.CTkProgressBar(
            content,
            width=120,
            height=6,
            progress_color=color_acento,
            fg_color=st.Colors.BG_PANEL
        )
        prog.pack(anchor="w", pady=5)
        prog.set(val_float)
    else:
        # Línea simple
        ctk.CTkFrame(
            content, 
            height=3, 
            width=40, 
            fg_color=color_acento,
            corner_radius=2
        ).pack(anchor="w", pady=5)
    
    return card

def crear_badge_estado(parent, texto, color_bg, ancho=85):
    """
    Crea un badge (etiqueta redondeada) para estados.
    """
    container = ctk.CTkFrame(parent, fg_color="transparent", height=40)
    container.pack_propagate(False)
    
    badge = ctk.CTkLabel(
        container, 
        text=texto, 
        fg_color=color_bg, 
        text_color="white", 
        corner_radius=5, 
        width=ancho, 
        height=22, 
        font=("Arial", 9, "bold")
    )
    badge.place(relx=0.5, rely=0.5, anchor="center")
    
    return container
