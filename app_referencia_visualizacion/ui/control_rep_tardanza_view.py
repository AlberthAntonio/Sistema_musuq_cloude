import customtkinter as ctk
from tkinter import messagebox
from datetime import date, timedelta, datetime
import webbrowser
import urllib.parse
import threading 
from tkcalendar import DateEntry
from app.controllers.rep_tardanza_controller import ReporteTardanzaController

# --- ESTILOS ---
import app.styles.tabla_style as st

class ReporteTardanzaView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        self.controller = ReporteTardanzaController()
        
        # Variables de Control
        self.cargando = False 
        self.datos_por_fecha = {} # Diccionario: {"12/01/2025": [lista_alumnos]} TARDE
        self.botones_fecha = {}   # Diccionario: {"12/01/2025": widget_boton}
        self.fecha_activa = None

        self.registros_cache_tab = []  # Cache de registros del tab actual
        self.registros_cargados_tab = 0  # Cuántos se están mostrando
        self.lote_tamano = 20  # Cargar de 20 en 20
        self.cargando_mas = False  # Lock

        # Configuración Visual
        self.configure(fg_color=st.Colors.BG_MAIN)
        self.ANCHOS = [80, 250, 100, 80, 140, 130, 80]

        # Layout Principal
        self.pack(fill="both", expand=True)

        # ============================================================
        #                    ENCABEZADO
        # ============================================================
        self.fr_header = ctk.CTkFrame(self, fg_color="transparent")
        self.fr_header.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(self.fr_header, text="📊 GESTIÓN DE TARDANZAS",
                     font=st.Fonts.TITLE, text_color=st.Colors.TARDANZA).pack(side="left")
        
        self.lbl_loader = ctk.CTkLabel(self.fr_header, text="⏳ Procesando datos...", 
                                     text_color="#f39c12", font=("Roboto", 12, "bold"))

        # ============================================================
        #              TARJETA DE FILTROS
        # ============================================================
        self.card_filtros = ctk.CTkFrame(self, fg_color=st.Colors.BG_PANEL, corner_radius=10)
        self.card_filtros.pack(fill="x", padx=20, pady=5)

        self.card_filtros.columnconfigure((0, 1, 2), weight=1)

        # --- COLUMNA 1: FECHAS ---
        self.fr_col1 = ctk.CTkFrame(self.card_filtros, fg_color="transparent")
        self.fr_col1.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.fr_col1, text="📅 Rango de Fechas", font=("Roboto", 12, "bold"), text_color="gray").pack(pady=(0, 5))
        
        f_d = ctk.CTkFrame(self.fr_col1, fg_color="transparent")
        f_d.pack(pady=2)
        ctk.CTkLabel(f_d, text="Desde:", width=50, anchor="w", font=("Roboto", 11)).pack(side="left")
        self.ent_desde = DateEntry(f_d, width=12, background=st.Colors.TARDANZA, 
                                   foreground='white', borderwidth=0, date_pattern='dd/mm/yyyy')
        self.ent_desde.pack(side="left")
        self.ent_desde.set_date(date.today() - timedelta(days=7))

        f_h = ctk.CTkFrame(self.fr_col1, fg_color="transparent")
        f_h.pack(pady=2)
        ctk.CTkLabel(f_h, text="Hasta:", width=50, anchor="w", font=("Roboto", 11)).pack(side="left")
        self.ent_hasta = DateEntry(f_h, width=12, background=st.Colors.TARDANZA, 
                                   foreground='white', borderwidth=0, date_pattern='dd/mm/yyyy')
        self.ent_hasta.pack(side="left")
        self.ent_hasta.set_date(date.today())

        # --- COLUMNA 2: FILTROS ---
        self.fr_col2 = ctk.CTkFrame(self.card_filtros, fg_color="transparent")
        self.fr_col2.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        # Título
        ctk.CTkLabel(self.fr_col2, text="🔍 Filtros", font=("Roboto", 12, "bold"), text_color="gray").pack(pady=(0, 10))

        # Contenedor interno para usar GRID (Filas y Columnas)
        self.fr_grid_inputs = ctk.CTkFrame(self.fr_col2, fg_color="transparent")
        self.fr_grid_inputs.pack()

        # Fila 1: Turno
        ctk.CTkLabel(self.fr_grid_inputs, text="Turno:", font=("Roboto", 11), text_color="silver").grid(row=0, column=0, padx=(0, 10), pady=5, sticky="e")
        self.cb_horario = ctk.CTkComboBox(self.fr_grid_inputs, values=["Todos", "MATUTINO", "VESPERTINO", "DOBLE HORARIO"], width=130)
        self.cb_horario.grid(row=0, column=1, pady=5)

        # Fila 2: Grupo
        ctk.CTkLabel(self.fr_grid_inputs, text="Grupo:", font=("Roboto", 11), text_color="silver").grid(row=1, column=0, padx=(0, 10), pady=5, sticky="e")
        self.cb_grupo = ctk.CTkComboBox(self.fr_grid_inputs, values=["Todos", "A", "B", "C", "D"], width=130)
        self.cb_grupo.set("Todos")
        self.cb_grupo.grid(row=1, column=1, pady=5)

        # Fila 3: Modalidad
        ctk.CTkLabel(self.fr_grid_inputs, text="Modalidad:", font=("Roboto", 11), text_color="silver").grid(row=2, column=0, padx=(0, 10), pady=5, sticky="e")
        self.cb_modalidad = ctk.CTkComboBox(self.fr_grid_inputs, values=["Todos", "ORDINARIO", "PRIMERA OPCION", "COLEGIO"], width=130)
        self.cb_modalidad.set("Todos")
        self.cb_modalidad.grid(row=2, column=1, pady=5)

        # --- COLUMNA 3: ACCIONES ---
        self.fr_col3 = ctk.CTkFrame(self.card_filtros, fg_color="transparent")
        self.fr_col3.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
        ctk.CTkLabel(self.fr_col3, text="⚡ Acciones", font=("Roboto", 12, "bold"), text_color="gray").pack(pady=(0, 5))

        self.btn_buscar = ctk.CTkButton(self.fr_col3, text="🔎 BUSCAR AHORA", width=160,
                                        fg_color="#404040", hover_color="gray30",
                                        command=self.iniciar_busqueda_thread) 
        self.btn_buscar.pack(pady=2)

        self.btn_pdf = ctk.CTkButton(self.fr_col3, text="📄 EXPORTAR CSV", width=160,
                                     fg_color=st.Colors.TARDANZA, hover_color="#d35400",
                                     command=self.generar_pdf)
        self.btn_pdf.pack(pady=2)

        # ============================================================
        #          BARRA DE NAVEGACIÓN POR FECHAS (TABS)
        # ============================================================
        self.fr_tabs_container = ctk.CTkFrame(self, fg_color="transparent", height=50)
        self.fr_tabs_container.pack(fill="x", padx=20, pady=(5, 0))
        
        # Scroll horizontal para las pestañas
        self.fr_nav_fechas = ctk.CTkScrollableFrame(self.fr_tabs_container, orientation="horizontal", 
                                                    height=40, fg_color="transparent")
        self.fr_nav_fechas.pack(fill="x", expand=True)
        
        # Mensaje inicial en la barra
        self.lbl_nav_info = ctk.CTkLabel(self.fr_nav_fechas, text="Seleccione un rango y busque para ver los días disponibles", text_color="gray")
        self.lbl_nav_info.pack(padx=10, pady=5)

        # ============================================================
        #                    TABLA DE RESULTADOS
        # ============================================================
        self.container_tabla = ctk.CTkFrame(self, fg_color=st.Colors.BG_PANEL)
        self.container_tabla.pack(fill="both", expand=True, padx=20, pady=5)

        self.crear_cabecera()

        self.scroll_tabla = ctk.CTkScrollableFrame(self.container_tabla, fg_color="transparent")
        self.scroll_tabla.pack(fill="both", expand=True)

        # ===== AGREGAR HOOK DEL SCROLL =====
        self.scroll_tabla._parent_canvas.configure(yscrollcommand=self._hook_scroll)
        # ===================================

        self.lbl_mensaje = ctk.CTkLabel(self.scroll_tabla, 
                                        text="\n🔍 Realiza una búsqueda para ver resultados",
                                        font=st.Fonts.SUBTITLE, text_color="gray")
        self.lbl_mensaje.pack()

        # ===== AGREGAR LABEL DE CARGANDO MÁS =====
        self.lbl_cargando_mas = ctk.CTkLabel(
            self.scroll_tabla,
            text="⏳ Cargando más registros...",
            text_color="#3498db",
            font=("Roboto", 10, "italic")
            )

    # ============================================================
    #          LÓGICA ASÍNCRONA (HILOS + AGRUPACIÓN)
    # ============================================================
    def iniciar_busqueda_thread(self):
        if self.cargando: return
        self.cargando = True
        
        self.lbl_loader.pack(side="left", padx=10)
        self.btn_buscar.configure(state="disabled", text="Buscando...")
        self.update_idletasks()
        
        # Limpieza visual inicial
        for w in self.scroll_tabla.winfo_children(): w.destroy()
        for w in self.fr_nav_fechas.winfo_children(): w.destroy() # Limpiar pestañas anteriores
        
        params = {
            "inicio": self.ent_desde.get(),
            "fin": self.ent_hasta.get(),
            "horario": self.cb_horario.get(),
            "grupo": self.cb_grupo.get(),
            "mod": self.cb_modalidad.get()
        }
        
        self.scroll_tabla._parent_canvas.yview_moveto(0.0)

        threading.Thread(target=self._proceso_buscar_db, args=(params,), daemon=True).start()

    def _proceso_buscar_db(self, params):
        try:
            # 1. Obtener TODOS los datos del rango (puede tardar un poco)
            exito, mensaje, datos_brutos = self.controller.filtrar_tardanzas(
                params["inicio"],
                params["fin"], 
                params["horario"], 
                params["grupo"], 
                params["mod"]
            )
            
            # 2. PROCESAR Y AGRUPAR POR FECHA (En memoria es rápido)
            if exito and datos_brutos:
                agrupados = {}
                for d in datos_brutos:
                    # Extraer solo la fecha "dd/mm/yyyy" eliminando la hora si existe
                    fecha_str = str(d["fecha"]).split(" ")[0]
                    if fecha_str not in agrupados:
                        agrupados[fecha_str] = []
                    agrupados[fecha_str].append(d)
                
                # Ordenar fechas (de más antigua a más reciente o viceversa)
                # Convertimos a objeto date para ordenar correctamente
                fechas_ordenadas = sorted(agrupados.keys(), key=lambda x: datetime.strptime(x, "%d/%m/%Y"))
                
                res_final = {
                    "datos_agrupados": agrupados,
                    "fechas_ordenadas": fechas_ordenadas
                }
            else:
                res_final = None

        except Exception as e:
            exito, mensaje, res_final = False, str(e), None
            
        self.after(0, lambda: self._configurar_navegacion(exito, mensaje, res_final))

    def _configurar_navegacion(self, exito, mensaje, resultado):
        """Crea los botones de las pestañas (días)"""
        self.lbl_loader.pack_forget()
        self.btn_buscar.configure(state="normal", text="🔎 BUSCAR AHORA")
        self.cargando = False

        if not exito:
            messagebox.showerror("Error", mensaje)
            return
        
        if not resultado or not resultado["fechas_ordenadas"]:
            ctk.CTkLabel(self.scroll_tabla, text="\n✅ No se encontraron tardanzas en este rango.", 
                         font=st.Fonts.SUBTITLE, text_color="gray").pack()
            ctk.CTkLabel(self.fr_nav_fechas, text="Sin resultados", text_color="gray").pack(pady=5)
            return

        # Guardamos la data agrupada
        self.datos_por_fecha = resultado["datos_agrupados"]
        fechas = resultado["fechas_ordenadas"]
        self.botones_fecha = {}

        # CREAR BOTONES DE PESTAÑA
        for fecha in fechas:
            cant = len(self.datos_por_fecha[fecha])
            texto_btn = f"{fecha}\n({cant})"
            
            # Botón estilo "Tab"
            btn = ctk.CTkButton(self.fr_nav_fechas, text=texto_btn, width=100, height=35,
                                fg_color="transparent", border_width=1, border_color="gray",
                                text_color="gray80",
                                command=lambda f=fecha: self.mostrar_dia_especifico(f))
            btn.pack(side="left", padx=5, pady=2)
            self.botones_fecha[fecha] = btn
        
        # Seleccionar automáticamente el primer día (o el último, como prefieras)
        primera_fecha = fechas[0]
        self.mostrar_dia_especifico(primera_fecha)

    def mostrar_dia_especifico(self, fecha):
        """Renderiza SOLO los alumnos de la fecha seleccionada CON SCROLL INFINITO"""
        # 1. Actualizar estilo de botones
        if self.fecha_activa and self.fecha_activa in self.botones_fecha:
            self.botones_fecha[self.fecha_activa].configure(
                fg_color="transparent",
                border_color="gray",
                text_color="gray80"
            )
        
        self.fecha_activa = fecha
        self.botones_fecha[fecha].configure(
            fg_color=st.Colors.TARDANZA,
            border_color=st.Colors.TARDANZA,
            text_color="white"
        )
        
        # 2. Limpiar tabla
        for widget in self.scroll_tabla.winfo_children():
            widget.destroy()
        
        # ===== RESETEAR VARIABLES DE SCROLL INFINITO =====
        self.registros_cache_tab = []
        self.registros_cargados_tab = 0
        self.cargando_mas = False
        # =================================================
        
        # 3. Mostrar loader
        self.lbl_loading_tab = ctk.CTkLabel(
            self.scroll_tabla,
            text=f"⏳ Cargando registros del {fecha}...",
            text_color="#f39c12",
            font=("Roboto", 14)
        )
        self.lbl_loading_tab.pack(pady=20)
        self.scroll_tabla._parent_canvas.yview_moveto(0.0)
        self.update_idletasks()
        
        # 4. Programar carga con scroll infinito
        self.after(250, lambda: self._inicializar_tab_con_scroll_infinito(fecha))

    def _inicializar_tab_con_scroll_infinito(self, fecha):
        """Inicializa el tab con scroll infinito"""
        # 1. Eliminar loader
        if hasattr(self, "lbl_loading_tab"):
            self.lbl_loading_tab.destroy()
        
        # 2. Obtener datos de la fecha
        datos_dia = self.datos_por_fecha.get(fecha, [])
        
        if not datos_dia:
            ctk.CTkLabel(
                self.scroll_tabla, 
                text="No hay registros.", 
                text_color="gray"
            ).pack(pady=10)
            return
        
        # 3. Guardar en cache
        self.registros_cache_tab = datos_dia
        self.registros_cargados_tab = 0
        self.cargando_mas = False
        
        # 4. Cargar primer lote
        self._renderizar_siguiente_lote_tab()

    def _renderizar_siguiente_lote_tab(self):
        """Renderiza el siguiente grupo de N registros del tab actual"""
        # Calcular rango
        inicio = self.registros_cargados_tab
        fin = inicio + self.lote_tamano
        
        # Extraer lote
        lote = self.registros_cache_tab[inicio:fin]
        
        # Renderizar cada registro
        for item in lote:
            # Calcular índice global para colores alternados
            index_global = self.registros_cargados_tab
            self._crear_fila_optimizada(item, index_global)
            self.registros_cargados_tab += 1
        
        # Ocultar indicador
        try:
            self.lbl_cargando_mas.pack_forget()
        except:
            pass
        
        # Liberar lock
        self.cargando_mas = False
        
        # Debug
        print(f"📊 Tab {self.fecha_activa}: {self.registros_cargados_tab}/{len(self.registros_cache_tab)}")

    def _hook_scroll(self, first, last):
        """Hook del scrollbar para detectar cuando llega al final"""
        # 1. Actualizar scrollbar
        try:
            self.scroll_tabla._scrollbar.set(first, last)
        except:
            pass
        
        # 2. Validaciones
        if self.cargando_mas:
            return
        if not hasattr(self, 'registros_cache_tab'):
            return
        if not self.registros_cache_tab:
            return
        
        # 3. Detectar si llegamos al 90%
        try:
            posicion_actual = float(last)
            
            if (posicion_actual >= 0.90 and 
                self.registros_cargados_tab < len(self.registros_cache_tab)):
                
                self.cargando_mas = True
                
                # Mostrar indicador
                try:
                    if self.lbl_cargando_mas.winfo_exists():
                        self.lbl_cargando_mas.pack(pady=10)
                except:
                    pass
                
                # Cargar siguiente lote
                self.after(200, self._renderizar_siguiente_lote_tab)
        
        except Exception as e:
            if "bad window path" not in str(e):
                print(f"Error en _hook_scroll: {e}")
            self.cargando_mas = False


    # ============================================================
    #              DISEÑO DE FILAS (TU ESTILO)
    # ============================================================

    def crear_cabecera(self):
        header = ctk.CTkFrame(self.container_tabla, height=45, fg_color=st.Colors.TABLE_HEADER, corner_radius=10)
        header.pack(fill="x", padx=5, pady=(5, 5))
        
        titulos = ["CÓDIGO", "ALUMNO", "ESTADO", "TURNO", "FECHA/HORA", "CELULAR", "CONTACTAR"]
        for i, t in enumerate(titulos):
            w = self.ANCHOS[i]
            ctk.CTkLabel(header, text=t, font=("Roboto", 11, "bold"), text_color="white", width=w).pack(side="left", padx=2)

    def _crear_fila_optimizada(self, d, index):
        """Versión optimizada de crear_fila_manual para scroll infinito"""
        bg = st.Colors.ROW_ODD if index % 2 == 0 else st.Colors.ROW_EVEN
        
        row = ctk.CTkFrame(self.scroll_tabla, fg_color=bg, corner_radius=0, height=35)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        
        font_row = ("Roboto", 11)
        
        # Código
        ctk.CTkLabel(row, text=d["codigo"], width=self.ANCHOS[0], 
                    text_color="white", font=font_row).pack(side="left", padx=2)
        
        # Nombre
        ctk.CTkLabel(row, text=d["nombre"], width=self.ANCHOS[1], anchor="w",
                    text_color="white", font=font_row).pack(side="left", padx=2)
        
        # Estado (Badge)
        f_st = ctk.CTkFrame(row, fg_color="transparent", width=self.ANCHOS[2], height=35)
        f_st.pack(side="left", padx=2)
        f_st.pack_propagate(False)
        ctk.CTkLabel(f_st, text="TARDANZA", fg_color=st.Colors.TARDANZA, 
                    text_color="white", corner_radius=5, width=80, height=20,
                    font=("Arial", 9, "bold")).place(relx=0.5, rely=0.5, anchor="center")
        
        # Turno
        ctk.CTkLabel(row, text=d["horario"], width=self.ANCHOS[3],
                    text_color="gray", font=font_row).pack(side="left", padx=2)
        
        # Fecha/Hora
        ctk.CTkLabel(row, text=d["fecha"], width=self.ANCHOS[4],
                    text_color="white", font=font_row).pack(side="left", padx=2)
        
        # Celular
        ctk.CTkLabel(row, text=d["celular"], width=self.ANCHOS[5],
                    text_color="gray", font=font_row).pack(side="left", padx=2)
        
        # Botón WhatsApp
        f_wa = ctk.CTkFrame(row, fg_color="transparent", width=self.ANCHOS[6], height=35)
        f_wa.pack(side="left", padx=2)
        f_wa.pack_propagate(False)
        
        btn_wa = ctk.CTkButton(
            f_wa, text="📲", width=30, height=25,
            fg_color="#27ae60", hover_color="#2ecc71",
            font=("Arial", 12),
            command=lambda cel=d["celular"], nom=d["nombre"], 
                        fech=d["fecha"]: self.enviar_whatsapp(cel, nom, fech)
        )
        btn_wa.place(relx=0.5, rely=0.5, anchor="center")


    # ================= LÓGICA DE NEGOCIO =================

    def enviar_whatsapp(self, celular_raw, nombre, fecha):
        if not celular_raw or celular_raw == "None":
            messagebox.showwarning("Atención", "No hay número registrado.")
            return

        celular = str(celular_raw).split("/")[0].strip().replace(" ", "")
        if len(celular) < 9:
            messagebox.showwarning("Error", "Número celular inválido.")
            return

        mensaje = (f"Estimado padre de familia, le informamos que su hijo(a) "
                   f"*{nombre}* registró una TARDANZA el día {fecha}. "
                   f"Atte. La Dirección.")
        
        try:
            url = f"https://wa.me/51{celular}?text={urllib.parse.quote(mensaje)}"
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir navegador: {e}")

    def generar_pdf(self):
        f_inicio = self.ent_desde.get()
        f_fin = self.ent_hasta.get()
        horario = self.cb_turno.get()
        grupo = self.cb_grupo.get()
        mod = self.cb_modalidad.get()
        
        exito, mensaje, datos = self.controller.filtrar_tardanzas(f_inicio, f_fin, horario, grupo, mod)

        if not datos:
            messagebox.showwarning("Vacío", "No hay datos para exportar.")
            return

        try:
            filename = f"Reporte_Tardanzas_{date.today()}.csv"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("CODIGO,ALUMNO,ESTADO,HORARIO,FECHA,CELULAR\n")
                for d in datos:
                    row = [d["codigo"], d["nombre"], d["estado"], d["horario"], d["fecha"], d["celular"]]
                    f.write(",".join(map(str, row)) + "\n")
            
            messagebox.showinfo("Exportado", f"Se generó el archivo: {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el archivo: {e}")