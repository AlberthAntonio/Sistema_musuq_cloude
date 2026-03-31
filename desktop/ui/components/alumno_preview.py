import customtkinter as ctk
from typing import Optional, Callable
from PIL import Image
import tkinter as tk
from core.theme_manager import ThemeManager as TM

class StudentPreviewCard(ctk.CTkFrame):
    """Panel de vista previa con diseño tipo 'ID Card' moderno"""
    def __init__(self, parent):
        super().__init__(parent, fg_color=TM.bg_card(), corner_radius=16, 
                        border_width=1, border_color=TM.get_theme().border)

        self._on_pick_photo: Optional[Callable[[], None]] = None
        self._on_capture_photo: Optional[Callable[[], None]] = None
        self._on_clear_photo: Optional[Callable[[], None]] = None
        self._photo_image = None
        
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
        foto_panel = ctk.CTkFrame(content_carnet, fg_color="transparent")
        foto_panel.grid(row=0, column=0, rowspan=2, padx=(0, 15), sticky="n")

        self.foto_container = ctk.CTkFrame(
            foto_panel,
            width=90, 
            height=110, 
            fg_color=TM.bg_panel(),
            corner_radius=12,
            border_width=1,
            border_color=TM.get_theme().border
        )
        self.foto_container.pack(fill="x")
        self.foto_container.pack_propagate(False)

        self.lbl_photo = ctk.CTkLabel(
            self.foto_container,
            text="👤", 
            font=ctk.CTkFont(size=40)
        )
        self.lbl_photo.place(relx=0, rely=0, relwidth=1, relheight=1)

        foto_actions = ctk.CTkFrame(foto_panel, fg_color="transparent")
        foto_actions.pack(fill="x", pady=(6, 0))

        self.btn_subir_foto = ctk.CTkButton(
            foto_actions,
            text="Subir",
            height=26,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color=TM.primary(),
            state="disabled",
            command=self._handle_pick_photo,
        )
        self.btn_subir_foto.pack(fill="x", pady=(0, 4))

        self.btn_capturar_foto = ctk.CTkButton(
            foto_actions,
            text="Camara",
            height=26,
            font=ctk.CTkFont(size=10, weight="bold"),
            fg_color="#0ea5e9",
            hover_color="#0284c7",
            state="disabled",
            command=self._handle_capture_photo,
        )
        self.btn_capturar_foto.pack(fill="x", pady=(0, 4))

        self.btn_quitar_foto = ctk.CTkButton(
            foto_actions,
            text="Quitar",
            height=24,
            font=ctk.CTkFont(size=10),
            fg_color="transparent",
            border_width=1,
            border_color=TM.get_theme().border,
            text_color=TM.text_secondary(),
            state="disabled",
            command=self._handle_clear_photo,
        )
        self.btn_quitar_foto.pack(fill="x")

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

        # Fila Modalidad + Nivel (nivel oculto por defecto)
        row_modalidad = ctk.CTkFrame(meta_frame, fg_color="transparent")
        row_modalidad.pack(fill="x", anchor="w", pady=1)

        ctk.CTkLabel(row_modalidad, text="📋", font=ctk.CTkFont(size=12)).pack(side="left", padx=(0, 5))
        self.lbl_modalidad_preview = ctk.CTkLabel(
            row_modalidad,
            text="-",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary(),
            anchor="w"
        )
        self.lbl_modalidad_preview.pack(side="left")

        # Nivel al costado de modalidad
        self.fr_nivel_badge = ctk.CTkFrame(row_modalidad, fg_color="transparent")
        # No se hace pack todavía (oculto por defecto)
        ctk.CTkLabel(self.fr_nivel_badge, text="  |", font=ctk.CTkFont(size=11),
                     text_color="#505050").pack(side="left")
        ctk.CTkLabel(self.fr_nivel_badge, text="🏫", font=ctk.CTkFont(size=12)).pack(side="left", padx=(4, 4))
        self.lbl_nivel_preview = ctk.CTkLabel(
            self.fr_nivel_badge,
            text="-",
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color="#3498db",
            anchor="w"
        )
        self.lbl_nivel_preview.pack(side="left")

        # Grado al costado del nivel
        ctk.CTkLabel(self.fr_nivel_badge, text=" ·", font=ctk.CTkFont(size=11),
                     text_color="#505050").pack(side="left")
        self.lbl_grado_preview = ctk.CTkLabel(
            self.fr_nivel_badge,
            text="",
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color="#2ecc71",
            anchor="w"
        )
        self.lbl_grado_preview.pack(side="left", padx=(3, 0))

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

    def set_photo_actions(
        self,
        on_pick_photo: Optional[Callable[[], None]] = None,
        on_capture_photo: Optional[Callable[[], None]] = None,
        on_clear_photo: Optional[Callable[[], None]] = None,
    ):
        """Vincula callbacks para acciones de foto del panel."""
        self._on_pick_photo = on_pick_photo
        self._on_capture_photo = on_capture_photo
        self._on_clear_photo = on_clear_photo

        self.btn_subir_foto.configure(state="normal" if on_pick_photo else "disabled")
        self.btn_capturar_foto.configure(state="normal" if on_capture_photo else "disabled")
        self.btn_quitar_foto.configure(state="normal" if on_clear_photo else "disabled")

    def _handle_pick_photo(self):
        if self._on_pick_photo:
            self._on_pick_photo()

    def _handle_capture_photo(self):
        if self._on_capture_photo:
            self._on_capture_photo()

    def _handle_clear_photo(self):
        if self._on_clear_photo:
            self._on_clear_photo()

    def _get_photo_target_size(self):
        """Obtiene ancho/alto interno del cuadro de foto para cubrirlo completo."""
        self.foto_container.update_idletasks()

        # Primero intentar tamaño real renderizado.
        target_w = int(self.foto_container.winfo_width())
        target_h = int(self.foto_container.winfo_height())

        # Fallback a tamaño configurado si el widget aun no fue calculado.
        if target_w <= 1:
            target_w = int(float(self.foto_container.cget("width")))
        if target_h <= 1:
            target_h = int(float(self.foto_container.cget("height")))

        # Descontar borde para cubrir el area interna visible.
        border_width = int(float(self.foto_container.cget("border_width") or 0))
        target_w = max(1, target_w - (border_width * 2))
        target_h = max(1, target_h - (border_width * 2))
        return target_w, target_h

    def set_photo_image(self, image: Image.Image):
        """Renderiza una imagen en el placeholder de foto."""
        target_w, target_h = self._get_photo_target_size()
        preview = image.copy().convert("RGB")

        src_w, src_h = preview.size
        if src_w <= 0 or src_h <= 0:
            return

        target_ratio = target_w / target_h
        src_ratio = src_w / src_h

        # Escalado tipo "cover": llena todo el cuadro y recorta centrado.
        if src_ratio > target_ratio:
            new_h = target_h
            new_w = int(new_h * src_ratio)
        else:
            new_w = target_w
            new_h = int(new_w / src_ratio)

        resized = preview.resize((new_w, new_h), Image.Resampling.LANCZOS)
        left = max(0, (new_w - target_w) // 2)
        top = max(0, (new_h - target_h) // 2)
        covered = resized.crop((left, top, left + target_w, top + target_h))

        self._photo_image = ctk.CTkImage(light_image=covered, size=(target_w, target_h))
        self.lbl_photo.configure(image=self._photo_image, text="")

    def clear_photo(self):
        """Restaura el placeholder sin foto."""
        # En algunos casos Tk puede conservar una referencia rota a un pyimage.
        # Limpiamos el image del label interno primero y, si falla, recreamos el widget.
        if not hasattr(self, "lbl_photo"):
            self._photo_image = None
            return

        try:
            if self.lbl_photo.winfo_exists():
                inner_label = getattr(self.lbl_photo, "_label", None)
                if inner_label is not None:
                    inner_label.configure(image="")
                self.lbl_photo.configure(image=None, text="👤")
        except tk.TclError:
            try:
                if self.lbl_photo.winfo_exists():
                    self.lbl_photo.destroy()
            except tk.TclError:
                pass

            self.lbl_photo = ctk.CTkLabel(
                self.foto_container,
                text="👤",
                font=ctk.CTkFont(size=40),
            )
            self.lbl_photo.place(relx=0, rely=0, relwidth=1, relheight=1)
        finally:
            self._photo_image = None

    def update_data(self, nombre_completo: str, dni: str, carrera: str, grupo: str, modalidad: str, nivel: str = None, grado: str = None):
        """Actualizar datos del carnet"""""
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

        # Nivel y Grado: visibles solo si modalidad es COLEGIO
        if modalidad == "COLEGIO" and nivel and nivel != "--Seleccione":
            self.lbl_nivel_preview.configure(text=nivel)
            grado_texto = grado if (grado and grado != "--Seleccione") else ""
            self.lbl_grado_preview.configure(text=grado_texto)
            self.fr_nivel_badge.pack(side="left")
        else:
            self.fr_nivel_badge.pack_forget()
            
    def reset(self):
        self.lbl_preview_nombre.configure(text="NOMBRE APELLIDOS")
        self.lbl_carrera_preview.configure(text="SELECCIONE CARRERA")
        self.lbl_preview_dni.configure(text="DNI: --------")
        self.lbl_grupo_preview.configure(text="-")
        self.lbl_modalidad_preview.configure(text="-")
        self.lbl_nivel_preview.configure(text="-")
        self.lbl_grado_preview.configure(text="")
        self.fr_nivel_badge.pack_forget()
        self.clear_photo()
