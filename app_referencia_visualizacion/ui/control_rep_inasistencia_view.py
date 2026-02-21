import customtkinter as ctk
from tkinter import messagebox
import webbrowser
import urllib.parse
from datetime import date
import threading # <--- HILOS
import math      # <--- CÁLCULO DE PÁGINAS
from tkcalendar import DateEntry
from app.controllers.rep_inasistencia_controller import ReporteInasistenciaController

# --- IMPORTACIÓN DE ESTILOS CENTRALIZADOS ---
import app.styles.tabla_style as st
import app.utils.components_ui as ui

# ===== IMPORTAR EL MIXIN =====
from app.mixins import InfiniteScrollMixin
# =============================

class ReporteInasistenciaView(ctk.CTkFrame, InfiniteScrollMixin):
    def __init__(self, master):
        super().__init__(master)
        self.controller = ReporteInasistenciaController()

        # Configuración de anchos para la tabla
        # ID (Oculto), Código, Alumno, Turno, Celular, Estado, WhatsApp, Acción
        self.ANCHOS = [100, 250, 80, 100, 120, 100, 100] 

        # VARIABLES DE PAGINACIÓN Y ESTADO
        self.cargando = False

        # Configuración Visual
        self.configure(fg_color=st.Colors.BG_MAIN)

        # ============================================================
        #                    ENCABEZADO Y TÍTULO
        # ============================================================
        self.fr_header = ctk.CTkFrame(self, fg_color="transparent")
        self.fr_header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(self.fr_header, text="🚨 CONTROL DIARIO DE INASISTENCIAS", 
                     font=st.Fonts.TITLE, text_color=st.Colors.FALTA).pack(side="left")
        
        # Loader
        self.lbl_loader = ctk.CTkLabel(self.fr_header, text="⏳ Cargando...", 
                                     text_color="#f39c12", font=("Roboto", 12, "bold"))
        # (Se muestra al buscar)

        # ============================================================
        #             ZONA SUPERIOR: FECHA Y KPIS
        # ============================================================
        self.fr_top = ctk.CTkFrame(self, fg_color="transparent")
        self.fr_top.pack(fill="x", padx=20, pady=5)
        
        # --- Selector de Fecha (Panel Izquierdo) ---
        self.fr_fecha = ctk.CTkFrame(self.fr_top, fg_color=st.Colors.BG_PANEL, corner_radius=10)
        self.fr_fecha.pack(side="left", padx=(0, 20), fill="y")
        
        ctk.CTkLabel(self.fr_fecha, text="📅 FECHA DEL REPORTE", 
                     font=("Roboto", 11, "bold"), text_color="gray").pack(pady=(10, 5), padx=15)
        
        self.ent_fecha = DateEntry(self.fr_fecha, width=12, background=st.Colors.FALTA, 
                                   foreground='white', borderwidth=0, date_pattern='dd/mm/yyyy',
                                   font=("Roboto", 12, "bold"))
        self.ent_fecha.pack(padx=15, pady=(0, 15))
        self.ent_fecha.set_date(date.today())

        # --- KPIs (Panel Derecho - Grid) ---
        self.fr_kpis = ctk.CTkFrame(self.fr_top, fg_color="transparent")
        self.fr_kpis.pack(side="left", fill="both", expand=True)
        self.fr_kpis.columnconfigure((0, 1, 2), weight=1)

        # Inicializar KPIs en 0
        ui.crear_tarjeta_metrica(self.fr_kpis, "TOTAL AUSENTES", "0", "🚫", "gray", 0)
        ui.crear_tarjeta_metrica(self.fr_kpis, "SIN JUSTIFICAR", "0", "🔥", st.Colors.FALTA, 1)
        ui.crear_tarjeta_metrica(self.fr_kpis, "JUSTIFICADOS", "0", "✅", st.Colors.ASISTENCIA, 2)

        # ============================================================
        #                  BARRA DE FILTROS
        # ============================================================
        self.fr_filtros = ctk.CTkFrame(self, fg_color=st.Colors.BG_PANEL, height=50)
        self.fr_filtros.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(self.fr_filtros, text="Filtros:", font=("Roboto", 12, "bold")).pack(side="left", padx=15)

        self.cb_turno = ctk.CTkComboBox(self.fr_filtros, values=["Todos", "MAÑANA", "TARDE", "DOBLE HORARIO"], width=100)
        self.cb_turno.pack(side="left", padx=5, pady=10)
        
        self.cb_grupo = ctk.CTkComboBox(self.fr_filtros, values=["Todos", "A", "B", "C", "D"], width=100)
        self.cb_grupo.set("Todos")
        self.cb_grupo.pack(side="left", padx=5)

        # Switch "Solo Injustificadas"
        self.var_solo_injust = ctk.BooleanVar(value=True)
        self.sw_filtro = ctk.CTkSwitch(self.fr_filtros, text="🔴 Solo Injustificadas", 
                                       variable=self.var_solo_injust, progress_color=st.Colors.FALTA,
                                       command=self.iniciar_busqueda_thread) # <--- Ahora llama al hilo
        self.sw_filtro.pack(side="left", padx=20)

        # Botón Buscar
        self.btn_buscar = ctk.CTkButton(self.fr_filtros, text="🔄 ACTUALIZAR LISTA", width=140,
                                        fg_color="#404040", hover_color="gray30",
                                        command=self.iniciar_busqueda_thread)
        self.btn_buscar.pack(side="right", padx=15)

        self.btn_imprimir = ctk.CTkButton(self.fr_filtros, text="🖨️ IMPRIMIR REPORTE",
                                  fg_color=st.Colors.FALTA, hover_color="#c0392b",
                                  width=150, command=self.imprimir_reporte)
        self.btn_imprimir.pack(side="right", padx=15)

        # ============================================================
        #                  TABLA (SCROLLABLE CUSTOM)
        # ============================================================
        self.container_tabla = ctk.CTkFrame(self, fg_color=st.Colors.BG_PANEL)
        self.container_tabla.pack(fill="both", expand=True, padx=20)

        # 1. Cabecera
        self.crear_cabecera()

        # 2. Cuerpo
        self.scroll_tabla = ctk.CTkScrollableFrame(self.container_tabla, fg_color="transparent")
        self.scroll_tabla.pack(fill="both", expand=True)

        # ===== INICIALIZAR SCROLL INFINITO =====
        self.init_infinite_scroll(self.scroll_tabla, lote_tamano=20)
        # =======================================

        # 3. Estado Vacío
        self.empty_state = ctk.CTkLabel(self.scroll_tabla, text="\n\n🔍 No hay inasistencias para mostrar", font=st.Fonts.SUBTITLE, text_color="gray")
        self.empty_state.pack()

        # Carga inicial
        self.iniciar_busqueda_thread()

    # ============================================================
    #          LÓGICA ASÍNCRONA (THREADING)
    # ============================================================

    def iniciar_busqueda_thread(self):
        if self.cargando: return
        self.cargando = True
        
        # Feedback Visual
        self.lbl_loader.pack(side="left", padx=10)
        self.btn_buscar.configure(state="disabled", text="Cargando...")
        self.empty_state.pack_forget()
        
        # Limpiar tabla
        self.limpiar_scroll()

        # Recoger Filtros
        params = {
            "fecha": self.ent_fecha.get(),
            "turno": self.cb_turno.get(),
            "grupo": self.cb_grupo.get(),
            "solo_inj": self.var_solo_injust.get()
        }

        # Lanzar Hilo
        threading.Thread(target=self._proceso_busqueda, args=(params,), daemon=True).start()

    def _proceso_busqueda(self, p):
        try:
            exito, msg, stats, datos = self.controller.obtener_inasistencias_dia(
                p["fecha"], p["turno"], p["grupo"], "Todos", p["solo_inj"]
            )
        except Exception as e:
            exito, msg, stats, datos = False, str(e), {}, []
        
        self.after(0, lambda: self._finalizar_busqueda(exito, msg, stats, datos))

    def _finalizar_busqueda(self, exito, msg, stats, datos):
        """Main Thread - Actualizar UI"""
        self.cargando = False
        self.lbl_loader.pack_forget()
        self.btn_buscar.configure(state="normal", text="🔄 ACTUALIZAR LISTA")
        
        if not exito:
            messagebox.showerror("Error", msg)
            return
        
        # Actualizar KPIs
        for w in self.fr_kpis.winfo_children():
            w.destroy()
        
        ui.crear_tarjeta_metrica(self.fr_kpis, "TOTAL AUSENTES", str(stats.get("total", 0)), 
                                 "🚫", "gray", 0)
        ui.crear_tarjeta_metrica(self.fr_kpis, "SIN JUSTIFICAR", str(stats.get("injustificadas", 0)), 
                                 "🔥", st.Colors.FALTA, 1)
        ui.crear_tarjeta_metrica(self.fr_kpis, "JUSTIFICADOS", str(stats.get("justificadas", 0)), 
                                 "✅", st.Colors.ASISTENCIA, 2)
        
        # Validar datos
        if not datos:
            self.empty_state.configure(text="\n✅ No hay faltas registradas con estos filtros.")
            self.empty_state.pack(pady=20)
            return
        
        # ===== CARGAR DATOS CON SCROLL INFINITO =====
        self.cargar_datos_scroll(datos)  # ← Método del Mixin
    
    # ============================================================
    #              DISEÑO DE FILAS (TU ESTILO ORIGINAL)
    # ============================================================

    def crear_cabecera(self):
        header = ctk.CTkFrame(self.container_tabla, height=45, fg_color=st.Colors.TABLE_HEADER, corner_radius=5)
        header.pack(fill="x", padx=5, pady=(5, 5))
        
        titulos = ["CÓDIGO", "ALUMNO", "TURNO", "CELULAR", "ESTADO", "CONTACTAR", "ACCIÓN"]
        
        for i, t in enumerate(titulos):
            w = self.ANCHOS[i]
            ctk.CTkLabel(header, text=t, font=("Roboto", 11, "bold"), text_color="white", width=w).pack(side="left", padx=2)

    def render_fila_scroll(self, d, index):
        """Método requerido por InfiniteScrollMixin"""
        bg = st.Colors.ROW_ODD if index % 2 == 0 else st.Colors.ROW_EVEN
        
        row = ctk.CTkFrame(self._scroll_widget_inf, fg_color=bg, corner_radius=0, height=40)
        row.pack(fill="x", pady=0, padx=0)
        row.pack_propagate(False)
        
        font_row = ("Roboto", 12)
        
        # Código
        ctk.CTkLabel(row, text=d["codigo"], width=self.ANCHOS[0], 
                    text_color="white", font=font_row).pack(side="left", padx=2, fill="y")
        
        # Nombre (con indicador de reincidente)
        nom_txt = d["nombre"]
        nom_col = "white"
        if d.get("reincidente", False):
            nom_txt = f"🔥 {nom_txt}"
            nom_col = st.Colors.TARDANZA
        
        ctk.CTkLabel(row, text=nom_txt, width=self.ANCHOS[1], anchor="w", 
                    text_color=nom_col, font=font_row).pack(side="left", padx=2, fill="y")
        
        # Turno
        ctk.CTkLabel(row, text=d["turno"], width=self.ANCHOS[2], 
                    text_color="gray", font=font_row).pack(side="left", padx=2, fill="y")
        
        # Celular
        ctk.CTkLabel(row, text=d["celular"], width=self.ANCHOS[3], 
                    text_color="gray", font=font_row).pack(side="left", padx=2, fill="y")
        
        # Estado (Badge)
        st_txt = d["estado"]
        st_bg = st.Colors.FALTA if st_txt == "INASISTENCIA" else st.Colors.ASISTENCIA
        
        f_st = ctk.CTkFrame(row, fg_color="transparent", width=self.ANCHOS[4], height=40)
        f_st.pack(side="left", padx=2)
        f_st.pack_propagate(False)
        
        ctk.CTkLabel(f_st, text=st_txt, fg_color=st_bg, text_color="white", 
                    corner_radius=2, width=85, height=22, 
                    font=("Arial", 10, "bold")).place(relx=0.5, rely=0.5, anchor="center")
        
        # Botón WhatsApp
        f_wa = ctk.CTkFrame(row, fg_color="transparent", width=self.ANCHOS[5], height=40)
        f_wa.pack(side="left", padx=2)
        f_wa.pack_propagate(False)
        
        btn_wa = ctk.CTkButton(f_wa, text="📲", width=60, height=22, 
                               fg_color="#27ae60", hover_color="#2ecc71", font=("Arial", 10),
                               command=lambda cel=d["celular"], nom=d["nombre"]: 
                                   self.enviar_whatsapp(cel, nom))
        btn_wa.place(relx=0.5, rely=0.5, anchor="center")
        
        # Botón Justificar
        f_jus = ctk.CTkFrame(row, fg_color="transparent", width=self.ANCHOS[6], height=40)
        f_jus.pack(side="left", padx=2)
        f_jus.pack_propagate(False)
        
        if st_txt == "INASISTENCIA":
            btn_jus = ctk.CTkButton(f_jus, text="📝", width=60, height=22, 
                                    fg_color="#f39c12", hover_color="#e67e22", font=("Arial", 10),
                                    command=lambda id_as=d["id_asistencia"], nom=d["nombre"]: 
                                        self.justificar_falta(id_as, nom))
            btn_jus.place(relx=0.5, rely=0.5, anchor="center")
        else:
            ctk.CTkLabel(f_jus, text="✔️", text_color="gray", 
                        font=("Arial", 10)).place(relx=0.5, rely=0.5, anchor="center")

    # ================= LÓGICA DE NEGOCIO =================

    def enviar_whatsapp(self, celular, nombre):
        cel_clean = str(celular).split("/")[0].strip()
        if len(cel_clean) < 9:
            messagebox.showwarning("Error", "Número celular inválido")
            return
            
        mensaje = (f"Estimado apoderado, le informamos que el estudiante *{nombre}* "
                   f"NO ASISTIÓ hoy a clases ({self.ent_fecha.get()}). "
                   f"Favor de comunicarse con coordinación urgentemente.")
        
        try:
            url = f"https://wa.me/51{cel_clean}?text={urllib.parse.quote(mensaje)}"
            webbrowser.open(url)
        except: pass

    def justificar_falta(self, id_asistencia, nombre):
        motivo = ctk.CTkInputDialog(text=f"Justificar falta de:\n{nombre}\n\nIngrese motivo:", title="Justificación Rápida").get_input()
        
        if motivo:
            exito, msg = self.controller.justificar_rapida(id_asistencia, motivo)
            if exito:
                self.iniciar_busqueda_thread() # Recargar datos
            else:
                messagebox.showerror("Error", msg)

    def imprimir_reporte(self):
        """Genera reporte PDF/CSV"""
        # ✅ CAMBIAR:
        if not self.get_total_registros():  # ← Método del Mixin
            messagebox.showwarning("Atención", "No hay datos para exportar")
            return
        
        messagebox.showinfo("Imprimir", 
                        f"Generando reporte con {self.get_total_registros()} registros...")