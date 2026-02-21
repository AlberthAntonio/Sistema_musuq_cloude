"""
CarnetView - Emisión de carnets - VERSIÓN VISUAL PREMIUM (Musuq Cloud)
Refactor visual usando ThemeManager (TM), manteniendo la lógica original.
"""

import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog

from controllers.carnet_controller import CarnetController
from PIL import Image, ImageTk
import barcode
from barcode.writer import ImageWriter
import qrcode
import io
import threading
import time

from core.theme_manager import TM


class CarnetView(ctk.CTkFrame):
    def __init__(self, master, auth_client=None, **kwargs):
        super().__init__(master, fg_color="transparent")
        self.auth_client = auth_client

        self.controller = CarnetController()

        # --- ESTADO Y VARIABLES ---
        self.alumno_seleccionado = None
        self.todos_alumnos = []     # Copia para el buscador
        self.impresos_ids = set()   # Cache de IDs impresos en esta sesión
        self.color_acento = TM.primary()  # Color header carnet
        self.lado_actual = "frente"  # 'frente' o 'reverso'

        # Estilos Treeview (Tabla Oscura integrada al tema)
        self._configurar_estilos_treeview()

        # Layout principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)  # Panel principal
        self.grid_rowconfigure(1, weight=0)  # Barra progreso

        # Panel izquierdo: controles
        self._crear_panel_izquierdo()

        # Panel derecho: vista previa de carnet
        self._crear_panel_derecho()

        # Barra de progreso inferior
        self._crear_barra_progreso()

    # ============================================================
    # ESTILOS
    # ============================================================

    def _configurar_estilos_treeview(self):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=TM.bg_panel(),
            foreground=TM.text(),
            fieldbackground=TM.bg_panel(),
            borderwidth=0,
            rowheight=30,
            font=("Roboto", 10)
        )
        style.configure(
            "Treeview.Heading",
            background=TM.primary(),
            foreground="white",
            relief="flat",
            font=("Roboto", 10, "bold")
        )
        style.map("Treeview", background=[("selected", TM.hover())])

    # ============================================================
    # PANEL IZQUIERDO - CONTROLES
    # ============================================================

    def _crear_panel_izquierdo(self):
        pnl_izq = ctk.CTkFrame(
            self,
            fg_color=TM.bg_panel(),
            corner_radius=15,
            border_width=1,
            border_color=TM.bg_card()
        )
        pnl_izq.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Header
        ctk.CTkLabel(
            pnl_izq,
            text="EMISIÓN DE CARNETS",
            font=("Roboto", 16, "bold"),
            text_color=TM.text()
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            pnl_izq,
            text="Buscar alumnos y generar carnet en PDF",
            font=("Roboto", 10),
            text_color=TM.text_secondary()
        ).pack(pady=(0, 10))

        # --- 1. Buscador ---
        fr_search = ctk.CTkFrame(pnl_izq, fg_color="transparent")
        fr_search.pack(fill="x", padx=15, pady=5)

        self.entry_search = ctk.CTkEntry(
            fr_search,
            placeholder_text="🔍 Buscar por nombre o DNI...",
            fg_color=TM.bg_main(),
            border_color=TM.primary(),
            text_color=TM.text(),
            height=34
        )
        self.entry_search.pack(fill="x")
        self.entry_search.bind("<KeyRelease>", self.filtrar_lista)  # tiempo real

        # --- Filtro Grupo ---
        ctk.CTkLabel(
            pnl_izq,
            text="Grupo:",
            anchor="w",
            text_color=TM.text_secondary(),
            font=("Roboto", 11)
        ).pack(fill="x", padx=15, pady=(10, 0))

        self.cb_grupo = ctk.CTkComboBox(
            pnl_izq,
            values=self.controller.obtener_grupos(),
            command=self.cargar_lista,
            fg_color=TM.bg_card(),
            dropdown_fg_color=TM.bg_panel(),
            text_color=TM.text(),
            button_color=TM.primary(),
            button_hover_color=TM.hover(),
            height=34
        )
        self.cb_grupo.pack(fill="x", padx=15, pady=5)

        # --- Tabla Alumnos ---
        fr_tree = ctk.CTkFrame(pnl_izq, fg_color="transparent")
        fr_tree.pack(fill="both", expand=True, padx=15, pady=5)

        self.tree = ttk.Treeview(fr_tree, columns=("id", "nombre", "estado"), show="headings")
        self.tree.heading("id", text="ID")
        self.tree.column("id", width=0, stretch=False)
        self.tree.heading("nombre", text="Alumno")
        self.tree.column("nombre", width=180)
        self.tree.heading("estado", text="Estado")
        self.tree.column("estado", width=60, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<<TreeviewSelect>>", self.on_select_alumno)

        # Botones selección
        fr_btn_sel = ctk.CTkFrame(pnl_izq, fg_color="transparent")
        fr_btn_sel.pack(fill="x", pady=5, padx=10)

        ctk.CTkButton(
            fr_btn_sel,
            text="☑ Seleccionar Todos",
            height=28,
            fg_color="#34495e",
            hover_color="#2c3e50",
            font=("Roboto", 11, "bold"),
            corner_radius=8,
            command=self.seleccionar_todo
        ).pack(fill="x")

        # Separador
        ctk.CTkFrame(pnl_izq, height=2, fg_color=TM.bg_card()).pack(fill="x", pady=10, padx=15)

        # --- Personalización Visual ---
        ctk.CTkLabel(
            pnl_izq,
            text="TEMA DEL CARNET:",
            font=("Roboto", 10, "bold"),
            text_color=TM.text_secondary(),
            anchor="w"
        ).pack(fill="x", padx=15)

        fr_colores = ctk.CTkFrame(pnl_izq, fg_color="transparent")
        fr_colores.pack(fill="x", padx=15, pady=5)

        colores = [TM.primary(), TM.danger(), TM.success(), TM.info(), "#d35400"]
        for col in colores:
            btn = ctk.CTkButton(
                fr_colores,
                text="",
                width=24,
                height=24,
                corner_radius=12,
                fg_color=col,
                hover_color=col,
                command=lambda c=col: self.cambiar_acento(c)
            )
            btn.pack(side="left", padx=2)

        # Tipo de código
        self.var_tipo_codigo = ctk.StringVar(value="QR")
        self.seg_codigo = ctk.CTkSegmentedButton(
            pnl_izq,
            values=["Barras", "QR"],
            variable=self.var_tipo_codigo,
            command=self.cambiar_tipo_codigo,
            fg_color=TM.bg_card(),
            selected_color=TM.primary(),
            selected_hover_color=TM.hover(),
            unselected_color=TM.bg_panel(),
            unselected_hover_color=TM.bg_card(),
        )
        self.seg_codigo.pack(fill="x", padx=15, pady=10)

        # Fondo carnet
        self.btn_fondo = ctk.CTkButton(
            pnl_izq,
            text="📂 Cargar / Arrastrar Fondo",
            fg_color=TM.primary(),
            hover_color=TM.hover(),
            font=("Roboto", 11, "bold"),
            corner_radius=8,
            command=self.cargar_fondo
        )
        self.btn_fondo.pack(fill="x", padx=15, pady=5)

        # Separador
        ctk.CTkFrame(pnl_izq, height=2, fg_color=TM.bg_card()).pack(fill="x", pady=10, padx=15)

        # Botón principal
        self.btn_imprimir = ctk.CTkButton(
            pnl_izq,
            text="🖨️ GENERAR PDF",
            height=40,
            font=("Roboto", 14, "bold"),
            fg_color=TM.danger(),
            hover_color="#c0392b",
            corner_radius=8,
            command=self.iniciar_impresion_thread
        )
        self.btn_imprimir.pack(fill="x", padx=15, pady=10)

    # ============================================================
    # PANEL DERECHO - VISTA PREVIA
    # ============================================================

    def _crear_panel_derecho(self):
        pnl_der = ctk.CTkFrame(
            self,
            fg_color=TM.bg_panel(),
            corner_radius=15,
            border_width=1,
            border_color=TM.bg_card()
        )
        pnl_der.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Header
        fr_head_der = ctk.CTkFrame(pnl_der, fg_color="transparent")
        fr_head_der.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(
            fr_head_der,
            text="VISTA PREVIA",
            text_color=TM.text_secondary(),
            font=("Roboto", 11)
        ).pack(side="left")

        self.switch_lado = ctk.CTkSwitch(
            fr_head_der,
            text="Ver Reverso",
            command=self.toggle_lado,
            progress_color=TM.success(),
            text_color=TM.text_secondary()
        )
        self.switch_lado.pack(side="right")

        # Área de tarjeta
        self.container_tarjeta = ctk.CTkFrame(pnl_der, fg_color="transparent")
        self.container_tarjeta.pack(expand=True)

        # Sombra
        self.shadow_frame = ctk.CTkFrame(
            self.container_tarjeta,
            width=425,
            height=270,
            fg_color="#000000",
            corner_radius=12,
            bg_color="transparent"
        )
        self.shadow_frame.place(x=10, y=14)

        # Marco del carnet
        self.card_frame = ctk.CTkFrame(
            self.container_tarjeta,
            width=425,
            height=270,
            fg_color="white",
            corner_radius=10
        )
        self.card_frame.place(x=0, y=0)

        # Fijar tamaño del contenedor
        self.container_tarjeta.configure(width=440, height=290)

        # Construir elementos internos
        self.construir_carnet_ui()

        ctk.CTkLabel(
            pnl_der,
            text="💡 Doble clic sobre el texto del carnet para editarlo antes de imprimir",
            font=("Roboto", 9),
            text_color=TM.text_muted(),
            justify="center"
        ).pack(pady=10)

    # ============================================================
    # BARRA DE PROGRESO INFERIOR
    # ============================================================

    def _crear_barra_progreso(self):
        self.progress_bar = ctk.CTkProgressBar(
            self,
            mode="determinate",
            height=10,
            corner_radius=0,
            progress_color=TM.success()
        )
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.progress_bar.grid_remove()

    # ============================================================
    # UI INTERNA DEL CARNET
    # ============================================================

    def construir_carnet_ui(self):
        # Limpiar frame
        for widget in self.card_frame.winfo_children():
            widget.destroy()

        if self.lado_actual == "frente":
            # HEADER
            self.header_preview = ctk.CTkFrame(
                self.card_frame,
                height=50,
                fg_color=self.color_acento,
                corner_radius=0
            )
            self.header_preview.place(x=0, y=0, relwidth=1)

            ctk.CTkLabel(
                self.header_preview,
                text="INSTITUCIÓN EDUCATIVA MUSUQ",
                font=("Arial", 14, "bold"),
                text_color="white"
            ).place(relx=0.5, rely=0.5, anchor="center")

            # FOTO
            self.foto_placeholder = ctk.CTkFrame(
                self.card_frame,
                width=100,
                height=120,
                fg_color="#ecf0f1",
                border_width=1,
                border_color="#bdc3c7"
            )
            self.foto_placeholder.place(x=20, y=70)

            ctk.CTkLabel(
                self.foto_placeholder,
                text="FOTO",
                text_color="gray"
            ).place(relx=0.5, rely=0.5, anchor="center")

            # DATOS (Editables)
            self.lbl_ape = ctk.CTkLabel(
                self.card_frame,
                text="APELLIDOS",
                font=("Arial", 18, "bold"),
                text_color="black",
                anchor="w"
            )
            self.lbl_ape.place(x=140, y=70)
            self.hacer_editable(self.lbl_ape)

            self.lbl_nom = ctk.CTkLabel(
                self.card_frame,
                text="Nombres",
                font=("Arial", 14),
                text_color="#333",
                anchor="w"
            )
            self.lbl_nom.place(x=140, y=100)
            self.hacer_editable(self.lbl_nom)

            self.lbl_dni = ctk.CTkLabel(
                self.card_frame,
                text="DNI: ----",
                font=("Arial", 12),
                text_color="#555",
                anchor="w"
            )
            self.lbl_dni.place(x=140, y=130)

            # CÓDIGO
            self.lbl_codigo = ctk.CTkLabel(self.card_frame, text="")
            self.lbl_codigo.place(relx=0.5, y=220, anchor="center")

        else:  # REVERSO
            ctk.CTkLabel(
                self.card_frame,
                text="NORMAS DE USO",
                font=("Arial", 12, "bold"),
                text_color="#333"
            ).pack(pady=20)

            ctk.CTkLabel(
                self.card_frame,
                text=(
                    "1. Este carnet es personal e intransferible."
                    "2. En caso de pérdida, reportar a dirección."
                ),
                font=("Arial", 10),
                text_color="#555",
                justify="left"
            ).pack(padx=20)

            fr_firma = ctk.CTkFrame(
                self.card_frame,
                width=200,
                height=2,
                fg_color="black"
            )
            fr_firma.place(relx=0.5, rely=0.8, anchor="center")

            ctk.CTkLabel(
                self.card_frame,
                text="Firma Dirección",
                font=("Arial", 10),
                text_color="black"
            ).place(relx=0.5, rely=0.85, anchor="center")

            footer = ctk.CTkFrame(
                self.card_frame,
                height=20,
                fg_color=self.color_acento,
                corner_radius=0
            )
            footer.place(x=0, y=250, relwidth=1)

    # ============================================================
    # EDICIÓN IN-PLACE DE LABELS
    # ============================================================

    def hacer_editable(self, label_widget):
        """Permite editar el texto de un Label al hacer doble clic"""

        def iniciar_edicion(event):
            texto_actual = label_widget.cget("text")

            entry = ctk.CTkEntry(
                self.card_frame,
                width=label_widget.winfo_width() + 20,
                height=label_widget.winfo_height(),
                fg_color="white",
                text_color="black"
            )
            entry.insert(0, texto_actual)
            entry.place(x=label_widget.winfo_x(), y=label_widget.winfo_y())
            entry.focus_set()

            def guardar_cambios(event=None):
                nuevo_texto = entry.get()
                label_widget.configure(text=nuevo_texto)
                entry.destroy()

            entry.bind("<Return>", guardar_cambios)
            entry.bind("<FocusOut>", guardar_cambios)

        label_widget.bind("<Double-Button-1>", iniciar_edicion)
        label_widget.bind("<Enter>", lambda e: label_widget.configure(cursor="hand2"))
        label_widget.bind("<Leave>", lambda e: label_widget.configure(cursor=""))

    # ============================================================
    # LÓGICA DE DATOS (MISMA QUE ORIGINAL)
    # ============================================================

    def cargar_lista(self, grupo):
        self.todos_alumnos = self.controller.buscar_alumnos(grupo)
        self.actualizar_treeview(self.todos_alumnos)

    def actualizar_treeview(self, lista_alumnos):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for alu in lista_alumnos:
            estado = "✔" if alu.id in self.impresos_ids else ""
            self.tree.insert(
                "",
                "end",
                values=(
                    alu.id,
                    f"{alu.apell_paterno} {alu.apell_materno}, {alu.nombres}",
                    estado,
                ),
            )

    def filtrar_lista(self, event):
        query = self.entry_search.get().lower()
        if not query:
            self.actualizar_treeview(self.todos_alumnos)
            return

        filtrados = [
            alu
            for alu in self.todos_alumnos
            if query in alu.nombres.lower()
            or query in alu.apell_paterno.lower()
            or query in alu.dni
        ]
        self.actualizar_treeview(filtrados)

    def on_select_alumno(self, event):
        sel = self.tree.selection()
        if not sel:
            return

        id_sel = self.tree.item(sel[0])["values"][0]
        self.alumno_seleccionado = next(
            (a for a in self.todos_alumnos if a.id == id_sel),
            None,
        )

        if self.alumno_seleccionado and self.lado_actual == "frente":
            self.actualizar_preview_datos()

    def actualizar_preview_datos(self):
        alumno = self.alumno_seleccionado
        if not alumno:
            return

        if self.lado_actual == "frente":
            self.lbl_ape.configure(
                text=f"{alumno.apell_paterno} {alumno.apell_materno}"
            )
            self.lbl_nom.configure(text=alumno.nombres)
            self.lbl_dni.configure(
                text=f"DNI: {alumno.dni} | Cód: {alumno.codigo_matricula}"
            )
            self.generar_codigo_visual(alumno.codigo_matricula)

    def generar_codigo_visual(self, codigo):
        tipo = self.var_tipo_codigo.get()
        try:
            if tipo == "Barras":
                code128 = barcode.get_barcode_class("code128")
                my_code = code128(codigo, writer=ImageWriter())
                buffer = io.BytesIO()
                my_code.write(
                    buffer,
                    options={
                        "write_text": False,
                        "module_height": 8.0,
                        "quiet_zone": 1.0,
                    },
                )
                img_size = (250, 50)
                y_pos = 225
            else:  # QR
                qr = qrcode.QRCode(box_size=10, border=1)
                qr.add_data(codigo)
                qr.make(fit=True)
                pil_img = qr.make_image(fill_color="black", back_color="white")
                buffer = io.BytesIO()
                pil_img.save(buffer, format="PNG")
                img_size = (80, 80)
                y_pos = 215

            buffer.seek(0)
            img = Image.open(buffer)
            img = img.resize(img_size, Image.Resampling.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, size=img_size)
            self.lbl_codigo.configure(image=ctk_img, text="")
            self.lbl_codigo.image = ctk_img
            self.lbl_codigo.place(relx=0.5, y=y_pos, anchor="center")
        except Exception:
            self.lbl_codigo.configure(text="(Error Código)", image=None)

    def cambiar_acento(self, nuevo_color):
        self.color_acento = nuevo_color
        if self.lado_actual == "frente":
            self.header_preview.configure(fg_color=nuevo_color)
        else:
            self.construir_carnet_ui()

    def toggle_lado(self):
        self.lado_actual = "reverso" if self.switch_lado.get() == 1 else "frente"
        self.construir_carnet_ui()
        if self.lado_actual == "frente" and self.alumno_seleccionado:
            self.actualizar_preview_datos()

    def cambiar_tipo_codigo(self, val):
        if self.alumno_seleccionado and self.lado_actual == "frente":
            self.actualizar_preview_datos()

    # ============================================================
    # IMPRESIÓN CON THREAD Y PROGRESO
    # ============================================================

    def iniciar_impresion_thread(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Seleccione alumnos.")
            return

        ids = [self.tree.item(i)["values"][0] for i in sel]

        self.btn_imprimir.configure(state="disabled", text="Generando...")
        self.progress_bar.grid()
        self.progress_bar.set(0)

        threading.Thread(
            target=self.proceso_impresion,
            args=(ids,),
            daemon=True,
        ).start()

    def proceso_impresion(self, ids):
        total = len(ids)

        for i, _ in enumerate(ids):
            time.sleep(0.1)  # Simula tiempo por carnet
            progreso = (i + 1) / total
            self.progress_bar.set(progreso)

        exito, msg = self.controller.generar_carnets_pdf(ids)
        self.after(0, lambda: self.finalizar_impresion(exito, msg, ids))

    def finalizar_impresion(self, exito, msg, ids_procesados):
        self.btn_imprimir.configure(state="normal", text="🖨️ GENERAR PDF")
        self.progress_bar.grid_remove()

        if exito:
            for uid in ids_procesados:
                self.impresos_ids.add(uid)
            self.filtrar_lista(None)
            messagebox.showinfo("Éxito", msg)
        else:
            messagebox.showerror("Error", msg)

    def cargar_fondo(self):
        ruta = filedialog.askopenfilename(
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg")]
        )
        if ruta:
            exito, msg = self.controller.cargar_plantilla_fondo(ruta)
            if exito:
                messagebox.showinfo("Éxito", msg)

    def seleccionar_todo(self):
        self.tree.selection_set(self.tree.get_children())
