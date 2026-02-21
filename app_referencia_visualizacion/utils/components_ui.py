# componentes_ui.py
import customtkinter as ctk
import app.styles.tabla_style as style

def crear_fila_tabla(parent, datos, index):
    """
    Crea una fila estandarizada con estilo Zebra.
    datos: Lista o tupla con los textos de la fila
    index: El índice (i) del bucle para calcular el color par/impar
    """
    # Lógica Zebra (Alternar colores)
    bg_color = style.Colors.ROW_ODD if index % 2 == 0 else style.Colors.ROW_EVEN
    
    row = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=5, height=40)
    row.pack(fill="x", pady=2)
    
    for item in datos:
        # Si el item es una tupla (Texto, Color), lo tratamos especial (para estados)
        if isinstance(item, tuple):
            texto, color_texto = item
            font_uso = style.Fonts.HEADER # Negrita para estados
        else:
            texto = item
            color_texto = style.Colors.TEXT_WHITE
            font_uso = style.Fonts.BODY

        # Creamos la celda
        ctk.CTkLabel(row, text=texto, 
                     text_color=color_texto, 
                     font=font_uso).pack(side="left", expand=True)
    
    return row

def crear_tarjeta_metrica(parent, titulo, valor, icono, color_acento, grid_col):
    """
    Crea una tarjeta de métrica estandarizada.
    """
    card = ctk.CTkFrame(parent, fg_color=style.Colors.BG_PANEL, corner_radius=10)
    card.grid(row=0, column=grid_col, sticky="ew", padx=5)
    
    # Icono de fondo
    ctk.CTkLabel(card, text=icono, font=("Arial", 40), 
                 text_color="#363636").place(relx=0.85, rely=0.5, anchor="center")

    # Contenido
    content = ctk.CTkFrame(card, fg_color="transparent")
    content.pack(fill="both", padx=15, pady=15)

    ctk.CTkLabel(content, text=titulo, font=style.Fonts.HEADER, text_color=color_acento).pack(anchor="w")
    ctk.CTkLabel(content, text=valor, font=style.Fonts.NUMBER_BIG, text_color="white").pack(anchor="w", pady=(0, 5))
    
    # Línea decorativa
    ctk.CTkFrame(content, height=2, width=30, fg_color=color_acento).pack(anchor="w", pady=5)