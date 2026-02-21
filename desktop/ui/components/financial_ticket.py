import customtkinter as ctk
from core.theme_manager import ThemeManager as TM

class StatusChip(ctk.CTkFrame):
    """Chip de Estado Dinámico para estado financiero"""
    def __init__(self, parent):
        super().__init__(parent, corner_radius=100, height=24, 
                        border_width=1, border_color=TM.get_theme().border)
        self.label = ctk.CTkLabel(
            self, text="PENDIENTE", 
            font=ctk.CTkFont(family="Roboto", size=9, weight="bold"), 
            text_color="white"
        )
        self.label.pack(padx=10, pady=2)
        
    def set_status(self, status):
        colores = {
            "PAGADO": TM.success(),
            "PARCIAL": TM.warning(),
            "DEUDA": TM.danger(),
            "VACÍO": TM.bg_panel()
        }
        self.configure(fg_color=colores.get(status, TM.bg_panel()))
        self.label.configure(text=status)

class FinancialTicket(ctk.CTkFrame):
    """Ticket financiero con diseño tipo recibo"""
    def __init__(self, parent):
        super().__init__(parent, fg_color=TM.bg_panel(), corner_radius=12, 
                        border_width=1, border_color=TM.get_theme().border)
        
        self.ticket_lbls = {}
        self._create_ui()
        
    def _create_ui(self):
        # Header con StatusChip
        header = ctk.CTkFrame(self, fg_color=TM.bg_card(), height=40, corner_radius=0)
        header.pack(fill="x", padx=1, pady=1)
        
        ctk.CTkLabel(
            header, text="LIQUIDACIÓN", 
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"), 
            text_color=TM.text()
        ).place(x=10, y=10)
        
        self.chip_status = StatusChip(header)
        self.chip_status.place(relx=0.95, rely=0.5, anchor="e")
        self.chip_status.set_status("VACÍO")
        
        # Body
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="x", padx=15, pady=10)
        
        self._crear_ticket_row(body, "Costo Matrícula", "0.00", "t_costo")
        self._crear_ticket_row(body, "Pago a Cuenta", "0.00", "t_pago")
        
        ctk.CTkLabel(
            body, text="- "*20, 
            font=ctk.CTkFont(family="Roboto", size=10), 
            text_color=TM.text_secondary()
        ).pack(fill="x", pady=5)
        
        total_frame = ctk.CTkFrame(body, fg_color="transparent")
        total_frame.pack(fill="x")
        
        ctk.CTkLabel(
            total_frame, text="PENDIENTE", 
            font=ctk.CTkFont(family="Roboto", size=10, weight="bold"), 
            text_color=TM.text_secondary()
        ).pack(side="left")
        
        self.lbl_total_big = ctk.CTkLabel(
            total_frame, text="S/. 0.00", 
            font=ctk.CTkFont(family="Roboto", size=16, weight="bold"), 
            text_color=TM.text()
        )
        self.lbl_total_big.pack(side="right")
        
    def _crear_ticket_row(self, parent, label, val, key):
        """Helper para crear fila del ticket"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x")
        
        ctk.CTkLabel(
            frame, text=label, 
            font=ctk.CTkFont(family="Roboto", size=10), 
            text_color=TM.text_secondary()
        ).pack(side="left")
        
        lbl = ctk.CTkLabel(
            frame, text=val, 
            font=ctk.CTkFont(family="Roboto", size=10, weight="bold"), 
            text_color=TM.text()
        )
        lbl.pack(side="right")
        self.ticket_lbls[key] = lbl

    def update_values(self, costo: float, a_cuenta: float):
        """Actualizar ticket financiero con lógica del chip de estado"""
        saldo = max(0, costo - a_cuenta)
        
        # Actualizar valores
        self.ticket_lbls["t_costo"].configure(text=f"{costo:.2f}")
        self.ticket_lbls["t_pago"].configure(text=f"{a_cuenta:.2f}")
        self.lbl_total_big.configure(text=f"S/. {saldo:.2f}")
        
        # Lógica del chip de estado
        if costo == 0:
            self.chip_status.set_status("VACÍO")
            self.lbl_total_big.configure(text_color=TM.text_secondary())
        elif saldo <= 0:
            self.chip_status.set_status("PAGADO")
            self.lbl_total_big.configure(text_color=TM.success())
        elif a_cuenta > 0:
            self.chip_status.set_status("PARCIAL")
            self.lbl_total_big.configure(text_color=TM.warning())
        else:
            self.chip_status.set_status("DEUDA")
            self.lbl_total_big.configure(text_color=TM.danger())
            
    def reset(self):
        self.chip_status.set_status("VACÍO")
        self.ticket_lbls["t_costo"].configure(text="0.00")
        self.ticket_lbls["t_pago"].configure(text="0.00")
        self.lbl_total_big.configure(text="S/. 0.00", text_color=TM.text())
