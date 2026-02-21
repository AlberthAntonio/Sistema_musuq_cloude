import customtkinter as ctk
from core.theme_manager import ThemeManager as TM

class StudentPreviewCard(ctk.CTkFrame):
    """Panel de vista previa con diseño tipo 'ID Card' moderno"""
    def __init__(self, parent):
        super().__init__(parent, fg_color=TM.bg_card(), corner_radius=16, 
                        border_width=1, border_color=TM.get_theme().border)
        
        self._create_ui()
        
    def _create_ui(self):
        # --- 1. HEADER ---
        header_carnet = ctk.CTkFrame(self, fg_color=TM.primary(), corner_radius=16, height=45)
        header_carnet.pack(fill="x", padx=0, pady=0)
        
        header_patch = ctk.CTkFrame(header_carnet, fg_color=TM.primary(), height=10, corner_radius=0)
        header_patch.place(relx=0, rely=0.8, relwidth=1, relheight=0.2)

        header_lbl = ctk.CTkLabel(
            header_carnet,
            text="SISTEMA MUSUQ  |  ESTUDIANTE",
            font=ctk.CTkFont(family="Roboto", size=10, weight="bold"),
            text_color="white"
        )
        header_lbl.place(relx=0.5, rely=0.5, anchor="center")

        # --- 2. CUERPO DE LA TARJETA ---
        content_carnet = ctk.CTkFrame(self, fg_color="#323232")
        content_carnet.pack(fill="x", padx=20, pady=(20, 10))
        content_carnet.grid_columnconfigure(1, weight=1)

        # --- A. FOTO ---
        foto_container = ctk.CTkFrame(
            content_carnet, 
            width=90, 
            height=110, 
            fg_color=TM.bg_panel(),
            corner_radius=12,
            border_width=1,
            border_color=TM.get_theme().border
        )
        foto_container.grid(row=0, column=0, rowspan=2, padx=(0, 15))
        foto_container.pack_propagate(False)

        ctk.CTkLabel(
            foto_container, 
            text="👤", 
            font=ctk.CTkFont(size=40)
        ).place(relx=0.5, rely=0.5, anchor="center")

        # --- B. DATOS PRINCIPALES ---
        info_frame = ctk.CTkFrame(content_carnet, fg_color="transparent")
        info_frame.grid(row=0, column=1, sticky="nw")

        self.lbl_preview_nombre = ctk.CTkLabel(
            info_frame,
            text="NOMBRE APELLIDOS",
            font=ctk.CTkFont(family="Roboto", size=15, weight="bold"),
            text_color=TM.text(),
            anchor="w",
            wraplength=250,
            justify="left"
        )
        self.lbl_preview_nombre.pack(fill="x", anchor="w")

        self.lbl_carrera_preview = ctk.CTkLabel(
            info_frame,
            text="SELECCIONE CARRERA",
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.primary(),
            anchor="w",
            wraplength=150,
            justify="left"
        )
        self.lbl_carrera_preview.pack(fill="x", anchor="w", pady=(2, 0))

        # --- C. METADATA / BADGES ---
        meta_frame = ctk.CTkFrame(content_carnet, fg_color="transparent")
        meta_frame.grid(row=1, column=1, sticky="sw", pady=(0, 0))

        # Badge DNI
        self._crear_badge(meta_frame, "🪪", "lbl_preview_dni", "--------", TM.text_secondary())
        
        ctk.CTkFrame(meta_frame, height=5, fg_color="transparent").pack()

        # Badge Grupo
        row_grupo = ctk.CTkFrame(meta_frame, fg_color="transparent")
        row_grupo.pack(fill="x", anchor="w")
        ctk.CTkLabel(row_grupo, text="GRUPO:", font=ctk.CTkFont(size=9, weight="bold"), text_color=TM.text_secondary()).pack(side="left", padx=(0,5))
        
        self.lbl_grupo_preview = ctk.CTkLabel(
            row_grupo,
            text="-",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="white",
            fg_color=TM.primary(),
            corner_radius=6,
            width=25,
            height=20
        )
        self.lbl_grupo_preview.pack(side="left")

        ctk.CTkFrame(meta_frame, height=5, fg_color="transparent").pack()

        # Badge Modalidad
        self._crear_badge(meta_frame, "📋", "lbl_modalidad_preview", "-", TM.text_secondary())

    def _crear_badge(self, parent, icon, attr_name, default_text, color):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", anchor="w", pady=1)
        
        ctk.CTkLabel(frame, text=icon, font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 5))
        
        lbl = ctk.CTkLabel(
            frame, 
            text=default_text, 
            font=ctk.CTkFont(family="Roboto", size=11), 
            text_color=color,
            anchor="w"
        )
        lbl.pack(side="left")
        setattr(self, attr_name, lbl)

    def update_data(self, nombre_completo: str, dni: str, carrera: str, grupo: str, modalidad: str):
        """Actualizar datos del carnet"""
        if nombre_completo:
            self.lbl_preview_nombre.configure(text=nombre_completo.upper())
        else:
            self.lbl_preview_nombre.configure(text="NOMBRE APELLIDOS")
            
        if carrera and carrera != "--Seleccione":
            self.lbl_carrera_preview.configure(text=carrera)
        else:
            self.lbl_carrera_preview.configure(text="SELECCIONE CARRERA")
            
        if dni:
            self.lbl_preview_dni.configure(text=f"DNI: {dni}")
        else:
            self.lbl_preview_dni.configure(text="DNI: --------")
            
        if grupo and grupo != "--Seleccione":
            self.lbl_grupo_preview.configure(text=grupo)
        else:
            self.lbl_grupo_preview.configure(text="-")
            
        if modalidad and modalidad != "--Seleccione":
            self.lbl_modalidad_preview.configure(text=modalidad)
        else:
            self.lbl_modalidad_preview.configure(text="-")
            
    def reset(self):
        self.lbl_preview_nombre.configure(text="NOMBRE APELLIDOS")
        self.lbl_carrera_preview.configure(text="SELECCIONE CARRERA")
        self.lbl_preview_dni.configure(text="DNI: --------")
        self.lbl_grupo_preview.configure(text="-")
        self.lbl_modalidad_preview.configure(text="-")
