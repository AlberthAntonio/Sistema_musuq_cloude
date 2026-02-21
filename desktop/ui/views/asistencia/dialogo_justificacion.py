import customtkinter as ctk
from styles import tabla_style as st

class DialogoJustificacion(ctk.CTkToplevel):
    def __init__(self, parent, datos_asistencia, on_confirm=None):
        super().__init__(parent)
        self.on_confirm = on_confirm
        self._resultado = None

        # Configuración de ventana
        self.title("Justificar Inasistencia")
        self.geometry("450x550")
        self.resizable(False, False)
        
        # Centrar en pantalla (aprox)
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (450 // 2)
        y = (self.winfo_screenheight() // 2) - (550 // 2)
        self.geometry(f"+{x}+{y}")
        
        # Modal effect
        self.transient(parent)
        self.grab_set()
        
        # UI Setup
        self.configure(fg_color="#1a1a1a")
        self._crear_widgets(datos_asistencia)
        
    def _crear_widgets(self, datos):
        id_asist, fecha, estado = datos
        
        # 1. Cabecera Visual
        self.fr_header = ctk.CTkFrame(self, fg_color="#2c3e50", corner_radius=0, height=80)
        self.fr_header.pack(fill="x")
        self.fr_header.pack_propagate(False)
        
        ctk.CTkLabel(
            self.fr_header, 
            text="PROCESO DE JUSTIFICACIÓN",
            font=("Roboto", 18, "bold"), 
            text_color="white"
        ).pack(pady=(20, 5))
        
        ctk.CTkLabel(
            self.fr_header, 
            text=f"ID Registro: {id_asist}",
            font=("Roboto", 11), 
            text_color="#bdc3c7"
        ).pack()
        
        # 2. Resumen del incidente
        self.fr_info = ctk.CTkFrame(self, fg_color="#2b2b2b", corner_radius=10)
        self.fr_info.pack(fill="x", padx=25, pady=20)
        
        bg_badge = st.Colors.FALTA if "FALTA" in estado or "INASISTENCIA" in estado else st.Colors.TARDANZA
        
        # Fila Fecha
        f1 = ctk.CTkFrame(self.fr_info, fg_color="transparent")
        f1.pack(fill="x", padx=15, pady=(15,5))
        ctk.CTkLabel(f1, text="FECHA DEL SUCESO:", font=("Roboto", 11, "bold"), text_color="gray").pack(side="left")
        ctk.CTkLabel(f1, text=fecha, font=("Roboto", 12, "bold"), text_color="white").pack(side="right")
        
        # Fila Estado
        f2 = ctk.CTkFrame(self.fr_info, fg_color="transparent")
        f2.pack(fill="x", padx=15, pady=(5,15))
        ctk.CTkLabel(f2, text="ESTADO ACTUAL:", font=("Roboto", 11, "bold"), text_color="gray").pack(side="left")
        
        lbl_st = ctk.CTkLabel(f2, text=estado, font=("Roboto", 12, "bold"), text_color="white", fg_color=bg_badge, corner_radius=5, padx=10)
        lbl_st.pack(side="right")
        
        # 3. Formulario
        ctk.CTkLabel(self, text="Motivo Principal", font=("Roboto", 13, "bold"), text_color="silver").pack(anchor="w", padx=25, pady=(10,5))
        
        self.combo_motivo = ctk.CTkComboBox(
            self,
            values=["Salud / Médico", "Calamidad Doméstica", "Transporte / Huelga", "Error de Sistema", "Comisión de Servicio", "Otro"],
            width=400,
            height=35,
            dropdown_hover_color="#3498db",
            font=("Roboto", 12)
        )
        self.combo_motivo.pack(fill="x", padx=25, pady=(0, 15))
        self.combo_motivo.set("Salud / Médico")
        
        ctk.CTkLabel(self, text="Detalles / Observación", font=("Roboto", 13, "bold"), text_color="silver").pack(anchor="w", padx=25, pady=(0,5))
        
        self.txt_detalle = ctk.CTkTextbox(
            self, 
            height=80, 
            corner_radius=10, 
            fg_color="#333333", 
            border_color="gray", 
            border_width=1
        )
        self.txt_detalle.pack(fill="x", padx=25, pady=(0, 20))
        
        # 4. Botones Acción
        fr_btns = ctk.CTkFrame(self, fg_color="transparent")
        fr_btns.pack(fill="x", padx=25, pady=10, side="bottom")
        
        self.btn_cancelar = ctk.CTkButton(
            fr_btns, 
            text="Cancelar", 
            fg_color="transparent", 
            border_width=1, 
            border_color="gray", 
            hover_color="#404040",
            width=120, 
            height=40,
            command=self.destroy
        )
        self.btn_cancelar.pack(side="left")
                      
        self.btn_confirmar = ctk.CTkButton(
            fr_btns, 
            text="CONFIRMAR JUSTIFICACIÓN", 
            fg_color="#3498db", 
            hover_color="#2980b9",
            height=40,
            font=("Roboto", 12, "bold"),
            command=self._confirmar_accion
        )
        self.btn_confirmar.pack(side="right", fill="x", expand=True, padx=(10,0))

    def _confirmar_accion(self):
        motivo = self.combo_motivo.get()
        detalle = self.txt_detalle.get("1.0", "end").strip()
        
        if not detalle:
            self.txt_detalle.configure(border_color="#e74c3c")
            return
            
        full_motivo = f"[{motivo}] {detalle}"
        
        if self.on_confirm:
            # Deshabilitar para evitar doble click
            self.btn_confirmar.configure(state="disabled", text="Procesando...")
            self.on_confirm(full_motivo)
            
        self.destroy()
