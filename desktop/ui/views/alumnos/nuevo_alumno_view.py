"""
Panel para Registrar Nuevo Alumno - Refactorizado MVC
Sistema Musuq Cloud
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
import io
import importlib
import os
from typing import Dict, Optional, List
from datetime import date, datetime
from tkcalendar import DateEntry
from PIL import Image

from core.api_client import APIClient
from core.theme_manager import ThemeManager as TM
from controllers.alumno_controller import AlumnoController
from ui.components.alumno_preview import StudentPreviewCard
from ui.components.audit_panel import AuditPanel
from ui.components.financial_ticket import FinancialTicket


class NuevoAlumnoPanel(ctk.CTkFrame):
    """Formulario completo para registrar un nuevo alumno con Grid Layout"""
    
    def __init__(self, parent, auth_client: APIClient):
        super().__init__(parent, fg_color="transparent")
        
        self.auth_client = auth_client
        self._auth_token = auth_client.token
        self.controller = None
        
        # Diccionarios de widgets
        self.entries: Dict[str, ctk.CTkEntry] = {}
        self.combos: Dict[str, ctk.CTkComboBox] = {}
        self.date_entries: Dict[str, DateEntry] = {}
        self.entry_deuda = None
        self._ui_ready = False
        self._loading_frame = None
        self._foto_bytes: Optional[bytes] = None
        self._foto_filename: Optional[str] = None
        self._foto_mime_type: Optional[str] = None
        
        self._show_loading_state()
        # Diferimos la construcción completa para evitar bloquear la primera pintura de la vista.
        self.after(1, self._build_ui_deferred)
        #self._recargar_ultimos_registros()

    def _show_loading_state(self):
        """Placeholder liviano mientras se construye el formulario completo."""
        self._loading_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._loading_frame.pack(fill="both", expand=True)
        ctk.CTkLabel(
            self._loading_frame,
            text="Cargando formulario de matrícula...",
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            text_color=TM.text_secondary(),
        ).pack(expand=True)

    def _build_ui_deferred(self):
        """Construye la UI pesada después del primer render."""
        if self._ui_ready:
            return

        if self.controller is None:
            self.controller = AlumnoController(self._auth_token)

        if self._loading_frame is not None:
            self._loading_frame.destroy()
            self._loading_frame = None

        self.create_widgets()
        self._ui_ready = True
    
    def create_widgets(self):
        """Crear widgets del formulario"""
        
        # ==================== HEADER ====================
        header = ctk.CTkFrame(self, fg_color="transparent", height=60)
        header.pack(fill="x", padx=25, pady=(20, 15))
        header.pack_propagate(False)
        
        # Título
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", fill="y")
        
        ctk.CTkLabel(
            title_frame,
            text="➕",
            font=ctk.CTkFont(size=28)
        ).pack(side="left", padx=(0, 10))
        
        title_text = ctk.CTkFrame(title_frame, fg_color="transparent")
        title_text.pack(side="left")
        
        ctk.CTkLabel(
            title_text,
            text="NUEVA MATRÍCULA",
            font=ctk.CTkFont(family="Roboto", size=22, weight="bold"),
            text_color=TM.text()
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            title_text,
            text="Complete los datos del estudiante",
            font=ctk.CTkFont(size=11),
            text_color=TM.text_secondary()
        ).pack(anchor="w")
        
        # Botones
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.pack(side="right", fill="y")
        
        self.btn_limpiar = ctk.CTkButton(
            btn_frame,
            text="🗑️ Limpiar",
            width=110,
            height=38,
            fg_color="transparent",
            border_width=2,
            border_color=TM.get_theme().border,
            hover_color=TM.bg_panel(),
            text_color=TM.text_secondary(),
            command=self.limpiar_formulario
        )
        self.btn_limpiar.pack(side="left", padx=(0, 10))
        
        self.btn_guardar = ctk.CTkButton(
            btn_frame,
            text="💾 GUARDAR MATRÍCULA",
            width=180,
            height=38,
            fg_color=TM.primary(),
            hover_color=TM.success(),
            font=ctk.CTkFont(weight="bold"),
            command=self.guardar_alumno
        )
        self.btn_guardar.pack(side="left")
        
        # ==================== MAIN CONTAINER ====================
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=25, pady=(0, 20))
        
        main_container.grid_columnconfigure(0, weight=2)
        main_container.grid_columnconfigure(1, weight=1)
        main_container.grid_rowconfigure(0, weight=1)
        
        # ==================== COLUMNA IZQUIERDA: FORMULARIO ====================
        form_scroll = ctk.CTkScrollableFrame(main_container, fg_color="transparent")
        form_scroll.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # SECCIÓN 1: DATOS DEL ALUMNO
        self.crear_seccion_card(form_scroll, "👤 1. DATOS DEL ALUMNO", "#3498db", self.crear_campos_alumno)
        
        # SECCIÓN 2: DATOS ACADÉMICOS
        self.crear_seccion_card(form_scroll, "🎓 2. DATOS ACADÉMICOS", "#2ecc71", self.crear_campos_academico)
        
        # SECCIÓN 3: DATOS PADRES/APODERADOS
        self.crear_seccion_card(form_scroll, "👪 3. DATOS PADRES/APODERADOS", "#9b59b6", self.crear_campos_padres)
        
        # SECCIÓN 4: IMPORTE Y PAGOS
        self.crear_seccion_card(form_scroll, "💰 4. IMPORTE Y PAGOS", "#f39c12", self.crear_campos_pago)
        
        #self.crear_seccion_registros(form_scroll)

        # ==================== COLUMNA DERECHA: VISTA PREVIA ====================
        self.crear_panel_preview(main_container)
    
    def crear_seccion_card(self, parent, titulo: str, color: str, content_func):
        """Crear tarjeta de sección con mejor diseño"""
        card = ctk.CTkFrame(parent, fg_color=TM.bg_card(), corner_radius=12)
        card.pack(fill="x", pady=(0, 15))
        
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 10))
        
        icon_frame = ctk.CTkFrame(header, fg_color=color, corner_radius=20, width=6, height=6)
        icon_frame.pack(side="left", padx=(0, 12))
        icon_frame.pack_propagate(False)
        
        ctk.CTkLabel(header, text=titulo, font=ctk.CTkFont(family="Roboto", size=13, weight="bold"), text_color=color).pack(side="left")
        
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="x", padx=15, pady=(0, 15))
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        
        content_func(content)
    
    def crear_seccion_registros(self, parent):
        """Sección de últimos registros"""
        card = ctk.CTkFrame(parent, fg_color="transparent")
        card.pack(fill="x", pady=(10, 0))
        
        ctk.CTkLabel(card, text="ÚLTIMOS REGISTROS", font=ctk.CTkFont(size=12, weight="bold"), text_color=TM.text_secondary()).pack(anchor="w", pady=(0,5))
        
        self.lista_container = ctk.CTkFrame(card, fg_color=TM.bg_card())
        self.lista_container.pack(fill="x")
        
    def crear_panel_preview(self, parent):
        """Panel derecho con componentes modulares"""
        preview_container = ctk.CTkFrame(parent, fg_color="transparent")
        preview_container.grid(row=0, column=1, sticky="nsew", padx=(15, 0))
        
        # Componentes UI Refactorizados
        self.preview_card = StudentPreviewCard(preview_container)
        self.preview_card.pack(fill="x", pady=(0, 15))
        self.preview_card.set_photo_actions(
            on_pick_photo=self.seleccionar_foto_archivo,
            on_capture_photo=self.capturar_foto_camara,
            on_clear_photo=lambda: self.quitar_foto(pedir_confirmacion=True),
        )
        
        self.audit_panel = AuditPanel(preview_container)
        self.audit_panel.pack(fill="x", pady=(0, 15))
        
        self.financial_ticket = FinancialTicket(preview_container)
        self.financial_ticket.pack(fill="x", pady=(0, 15))

        self.lbl_status = ctk.CTkLabel(preview_container, text="", font=ctk.CTkFont(size=10), text_color=TM.text())
        self.lbl_status.pack(pady=(0,0))
        
    # ==================== GRID LAYOUT HELPERS ====================
    
    def crear_campo_grid(self, parent, key: str, label: str, row: int, col: int, colspan: int = 1, 
                         solo_numeros: bool = False, max_char: int = None, mayusculas: bool = False,
                         on_change=None, allow_decimal: bool = False):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=colspan, padx=10, pady=5, sticky="ew")
        
        text_color = TM.text() if "*" in label else TM.text_secondary()
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11, weight="bold"), 
                     text_color=text_color, anchor="w").pack(fill="x")
        
        entry = ctk.CTkEntry(frame, height=35, fg_color=TM.bg_panel(), 
                             border_color=TM.get_theme().border, corner_radius=6)
        entry.pack(fill="x", pady=(2, 0))
        
        # Validaciones
        if solo_numeros or max_char or allow_decimal:
            vcmd = (self.register(lambda t: self.validar_input(t, solo_numeros, max_char, allow_decimal)), '%P')
            entry.configure(validate="key", validatecommand=vcmd)
        
        if mayusculas:
            entry.bind("<KeyRelease>", lambda e: self.forzar_mayusculas(entry))
        
        if on_change:
            entry.bind("<KeyRelease>", lambda e: on_change())
        
        self.entries[key] = entry
    
    def crear_combo_grid(self, parent, key: str, label: str, valores: list, row: int, col: int, 
                         colspan: int = 1, on_change=None, state: str = "readonly"):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=colspan, padx=10, pady=5, sticky="ew")
        
        text_color = TM.text() if "*" in label else TM.text_secondary()
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11, weight="bold"), 
                     text_color=text_color, anchor="w").pack(fill="x")
        
        combo = ctk.CTkComboBox(
            frame,
            values=valores,
            height=35,
            state=state,
            fg_color=TM.bg_panel(),
            border_color=TM.get_theme().border,
            button_color=TM.primary(),
            dropdown_fg_color=TM.bg_panel(),
            corner_radius=6,
            command=on_change if on_change else None,
        )
        combo.pack(fill="x", pady=(2, 0))
        combo.set("--Seleccione")

        self.combos[key] = combo
    
    def crear_fecha_grid(self, parent, key: str, label: str, row: int, col: int, colspan: int = 1):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=row, column=col, columnspan=colspan, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(frame, text=label, font=ctk.CTkFont(size=11, weight="bold"), 
                     text_color=TM.text_secondary(), anchor="w").pack(fill="x")
        
        date_entry = DateEntry(
            frame, width=16, background='#3498db', foreground='white', borderwidth=2,
            date_pattern='dd/mm/yyyy', font=('Roboto', 10)
        )
        date_entry.pack(fill="x", pady=(2, 0))
        
        self.date_entries[key] = date_entry

    def crear_campos_alumno(self, parent):
        self.crear_campo_grid(parent, "nombres", "Nombres *", row=0, col=0, mayusculas=True, on_change=self.actualizar_preview)
        self.crear_campo_grid(parent, "apellido_paterno", "Ap. Paterno *", row=0, col=1, mayusculas=True, on_change=self.actualizar_preview)
        self.crear_campo_grid(parent, "apellido_materno", "Ap. Materno *", row=1, col=0, mayusculas=True, on_change=self.actualizar_preview)
        self.crear_campo_grid(parent, "dni", "DNI *", row=1, col=1, solo_numeros=True, max_char=8, on_change=self.actualizar_preview)
        self.crear_fecha_grid(parent, "fecha_nacimiento", "Fecha Nacimiento", row=2, col=0)
    
    def crear_campos_academico(self, parent):
        self.crear_combo_grid(parent, "grupo", "Grupo *", ["A", "B", "C", "D"], row=0, col=0, on_change=self.on_grupo_change)
        self.crear_combo_grid(parent, "carrera", "Carrera *", [], row=0, col=1, on_change=self.actualizar_preview)
        self.crear_combo_grid(parent, "modalidad", "Modalidad *", ["PRIMERA OPCION", "ORDINARIO", "COLEGIO", "REFORZAMIENTO"], row=1, col=0, on_change=self.on_modalidad_change)
        self.crear_combo_grid(parent, "horario", "Horario", ["MATUTINO", "VESPERTINO", "DOBLE HORARIO"], row=1, col=1)

        # --- CAMPOS COLEGIO: Nivel y Grado (ocultos por defecto) ---
        self.fr_colegio = ctk.CTkFrame(parent, fg_color="transparent")
        self.fr_colegio.grid(row=2, column=0, columnspan=2, sticky="ew")
        self.fr_colegio.grid_columnconfigure(0, weight=1)
        self.fr_colegio.grid_columnconfigure(1, weight=1)

        # Nivel
        fr_nivel = ctk.CTkFrame(self.fr_colegio, fg_color="transparent")
        fr_nivel.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(fr_nivel, text="Nivel *", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=TM.text(), anchor="w").pack(fill="x")
        self.combos["nivel"] = ctk.CTkComboBox(
            fr_nivel, values=["PRIMARIA", "SECUNDARIA"], height=35,
            fg_color=TM.bg_panel(), border_color=TM.get_theme().border,
            button_color=TM.primary(), dropdown_fg_color=TM.bg_panel(), corner_radius=6,
            command=self.on_nivel_change
        )
        self.combos["nivel"].set("--Seleccione")
        self.combos["nivel"].pack(fill="x", pady=(2, 0))

        # Grado
        fr_grado = ctk.CTkFrame(self.fr_colegio, fg_color="transparent")
        fr_grado.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
        ctk.CTkLabel(fr_grado, text="Grado *", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=TM.text(), anchor="w").pack(fill="x")
        self.combos["grado"] = ctk.CTkComboBox(
            fr_grado, values=[], height=35,
            fg_color=TM.bg_panel(), border_color=TM.get_theme().border,
            button_color=TM.primary(), dropdown_fg_color=TM.bg_panel(), corner_radius=6,
            command=lambda _: self.actualizar_preview()
        )
        self.combos["grado"].set("--Seleccione")
        self.combos["grado"].pack(fill="x", pady=(2, 0))

        self.fr_colegio.grid_remove()  # Oculto por defecto
    
    def crear_campos_padres(self, parent):
        self.crear_campo_grid(parent, "padre_nombres", "Nombres", row=0, col=0, mayusculas=True)
        self.crear_campo_grid(parent, "padre_ape_pat", "Ap. Paterno", row=0, col=1, mayusculas=True)
        self.crear_campo_grid(parent, "padre_ape_mat", "Ap. Materno", row=1, col=0, mayusculas=True)
        self.crear_campo_grid(parent, "celular1", "Celular 1", row=2, col=0, solo_numeros=True, max_char=9)
        self.crear_campo_grid(parent, "celular2", "Celular 2", row=2, col=1, solo_numeros=True, max_char=9)
        self.crear_campo_grid(parent, "descripcion", "Descripción", row=3, col=0, colspan=2)
    
    def crear_campos_pago(self, parent):
        self.crear_campo_grid(parent, "costo", "Costo Total", row=0, col=0, on_change=self.calcular_deuda, allow_decimal=True)
        self.crear_campo_grid(parent, "a_cuenta", "A Cuenta", row=0, col=1, on_change=self.calcular_deuda, allow_decimal=True)
        
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        ctk.CTkLabel(frame, text="Deuda", font=ctk.CTkFont(size=11, weight="bold"), 
                     text_color=TM.text_secondary(), anchor="w").pack(fill="x")
        
        self.entry_deuda = ctk.CTkEntry(frame, height=35, state="disabled", 
                                        fg_color="#2d3748", text_color=TM.warning())
        self.entry_deuda.pack(fill="x", pady=(2, 0))
        
        self.crear_fecha_grid(parent, "fecha_cancelacion", "Fecha Cancelación", row=1, col=1)

    # ==================== LÓGICA DE CONTROLADOR ====================

    def _infer_mime_type(self, filename: str) -> str:
        ext = os.path.splitext(filename.lower())[1]
        if ext in (".png",):
            return "image/png"
        if ext in (".webp",):
            return "image/webp"
        return "image/jpeg"

    def _set_foto_desde_imagen(self, image: Image.Image, suggested_name: str, preferred_mime: Optional[str] = None):
        """Normaliza imagen para guardar en BD y refresca la vista previa."""
        max_bytes = 2 * 1024 * 1024
        target_sizes = [(900, 900), (700, 700), (560, 560)]
        qualities = (90, 82, 72)

        payload = None
        preview_image = None
        for target_size in target_sizes:
            candidate = image.copy().convert("RGB")
            candidate.thumbnail(target_size, Image.Resampling.LANCZOS)

            for quality in qualities:
                buffer = io.BytesIO()
                candidate.save(buffer, format="JPEG", quality=quality, optimize=True)
                data = buffer.getvalue()
                if len(data) <= max_bytes:
                    payload = data
                    preview_image = candidate
                    break

            if payload:
                break

        if not payload or preview_image is None:
            messagebox.showwarning(
                "Imagen muy grande",
                "No se pudo optimizar la foto por debajo de 2MB. Use una imagen más ligera.",
            )
            return

        base_name = os.path.splitext(suggested_name or "foto_alumno")[0]
        self._foto_bytes = payload
        self._foto_filename = f"{base_name}.jpg"
        self._foto_mime_type = "image/jpeg"
        self.preview_card.set_photo_image(preview_image)

    def seleccionar_foto_archivo(self):
        filepath = filedialog.askopenfilename(
            title="Seleccionar foto del alumno",
            filetypes=[
                ("Imagenes", "*.png *.jpg *.jpeg *.webp"),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("WEBP", "*.webp"),
            ],
        )
        if not filepath:
            return

        try:
            with Image.open(filepath) as img:
                loaded = img.copy()
            self._set_foto_desde_imagen(
                image=loaded,
                suggested_name=os.path.basename(filepath),
                preferred_mime=self._infer_mime_type(filepath),
            )
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar la foto seleccionada:\n{e}")

    def capturar_foto_camara(self):
        try:
            cv2 = importlib.import_module("cv2")
        except Exception:
            messagebox.showwarning(
                "Camara no disponible",
                "No se encontro OpenCV. Instale opencv-python para habilitar captura desde camara.",
            )
            return

        messagebox.showinfo(
            "Captura de foto",
            "Se abrira la camara. Presione ESPACIO o ENTER para capturar, y ESC para cancelar.",
        )

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            messagebox.showerror("Camara", "No se pudo acceder a ninguna camara conectada")
            return

        captured_image = None
        try:
            while True:
                ok, frame = cap.read()
                if not ok:
                    break
                cv2.imshow("Captura de foto - Alumno", frame)
                key = cv2.waitKey(1) & 0xFF

                if key in (13, 32):
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    captured_image = Image.fromarray(rgb)
                    break
                if key == 27:
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()

        if captured_image is None:
            return

        self._set_foto_desde_imagen(
            image=captured_image,
            suggested_name=f"camara_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg",
            preferred_mime="image/jpeg",
        )

    def quitar_foto(self, pedir_confirmacion: bool = False):
        if pedir_confirmacion and self._foto_bytes:
            if not messagebox.askyesno("Quitar foto", "Desea eliminar la foto seleccionada?"):
                return

        self._foto_bytes = None
        self._foto_filename = None
        self._foto_mime_type = None
        self.preview_card.clear_photo()

    def on_grupo_change(self, seleccion=None):
        grupo = self.combos["grupo"].get()
        carreras = self.controller.get_carreras_por_grupo(grupo)
        
        self.combos["carrera"].configure(values=carreras)
        self.combos["carrera"].set(carreras[0] if carreras else "--Seleccione")
        self.actualizar_preview()
    
    def on_modalidad_change(self, seleccion=None):
        modalidad = self.combos["modalidad"].get()
        if modalidad in ["ORDINARIO", "COLEGIO"]:
            self.combos["horario"].set("DOBLE HORARIO")
            self.combos["horario"].configure(state="disabled")
        else:
            self.combos["horario"].configure(state="readonly")
            self.combos["horario"].set("MATUTINO")

        # Mostrar u ocultar campos de colegio
        if modalidad == "COLEGIO":
            self.fr_colegio.grid()
        else:
            self.fr_colegio.grid_remove()
            self.combos["nivel"].set("--Seleccione")
            self.combos["grado"].configure(values=[])
            self.combos["grado"].set("--Seleccione")

        self.actualizar_preview()

    def on_nivel_change(self, seleccion=None):
        nivel = self.combos["nivel"].get()
        if nivel == "PRIMARIA":
            grados = ["1°", "2°", "3°", "4°", "5°", "6°"]
        elif nivel == "SECUNDARIA":
            grados = ["1°", "2°", "3°", "4°", "5°"]
        else:
            grados = []
        self.combos["grado"].configure(values=grados)
        self.combos["grado"].set(grados[0] if grados else "--Seleccione")
        self.actualizar_preview()
    
    def calcular_deuda(self, *args):
        try:
            costo = float(self.entries.get("costo", ctk.CTkEntry(self)).get() or 0)
            a_cuenta = float(self.entries.get("a_cuenta", ctk.CTkEntry(self)).get() or 0)
            
            deuda = self.controller.calcular_deuda(costo, a_cuenta)
            
            self.entry_deuda.configure(state="normal")
            self.entry_deuda.delete(0, "end")
            self.entry_deuda.insert(0, f"{deuda:.2f}")
            self.entry_deuda.configure(state="disabled")
            
            self.actualizar_preview()
        except:
            pass
            
    def actualizar_preview(self, *args):
        # Recolectar datos
        nombres = self.entries["nombres"].get()
        ap_pat = self.entries["apellido_paterno"].get()
        nombre_completo = f"{nombres} {ap_pat}".strip()
        
        dni = self.entries["dni"].get()
        grupo = self.combos["grupo"].get()
        carrera = self.combos["carrera"].get()
        modalidad = self.combos["modalidad"].get()
        nivel = self.combos["nivel"].get() if modalidad == "COLEGIO" else None
        grado = self.combos["grado"].get() if modalidad == "COLEGIO" else None
        
        # Actualizar componentes
        self.preview_card.update_data(nombre_completo, dni, carrera, grupo, modalidad, nivel, grado)
        
        try:
            costo = float(self.entries["costo"].get() or 0)
            a_cuenta = float(self.entries["a_cuenta"].get() or 0)
            self.financial_ticket.update_values(costo, a_cuenta)
            self.audit_panel.update_status(dni, nombres, carrera, costo)
        except:
            pass

    def validar_input(self, texto: str, solo_numeros: bool, max_char: int, allow_decimal: bool = False) -> bool:
        if max_char and len(texto) > max_char:
            return False

        if allow_decimal:
            if not texto:
                return True
            if texto.count(".") > 1:
                return False
            if not texto.replace(".", "", 1).isdigit():
                return False
            return True

        if solo_numeros and texto and not texto.isdigit():
            return False
        return True
    
    def forzar_mayusculas(self, entry):
        texto = entry.get()
        pos = entry.index("insert")
        entry.delete(0, "end")
        entry.insert(0, texto.upper())
        entry.icursor(pos)

    def obtener_datos(self) -> Dict:
        """Obtener y formatear datos del formulario"""
        # Fecha nacimiento
        fecha_nac = None
        if "fecha_nacimiento" in self.date_entries:
            try:
                fecha_obj = self.date_entries["fecha_nacimiento"].get_date()
                fecha_nac = fecha_obj.isoformat()
            except: pass

        # Fecha de cancelación esperada para el saldo restante
        fecha_cancelacion = None
        if "fecha_cancelacion" in self.date_entries:
            try:
                fecha_obj = self.date_entries["fecha_cancelacion"].get_date()
                fecha_cancelacion = fecha_obj.isoformat()
            except:
                pass

        padre_n = self.entries["padre_nombres"].get().strip()
        padre_p = self.entries["padre_ape_pat"].get().strip()
        padre_m = self.entries["padre_ape_mat"].get().strip()
        nombre_padre = f"{padre_n} {padre_p} {padre_m}".strip()

        datos = {
            "dni": self.entries["dni"].get().strip(),
            "nombres": self.entries["nombres"].get().strip(),
            "apell_paterno": self.entries["apellido_paterno"].get().strip(),
            "apell_materno": self.entries["apellido_materno"].get().strip(),
            "fecha_nacimiento": fecha_nac,
            "grupo": self.combos["grupo"].get(),
            "carrera": self.combos["carrera"].get(),
            "modalidad": self.combos["modalidad"].get(),
            "horario": self.combos["horario"].get(),
            "nivel": self.combos["nivel"].get() if self.combos["modalidad"].get() == "COLEGIO" else None,
            "grado": self.combos["grado"].get() if self.combos["modalidad"].get() == "COLEGIO" else None,
            "nombre_padre_completo": nombre_padre if nombre_padre else None,
            "celular_padre_1": self.entries["celular1"].get().strip() or None,
            "celular_padre_2": self.entries["celular2"].get().strip() or None,
            "descripcion": self.entries["descripcion"].get().strip() or None,
            "costo_matricula": float(self.entries["costo"].get() or 0),
            "a_cuenta": float(self.entries["a_cuenta"].get() or 0),
            "fecha_cancelacion": fecha_cancelacion,
            "foto_bytes": self._foto_bytes,
            "foto_filename": self._foto_filename,
            "foto_mime_type": self._foto_mime_type,
        }
        
        # Limpiar "--Seleccione"
        for k in ["grupo", "carrera", "modalidad", "horario", "nivel", "grado"]:
            if datos.get(k) == "--Seleccione": datos[k] = None
            
        return datos

    def limpiar_errores(self):
        for entry in self.entries.values():
            entry.configure(border_color=TM.get_theme().border)
        for combo in self.combos.values():
            combo.configure(border_color=TM.get_theme().border)

    def marcar_campo_error(self, key: str):
        if key in self.entries:
            self.entries[key].configure(border_color=TM.danger())
        elif key in self.combos:
            self.combos[key].configure(border_color=TM.danger())

    def guardar_alumno(self):
        if not self._ui_ready:
            return

        datos = self.obtener_datos()
        
        # Delegar validación al controlador
        es_valido, mensaje, campo_error = self.controller.validate_student_data(datos)
        
        if not es_valido:
            messagebox.showerror("Validación", mensaje)
            if campo_error:
                self.marcar_campo_error(campo_error)
            return
            
        self.btn_guardar.configure(state="disabled", text="⏳ Guardando...")
        self.lbl_status.configure(text="")
        
        threading.Thread(target=lambda: self._guardar(datos), daemon=True).start()
        
    def _guardar(self, datos):
        success, result = self.controller.create_student(datos)
        self.after(0, lambda: self._post_guardar(success, result))
        
    def _post_guardar(self, success, result):
        self.btn_guardar.configure(state="normal", text="💾 GUARDAR MATRÍCULA")
        
        if success:
            self.lbl_status.configure(text="✅ Registrado", text_color="#10b981")
            advertencia = result.get("_advertencia") if isinstance(result, dict) else None
            if advertencia:
                messagebox.showwarning(
                    "Registro con advertencias",
                    f"Matrícula registrada, pero se detectaron observaciones:\n\n{advertencia}"
                )
            else:
                messagebox.showinfo("Éxito", "Matrícula registrada correctamente")
            self.limpiar_formulario()
            #self._recargar_ultimos_registros()
        else:
            self.lbl_status.configure(text=f"❌ Error", text_color="#ef4444")
            messagebox.showerror("Error", result.get("error", "Error desconocido"))

    def limpiar_formulario(self):
        if not self._ui_ready:
            return

        self.limpiar_errores()
        
        for entry in self.entries.values():
            entry.delete(0, "end")
        
        for combo in self.combos.values():
            try:
                combo.configure(state="readonly")
                combo.set("--Seleccione")
            except: pass
            
        for date_entry in self.date_entries.values():
            date_entry.set_date(date.today())
            
        if self.entry_deuda:
            self.entry_deuda.configure(state="normal")
            self.entry_deuda.delete(0, "end")
            self.entry_deuda.configure(state="disabled")

        # Ocultar campos de colegio
        self.fr_colegio.grid_remove()
        self.combos["nivel"].set("--Seleccione")
        self.combos["grado"].configure(values=[])
        self.combos["grado"].set("--Seleccione")

        # Resetear componentes
        self.quitar_foto(pedir_confirmacion=False)
        self.preview_card.reset()
        self.audit_panel.reset()
        self.financial_ticket.reset()
        self.lbl_status.configure(text="")

    def _recargar_ultimos_registros(self):
        threading.Thread(target=self._cargar_registros_thread, daemon=True).start()
        
    def _cargar_registros_thread(self):
        success, data = self.controller.get_recent_students()
        if success:
            alumnos = data if isinstance(data, list) else data.get("items", [])
            self.after(0, lambda: self._mostrar_ultimos_registros(alumnos))

    def _mostrar_ultimos_registros(self, alumnos):
        for widget in self.lista_container.winfo_children():
            widget.destroy()
            
        for alumno in alumnos:
            f = ctk.CTkFrame(self.lista_container, fg_color="transparent")
            f.pack(fill="x", pady=2)
            ctk.CTkLabel(f, text=f"👤 {alumno['nombres']} {alumno['apell_paterno']}", 
                         font=ctk.CTkFont(size=11)).pack(side="left")
            ctk.CTkLabel(f, text=f"{alumno['dni']}", 
                         font=ctk.CTkFont(size=11), text_color=TM.text_secondary()).pack(side="right")
    
    def refresh(self):
        if not self._ui_ready:
            self.after(1, self._build_ui_deferred)
            return

        self.limpiar_formulario()
        #self._recargar_ultimos_registros()
