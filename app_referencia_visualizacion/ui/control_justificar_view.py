import customtkinter as ctk
from tkinter import messagebox
import threading
from datetime import datetime

# --- IMPORTACIONES DE BASE DE DATOS Y MODELOS ---
from app.database import SessionLocal
from app.models.alumno_model import Alumno
from app.models.asistencia_model import Asistencia
from sqlalchemy import or_, desc

# --- CONTROLLER Y ESTILOS ---
from app.controllers.asistencia_controller import AsistenciaController
import app.styles.tabla_style as st
import app.utils.components_ui as ui

class JustificarView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.controller = AsistenciaController()
        self.alumno_seleccionado_id = None 
        
        # Variables para manejo de selección
        self.fila_seleccionada = None   
        self.datos_seleccionados = None 
        self.color_original_seleccion = None 
        self.buscando = False  # Semáforo para hilos

        self.historial_cache = []  # Todos los registros en memoria
        self.registros_cargados = 0  # Cuántos se están mostrando
        self.lote_tamano = 20  # Cargar de 20 en 20
        self.cargando_mas = False  # Lock para evitar cargas múltiples

        # Configuración Visual
        self.configure(fg_color=st.Colors.BG_MAIN)
        
        # Anchos fijos para la tabla: [FECHA, HORA, TURNO, ESTADO, OBSERVACION]
        self.ANCHOS = [100, 100, 100, 150, 250]

        # Layout Principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # =================================================
        # 1. TÍTULO SUPERIOR
        # =================================================
        self.fr_top = ctk.CTkFrame(self, fg_color="transparent")
        self.fr_top.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        
        ctk.CTkLabel(self.fr_top, text="GESTIÓN DE JUSTIFICACIONES", 
                     font=st.Fonts.TITLE, text_color="white").pack(anchor="w")
        ctk.CTkLabel(self.fr_top, text="Busque al alumno para ver su historial completo.", 
                     font=("Roboto", 12), text_color="gray").pack(anchor="w")

        # =================================================
        # 2. ÁREA DE CONTROL (RESPONSIVE)
        # =================================================
        self.fr_cabecera_global = ctk.CTkFrame(self, fg_color="transparent")
        self.fr_cabecera_global.grid(row=1, column=0, sticky="ew", padx=(20, 20), pady=(0, 10))

        # --- TARJETA PERFIL (Derecha - Empaquetada primero) ---
        self.card_perfil = ctk.CTkFrame(self.fr_cabecera_global, fg_color="#2c3e50", 
                                        corner_radius=15, height=160, width=400) 
        self.card_perfil.pack(side="right", anchor="ne", padx=(5, 0))
        self.card_perfil.pack_propagate(False)

        ctk.CTkLabel(self.card_perfil, text="👤", font=("Arial", 40)).pack(side="left", padx=20)

        fr_info_card = ctk.CTkFrame(self.card_perfil, fg_color="transparent")
        fr_info_card.pack(side="left", anchor="center", pady=10)

        self.lbl_card_nombre = ctk.CTkLabel(fr_info_card, text="Seleccione un alumno", 
                                            font=("Roboto", 18, "bold"), text_color="white", anchor="w")
        self.lbl_card_nombre.pack(anchor="w")

        self.lbl_card_detalle = ctk.CTkLabel(fr_info_card, text="Historial de asistencias", 
                                             font=("Roboto", 12), text_color="silver", anchor="w")
        self.lbl_card_detalle.pack(anchor="w")

        # --- BUSCADOR (Izquierda - Con expand) ---
        self.fr_bloque_izq = ctk.CTkFrame(self.fr_cabecera_global, fg_color="transparent")
        self.fr_bloque_izq.pack(side="left", fill="x", expand=True, anchor="nw")

        # Caja de Búsqueda (responsive)
        self.fr_search_box = ctk.CTkFrame(self.fr_bloque_izq, fg_color=st.Colors.BG_PANEL, 
                                          corner_radius=10, height=50)
        self.fr_search_box.pack(side="top", fill="x", expand=True) 
        self.fr_search_box.pack_propagate(False)

        ctk.CTkLabel(self.fr_search_box, text="🔍", font=("Arial", 14), 
                     text_color="gray").pack(side="left", padx=(15, 5))

        self.box_input = ctk.CTkFrame(self.fr_search_box, fg_color="#404040", 
                                      corner_radius=20, height=35)
        self.box_input.pack(side="left", fill="x", expand=True, padx=10, pady=7) 
        self.box_input.pack_propagate(False)

        self.entry_busqueda = ctk.CTkEntry(self.box_input, 
                                           placeholder_text="Escriba nombre o código...", 
                                           height=35, border_width=0, 
                                           fg_color="transparent", text_color="white")
        self.entry_busqueda.pack(side="left", fill="both", expand=True, padx=10)
        self.entry_busqueda.bind("<KeyRelease>", self.evento_buscar)

        # Wrapper de Sugerencias (Ahora visible desde el inicio)
        self.wrapper_sugerencias = ctk.CTkFrame(self.fr_bloque_izq, fg_color="transparent", height=110)
        self.wrapper_sugerencias.pack(side="top", fill="x", pady=(2, 0))
        self.wrapper_sugerencias.pack_propagate(False)
        
        self.fr_resultados = ctk.CTkScrollableFrame(self.wrapper_sugerencias, 
                                                    fg_color=st.Colors.BG_PANEL)
        self.fr_resultados.pack(fill="both", expand=True)
        
        # =================================================
        # 3. TABLA DE HISTORIAL
        # =================================================
        self.fr_tabla = ctk.CTkFrame(self, fg_color="transparent")
        self.fr_tabla.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0,5))
        
        self.container_list = ctk.CTkFrame(self.fr_tabla, fg_color=st.Colors.BG_PANEL, corner_radius=10)
        self.container_list.pack(fill="both", expand=True)

        self.crear_cabecera()

        self.scroll_tabla = ctk.CTkScrollableFrame(self.container_list, fg_color="transparent")
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)

        # ===== AGREGAR HOOK DEL SCROLL =====
        self.scroll_tabla._parent_canvas.configure(yscrollcommand=self._hook_scroll)
        # ===================================

        # Mensaje inicial
        ctk.CTkLabel(self.scroll_tabla, text="\n👋", text_color="white", 
                    font=("Roboto", 40)).pack()
        self.lbl_mensaje_tabla = ctk.CTkLabel(self.scroll_tabla, 
                                            text="\nUse el buscador de arriba para comenzar",
                                            text_color="gray", font=("Roboto", 16))
        self.lbl_mensaje_tabla.pack()

        # ===== AGREGAR LABEL DE CARGANDO MÁS =====
        self.lbl_cargando_mas = ctk.CTkLabel(
            self.scroll_tabla,
            text="⏳ Cargando más registros...",
            text_color="#3498db",
            font=("Roboto", 10, "italic")
        )

        # =================================================
        # 4. PANEL DE ACCIONES
        # =================================================
        self.fr_acciones = ctk.CTkFrame(self, fg_color=st.Colors.BG_PANEL, 
                                        height=60, corner_radius=10)
        self.fr_acciones.grid(row=3, column=0, sticky="ew", padx=20, pady=(0,10))
        
        ctk.CTkLabel(self.fr_acciones, 
                     text="ℹ️ Seleccione una inasistencia para justificar:", 
                     font=("Roboto", 13), text_color="gray").pack(side="left", padx=20)
        
        self.btn_justificar = ctk.CTkButton(self.fr_acciones, 
                                            text="📝 JUSTIFICAR SELECCIONADO", 
                                            fg_color=st.Colors.TARDANZA, 
                                            hover_color="#d35400",
                                            font=("Roboto", 13, "bold"), 
                                            height=40,
                                            state="disabled", 
                                            text_color="#404040",
                                            command=self.accion_justificar)
        self.btn_justificar.pack(side="right", padx=20, pady=10)

    # ============================================================
    #              THREADING - BÚSQUEDA DE ALUMNOS
    # ============================================================

    def evento_buscar(self, event=None):
        """Evento de búsqueda con threading."""
        texto = self.entry_busqueda.get().strip()
        
        # Limpiar visualmente antes de buscar
        for w in self.fr_resultados.winfo_children():
            w.destroy()
        
        # Ocultar sugerencias si está vacío
        if not texto:
            return
        
        # Loader pequeño
        lbl_load = ctk.CTkLabel(self.fr_resultados, text="⏳ Buscando...", 
                                text_color="#f1c40f")
        lbl_load.pack(pady=5)
        
        # Lanzar hilo
        threading.Thread(target=self._thread_buscar_alumnos, 
                        args=(texto,), daemon=True).start()

    def _thread_buscar_alumnos(self, texto):
        """Worker Thread - Búsqueda en BD."""
        session_temp = SessionLocal()
        data_safe = []
        try:
            busqueda = f"%{texto}%"
            resultados = session_temp.query(Alumno).filter(
                or_(
                    Alumno.apell_paterno.ilike(busqueda),
                    Alumno.apell_materno.ilike(busqueda),
                    Alumno.nombres.ilike(busqueda),
                    Alumno.codigo_matricula.ilike(busqueda)
                )
            ).limit(10).all()

            # Extraer datos primitivos para evitar problemas de sesión cerrada
            for alum in resultados:
                data_safe.append({
                    "id": alum.id,
                    "nombre_completo": f"{alum.apell_paterno} {alum.apell_materno}, {alum.nombres}",
                    "codigo": alum.codigo_matricula
                })
        except Exception as e:
            print(f"Error búsqueda: {e}")
        finally:
            session_temp.close()

        # Actualizar UI en el hilo principal
        self.after(0, lambda: self._mostrar_sugerencias(data_safe))

    def _mostrar_sugerencias(self, datos):
        """Main Thread - Mostrar resultados de búsqueda."""
        # Limpiar loader
        for w in self.fr_resultados.winfo_children():
            w.destroy()

        if not datos:
            ctk.CTkLabel(self.fr_resultados, text="Sin resultados", 
                        text_color="gray").pack(pady=5)
            return

        for d in datos:
            texto_btn = f"({d['codigo']})  |  {d['nombre_completo']}"
            btn = ctk.CTkButton(self.fr_resultados, 
                                text=texto_btn, 
                                anchor="w", 
                                fg_color="transparent", 
                                text_color="silver", 
                                hover_color="#404040", 
                                height=30,
                                command=lambda x=d: self.seleccionar_alumno(x))
            btn.pack(fill="x", pady=1)

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
            
            # Si estamos al 90% Y hay más registros por cargar
            if (posicion_actual >= 0.90 and 
                self.registros_cargados < len(self.historial_cache)):
                
                # Activar lock
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
    #              THREADING - CARGA DE HISTORIAL
    # ============================================================

    def seleccionar_alumno(self, alumno_data):
        """Se activa al hacer clic en un alumno de la búsqueda."""
        self.alumno_seleccionado_id = alumno_data["id"]
        
        # 1. Actualizar Tarjeta de Perfil
        self.lbl_card_nombre.configure(text=alumno_data["nombre_completo"])
        self.lbl_card_detalle.configure(
            text=f"CÓDIGO: {alumno_data['codigo']}  |  Visualizando historial completo"
        )
        
        # 2. Limpiar buscador
        for w in self.fr_resultados.winfo_children():
            w.destroy()
        self.entry_busqueda.delete(0, "end")
        

        # 3. Preparar tabla para carga
        for w in self.scroll_tabla.winfo_children():
            w.destroy()
        
        self.fr_resultados._parent_canvas.yview_moveto(0.0)
        self.scroll_tabla._parent_canvas.yview_moveto(0.0)

        # Mostrar Loader grande en la tabla
        self.lbl_loader_tabla = ctk.CTkLabel(
            self.scroll_tabla, 
            text="\n⏳ Cargando historial de asistencia...", 
            font=("Roboto", 16), 
            text_color="#f39c12"
        )
        self.lbl_loader_tabla.pack()
        self.update_idletasks()  # Forzar pintado

        # 4. Lanzar Hilo
        threading.Thread(target=self._thread_cargar_historial, 
                        args=(alumno_data["id"],), daemon=True).start()

    def _thread_cargar_historial(self, alumno_id):
        """Worker Thread - Cargar historial desde BD."""
        session_temp = SessionLocal()
        historial_safe = []
        
        try:
            # ===== CAMBIAR LIMIT =====
            # ANTES: .limit(50).all()
            # AHORA: Traer TODOS los registros (sin limit)
            asistencias = session_temp.query(Asistencia)\
                .filter(Asistencia.alumno_id == alumno_id)\
                .order_by(desc(Asistencia.fecha), desc(Asistencia.hora))\
                .all()  # ← Sin límite
            # =========================
            
            for asis in asistencias:
                historial_safe.append({
                    "id": asis.id,
                    "fecha": asis.fecha.strftime("%d/%m/%Y") if asis.fecha else "--",
                    "hora": asis.hora.strftime("%H:%M:%S") if asis.hora else "--:--",
                    "turno": getattr(asis, "turno", "-") or "-",
                    "estado": str(asis.estado).upper(),
                    "observacion": asis.observacion or ""
                })
        
        except Exception as e:
            print(f"Error historial: {e}")
        finally:
            session_temp.close()
        
        self.after(0, lambda: self._mostrar_historial_ui(historial_safe))


    def _mostrar_historial_ui(self, historial):
        """Main Thread - Renderizar historial en la tabla CON SCROLL INFINITO"""
        # Limpiar tabla
        for widget in self.scroll_tabla.winfo_children():
            widget.destroy()
        
        if hasattr(self, "lbl_loader_tabla"):
            self.lbl_loader_tabla.destroy()
        
        # Resetear selección y variables de scroll
        self.btn_justificar.configure(state="disabled", fg_color="gray")
        self.fila_seleccionada = None
        self.datos_seleccionados = None
        
        # ===== INICIALIZAR SCROLL INFINITO =====
        self.historial_cache = historial
        self.registros_cargados = 0
        self.cargando_mas = False
        # =======================================
        
        # Caso sin registros
        if not historial:
            ctk.CTkLabel(self.scroll_tabla, text="\n👋", text_color="white",
                        font=("Roboto", 40)).pack()
            ctk.CTkLabel(self.scroll_tabla,
                        text="\n✅ El alumno no tiene registros de asistencia.",
                        text_color="gray", font=("Roboto", 14)).pack()
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
            # Calcular índice global para el color alternado
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
        
        # Debug
        print(f"📊 Cargados: {self.registros_cargados} de {len(self.historial_cache)}")

    # ============================================================
    #              MÉTODOS VISUALES - TABLA
    # ============================================================

    def crear_cabecera(self):
        """Crea la cabecera de la tabla."""
        header = ctk.CTkFrame(self.container_list, height=45, 
                             fg_color=st.Colors.TABLE_HEADER, corner_radius=10)
        header.pack(fill="x", padx=5, pady=(5,0))
        
        titulos = ["FECHA", "HORA", "TURNO", "ESTADO", "OBSERVACIÓN"]
        for i, t in enumerate(titulos):
            ctk.CTkLabel(header, text=t, font=("Roboto", 11, "bold"), 
                        text_color="white", width=self.ANCHOS[i]).pack(side="left", padx=2)

    def _crear_fila_asistencia_optimizada(self, datos, index_global):
        """Crea una fila optimizada para scroll infinito"""
        bg = st.Colors.ROW_ODD if index_global % 2 == 0 else st.Colors.ROW_EVEN
        
        # Frame de la fila
        row = ctk.CTkFrame(self.scroll_tabla, fg_color=bg, corner_radius=5, height=35)
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
        font_celda = ("Roboto", 12)
        
        def crear_celda(parent, txt, w, col="white", anchor="center", bg_badge=None):
            """Helper para crear celdas con o sin badge."""
            if bg_badge:
                f = ctk.CTkFrame(parent, fg_color="transparent", width=w, height=30)
                f.pack(side="left", padx=2)
                f.pack_propagate(False)
                
                lbl = ctk.CTkLabel(f, text=txt, fg_color=bg_badge,
                                text_color="white", corner_radius=3,
                                width=100, height=18,
                                font=("Arial", 11, "bold"))
                lbl.place(relx=0.5, rely=0.5, anchor="center")
                
                # Propagar eventos
                lbl.bind("<Button-1>", on_click)
                lbl.bind("<Enter>", on_enter)
                lbl.bind("<Leave>", on_leave)
                f.bind("<Button-1>", on_click)
                f.bind("<Enter>", on_enter)
                f.bind("<Leave>", on_leave)
            else:
                lbl = ctk.CTkLabel(parent, text=txt, width=w,
                                text_color=col, font=font_celda, anchor=anchor)
                lbl.pack(side="left", padx=2, fill="y")
                lbl.bind("<Button-1>", on_click)
                lbl.bind("<Enter>", on_enter)
                lbl.bind("<Leave>", on_leave)
        
        # Crear celdas
        crear_celda(row, datos["fecha"], self.ANCHOS[0])
        crear_celda(row, datos["hora"], self.ANCHOS[1], "gray")
        crear_celda(row, datos["turno"], self.ANCHOS[2], "gray")
        
        # Estado con color
        estado = datos["estado"]
        bg_estado = st.Colors.BG_PANEL
        if "PUNTUAL" in estado:
            bg_estado = st.Colors.PUNTUAL
        elif "TARDANZA" in estado:
            bg_estado = st.Colors.TARDANZA
        elif "INASISTENCIA" in estado or "FALTA" in estado:
            bg_estado = st.Colors.FALTA
        elif "JUSTIFICADO" in estado:
            bg_estado = st.Colors.ASISTENCIA
        
        crear_celda(row, estado, self.ANCHOS[3], bg_badge=bg_estado)
        crear_celda(row, datos["observacion"], self.ANCHOS[4], "gray", "w")

    def seleccionar_fila_visual(self, widget_fila, datos, bg_original):
        """Maneja la selección visual de una fila."""
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
        
        # Resaltar fila seleccionada
        widget_fila.configure(fg_color="#34495e")

        # Habilitar botón según el estado
        id_asistencia, fecha, estado = datos
        
        if "JUSTIFICADO" in estado:
            self.btn_justificar.configure(
                state="disabled", 
                text="✅ YA JUSTIFICADO", 
                fg_color="gray"
            )
        else:
            self.btn_justificar.configure(
                state="normal", 
                text=f"📝 JUSTIFICAR (ID: {id_asistencia})", 
                fg_color=st.Colors.TARDANZA
            )

    # ============================================================
    #              ACCIÓN DE JUSTIFICACIÓN
    # ============================================================

    def accion_justificar(self):
        """Abre diálogo para justificar la asistencia seleccionada."""
        if not self.datos_seleccionados:
            return

        id_asistencia, fecha, estado = self.datos_seleccionados
        
        # Diálogo de confirmación
        dialogo = ctk.CTkInputDialog(
            text=f"Justificar {estado} del {fecha}.\nIngrese el motivo:", 
            title="Justificar Asistencia"
        )
        motivo = dialogo.get_input()
        
        if motivo:
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




# hora_ingreso