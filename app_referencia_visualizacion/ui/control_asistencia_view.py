# app/ui/control_asistencia_view.py (REEMPLAZAR COMPLETO)

import customtkinter as ctk
from tkinter import messagebox
import time
import locale
import threading
from app.controllers.asistencia_controller import AsistenciaController
from app.utils.audio_helper import AudioHelper
from app.ui.dialogo_alerta_turno import DialogoAlertaTurno
from app.ui.dialogo_cierre_turno import DialogoCierreTurno
import app.styles.tabla_style as st
import app.utils.components_ui as ui

from app.mixins import InfiniteScrollMixin

# Intentar poner fechas en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    pass

class AsistenciaView(ctk.CTkFrame, InfiniteScrollMixin):
    def __init__(self, master):
        super().__init__(master)
        
        self.controller = AsistenciaController()
        self.audio = AudioHelper()  # ← NUEVO: Sistema de audio
        
        # Variables de estado
        self.fila_seleccionada = None
        self.datos_seleccionados = None
        self.color_original_seleccion = None
        self._reloj_after = None

        self.turno_actual_cache = self._obtener_turno_actual()
        self.filtro_turno_activo = True  # True = filtrar por turno, False = mostrar todos
        self._monitor_turno_after = None
        
        # Variables de lógica
        self.primer_widget_fila = None
        self.cargando = False

        # Configuración Visual
        self.configure(fg_color=st.Colors.BG_MAIN)
        
        # Anchos fijos para la tabla (MODIFICADO: +1 columna para TURNO)
        self.ANCHOS = [0, 100, 300, 80, 100, 100]  # ← Agregamos columna TURNO
        
        # Grid Principal
        self.grid_columnconfigure(0, weight=7)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)
        
        # ============================================================
        # 📄 TARJETA IZQUIERDA
        # ============================================================
        self.card_izq = ctk.CTkFrame(self, fg_color=st.Colors.BG_MAIN, corner_radius=10)
        self.card_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=0)
        self.card_izq.grid_rowconfigure(4, weight=1)
        self.card_izq.grid_columnconfigure(0, weight=1)
        
        # 1. Encabezado
        self.lbl_titulo = ctk.CTkLabel(
            self.card_izq, 
            text="CONTROL DE ASISTENCIA",
            font=st.Fonts.TITLE, 
            text_color="white"
        )
        self.lbl_titulo.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 5))
        
        self.lbl_instr = ctk.CTkLabel(
            self.card_izq, 
            text="Ingrese CÓDIGO o escanee carnet ➝",
            font=("Roboto", 11), 
            text_color="gray"
        )
        self.lbl_instr.grid(row=0, column=0, sticky="e", padx=20, pady=(20, 5))
        
        # 2. Input Principal
        self.fr_input = ctk.CTkFrame(self.card_izq, fg_color="transparent")
        self.fr_input.grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 10))
        
        self.entry_codigo = ctk.CTkEntry(
            self.fr_input, 
            placeholder_text="📷 Código aquí...",
            height=50, 
            font=("Roboto", 24, "bold"), 
            border_width=0,
            fg_color=st.Colors.BG_PANEL, 
            text_color="white",
            justify="center", 
            corner_radius=10
        )
        self.entry_codigo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_codigo.bind("<Return>", self.registrar_asistencia)
        self.entry_codigo.bind("<KeyRelease>", lambda event: self.mayusculas(self.entry_codigo))
        
        self.btn_marcar = ctk.CTkButton(
            self.fr_input, 
            text="MARCAR", 
            width=120, 
            height=50,
            fg_color=st.Colors.ASISTENCIA, 
            hover_color="#2980b9",
            font=("Roboto", 14, "bold"), 
            corner_radius=10,
            command=self.registrar_asistencia
        )
        self.btn_marcar.pack(side="right")
        
        # 3. Barra de Búsqueda
        self.fr_busqueda = ctk.CTkFrame(self.card_izq, fg_color="transparent", height=40)
        self.fr_busqueda.grid(row=2, column=0, sticky="ew", padx=15, pady=(5, 5))
        
        self.bg_search = ctk.CTkFrame(self.fr_busqueda, fg_color=st.Colors.BG_PANEL, corner_radius=15, height=35)
        self.bg_search.pack(fill="x")
        self.bg_search.pack_propagate(False)
        
        ctk.CTkLabel(self.bg_search, text="🔍", font=("Arial", 14), text_color="gray").pack(side="left", padx=(15, 5))
        
        self.entry_busqueda = ctk.CTkEntry(
            self.bg_search, 
            placeholder_text="Buscar por Nombre, DNI o Código...",
            height=30, 
            border_width=0, 
            fg_color=st.Colors.BG_PANEL, 
            text_color="white", 
            corner_radius=30
        )
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_busqueda.bind("<KeyRelease>", self.evento_buscar_alumno)
        
        # 4. Lista de Resultados
        self.wrapper_resultados = ctk.CTkFrame(self.card_izq, fg_color="transparent", height=100)
        self.wrapper_resultados.grid(row=3, column=0, sticky="ew", padx=15, pady=(0, 5))
        self.wrapper_resultados.pack_propagate(False)
        
        self.fr_resultados = ctk.CTkScrollableFrame(self.wrapper_resultados, fg_color=st.Colors.BG_PANEL)
        self.fr_resultados.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self.fr_resultados, text="... Escriba para buscar ...", text_color="gray").pack()
        
        # 5. Tabla Expandida
        self.fr_tabla = ctk.CTkFrame(self.card_izq, fg_color="transparent")
        self.fr_tabla.grid(row=4, column=0, sticky="nsew", padx=15, pady=(5, 15))
        
        # Header y Loader
        self.fr_header_tabla = ctk.CTkFrame(self.fr_tabla, fg_color="transparent")
        self.fr_header_tabla.pack(fill="x", pady=(0,5))
        
        # Frame izquierdo: Título + Contador + Switch
        fr_info_izq = ctk.CTkFrame(self.fr_header_tabla, fg_color="transparent")
        fr_info_izq.pack(side="left")

        # Título
        ctk.CTkLabel(
            fr_info_izq,
            text="HISTORIAL DE HOY",
            font=("Roboto", 12, "bold"),
            text_color="gray"
        ).pack(side="left")

        # Contador con formato (actual/total)
        self.lbl_contador = ctk.CTkLabel(
            fr_info_izq,
            text="(0/0)",
            font=("Roboto", 11, "bold"),
            text_color="#3498db",
            fg_color="#1a1a1a",
            corner_radius=5,
            padx=8,
            pady=2
        )
        self.lbl_contador.pack(side="left", padx=10)

        # Switch compacto
        self.switch_filtro = ctk.CTkSwitch(
            fr_info_izq,
            text="Filtrar",
            font=("Roboto", 9),
            command=self.toggle_filtro_turno,
            width=80,
            height=20,
            switch_width=35,
            switch_height=18
        )
        self.switch_filtro.pack(side="left", padx=10)
        self.switch_filtro.select()

        # Loader (lado derecho)
        self.lbl_loader = ctk.CTkLabel(
            self.fr_header_tabla, 
            text="⏳ Cargando...", 
            text_color="#f39c12"
        )

        self.container_list = ctk.CTkFrame(self.fr_tabla, fg_color="#2b2b2b", corner_radius=10)
        self.container_list.pack(fill="both", expand=True)
        
        self.crear_cabecera()
        
        self.scroll_tabla = ctk.CTkScrollableFrame(self.container_list, fg_color="transparent")
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)

        self.init_infinite_scroll(self.scroll_tabla, lote_tamano=25)
        
        self.lbl_cargando_mas = ctk.CTkLabel(
            self.scroll_tabla,
            text="⏳ Cargando más registros...",
            text_color="#3498db",
            font=("Roboto", 10, "italic")
        )

        # ============================================================
        # 🎛️ TARJETA DERECHA
        # ============================================================
        self.card_der = ctk.CTkFrame(self, fg_color=st.Colors.BG_MAIN, corner_radius=10)
        self.card_der.grid(row=0, column=1, sticky="nsew", padx=(0, 0), pady=0)
        
        # Reloj
        self.fr_reloj = ctk.CTkFrame(self.card_der, fg_color="transparent")
        self.fr_reloj.pack(pady=(40, 10), fill="x")
        
        self.lbl_reloj = ctk.CTkLabel(
            self.fr_reloj, 
            text="00:00:00", 
            font=("Roboto", 42, "bold"), 
            text_color="white"
        )
        self.lbl_reloj.pack()
        
        self.lbl_fecha = ctk.CTkLabel(
            self.fr_reloj, 
            text="--/--/----", 
            font=("Roboto", 13), 
            text_color="#f39c12"
        )
        self.lbl_fecha.pack()
        
        # ===== NUEVO: Indicador de turno activo =====
        self.lbl_turno_activo = ctk.CTkLabel(
            self.card_der,
            text=self._obtener_turno_actual(),
            font=("Roboto", 11, "bold"),
            text_color="#3498db",
            fg_color="#1a1a1a",
            corner_radius=8,
            height=35
        )
        self.lbl_turno_activo.pack(pady=(10, 5), padx=20, fill="x")
        
        # Estado
        self.lbl_estado = ctk.CTkLabel(
            self.card_der, 
            text="ESPERANDO...", 
            width=200, 
            height=70, 
            corner_radius=15,
            fg_color="#404040", 
            text_color="gray", 
            font=("Roboto", 18, "bold")
        )
        self.lbl_estado.pack(pady=(20, 30), padx=20)
        
        # Botones
        self.fr_botones = ctk.CTkFrame(self.card_der, fg_color="transparent")
        self.fr_botones.pack(fill="both", expand=True, padx=20, pady=5)
        
        self.btn_limpiar = ctk.CTkButton(
            self.fr_botones, 
            text="🧹 REFRESCAR TABLA", 
            height=40,
            fg_color="#404040", 
            hover_color="#505050",
            command=self.cargar_tabla_thread
        )
        self.btn_limpiar.pack(fill="x", pady=5)
        
        self.btn_falta = ctk.CTkButton(
            self.fr_botones, 
            text="🚫 MARCAR FALTA MANUAL", 
            height=40,
            fg_color="#e67e22", 
            hover_color="#d35400",
            command=self.accion_marcar_falta
        )
        self.btn_falta.pack(fill="x", pady=5)
        
        ctk.CTkLabel(self.fr_botones, text="──────────────", text_color="#4E4E4E").pack(pady=10)
        
        self.btn_eliminar = ctk.CTkButton(
            self.fr_botones, 
            text="🗑️ ELIMINAR REGISTRO", 
            height=40,
            fg_color=st.Colors.FALTA, 
            hover_color="#c0392b",
            command=self.accion_eliminar
        )
        self.btn_eliminar.pack(fill="x", pady=5)
        
        self.btn_cierre = ctk.CTkButton(
            self.fr_botones, 
            text=self._obtener_texto_boton_cierre(), 
            height=50,
            fg_color="#2c3e50", 
            hover_color="#1a252f",
            font=("Roboto", 13, "bold"), 
            border_width=1, 
            border_color="gray40",
            command=self.abrir_dialogo_cierre
        )
        self.btn_cierre.pack(side="bottom", fill="x", pady=(10, 30))
        
        # --- INICIO ---
        self.actualizar_reloj()
        self.actualizar_boton_cierre()
        self.actualizar_turno_display()  # ← NUEVO
        self.cargar_tabla_thread()
        self.entry_codigo.focus()

        self._verificar_cambio_turno()
    
    # ================= MÉTODOS VISUALES =================
    
    def crear_cabecera(self):
        """Crear cabecera de tabla con filtro de turno"""
        header = ctk.CTkFrame(
            self.container_list,
            height=40,
            fg_color=st.Colors.TABLE_HEADER,
            corner_radius=10
        )
        header.pack(fill="x", padx=5, pady=(5,0))
        
        # Columnas (centradas)
        fr_columnas = ctk.CTkFrame(header, fg_color="transparent")
        fr_columnas.pack(side="left", expand=True)
        
        cols = ["", "CÓDIGO", "ALUMNO", "TURNO", "ESTADO", "HORA"]
        for i, t in enumerate(cols):
            if i == 0:
                continue
            w = self.ANCHOS[i]
            ctk.CTkLabel(
                fr_columnas,
                text=t,
                font=("Roboto", 11, "bold"),
                text_color="white",
                width=w
            ).pack(side="left", padx=2)
    
    def toggle_filtro_turno(self):
        """Alternar entre filtro de turno actual y ver todos"""
        self.filtro_turno_activo = self.switch_filtro.get()
        
        # Actualizar texto del switch
        if self.filtro_turno_activo:
            self.switch_filtro.configure(text="🔍 Solo turno actual")
        else:
            self.switch_filtro.configure(text="📋 Viendo todos")
        
        # Recargar tabla con nuevo filtro
        self.cargar_tabla_thread()
        self.scroll_tabla._parent_canvas.yview_moveto(0.0)

    def crear_fila(self, datos, insertar_inicio=False):
        """
        Crear fila de registro (MODIFICADA: +columna TURNO)
        Datos: (id, codigo, nombre, turno, estado, hora)
        """
        id_asistencia, cod, nom, turno, estado, hora = datos
        
        bg = st.Colors.ROW_ODD
        row = ctk.CTkFrame(self.scroll_tabla, fg_color=bg, corner_radius=0, height=35)
        
        # Lógica de inserción
        if insertar_inicio and self.primer_widget_fila is not None:
            try:
                row.pack(fill="x", pady=1, before=self.primer_widget_fila)
            except:
                row.pack(fill="x", pady=1)
            self.primer_widget_fila = row
        else:
            row.pack(fill="x", pady=1)
        
        if self.primer_widget_fila is None:
            self.primer_widget_fila = row
        
        row.pack_propagate(False)
        datos_fila = (id_asistencia, nom)
        
        def on_click(e):
            self.seleccionar_fila(row, datos_fila)
        
        def on_enter(e):
            if self.fila_seleccionada != row: 
                row.configure(fg_color="#3a3a3a")
        
        def on_leave(e):
            if self.fila_seleccionada != row: 
                row.configure(fg_color=bg)
        
        row.bind("<Button-1>", on_click)
        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)
        
        font_row = ("Roboto", 11)
        
        def celda(txt, w, col="white", anchor="center", bg_badge=None):
            if bg_badge:
                f = ctk.CTkFrame(row, fg_color="transparent", width=w, height=35)
                f.pack(side="left", padx=2)
                f.pack_propagate(False)
                
                lbl = ctk.CTkLabel(
                    f, 
                    text=txt, 
                    fg_color=bg_badge, 
                    text_color="white", 
                    corner_radius=3, 
                    width=w-10, 
                    height=20, 
                    font=("Arial", 9, "bold")
                )
                lbl.place(relx=0.5, rely=0.5, anchor="center")
                lbl.bind("<Button-1>", on_click)
            else:
                lbl = ctk.CTkLabel(
                    row, 
                    text=txt, 
                    width=w, 
                    text_color=col, 
                    font=font_row, 
                    anchor=anchor
                )
                lbl.pack(side="left", padx=2)
                lbl.bind("<Button-1>", on_click)
        
        # Columnas
        celda(cod, self.ANCHOS[1], "gray")
        celda(nom, self.ANCHOS[2], "white", "w")
        
        # ===== NUEVA COLUMNA: TURNO =====
        turno_icono = "🌅" if turno == "MAÑANA" else "🌆"
        celda(f"{turno_icono} {turno[0]}", self.ANCHOS[3], "#3498db")
        
        # Estado con color
        bg_st = st.Colors.BG_PANEL
        if "PUNTUAL" in str(estado): 
            bg_st = st.Colors.PUNTUAL
        elif "TARDANZA" in str(estado): 
            bg_st = st.Colors.TARDANZA
        elif "INASISTENCIA" in str(estado): 
            bg_st = st.Colors.FALTA
        
        celda(estado, self.ANCHOS[4], bg_badge=bg_st)
        celda(hora, self.ANCHOS[5], "gray")
    
    def seleccionar_fila(self, widget, datos):
        """Seleccionar fila en tabla"""
        if self.fila_seleccionada and self.fila_seleccionada.winfo_exists():
            self.fila_seleccionada.configure(fg_color=st.Colors.ROW_ODD)
        
        self.fila_seleccionada = widget
        self.datos_seleccionados = datos
        self.fila_seleccionada.configure(fg_color="#34495e")

    # ================= LÓGICA DE REGISTRO (MODIFICADA) =================
    
    def registrar_asistencia(self, event=None):
        """Registrar asistencia con detección de turno cruzado"""
        codigo = self.entry_codigo.get().strip()
        if not codigo: 
            return
        
        # Bloquear input
        self.entry_codigo.configure(state="disabled")
        self.btn_marcar.configure(state="disabled")
        self.lbl_estado.configure(text="PROCESANDO...", fg_color="#f39c12", text_color="white")
        
        # Lanzar hilo
        threading.Thread(target=self._hilo_registrar, args=(codigo,), daemon=True).start()
    
    def _hilo_registrar(self, codigo):
        """Procesar registro en segundo plano"""
        # Llamar al controller (retorna 4 valores ahora)
        exito, mensaje, datos, requiere_alerta = self.controller.registrar_por_dni(codigo)
        
        # Volver al hilo principal
        self.after(0, lambda: self._post_registro(exito, mensaje, datos, requiere_alerta))
    
    def _post_registro(self, exito, mensaje, datos, requiere_alerta):
        """Procesar resultado del registro"""
        if not self.winfo_exists():
            return

        # Reactivar controles
        self.entry_codigo.configure(state="normal")
        self.entry_codigo.delete(0, 'end')
        self.entry_codigo.focus()
        self.btn_marcar.configure(state="normal")
        
        if not exito:
            # Error o duplicado
            self.lbl_estado.configure(text="❌ ERROR", fg_color=st.Colors.FALTA, text_color="white")
            self.audio.reproducir_alerta_error()
            messagebox.showerror("Error", mensaje)
            self.after(3000, lambda: self.lbl_estado.configure(
                text="ESPERANDO...", 
                fg_color="#404040", 
                text_color="gray"
            ) if self.winfo_exists() else None)
            return
        
        if requiere_alerta:
            # ===== TURNO CRUZADO: Mostrar diálogo modal =====
            self._mostrar_dialogo_alerta(datos)
        else:
            # Registro normal exitoso (NO SONIDO, lector de código ya lo hace)
            self._finalizar_registro_exitoso(datos)

        self.scroll_tabla._parent_canvas.yview_moveto(0.0)

    def _inicializar_tabla_con_scroll_infinito(self, registros):
        """Recibe todos los registros e inicializa el scroll infinito"""
        if not self.winfo_exists():
            return

        # Ocultar loader
        try:
            self.lbl_loader.pack_forget()
        except:
             pass
        self.cargando = False
        
        # Guardar registros
        self.registros_cache = registros
        self.registros_cargados = 0
        self.cargando_mas = False
        
        # ===== ACTUALIZAR CONTADOR CON LÓGICA DE COLOR =====
        actual = len(registros)
        
        if self.filtro_turno_activo:
            # Determinar turno actual
            turno_actual_str = self._obtener_turno_actual()
            if "MAÑANA" in turno_actual_str:
                turno = "MAÑANA"
            elif "TARDE" in turno_actual_str:
                turno = "TARDE"
            else:
                turno = None
            
            # Calcular total esperado
            if turno:
                total = self._calcular_total_esperado(turno)
            else:
                total = self.controller.contar_todos_alumnos()
        else:
            # Mostrando todos, calcular total de todos los alumnos
            total = self.controller.contar_todos_alumnos()
        
        # Determinar color según si excede el total
        if actual > total:
            color = "#e74c3c"  # Rojo si excede
            icono = "⚠️"
        elif actual == total:
            color = "#2ecc71"  # Verde si están todos
            icono = "✅"
        else:
            color = "#3498db"  # Azul normal
            icono = "📊"
        
        # Actualizar label
        self.lbl_contador.configure(
            text=f"{icono} {actual}/{total}",
            text_color=color
        )
        # ==================================================
        
        # Caso sin registros
        if not registros:
            ctk.CTkLabel(
                self.scroll_tabla,
                text="\nNo hay registros hoy.",
                text_color="gray"
            ).pack()
            return
        
        # Cargar primer lote
        self.cargar_datos_scroll(registros)

    def render_fila_scroll(self, reg, index):
        """
        Método requerido por InfiniteScrollMixin.
        Dibuja una fila de asistencia en la tabla.
        
        Args:
            reg: Objeto Asistencia o tupla con datos
            index: Índice global del registro (para colores alternados)
        """
        # 0. Validar existencia antes de dibujar
        if not self.winfo_exists():
            return

        # 1. Extraer datos (soporta objetos ORM y tuplas)
        if hasattr(reg, 'hora'):  # Es un objeto ORM
            id_asistencia = reg.id
            codigo = reg.alumno.codigo_matricula if reg.alumno else "?"
            nombre = f"{reg.alumno.apell_paterno} {reg.alumno.apell_materno}, {reg.alumno.nombres}" if reg.alumno else "Desconocido"
            turno = reg.turno or "MAÑANA"
            estado = reg.estado
            hora_str = reg.hora.strftime("%H:%M:%S")
        else:  # Es una tupla (compatibilidad con crear_fila antiguo)
            id_asistencia, codigo, nombre, turno, estado, hora_str = reg
        
        # 2. Color de fondo alternado
        bg = st.Colors.ROW_ODD if index % 2 == 0 else st.Colors.ROW_EVEN
        
        # 3. Crear frame de la fila (⭐ IMPORTANTE: self._scroll_widget_inf)
        row = ctk.CTkFrame(self._scroll_widget_inf, fg_color=bg, 
                        corner_radius=0, height=35)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        
        # 4. Configurar eventos de interacción
        datos_fila = (id_asistencia, nombre)
        
        def on_click(e):
            self.seleccionar_fila(row, datos_fila)
        
        def on_enter(e):
            if self.fila_seleccionada != row:
                row.configure(fg_color="#3a3a3a")
        
        def on_leave(e):
            if self.fila_seleccionada != row:
                row.configure(fg_color=bg)
        
        row.bind("<Button-1>", on_click)
        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)
        
        # 5. Crear celdas (Optimizado: Menos frames anidados)
        font_row = ("Roboto", 11)
        
        # Código
        ctk.CTkLabel(row, text=codigo, width=self.ANCHOS[1], 
                    text_color="gray", font=font_row).pack(side="left", padx=2)
        
        # Nombre
        ctk.CTkLabel(row, text=nombre, width=self.ANCHOS[2], 
                    text_color="white", anchor="w", 
                    font=font_row).pack(side="left", padx=2)
        
        # Turno con icono
        turno_icono = "🌅" if turno == "MAÑANA" else "🌆"
        ctk.CTkLabel(row, text=f"{turno_icono} {turno[0]}", 
                    width=self.ANCHOS[3], text_color="#3498db",
                    font=font_row).pack(side="left", padx=2)
        
        # Estado con badge de color (Optimizado: Sin frame extra, directo Label con corner_radius)
        bg_estado = st.Colors.BG_PANEL
        if "PUNTUAL" in str(estado):
            bg_estado = st.Colors.PUNTUAL
        elif "TARDANZA" in str(estado):
            bg_estado = st.Colors.TARDANZA
        elif "INASISTENCIA" in str(estado):
            bg_estado = st.Colors.FALTA
        
        # Label Badge directo
        lbl_estado = ctk.CTkLabel(
            row, 
            text=estado, 
            fg_color=bg_estado,
            text_color="white", 
            corner_radius=6,
            width=85, 
            height=22,
            font=("Arial", 10, "bold")
        )
        # Usamos pack con pady/padx para centrar verticalmente si hace falta, 
        # pero como row tiene pack_propagate(False) y height fijo, pack side left funciona bien.
        # Para centrarlo mejor en su "columna" de ancho fijo, podríamos usar un frame contenedor invisible
        # O simular el ancho con padding. 
        # La solución anterior usaba un frame contenedor de ancho ANCHOS[4]. 
        # Para mantener alineación perfecta, mantendré el frame contenedor transparente pero simple.
        
        f_conte = ctk.CTkFrame(row, fg_color="transparent", width=self.ANCHOS[4], height=35)
        f_conte.pack(side="left", padx=2)
        f_conte.pack_propagate(False) # Importante para mantener ancho fijo
        lbl_estado.place(relx=0.5, rely=0.5, anchor="center")
        
        # Hora
        ctk.CTkLabel(row, text=hora_str, width=self.ANCHOS[5],
                    text_color="gray", font=font_row).pack(side="left", padx=2)

    def _verificar_cambio_turno(self):
        """Verifica cambio de turno y recarga automáticamente si está filtrado"""
        if not self.winfo_exists():
            return

        turno_nuevo = self._obtener_turno_actual()
        
        if turno_nuevo != self.turno_actual_cache:
            print(f"🔄 Cambio de turno: {self.turno_actual_cache} → {turno_nuevo}")
            
            self.turno_actual_cache = turno_nuevo
            
            # Solo recargar si el filtro está activo
            if self.filtro_turno_activo:
                self.cargar_tabla_thread()
                
                # Notificación visual
                self.lbl_estado.configure(
                    text=f"🔄 {turno_nuevo}",
                    fg_color="#3498db",
                    text_color="white"
                )
                
                self.after(4000, lambda: self.lbl_estado.configure(
                    text="ESPERANDO...",
                    fg_color="#404040",
                    text_color="gray"
                ) if self.winfo_exists() else None)
            
            # Actualizar displays
            self.actualizar_turno_display()
            self.actualizar_boton_cierre()
        
        # Programar siguiente verificación (cada 60 segundos)
        if self.winfo_exists():
            self._monitor_turno_after = self.after(60000, self._verificar_cambio_turno)

    def _calcular_total_esperado(self, turno):
        """
        Calcula cuántos alumnos DEBEN asistir al turno especificado
        Args:
            turno: "MAÑANA" o "TARDE"
        Returns:
            int: Total de alumnos esperados
        """
        try:
            if turno == "MAÑANA":
                total = self.controller.contar_alumnos_por_turno("MATUTINO", "DOBLE HORARIO")
            elif turno == "TARDE":
                total = self.controller.contar_alumnos_por_turno("VESPERTINO", "DOBLE HORARIO")
            else:
                # Fuera de horario, contar todos los alumnos
                total = self.controller.contar_todos_alumnos()
            
            return total
        except Exception as e:
            print(f"Error calculando total esperado: {e}")
            return 0

    
    # ================= MÉTODOS AUXILIARES =================
    
    def _obtener_turno_actual(self):
        """Detecta qué turno está activo según la hora"""
        from datetime import datetime, time as dt_time
        
        hora_actual = datetime.now().time()
        
        if dt_time(6, 0, 0) <= hora_actual < dt_time(12, 0, 0):
            return "🌅 TURNO MAÑANA ACTIVO"
        elif dt_time(13, 0, 0) <= hora_actual <= dt_time(23, 59, 59):
            return "🌆 TURNO TARDE ACTIVO"
        else:
            return "⏸️ FUERA DE HORARIO"
    
    def actualizar_turno_display(self):
        """Actualizar indicador de turno cada minuto"""
        if not self.winfo_exists(): return
        self.lbl_turno_activo.configure(text=self._obtener_turno_actual())
        self.after(60000, self.actualizar_turno_display)  # Cada 60 segundos
    
    def evento_buscar_alumno(self, event):
        """Buscar alumnos en tiempo real"""
        texto = self.entry_busqueda.get().strip()
        
        for w in self.fr_resultados.winfo_children(): 
            w.destroy()
        
        if not texto:
            ctk.CTkLabel(
                self.fr_resultados, 
                text="... Escriba para buscar ...", 
                text_color="gray"
            ).pack()
            return
        
        resultados = self.controller.buscar_alumnos_general(texto)
        
        if not resultados:
            ctk.CTkLabel(
                self.fr_resultados, 
                text="Sin resultados", 
                text_color="gray"
            ).pack()
        else:
            for alu in resultados:
                txt = f"[{alu.codigo_matricula}] | {alu.apell_paterno} {alu.apell_materno}, {alu.nombres}"
                btn = ctk.CTkButton(
                    self.fr_resultados, 
                    text=txt, 
                    fg_color="transparent", 
                    hover_color="#404040",
                    anchor="w", 
                    height=25, 
                    text_color="gray80",
                    command=lambda c=alu.codigo_matricula: self.seleccionar_busqueda(c)
                )
                btn.pack(fill="x", pady=0)
    
    def seleccionar_busqueda(self, codigo):
        """Seleccionar resultado de búsqueda"""
        self.entry_codigo.delete(0, 'end')
        self.entry_codigo.insert(0, codigo)
        self.entry_codigo.focus()
        self.entry_busqueda.delete(0, 'end')
        
        for w in self.fr_resultados.winfo_children(): 
            w.destroy()

        self.fr_resultados._parent_canvas.yview_moveto(0.0)
        
        ctk.CTkLabel(
            self.fr_resultados, 
            text="Alumno seleccionado", 
            text_color=st.Colors.ASISTENCIA
        ).pack()
    
    def mayusculas(self, entry):
        """Convertir a mayúsculas automáticamente"""
        if entry.cget("state") != "disabled":
            pos = entry.index("insert")
            try:
                txt = entry.get().upper()
                entry.delete(0, 'end')
                entry.insert(0, txt)
                entry.icursor(pos)
            except Exception as e:
                print(e)
    
    def actualizar_reloj(self):
        """Actualizar reloj cada segundo"""
        if not self.winfo_exists(): return
        ahora = time.strftime("%H:%M:%S")
        try:
            fecha_str = time.strftime("%A, %d de %B").capitalize()
        except:
            fecha_str = time.strftime("%d/%m/%Y")
        
        self.lbl_reloj.configure(text=ahora)
        self.lbl_fecha.configure(text=fecha_str)
        self._reloj_after = self.after(1000, self.actualizar_reloj)
    
    def destroy(self):
        """Limpiar al destruir"""
        if self._reloj_after:
            try: self.after_cancel(self._reloj_after)
            except: pass
        
        if self._monitor_turno_after:
            try: self.after_cancel(self._monitor_turno_after)
            except: pass
        
        super().destroy()
    
    def marcar_faltas_masivas(self):
        """Cerrar día y marcar faltas automáticas"""
        if messagebox.askyesno(
            "Confirmar", 
            "¿Cerrar el día y marcar faltas a todos los que no vinieron?"
        ):
            self.lbl_loader.pack(side="right")
            
            def proceso():
                self.controller.marcar_inasistencias_automaticas()
                if self.winfo_exists():
                    self.after(0, self.cargar_tabla_thread)
            
            threading.Thread(target=proceso, daemon=True).start()
            messagebox.showinfo("Procesando", "Se está cerrando el día en segundo plano...")
    
    def accion_eliminar(self):
        """Eliminar registro seleccionado"""
        if not self.datos_seleccionados:
            messagebox.showwarning("Atención", "Seleccione un registro.")
            return
        
        id_asistencia, nombre = self.datos_seleccionados
        
        if id_asistencia in (None, "NEW"):
            messagebox.showwarning("Atención", "El registro aún no está sincronizado.")
            return
        
        if messagebox.askyesno("Eliminar", f"¿Eliminar asistencia de:\n{nombre}?"):
            exito, mensaje = self.controller.eliminar_asistencia(id_asistencia)
            
            if exito:
                self.fila_seleccionada.destroy()
                self.datos_seleccionados = None
            else:
                messagebox.showerror("Error", mensaje)
    
    def accion_marcar_falta(self):
        """Marcar falta manual"""
        messagebox.showinfo(
            "Info", 
            "Use el buscador para seleccionar un alumno y registrar falta manualmente."
        )

    def _obtener_texto_boton_cierre(self):
        """Detecta qué turno corresponde cerrar según la hora"""
        from datetime import datetime, time as dt_time
        
        hora_actual = datetime.now().time()
        
        if hora_actual < dt_time(12, 0, 0):
            return "🌅 CERRAR TURNO MAÑANA"
        else:
            return "🌆 CERRAR TURNO TARDE"

    def actualizar_boton_cierre(self):
        """Actualiza el texto del botón cada minuto"""
        if not self.winfo_exists(): return
        # Verificar estado de cierre
        estado = self.controller.obtener_estado_cierre_hoy()
        
        from datetime import datetime, time as dt_time
        hora_actual = datetime.now().time()
        
        if hora_actual < dt_time(12, 0, 0):
            # Turno mañana
            if estado["manana_cerrado"]:
                self.btn_cierre.configure(
                    text=f"✅ TURNO MAÑANA CERRADO ({estado['manana_cantidad']})",
                    fg_color="#27ae60",
                    
                )
            else:
                self.btn_cierre.configure(
                    text="🌅 CERRAR TURNO MAÑANA",
                    fg_color="#2c3e50",
                    state="normal"
                )
        else:
            # Turno tarde
            if estado["tarde_cerrado"]:
                self.btn_cierre.configure(
                    text=f"✅ TURNO TARDE CERRADO ({estado['tarde_cantidad']})",
                    fg_color="#27ae60",
                    
                )
            else:
                self.btn_cierre.configure(
                    text="🌆 CERRAR TURNO TARDE",
                    fg_color="#2c3e50",
                    state="normal"
                )
        
        # Repetir cada 60 segundos
        self.after(60000, self.actualizar_boton_cierre)

    def abrir_dialogo_cierre(self):
        """Abre diálogo de confirmación de cierre"""
        
        # Bloquear botón temporalmente
        self.btn_cierre.configure(state="disabled", text="⏳ Procesando...")
        
        # Obtener resumen (sin marcar aún)
        exito, mensaje, resumen = self.controller.marcar_inasistencias_automaticas()
        
        if not exito:
            # Error
            self.btn_cierre.configure(state="normal", text=self._obtener_texto_boton_cierre())
            messagebox.showerror("Error", mensaje)
            return
        
        if mensaje == "REQUIERE_CONFIRMACION":
            # Mostrar diálogo
            dialogo = DialogoCierreTurno(self, resumen)
            self.wait_window(dialogo)
            
            if dialogo.confirmado:
                # Usuario confirmó → Ejecutar marcado
                exito_final, mensaje_final = self.controller.confirmar_cierre_turno(resumen)
                
                if exito_final:
                    messagebox.showinfo("✅ Éxito", mensaje_final)
                    self.cargar_tabla_thread()  # Recargar tabla
                    self.actualizar_boton_cierre()  # Actualizar estado del botón
                else:
                    messagebox.showerror("Error", mensaje_final)
            
            # Restaurar botón
            self.btn_cierre.configure(state="normal", text=self._obtener_texto_boton_cierre())
        
        else:
            # Ya estaba cerrado o sin alumnos
            self.btn_cierre.configure(state="normal", text=self._obtener_texto_boton_cierre())
            messagebox.showinfo("Información", mensaje)
            self.actualizar_boton_cierre()




# _hook_scroll








