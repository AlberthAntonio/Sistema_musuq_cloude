import customtkinter as ctk
from core.theme_manager import ThemeManager as TM

class AuditPanel(ctk.CTkFrame):
    """Panel de auditoría con barra de progreso y checklist"""
    def __init__(self, parent):
        super().__init__(parent, fg_color=TM.bg_card(), corner_radius=12, 
                        border_width=1, border_color=TM.get_theme().border)
        
        self.checks_audit = {}
        self._create_ui()
        
    def _create_ui(self):
        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(padx=15, pady=15, fill="x")
        
        # Header
        header = ctk.CTkFrame(content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            header, 
            text="CALIDAD DE REGISTRO", 
            font=ctk.CTkFont(family="Roboto", size=10, weight="bold"), 
            text_color=TM.text_secondary()
        ).pack(side="left")
        
        self.lbl_audit_score = ctk.CTkLabel(
            header, text="0%", 
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"), 
            text_color=TM.text_secondary()
        )
        self.lbl_audit_score.pack(side="right")
        
        # Progress Bar
        self.progress_audit = ctk.CTkProgressBar(
            content, height=6, corner_radius=3, 
            progress_color=TM.primary(), 
            fg_color=TM.bg_panel()
        )
        self.progress_audit.pack(fill="x", pady=(0, 10))
        self.progress_audit.set(0)
        
        # Checklist
        self._crear_check_item(content, "Datos de Identidad", "chk_id")
        self._crear_check_item(content, "Asignación Académica", "chk_acad")
        self._crear_check_item(content, "Definición de Costos", "chk_fin")
    
    def _crear_check_item(self, parent, texto, key):
        """Helper para crear item de checklist"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=2)
        
        icon = ctk.CTkLabel(
            frame, text="⭕", 
            font=ctk.CTkFont(size=10), 
            text_color=TM.text_secondary(), 
            width=20
        )
        icon.pack(side="left")
        
        lbl = ctk.CTkLabel(
            frame, text=texto, 
            font=ctk.CTkFont(family="Roboto", size=11), 
            text_color=TM.text_secondary()
        )
        lbl.pack(side="left")
        
        self.checks_audit[key] = {"icon": icon, "label": lbl}

    def update_status(self, dni: str, nombres: str, carrera: str, costo: float):
        """Actualizar panel de auditoría según datos"""
        checks_ok = 0
        
        # Check 1: Datos de Identidad
        if dni and len(dni) >= 8 and nombres and len(nombres) > 2:
            self._set_check_status("chk_id", True)
            checks_ok += 1
        else:
            self._set_check_status("chk_id", False)
        
        # Check 2: Asignación Académica
        if carrera and carrera != "--Seleccione":
            self._set_check_status("chk_acad", True)
            checks_ok += 1
        else:
            self._set_check_status("chk_acad", False)
        
        # Check 3: Definición de Costos
        try:
            if costo > 0:
                self._set_check_status("chk_fin", True)
                checks_ok += 1
            else:
                self._set_check_status("chk_fin", False)
        except:
            self._set_check_status("chk_fin", False)
        
        # Actualizar progreso
        progreso = checks_ok / 3
        self.progress_audit.set(progreso)
        self.lbl_audit_score.configure(text=f"{int(progreso*100)}%")
        
        # Cambiar color del score según progreso
        if progreso == 1.0:
            self.lbl_audit_score.configure(text_color=TM.success())
        else:
            self.lbl_audit_score.configure(text_color=TM.text_secondary())
            
    def _set_check_status(self, key, status):
        if key in self.checks_audit:
            icon = self.checks_audit[key]["icon"]
            if status:
                icon.configure(text="✅", text_color=TM.success())
            else:
                icon.configure(text="⭕", text_color=TM.text_secondary())
                
    def reset(self):
        self.progress_audit.set(0)
        self.lbl_audit_score.configure(text="0%", text_color=TM.text_secondary())
        for key in self.checks_audit:
            self.checks_audit[key]["icon"].configure(text="⭕", text_color=TM.text_secondary())
