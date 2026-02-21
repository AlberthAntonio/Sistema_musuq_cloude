"""

Vista de Gestión de Justificaciones - ESTILO MEJORADO

Sistema Musuq Cloud

"""

import customtkinter as ctk
from tkinter import messagebox
import threading
from datetime import datetime

# --- CONTROLLER Y ESTILOS ---
from controllers.asistencia_controller import AsistenciaController
from styles import tabla_style as st
from core.theme_manager import ThemeManager as TM
from .dialogo_justificacion import DialogoJustificacion


class JustificarView(ctk.CTkFrame):
    """Vista para gestionar justificaciones de asistencia con diseño mejorado"""

    def __init__(self, parent, auth_client):
        super().__init__(parent, fg_color="transparent")
        self.controller = AsistenciaController(auth_client.token)
        self.alumno_seleccionado_id = None

        # Variables para manejo de selección
        self.fila_seleccionada = None
        self.datos_seleccionados = None
        self.color_original_seleccion = None
        self.buscando = False
        self.historial_cache = []
        self.registros_cargados = 0
        self.lote_tamano = 20
        self.cargando_mas = False

        # Anchos fijos para la tabla: [FECHA, HORA, TURNO, ESTADO, OBSERVACION]
        self.ANCHOS = [100, 100, 100, 150, 250]

        # Layout Principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.create_widgets()

    def create_widgets(self):
        # =================================================
        # 1. TÍTULO SUPERIOR (MEJORADO)
        # =================================================
        self.fr_top = ctk.CTkFrame(self, fg_color="transparent")
        self.fr_top.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 15))

        ctk.CTkLabel(
            self.fr_top,
            text="📋 GESTIÓN DE JUSTIFICACIONES",
            font=ctk.CTkFont(family="Roboto", size=20, weight="bold"),
            text_color=TM.text()
        ).pack(anchor="w")

        ctk.CTkLabel(
            self.fr_top,
            text="Busque al alumno para ver su historial completo",
            font=ctk.CTkFont(family="Roboto", size=12),
            text_color=TM.text_secondary()
        ).pack(anchor="w")

        # =================================================
        # 2. ÁREA DE CONTROL (RESPONSIVE) - MEJORADA
        # =================================================
        self.fr_cabecera_global = ctk.CTkFrame(self, fg_color="transparent")
        self.fr_cabecera_global.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 15))

        # --- TARJETA PERFIL (Derecha - con mejor diseño) ---
        self.card_perfil = ctk.CTkFrame(
            self.fr_cabecera_global,
            fg_color=TM.bg_card(),
            corner_radius=15,
            height=120,
            width=450
        )
        self.card_perfil.pack(side="right", anchor="ne", padx=(10, 0))
        self.card_perfil.pack_propagate(False)

        # Icono mejorado
        fr_icon_id = ctk.CTkFrame(
            self.card_perfil,
            fg_color=TM.bg_panel(),
            width=80,
            corner_radius=15
        )
        fr_icon_id.pack(side="left", fill="y", padx=10, pady=10)
        ctk.CTkLabel(
            fr_icon_id,
            text="👤",
            font=ctk.CTkFont(family="Arial", size=40)
        ).place(relx=0.5, rely=0.5, anchor="center")

        fr_info_card = ctk.CTkFrame(self.card_perfil, fg_color="transparent")
        fr_info_card.pack(side="left", fill="both", expand=True, pady=10, padx=5)

        self.lbl_card_nombre = ctk.CTkLabel(
            fr_info_card,
            text="SELECCIONE UN ALUMNO",
            font=ctk.CTkFont(family="Roboto", size=16, weight="bold"),
            text_color=TM.text(),
            anchor="w"
        )
        self.lbl_card_nombre.pack(anchor="w", pady=(5, 0))

        self.lbl_card_detalle = ctk.CTkLabel(
            fr_info_card,
            text="Visualice el historial completo de asistencia",
            font=ctk.CTkFont(family="Roboto", size=12),
            text_color=TM.text_secondary(),
            anchor="w"
        )
        self.lbl_card_detalle.pack(anchor="w")

        # Tags de info extra
        self.fr_tags = ctk.CTkFrame(fr_info_card, fg_color="transparent", height=30)
        self.fr_tags.pack(anchor="w", pady=(5, 0), fill="x")

        # --- BUSCADOR (Izquierda - Mejorado) ---
        self.fr_bloque_izq = ctk.CTkFrame(self.fr_cabecera_global, fg_color="transparent")
        self.fr_bloque_izq.pack(side="left", fill="x", expand=True, anchor="nw")

        # Caja de Búsqueda mejorada (estilo alumnos_list)
        self.fr_search_box = ctk.CTkFrame(
            self.fr_bloque_izq,
            height=50,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.fr_search_box.pack(side="top", fill="x", expand=True)
        self.fr_search_box.pack_propagate(False)

        ctk.CTkLabel(
            self.fr_search_box,
            text="🔍",
            font=ctk.CTkFont(family="Arial", size=14),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(15, 5))

        self.entry_busqueda = ctk.CTkEntry(
            self.fr_search_box,
            placeholder_text="Buscar por nombre, código o DNI...",
            height=35,
            border_width=0,
            fg_color=TM.bg_panel(),
            text_color=TM.text(),
            corner_radius=8
        )
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=5, pady=8)
        self.entry_busqueda.bind("<KeyRelease>", self.evento_buscar)

        # Wrapper de Sugerencias
        self.wrapper_sugerencias = ctk.CTkFrame(
            self.fr_bloque_izq,
            fg_color="transparent",
            height=110
        )
        self.wrapper_sugerencias.pack(side="top", fill="x", pady=(5, 0))
        self.wrapper_sugerencias.pack_propagate(False)

        self.fr_resultados = ctk.CTkScrollableFrame(
            self.wrapper_sugerencias,
            fg_color=TM.bg_card()
        )
        self.fr_resultados.pack(fill="both", expand=True)

        # =================================================
        # 3. TABLA DE HISTORIAL (MEJORADA)
        # =================================================
        self.fr_tabla = ctk.CTkFrame(self, fg_color="transparent")
        self.fr_tabla.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))

        self.container_list = ctk.CTkFrame(
            self.fr_tabla,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.container_list.pack(fill="both", expand=True)

        self.crear_cabecera()

        self.scroll_tabla = ctk.CTkScrollableFrame(
            self.container_list,
            fg_color="transparent"
        )
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)

        # Hook del scroll para carga infinita
        self.scroll_tabla._parent_canvas.configure(yscrollcommand=self._hook_scroll)

        # Mensaje inicial mejorado
        ctk.CTkLabel(
            self.scroll_tabla,
            text="🔍",
            text_color=TM.text(),
            font=ctk.CTkFont(family="Roboto", size=40)
        ).pack(pady=(20, 0))

        self.lbl_mensaje_tabla = ctk.CTkLabel(
            self.scroll_tabla,
            text="\nUse el buscador de arriba para comenzar",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(family="Roboto", size=16)
        )
        self.lbl_mensaje_tabla.pack()

        # Label de cargando más
        self.lbl_cargando_mas = ctk.CTkLabel(
            self.scroll_tabla,
            text="⏳ Cargando más registros...",
            text_color=TM.primary(),
            font=ctk.CTkFont(family="Roboto", size=10, slant="italic")
        )

        # =================================================
        # 4. PANEL DE ACCIONES (MEJORADO)
        # =================================================
        self.fr_acciones = ctk.CTkFrame(
            self,
            fg_color=TM.bg_card(),
            height=60,
            corner_radius=10
        )
        self.fr_acciones.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))

        ctk.CTkLabel(
            self.fr_acciones,
            text="ℹ️ Seleccione una inasistencia para justificar:",
            font=ctk.CTkFont(family="Roboto", size=13),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=20)

        self.btn_justificar = ctk.CTkButton(
            self.fr_acciones,
            text="📝 JUSTIFICAR SELECCIONADO",
            fg_color=st.Colors.TARDANZA,
            hover_color="#d35400",
            font=ctk.CTkFont(family="Roboto", size=13, weight="bold"),
            height=40,
            state="disabled",
            text_color=TM.text_secondary(),
            command=self.accion_justificar
        )
        self.btn_justificar.pack(side="right", padx=20, pady=10)
        self._debounce_timer = None  # Timer para debounce

    # ... (rest of __init__ remains, skipping to evento_buscar)

    # ============================================================
    # THREADING - BÚSQUEDA DE ALUMNOS
    # ============================================================

    def evento_buscar(self, event=None):
        """Evento de búsqueda con debounce (retraso)"""
        # Cancelar timer anterior si existe
        if self._debounce_timer:
            self.after_cancel(self._debounce_timer)
        
        # Programar nueva búsqueda en 500ms
        self._debounce_timer = self.after(500, self._ejecutar_busqueda)

    def _ejecutar_busqueda(self):
        """Ejecuta la búsqueda real después del debounce"""
        texto = self.entry_busqueda.get().strip()

        # Limpiar visualmente antes de buscar
        for w in self.fr_resultados.winfo_children():
            w.destroy()

        # Ocultar sugerencias si está vacío
        if not texto:
            return

        # Loader pequeño
        lbl_load = ctk.CTkLabel(
            self.fr_resultados,
            text="⏳ Buscando...",
            text_color=TM.warning()
        )
        lbl_load.pack(pady=5)

        # Lanzar hilo
        threading.Thread(
            target=self._thread_buscar_alumnos,
            args=(texto,),
            daemon=True
        ).start()

    def _thread_buscar_alumnos(self, texto):
        """Worker Thread - Búsqueda en Controlador"""
        try:
            resultados = self.controller.buscar_alumnos_general(texto)
            data_safe = []

            for alum in resultados:
                nombre = alum.get("nombre_completo")
                if not nombre:
                    nombre = f"{alum.get('apell_paterno', '')} {alum.get('apell_materno', '')}, {alum.get('nombres', '')}".strip()

                data_safe.append({
                    "id": alum.get("id"),
                    "nombre_completo": nombre,
                    "codigo": alum.get("codigo_matricula"),
                    "dni": alum.get("dni")
                })
        except Exception as e:
            print(f"Error búsqueda: {e}")
            data_safe = []

        # Actualizar UI en el hilo principal
        self.after(0, lambda: self._mostrar_sugerencias(data_safe))

    def _mostrar_sugerencias(self, datos):
        """Main Thread - Mostrar resultados de búsqueda"""
        # Limpiar loader
        for w in self.fr_resultados.winfo_children():
            w.destroy()

        if not datos:
            ctk.CTkLabel(
                self.fr_resultados,
                text="Sin resultados",
                text_color=TM.text_secondary()
            ).pack(pady=5)
            return

        for d in datos:
            texto_btn = f"👤 ({d['codigo']}) | {d['nombre_completo']}"

            btn = ctk.CTkButton(
                self.fr_resultados,
                text=texto_btn,
                anchor="w",
                fg_color="transparent",
                text_color=TM.text(),
                hover_color=st.Colors.HOVER,
                height=35,
                command=lambda x=d: self.seleccionar_alumno(x)
            )
            btn.pack(fill="x", pady=1, padx=5)

    def _hook_scroll(self, first, last):
        """
        Hook del scrollbar para detectar cuando llega al final
        y cargar más registros automáticamente
        """
        # 1. Actualizar scrollbar visualmente
        try:
            self.scroll_tabla._scrollbar.set(first, last)
        except:
            pass

        # 2. Validaciones
        if self.cargando_mas:
            return
        if not hasattr(self, 'historial_cache'):
            return
        if not self.historial_cache:
            return

        # 3. Detectar si llegamos al 90% del scroll
        try:
            posicion_actual = float(last)

            if (posicion_actual >= 0.90 and
                    self.registros_cargados < len(self.historial_cache)):
                self.cargando_mas = True

                # Mostrar indicador
                try:
                    if self.lbl_cargando_mas.winfo_exists():
                        self.lbl_cargando_mas.pack(pady=10)
                except:
                    pass

                # Cargar siguiente lote con delay
                self.after(200, self._renderizar_siguiente_lote)
        except Exception as e:
            if "bad window path" not in str(e):
                print(f"Error en _hook_scroll: {e}")
            self.cargando_mas = False

    # ============================================================
    # THREADING - CARGA DE HISTORIAL
    # ============================================================

    def seleccionar_alumno(self, alumno_data):
        """Se activa al hacer clic en un alumno de la búsqueda"""
        self.historial_cache = []
        self.registros_cargados = 0
        self.cargando_mas = False
        self.alumno_seleccionado_id = alumno_data["id"]

        # 1. Actualizar Tarjeta de Perfil
        self.lbl_card_nombre.configure(text=alumno_data["nombre_completo"].upper())
        self.lbl_card_detalle.configure(text=f"CÓDIGO: {alumno_data['codigo']}")

        # Limpiar tags previos
        for w in self.fr_tags.winfo_children():
            w.destroy()

        # Crear tags mejorados
        def add_tag(txt, col):
            f = ctk.CTkFrame(self.fr_tags, fg_color=col, corner_radius=5)
            f.pack(side="left", padx=(0, 5))
            ctk.CTkLabel(
                f,
                text=txt,
                font=ctk.CTkFont(family="Roboto", size=10, weight="bold"),
                text_color="white"
            ).pack(padx=8, pady=2)

        add_tag(f"DNI: {alumno_data['dni']}", TM.bg_panel())
        add_tag("ALUMNO ACTIVO", TM.success())

        # 2. Limpiar buscador
        for w in self.fr_resultados.winfo_children():
            w.destroy()
        self.entry_busqueda.delete(0, "end")

        # 3. Preparar tabla para carga
        for w in self.scroll_tabla.winfo_children():
            w.destroy()

        try:
            self.fr_resultados._parent_canvas.yview_moveto(0.0)
            self.scroll_tabla._parent_canvas.yview_moveto(0.0)
        except Exception:
            pass # Ignorar errores de canvas si la librería cambió

        # Mostrar Loader grande en la tabla
        self.lbl_loader_tabla = ctk.CTkLabel(
            self.scroll_tabla,
            text="\n⏳ Cargando historial de asistencia...",
            font=ctk.CTkFont(family="Roboto", size=16),
            text_color=TM.warning()
        )
        self.lbl_loader_tabla.pack()
        self.update_idletasks()

        # 4. Lanzar Hilo
        threading.Thread(
            target=self._thread_cargar_historial,
            args=(alumno_data["id"],),
            daemon=True
        ).start()

    def _thread_cargar_historial(self, alumno_id):
        """Worker Thread - Cargar historial"""
        try:
            historial = self.controller.obtener_historial_alumno(alumno_id)
        except Exception as e:
            print(f"Error historial: {e}")
            historial = []

        self.after(0, lambda: self._mostrar_historial_ui(historial))

    def _mostrar_historial_ui(self, historial):
        """Main Thread - Renderizar historial en la tabla CON SCROLL INFINITO"""
        # Limpiar tabla
        for widget in self.scroll_tabla.winfo_children():
            widget.destroy()

        if hasattr(self, "lbl_loader_tabla"):
            self.lbl_loader_tabla.destroy()

        # Resetear selección y variables de scroll
        self.btn_justificar.configure(
            state="disabled",
            fg_color=TM.bg_panel(),
            text_color=TM.text_secondary()
        )
        self.fila_seleccionada = None
        self.datos_seleccionados = None

        # Inicializar scroll infinito
        self.historial_cache = historial
        self.registros_cargados = 0
        self.cargando_mas = False

        # Caso sin registros
        if not historial:
            ctk.CTkLabel(
                self.scroll_tabla,
                text="\n📭",
                text_color=TM.text(),
                font=ctk.CTkFont(family="Roboto", size=40)
            ).pack()

            ctk.CTkLabel(
                self.scroll_tabla,
                text="\n✅ El alumno no tiene registros de asistencia.",
                text_color=TM.text_secondary(),
                font=ctk.CTkFont(family="Roboto", size=14)
            ).pack()
            return

        # Cargar primer lote
        self._renderizar_siguiente_lote()

    def _renderizar_siguiente_lote(self):
        """Renderiza el siguiente grupo de N registros"""
        # Calcular rango del lote actual
        inicio = self.registros_cargados
        fin = inicio + self.lote_tamano

        # Extraer lote
        lote = self.historial_cache[inicio:fin]

        # Renderizar cada registro
        for item in lote:
            index_global = self.registros_cargados
            self._crear_fila_asistencia_optimizada(item, index_global)
            self.registros_cargados += 1

        # Ocultar indicador
        try:
            self.lbl_cargando_mas.pack_forget()
        except:
            pass

        # Liberar lock
        self.cargando_mas = False

        print(f"📊 Cargados: {self.registros_cargados} de {len(self.historial_cache)}")

    # ============================================================
    # MÉTODOS VISUALES - TABLA
    # ============================================================

    def crear_cabecera(self):
        """Crea la cabecera de la tabla con diseño mejorado"""
        header = ctk.CTkFrame(
            self.container_list,
            height=40,
            fg_color=st.Colors.TABLE_HEADER,
            corner_radius=5
        )
        header.pack(fill="x", padx=5, pady=(5, 0))

        titulos = ["FECHA", "HORA", "TURNO", "ESTADO", "OBSERVACIÓN"]

        for i, t in enumerate(titulos):
            ctk.CTkLabel(
                header,
                text=t,
                font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
                text_color="white",
                width=self.ANCHOS[i]
            ).pack(side="left", padx=2)

    def _crear_fila_asistencia_optimizada(self, datos, index_global):
        """Crea una fila optimizada para scroll infinito con diseño mejorado"""
        # Colores mejorados (estilo alumnos_list)
        bg = "#2d2d2d" if index_global % 2 == 0 else "#363636"

        # Frame de la fila
        row = ctk.CTkFrame(
            self.scroll_tabla,
            fg_color=bg,
            corner_radius=5,
            height=35
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        # Datos para selección
        datos_seleccion = (datos["id"], datos["fecha"], datos["estado"])

        # --- EVENTOS DE INTERACCIÓN ---
        def on_click(event, widget=row, data=datos_seleccion, bg_orig=bg):
            self.seleccionar_fila_visual(widget, data, bg_orig)

        def on_enter(event, widget=row):
            if self.fila_seleccionada != widget:
                widget.configure(fg_color="#3a3a3a")

        def on_leave(event, widget=row, bg_orig=bg):
            if self.fila_seleccionada != widget:
                widget.configure(fg_color=bg_orig)

        row.bind("<Button-1>", on_click)
        row.bind("<Enter>", on_enter)
        row.bind("<Leave>", on_leave)

        # --- CELDAS ---
        font_celda = ctk.CTkFont(family="Roboto", size=11)

        def crear_celda(parent, txt, w, col=None, anchor="center", bg_badge=None):
            """Helper para crear celdas con o sin badge"""
            if col is None:
                col = TM.text()

            if bg_badge:
                f = ctk.CTkFrame(parent, fg_color="transparent", width=w, height=30)
                f.pack(side="left", padx=2)
                f.pack_propagate(False)

                lbl = ctk.CTkLabel(
                    f,
                    text=txt,
                    fg_color=bg_badge,
                    text_color="white",
                    corner_radius=5,
                    width=120,
                    height=22,
                    font=ctk.CTkFont(family="Roboto", size=11, weight="bold")
                )
                lbl.place(relx=0.5, rely=0.5, anchor="center")

                # Propagar eventos
                lbl.bind("<Button-1>", on_click)
                lbl.bind("<Enter>", on_enter)
                lbl.bind("<Leave>", on_leave)
                f.bind("<Button-1>", on_click)
                f.bind("<Enter>", on_enter)
                f.bind("<Leave>", on_leave)
            else:
                lbl = ctk.CTkLabel(
                    parent,
                    text=txt,
                    width=w,
                    text_color=col,
                    font=font_celda,
                    anchor=anchor
                )
                lbl.pack(side="left", padx=2, fill="y")
                lbl.bind("<Button-1>", on_click)
                lbl.bind("<Enter>", on_enter)
                lbl.bind("<Leave>", on_leave)

        # Crear celdas
        crear_celda(row, datos.get("fecha", ""), self.ANCHOS[0], TM.text())
        crear_celda(row, datos.get("hora", ""), self.ANCHOS[1], TM.text_secondary())
        crear_celda(row, datos.get("turno", ""), self.ANCHOS[2], TM.text_secondary())

        # Estado con color
        estado = datos.get("estado", "")
        bg_estado = TM.bg_panel()

        if "PUNTUAL" in estado:
            bg_estado = st.Colors.PUNTUAL
        elif "TARDANZA" in estado:
            bg_estado = st.Colors.TARDANZA
        elif "INASISTENCIA" in estado or "FALTA" in estado:
            bg_estado = st.Colors.FALTA
        elif "JUSTIFICADO" in estado:
            bg_estado = st.Colors.ASISTENCIA

        crear_celda(row, estado, self.ANCHOS[3], bg_badge=bg_estado)
        crear_celda(row, datos.get("observacion", ""), self.ANCHOS[4], TM.text_secondary(), "w")

    def seleccionar_fila_visual(self, widget_fila, datos, bg_original):
        """Maneja la selección visual de una fila"""
        # Restaurar fila anterior
        if self.fila_seleccionada and self.fila_seleccionada.winfo_exists():
            try:
                self.fila_seleccionada.configure(fg_color=self.color_original_seleccion)
            except:
                pass

        # Guardar nueva selección
        self.fila_seleccionada = widget_fila
        self.datos_seleccionados = datos
        self.color_original_seleccion = bg_original

        # Resaltar fila seleccionada (color consistente con otros archivos)
        widget_fila.configure(fg_color="#34495e")

        # Habilitar botón según el estado
        id_asistencia, fecha, estado = datos

        if "JUSTIFICADO" in estado:
            self.btn_justificar.configure(
                state="disabled",
                text="✅ YA JUSTIFICADO",
                fg_color=TM.bg_panel(),
                text_color=TM.text_secondary()
            )
        else:
            self.btn_justificar.configure(
                state="normal",
                text=f"📝 JUSTIFICAR (ID: {id_asistencia})",
                fg_color=st.Colors.TARDANZA,
                text_color="white"
            )

    # ============================================================
    # ACCIÓN DE JUSTIFICACIÓN
    # ============================================================

    def accion_justificar(self):
        """Abre diálogo para justificar la asistencia seleccionada"""
        if not self.datos_seleccionados:
            return

        # Usar el nuevo diálogo personalizado
        dialog = DialogoJustificacion(
            self.winfo_toplevel(),
            self.datos_seleccionados,
            on_confirm=self._procesar_justificacion
        )

    def _procesar_justificacion(self, motivo):
        """Procesar la justificación"""
        id_asistencia, fecha, estado = self.datos_seleccionados

        # Llamar al controller
        exito, msg = self.controller.justificar_asistencia(id_asistencia, motivo)

        if exito:
            messagebox.showinfo("Éxito", "Justificación aplicada correctamente.")

            # Recargar historial
            if self.alumno_seleccionado_id:
                threading.Thread(
                    target=self._thread_cargar_historial,
                    args=(self.alumno_seleccionado_id,),
                    daemon=True
                ).start()
        else:
            messagebox.showerror("Error", msg)
