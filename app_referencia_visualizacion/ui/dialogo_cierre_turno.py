# app/ui/dialogo_cierre_turno.py (CREAR NUEVO ARCHIVO)

import customtkinter as ctk
from tkinter import messagebox

class DialogoCierreTurno(ctk.CTkToplevel):
    """
    Diálogo de confirmación para cierre de turno con resumen detallado
    """
    
    def __init__(self, parent, resumen_cierre):
        super().__init__(parent)
        
        self.resumen = resumen_cierre
        self.confirmado = False
        
        # Configuración ventana
        turno = resumen_cierre["turno_cerrado"]
        self.title(f"⚠️ Confirmar Cierre de Turno {turno}")
        self.geometry("550x500")
        self.resizable(False, False)
        
        # Modal y centrado
        self.transient(parent)
        self.grab_set()
        self.focus_force()
        
        # Centrar
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (550 // 2)
        y = (self.winfo_screenheight() // 2) - (500 // 2)
        self.geometry(f"550x500+{x}+{y}")
        
        self.crear_ui()
    
    def crear_ui(self):
        """Crear interfaz del diálogo"""
        
        # Frame principal
        fr_main = ctk.CTkFrame(self, fg_color="#2d2d2d")
        fr_main.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Banner superior
        turno = self.resumen["turno_cerrado"]
        icono = "🌅" if turno == "MAÑANA" else "🌆"
        color_banner = "#f39c12" if turno == "MAÑANA" else "#3498db"
        
        fr_banner = ctk.CTkFrame(fr_main, fg_color=color_banner, height=70)
        fr_banner.pack(fill="x")
        fr_banner.pack_propagate(False)
        
        ctk.CTkLabel(
            fr_banner,
            text=icono,
            font=("Arial", 40),
            text_color="white"
        ).pack(side="left", padx=20)
        
        fr_texto = ctk.CTkFrame(fr_banner, fg_color="transparent")
        fr_texto.pack(side="left", fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(
            fr_texto,
            text=f"CERRAR TURNO {turno}",
            font=("Roboto", 16, "bold"),
            text_color="white",
            anchor="w"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            fr_texto,
            text="Confirme la información antes de continuar",
            font=("Roboto", 10),
            text_color="#2d2d2d",
            anchor="w"
        ).pack(anchor="w")
        
        # Contenido scrollable
        fr_scroll = ctk.CTkScrollableFrame(fr_main, fg_color="transparent")
        fr_scroll.pack(fill="both", expand=True, padx=20, pady=15)
        
        # Resumen estadístico
        fr_stats = ctk.CTkFrame(fr_scroll, fg_color="#1a1a1a", corner_radius=10)
        fr_stats.pack(fill="x", pady=(0, 15))
        
        ctk.CTkLabel(
            fr_stats,
            text="📊 RESUMEN",
            font=("Roboto", 12, "bold"),
            text_color="white"
        ).pack(pady=(15, 10))
        
        # Grid de estadísticas
        stats_data = [
            ("Total alumnos del turno:", self.resumen["total_alumnos_turno"]),
            ("Ya registraron asistencia:", self.resumen["total_presentes"]),
            ("Sin registro (inasistencias):", self.resumen["total_a_marcar"])
        ]
        
        for label, valor in stats_data:
            fr_stat = ctk.CTkFrame(fr_stats, fg_color="transparent")
            fr_stat.pack(fill="x", padx=20, pady=3)
            
            ctk.CTkLabel(
                fr_stat,
                text=label,
                font=("Roboto", 10),
                text_color="gray",
                anchor="w"
            ).pack(side="left")
            
            ctk.CTkLabel(
                fr_stat,
                text=str(valor),
                font=("Roboto", 11, "bold"),
                text_color="white",
                anchor="e"
            ).pack(side="right")
        
        # Desglose por tipo de turno
        desglose = self.resumen.get("desglose", {})
        
        if desglose and any(desglose.values()):
            ctk.CTkLabel(
                fr_stats,
                text="Desglose a marcar:",
                font=("Roboto", 9, "bold"),
                text_color="#3498db"
            ).pack(pady=(10, 5))
            
            for tipo, cantidad in desglose.items():
                if cantidad > 0:
                    fr_det = ctk.CTkFrame(fr_stats, fg_color="transparent")
                    fr_det.pack(fill="x", padx=30, pady=2)
                    
                    icono_tipo = "🌅" if tipo == "MAÑANA" else ("🌆" if tipo == "TARDE" else "🔄")
                    
                    ctk.CTkLabel(
                        fr_det,
                        text=f"{icono_tipo} {tipo}:",
                        font=("Roboto", 9),
                        text_color="gray",
                        anchor="w"
                    ).pack(side="left")
                    
                    ctk.CTkLabel(
                        fr_det,
                        text=f"{cantidad} alumno{'s' if cantidad != 1 else ''}",
                        font=("Roboto", 9),
                        text_color="white",
                        anchor="e"
                    ).pack(side="right")
        
        ctk.CTkLabel(fr_stats, text=" ").pack(pady=5)  # Espaciador
        
        # Lista de alumnos (opcional, mostrar solo si son pocos)
        alumnos = self.resumen.get("alumnos_sin_registro", [])
        
        if len(alumnos) > 0 and len(alumnos) <= 15:
            fr_lista = ctk.CTkFrame(fr_scroll, fg_color="#1a1a1a", corner_radius=10)
            fr_lista.pack(fill="x", pady=(0, 15))
            
            ctk.CTkLabel(
                fr_lista,
                text="📋 ALUMNOS A MARCAR",
                font=("Roboto", 11, "bold"),
                text_color="white"
            ).pack(pady=(15, 10))
            
            for alumno in alumnos[:15]:  # Máximo 15
                fr_alumno = ctk.CTkFrame(fr_lista, fg_color="#252525", corner_radius=5)
                fr_alumno.pack(fill="x", padx=15, pady=3)
                
                turno_icono = "🌅" if alumno["horario"] == "MATUTINO" else (
                    "🌆" if alumno["horario"] == "VESPERTINO" else "🔄"
                )
                
                ctk.CTkLabel(
                    fr_alumno,
                    text=f"{turno_icono} {alumno['codigo']} - {alumno['nombre']}",
                    font=("Roboto", 9),
                    text_color="white",
                    anchor="w"
                ).pack(side="left", padx=10, pady=8)
            
            if len(alumnos) > 15:
                ctk.CTkLabel(
                    fr_lista,
                    text=f"... y {len(alumnos) - 15} más",
                    font=("Roboto", 9, "italic"),
                    text_color="gray"
                ).pack(pady=(5, 10))
            
            ctk.CTkLabel(fr_lista, text=" ").pack(pady=5)
        
        # Advertencia
        fr_warning = ctk.CTkFrame(fr_scroll, fg_color="#c0392b", corner_radius=8)
        fr_warning.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            fr_warning,
            text="⚠️ Esta acción no se puede deshacer",
            font=("Roboto", 10, "bold"),
            text_color="white"
        ).pack(pady=12)
        
        # Botones de acción (fijos abajo)
        fr_botones_wrapper = ctk.CTkFrame(fr_main, fg_color="#1a1a1a", height=70)
        fr_botones_wrapper.pack(fill="x", side="bottom", padx=20, pady=(0, 20))
        fr_botones_wrapper.pack_propagate(False)
        
        fr_botones = ctk.CTkFrame(fr_botones_wrapper, fg_color="transparent")
        fr_botones.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkButton(
            fr_botones,
            text="❌ CANCELAR",
            height=45,
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            font=("Roboto", 12, "bold"),
            command=self.cancelar
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(
            fr_botones,
            text=f"✅ CONFIRMAR CIERRE",
            height=45,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            font=("Roboto", 12, "bold"),
            command=self.confirmar
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))
    
    def confirmar(self):
        """Usuario confirma el cierre"""
        self.confirmado = True
        self.destroy()
    
    def cancelar(self):
        """Usuario cancela"""
        self.confirmado = False
        self.destroy()
