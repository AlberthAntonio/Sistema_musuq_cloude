"""
Diálogo de confirmación para marcar inasistencias masivas.
Muestra un resumen completo antes de ejecutar la acción.
"""

import customtkinter as ctk
from core.theme_manager import ThemeManager as TM


class DialogoInasistencias(ctk.CTkToplevel):
    """
    Ventana modal que muestra el resumen de alumnos sin registro
    antes de marcar las inasistencias masivas.
    El personal decide: CONFIRMAR o CANCELAR.
    """

    def __init__(self, parent, resumen: dict):
        super().__init__(parent)

        self.resumen = resumen
        self.confirmado = False

        turno = resumen.get("turno", "")
        icono_turno = "🌅" if turno == "MAÑANA" else "🌆"
        color_banner = "#e67e22" if turno == "MAÑANA" else "#2980b9"

        self.title(f"{icono_turno} Confirmar Inasistencias — Turno {turno}")
        self.geometry("560x580")
        self.resizable(False, False)
        self.configure(fg_color="#1e1e1e")

        self.transient(parent)
        self.grab_set()
        self.focus_force()

        # Centrar en pantalla
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (560 // 2)
        y = (self.winfo_screenheight() // 2) - (580 // 2)
        self.geometry(f"560x580+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self.cancelar)

        self._crear_ui(color_banner, icono_turno, turno)

    # ─────────────────────────── UI ───────────────────────────────────

    def _crear_ui(self, color_banner: str, icono: str, turno: str):
        total_turno   = self.resumen.get("total_alumnos_turno", 0)
        total_pres    = self.resumen.get("total_presentes", 0)
        total_marcar  = self.resumen.get("total_a_marcar", 0)
        alumnos       = self.resumen.get("alumnos_sin_registro", [])

        # ── Banner superior ────────────────────────────────────────
        fr_banner = ctk.CTkFrame(self, fg_color=color_banner, height=80, corner_radius=0)
        fr_banner.pack(fill="x")
        fr_banner.pack_propagate(False)

        ctk.CTkLabel(
            fr_banner,
            text=icono,
            font=ctk.CTkFont(size=44),
            text_color="white"
        ).pack(side="left", padx=18)

        fr_txt = ctk.CTkFrame(fr_banner, fg_color="transparent")
        fr_txt.pack(side="left", fill="both", expand=True, pady=12)

        ctk.CTkLabel(
            fr_txt,
            text=f"MARCAR INASISTENCIAS — TURNO {turno}",
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            text_color="white",
            anchor="w"
        ).pack(anchor="w")

        ctk.CTkLabel(
            fr_txt,
            text="Revise el resumen antes de confirmar",
            font=ctk.CTkFont(family="Roboto", size=10),
            text_color="#2d2d2d",
            anchor="w"
        ).pack(anchor="w")

        # ── Cuerpo scrollable ────────────────────────────────────────
        fr_scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        fr_scroll.pack(fill="both", expand=True, padx=18, pady=14)

        # ── Tarjeta estadísticas ─────────────────────────────────────
        fr_stats = ctk.CTkFrame(fr_scroll, fg_color="#252525", corner_radius=10)
        fr_stats.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            fr_stats,
            text="📊  RESUMEN DEL TURNO",
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(pady=(14, 8), padx=16, anchor="w")

        ctk.CTkFrame(fr_stats, fg_color="#3a3a3a", height=1).pack(fill="x", padx=16)

        stats = [
            ("Total alumnos del turno",  str(total_turno),  TM.text()),
            ("Ya registraron asistencia", str(total_pres),   TM.success()),
            ("Sin registro (a marcar)",   str(total_marcar), "#e74c3c" if total_marcar > 0 else TM.success()),
        ]
        for label, valor, color in stats:
            fr_row = ctk.CTkFrame(fr_stats, fg_color="transparent")
            fr_row.pack(fill="x", padx=20, pady=5)
            ctk.CTkLabel(
                fr_row, text=label,
                font=ctk.CTkFont(family="Roboto", size=11),
                text_color=TM.text_secondary(), anchor="w"
            ).pack(side="left")
            ctk.CTkLabel(
                fr_row, text=valor,
                font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
                text_color=color, anchor="e"
            ).pack(side="right")

        ctk.CTkLabel(fr_stats, text="").pack(pady=4)

        # ── Lista de alumnos faltantes ───────────────────────────────
        if total_marcar == 0:
            fr_ok = ctk.CTkFrame(fr_scroll, fg_color="#1a3a2a", corner_radius=10)
            fr_ok.pack(fill="x", pady=(0, 12))
            ctk.CTkLabel(
                fr_ok,
                text="✅  Todos los alumnos ya tienen asistencia registrada.\nNo hay inasistencias que marcar.",
                font=ctk.CTkFont(family="Roboto", size=12),
                text_color=TM.success(),
                justify="center"
            ).pack(pady=20)
        else:
            fr_lista = ctk.CTkFrame(fr_scroll, fg_color="#252525", corner_radius=10)
            fr_lista.pack(fill="x", pady=(0, 12))

            ctk.CTkLabel(
                fr_lista,
                text=f"📋  ALUMNOS A MARCAR COMO FALTA  ({min(len(alumnos), 20)}"
                     + (f" de {len(alumnos)}" if len(alumnos) > 20 else "") + ")",
                font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
                text_color=TM.text_secondary()
            ).pack(pady=(14, 8), padx=16, anchor="w")

            ctk.CTkFrame(fr_lista, fg_color="#3a3a3a", height=1).pack(fill="x", padx=16)

            for i, alumno in enumerate(alumnos[:20]):
                bg = "#2a2a2a" if i % 2 == 0 else "#303030"
                fr_al = ctk.CTkFrame(fr_lista, fg_color=bg, corner_radius=5, height=34)
                fr_al.pack(fill="x", padx=12, pady=2)
                fr_al.pack_propagate(False)

                horario = alumno.get("horario", "").upper()
                if "DOBLE" in horario:
                    h_label, h_color = "DH", "#e67e22"
                elif "VESPERTINO" in horario:
                    h_label, h_color = "V", "#9b59b6"
                else:
                    h_label, h_color = "M", "#3498db"

                # Badge horario
                ctk.CTkLabel(
                    fr_al,
                    text=h_label,
                    font=ctk.CTkFont(family="Roboto", size=9, weight="bold"),
                    fg_color=h_color,
                    text_color="white",
                    width=22, height=20,
                    corner_radius=4
                ).pack(side="left", padx=(10, 6), pady=7)

                codigo = alumno.get("codigo", "")
                nombre = alumno.get("nombre", "")
                texto_alumno = f"{codigo}  —  {nombre}" if codigo else nombre

                ctk.CTkLabel(
                    fr_al,
                    text=texto_alumno,
                    font=ctk.CTkFont(family="Roboto", size=10),
                    text_color=TM.text(),
                    anchor="w"
                ).pack(side="left", fill="x", expand=True)

                # Badge FALTA
                ctk.CTkLabel(
                    fr_al,
                    text="FALTA",
                    font=ctk.CTkFont(family="Roboto", size=8, weight="bold"),
                    fg_color="#c0392b",
                    text_color="white",
                    width=40, height=18,
                    corner_radius=4
                ).pack(side="right", padx=10)

            if len(alumnos) > 20:
                ctk.CTkLabel(
                    fr_lista,
                    text=f"  ... y {len(alumnos) - 20} alumnos más",
                    font=ctk.CTkFont(family="Roboto", size=9, slant="italic"),
                    text_color=TM.text_secondary(),
                    anchor="w"
                ).pack(padx=16, pady=(6, 4), anchor="w")

            ctk.CTkLabel(fr_lista, text="").pack(pady=4)

        # ── Aviso de irreversibilidad ────────────────────────────────
        if total_marcar > 0:
            fr_warn = ctk.CTkFrame(fr_scroll, fg_color="#4a1010", corner_radius=8)
            fr_warn.pack(fill="x", pady=(0, 4))
            ctk.CTkLabel(
                fr_warn,
                text="⚠️  Esta acción registrará FALTAS y no se puede deshacer fácilmente.",
                font=ctk.CTkFont(family="Roboto", size=10, weight="bold"),
                text_color="#e74c3c"
            ).pack(pady=10, padx=14)

        # ── Botones de acción (pie fijo) ──────────────────────────────
        fr_pie = ctk.CTkFrame(self, fg_color="#1a1a1a", height=72, corner_radius=0)
        fr_pie.pack(fill="x", side="bottom")
        fr_pie.pack_propagate(False)

        fr_inner = ctk.CTkFrame(fr_pie, fg_color="transparent")
        fr_inner.pack(fill="both", expand=True, padx=18, pady=12)

        ctk.CTkButton(
            fr_inner,
            text="❌  CANCELAR",
            height=48,
            fg_color="#555555",
            hover_color="#666666",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            command=self.cancelar
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))

        texto_confirm = (
            f"✅  CONFIRMAR  ({total_marcar} faltas)" if total_marcar > 0
            else "✅  ACEPTAR"
        )
        estado_btn = "normal" if total_marcar > 0 else "disabled"

        ctk.CTkButton(
            fr_inner,
            text=texto_confirm,
            height=48,
            fg_color="#27ae60",
            hover_color="#2ecc71",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            state=estado_btn,
            command=self.confirmar
        ).pack(side="left", fill="x", expand=True, padx=(6, 0))

    # ─────────────────────────── Acciones ─────────────────────────────

    def confirmar(self):
        self.confirmado = True
        self.destroy()

    def cancelar(self):
        self.confirmado = False
        self.destroy()
