# app/ui/dialogo_alerta_turno.py (REEMPLAZAR COMPLETO)

import customtkinter as ctk
from tkinter import messagebox

class DialogoAlertaTurno(ctk.CTkToplevel):
    """
    Ventana modal que bloquea el sistema hasta que el personal decida
    """
    
    def __init__(self, parent, datos_alumno, audio_helper):
        super().__init__(parent)
        
        self.datos = datos_alumno
        self.audio = audio_helper
        self.confirmado = False  # True si el personal acepta
        
        # Configuración ventana
        self.title("⚠️ ALERTA DE TURNO CRUZADO")
        self.geometry("500x450")  # ← Aumentado altura
        self.resizable(False, False)
        
        # Modal y centrado
        self.transient(parent)
        self.grab_set()
        self.focus_force()
        
        # Centrar en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.winfo_screenheight() // 2) - (450 // 2)
        self.geometry(f"500x450+{x}+{y}")
        
        self.crear_ui()
        
        # Reproducir sonido de alerta
        self.audio.reproducir_alerta_turno_cruzado()
    
    def crear_ui(self):
        """Crear interfaz de alerta"""
        
        # Frame principal
        fr_main = ctk.CTkFrame(self, fg_color="#2d2d2d")
        fr_main.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Banner de alerta (amarillo)
        fr_banner = ctk.CTkFrame(fr_main, fg_color="#f39c12", height=80)
        fr_banner.pack(fill="x")
        fr_banner.pack_propagate(False)
        
        ctk.CTkLabel(
            fr_banner,
            text="⚠️",
            font=("Arial", 48),
            text_color="white"
        ).pack(side="left", padx=20)
        
        fr_texto_banner = ctk.CTkFrame(fr_banner, fg_color="transparent")
        fr_texto_banner.pack(side="left", fill="both", expand=True, pady=10)
        
        ctk.CTkLabel(
            fr_texto_banner,
            text="ATENCIÓN PERSONAL",
            font=("Roboto", 18, "bold"),
            text_color="white",
            anchor="w"
        ).pack(anchor="w")
        
        ctk.CTkLabel(
            fr_texto_banner,
            text="Alumno ingresando en turno diferente",
            font=("Roboto", 11),
            text_color="#2d2d2d",
            anchor="w"
        ).pack(anchor="w")
        
        # ===== CONTENIDO PRINCIPAL (SCROLLABLE) =====
        fr_scroll_wrapper = ctk.CTkFrame(fr_main, fg_color="transparent")
        fr_scroll_wrapper.pack(fill="both", expand=True, padx=20, pady=10)
        
        fr_content = ctk.CTkScrollableFrame(fr_scroll_wrapper, fg_color="transparent")
        fr_content.pack(fill="both", expand=True)
        
        # Datos del alumno
        self._crear_fila_info(fr_content, "ALUMNO:", self.datos.get("alumno", "Desconocido"))
        self._crear_fila_info(fr_content, "CÓDIGO:", self.datos.get("codigo", "---"))
        
        # Separador
        ctk.CTkFrame(fr_content, fg_color="#404040", height=2).pack(fill="x", pady=15)
        
        # Info de turnos
        horario_actual = self.datos.get("horario", "DESCONOCIDO")
        turno_actual = self.datos.get("turno", "DESCONOCIDO")
        
        fr_turnos = ctk.CTkFrame(fr_content, fg_color="#1a1a1a", corner_radius=10)
        fr_turnos.pack(fill="x", pady=10)
        
        ctk.CTkLabel(
            fr_turnos,
            text=f"Matriculado en: HORARIO {horario_actual}",
            font=("Roboto", 12, "bold"),
            text_color="#3498db"
        ).pack(pady=(15, 5))
        
        ctk.CTkLabel(
            fr_turnos,
            text="▼",
            font=("Arial", 20),
            text_color="#e74c3c"
        ).pack()
        
        ctk.CTkLabel(
            fr_turnos,
            text=f"Está marcando en: TURNO {turno_actual}",
            font=("Roboto", 12, "bold"),
            text_color="#e74c3c"
        ).pack(pady=(5, 15))
        
        # Estado calculado
        estado = self.datos.get("estado", "DESCONOCIDO")
        hora = self.datos.get("hora", "00:00:00")
        
        ctk.CTkLabel(
            fr_content,
            text=f"Estado: {estado} | Hora: {hora}",
            font=("Roboto", 10),
            text_color="gray"
        ).pack(pady=10)
        
        # ===== BOTONES DE DECISIÓN (FUERA DEL SCROLL, SIEMPRE VISIBLES) =====
        fr_botones_container = ctk.CTkFrame(fr_main, fg_color="#1a1a1a", height=80)
        fr_botones_container.pack(fill="x", side="bottom", padx=20, pady=(0, 20))
        fr_botones_container.pack_propagate(False)
        
        fr_botones = ctk.CTkFrame(fr_botones_container, fg_color="transparent")
        fr_botones.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkButton(
            fr_botones,
            text="❌ RECHAZAR INGRESO",
            height=50,
            fg_color="#c0392b",
            hover_color="#e74c3c",
            font=("Roboto", 13, "bold"),
            command=self.rechazar
        ).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(
            fr_botones,
            text="✅ PERMITIR INGRESO",
            height=50,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            font=("Roboto", 13, "bold"),
            command=self.confirmar
        ).pack(side="left", fill="x", expand=True, padx=(5, 0))
    
    def _crear_fila_info(self, parent, label, valor):
        """Crea una fila de información"""
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.pack(fill="x", pady=5)
        
        ctk.CTkLabel(
            fr,
            text=label,
            font=("Roboto", 10, "bold"),
            text_color="gray",
            width=100,
            anchor="w"
        ).pack(side="left")
        
        ctk.CTkLabel(
            fr,
            text=valor,
            font=("Roboto", 12),
            text_color="white",
            anchor="w"
        ).pack(side="left", fill="x", expand=True)
    
    def confirmar(self):
        """Personal acepta el ingreso"""
        self.confirmado = True
        self.destroy()
    
    def rechazar(self):
        """Personal rechaza el ingreso"""
        self.confirmado = False
        self.destroy()
