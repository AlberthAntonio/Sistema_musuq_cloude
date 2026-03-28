"""
Diálogo modal de alerta por turno cruzado.
Bloquea la UI hasta que el personal tome una decisión (permitir / rechazar).
"""

import customtkinter as ctk
from core.theme_manager import ThemeManager as TM


class DialogoAlertaTurno(ctk.CTkToplevel):
    """
    Ventana modal que se muestra cuando un alumno intenta ingresar
    en un turno distinto al de su horario matriculado.
    El personal debe decidir: PERMITIR o RECHAZAR el ingreso.
    """

    def __init__(self, parent, datos_alumno: dict, audio_helper):
        super().__init__(parent)

        self.datos = datos_alumno
        self.audio = audio_helper
        self.confirmado = False   # True si el personal acepta el ingreso

        # ── Configuración de la ventana ──────────────────────────────
        self.title("⚠️ ALERTA DE TURNO CRUZADO")
        self.geometry("520x480")
        self.resizable(False, False)
        self.configure(fg_color="#1e1e1e")

        # Modal: bloquea la ventana padre hasta que se cierre
        self.transient(parent)
        self.grab_set()
        self.focus_force()

        # Centrar en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (520 // 2)
        y = (self.winfo_screenheight() // 2) - (480 // 2)
        self.geometry(f"520x480+{x}+{y}")

        # Protocolo de cierre (X) equivale a rechazar
        self.protocol("WM_DELETE_WINDOW", self.rechazar)

        self._crear_ui()
        # Nota: el audio lo dispara la vista ANTES de crear este diálogo,
        # así evitamos que grab_set() interfiera con winsound.

    # ─────────────────────────── UI ───────────────────────────────────

    def _crear_ui(self):
        # ── Banner de alerta ────────────────────────────────────────
        fr_banner = ctk.CTkFrame(self, fg_color="#e67e22", height=90, corner_radius=0)
        fr_banner.pack(fill="x")
        fr_banner.pack_propagate(False)

        ctk.CTkLabel(
            fr_banner,
            text="⚠️",
            font=ctk.CTkFont(size=46),
            text_color="white"
        ).pack(side="left", padx=20)

        fr_txt_banner = ctk.CTkFrame(fr_banner, fg_color="transparent")
        fr_txt_banner.pack(side="left", fill="both", expand=True, pady=12)

        ctk.CTkLabel(
            fr_txt_banner,
            text="ATENCIÓN PERSONAL",
            font=ctk.CTkFont(family="Roboto", size=18, weight="bold"),
            text_color="white",
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            fr_txt_banner,
            text="Alumno ingresando en turno diferente al matriculado",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color="#2d2d2d",
            anchor="w"
        ).pack(anchor="w")

        # ── Cuerpo principal ────────────────────────────────────────
        fr_body = ctk.CTkFrame(self, fg_color="transparent")
        fr_body.pack(fill="both", expand=True, padx=24, pady=16)

        # Datos del alumno
        self._fila(fr_body, "ALUMNO",  self.datos.get("alumno", "Desconocido"))
        self._fila(fr_body, "CÓDIGO",  self.datos.get("codigo", "---"))

        # Separador
        ctk.CTkFrame(fr_body, fg_color="#404040", height=1).pack(fill="x", pady=14)

        # Tarjeta turno vs horario
        fr_card = ctk.CTkFrame(fr_body, fg_color="#2a2a2a", corner_radius=10)
        fr_card.pack(fill="x")

        horario = self.datos.get("horario", "DESCONOCIDO").upper()
        turno   = self.datos.get("turno",   "DESCONOCIDO").upper()

        ctk.CTkLabel(
            fr_card,
            text=f"Matriculado en: HORARIO {horario}",
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            text_color="#3498db"
        ).pack(pady=(18, 4))

        ctk.CTkLabel(
            fr_card,
            text="▼",
            font=ctk.CTkFont(size=20),
            text_color="#e74c3c"
        ).pack()

        ctk.CTkLabel(
            fr_card,
            text=f"Está marcando en: TURNO {turno}",
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            text_color="#e74c3c"
        ).pack(pady=(4, 18))

        # Estado / hora
        estado = self.datos.get("estado", "PUNTUAL")
        hora   = self.datos.get("hora",   "--:--:--")

        ctk.CTkLabel(
            fr_body,
            text=f"Estado calculado: {estado}   |   Hora: {hora}",
            font=ctk.CTkFont(family="Roboto", size=10),
            text_color="gray"
        ).pack(pady=12)

        # ── Botones de decisión ─────────────────────────────────────
        fr_bts = ctk.CTkFrame(self, fg_color="#1a1a1a", height=75, corner_radius=0)
        fr_bts.pack(fill="x", side="bottom")
        fr_bts.pack_propagate(False)

        fr_inner = ctk.CTkFrame(fr_bts, fg_color="transparent")
        fr_inner.pack(fill="both", expand=True, padx=20, pady=12)

        ctk.CTkButton(
            fr_inner,
            text="❌  RECHAZAR INGRESO",
            height=50,
            fg_color="#c0392b",
            hover_color="#e74c3c",
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            command=self.rechazar
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            fr_inner,
            text="✅  PERMITIR INGRESO",
            height=50,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            command=self.confirmar
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))

    def _fila(self, parent, label: str, valor: str):
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.pack(fill="x", pady=4)

        ctk.CTkLabel(
            fr,
            text=f"{label}:",
            font=ctk.CTkFont(family="Roboto", size=10, weight="bold"),
            text_color="gray",
            width=80,
            anchor="w"
        ).pack(side="left")

        ctk.CTkLabel(
            fr,
            text=valor,
            font=ctk.CTkFont(family="Roboto", size=12),
            text_color="white",
            anchor="w"
        ).pack(side="left", fill="x", expand=True)

    # ─────────────────────────── Acciones ─────────────────────────────

    def confirmar(self):
        """El personal permite el ingreso."""
        self.confirmado = True
        self.destroy()

    def rechazar(self):
        """El personal rechaza el ingreso (también al cerrar con X)."""
        self.confirmado = False
        self.destroy()
