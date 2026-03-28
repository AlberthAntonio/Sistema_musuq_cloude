"""
Panel de Lista de Alumnos
Sistema Musuq Cloud
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
from typing import Dict, List, Optional, Callable

from core.api_client import APIClient, AlumnoClient, MatriculasClient
from core.theme_manager import ThemeManager as TM
from styles import tabla_style as st


class AlumnosListPanel(ctk.CTkFrame):
    """Panel con tabla de alumnos, filtros y acciones"""
    
    def __init__(self, parent, auth_client: APIClient):
        super().__init__(parent, fg_color="transparent")
        
        self.auth_client = auth_client
        self.alumno_client = AlumnoClient()
        self.alumno_client.token = auth_client.token
        self.matricula_client = MatriculasClient()
        self.matricula_client.token = auth_client.token
        
        # Cache de datos
        self.alumnos_cache: List[Dict] = []
        self.alumnos_filtrados: List[Dict] = []
        self.cantidad_cargada = 0
        self.lote_tamano = 40
        self.cargando_lock = False
        
        # Selección
        self.fila_seleccionada: Optional[ctk.CTkFrame] = None
        self.datos_seleccionados: Optional[Dict] = None
        
        # Anchos de columnas
        self.ANCHOS = [70, 82, 190, 100, 40, 110, 135]
        
        self.create_widgets()
        self.cargar_datos_thread()
    
    def create_widgets(self):
        """Crear widgets del panel"""
        
        # Layout: 2 columnas (tabla | acciones)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)
        
        # ==================== PANEL IZQUIERDO (TABLA) ====================
        panel_izq = ctk.CTkFrame(self, fg_color="transparent")
        panel_izq.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        
        # Título
        ctk.CTkLabel(
            panel_izq,
            text="📋 LISTA DE ALUMNOS",
            font=ctk.CTkFont(family="Roboto", size=20, weight="bold"),
            text_color=TM.text()
        ).pack(anchor="w", pady=(0, 15))
        
        # ==================== BARRA DE FILTROS (2 filas) ====================
        fr_filtros = ctk.CTkFrame(
            panel_izq,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        fr_filtros.pack(fill="x", pady=(0, 10))

        # --- FILA 1: Búsqueda ---
        fr_fila1 = ctk.CTkFrame(fr_filtros, fg_color="transparent")
        fr_fila1.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(
            fr_fila1,
            text="🔍",
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(0, 5))

        self.entry_buscar = ctk.CTkEntry(
            fr_fila1,
            placeholder_text="Buscar por DNI, Nombre, Código...",
            height=35,
            border_width=0,
            fg_color=TM.bg_panel(),
            text_color=TM.text()
        )
        self.entry_buscar.pack(side="left", fill="x", expand=True)
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_tabla)

        ctk.CTkFrame(fr_fila1, width=2, height=22, fg_color="#505050").pack(side="left", padx=10)

        # Filtro Estado (junto a búsqueda)
        ctk.CTkLabel(
            fr_fila1,
            text="Estado:",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 2))

        self.cbo_estado = ctk.CTkComboBox(
            fr_fila1,
            values=["Todos", "Activo", "Inactivo"],
            width=110,
            command=lambda _: self.filtrar_tabla()
        )
        self.cbo_estado.set("Todos")
        self.cbo_estado.pack(side="left")

        # --- FILA 2: Filtros ---
        fr_fila2 = ctk.CTkFrame(fr_filtros, fg_color="transparent")
        fr_fila2.pack(fill="x", padx=10, pady=(0, 8))

        # Filtro Grupo
        ctk.CTkLabel(
            fr_fila2,
            text="Grupo:",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 2))

        self.cbo_grupo = ctk.CTkComboBox(
            fr_fila2,
            values=["Todos", "A", "B", "C", "D"],
            width=80,
            command=lambda _: self.filtrar_tabla()
        )
        self.cbo_grupo.set("Todos")
        self.cbo_grupo.pack(side="left", padx=(0, 10))

        # Separador
        ctk.CTkFrame(fr_fila2, width=2, height=22, fg_color="#505050").pack(side="left", padx=(0, 10))

        # Filtro Horario
        ctk.CTkLabel(
            fr_fila2,
            text="Horario:",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 2))

        self.cbo_horario = ctk.CTkComboBox(
            fr_fila2,
            values=["Todos", "MATUTINO", "VESPERTINO", "DOBLE HORARIO"],
            width=145,
            command=lambda _: self.filtrar_tabla()
        )
        self.cbo_horario.set("Todos")
        self.cbo_horario.pack(side="left", padx=(0, 10))

        # Separador
        ctk.CTkFrame(fr_fila2, width=2, height=22, fg_color="#505050").pack(side="left", padx=(0, 10))

        # Filtro Modalidad
        ctk.CTkLabel(
            fr_fila2,
            text="Modalidad:",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 2))

        self.cbo_modalidad = ctk.CTkComboBox(
            fr_fila2,
            values=["Todos", "PRIMERA OPCION", "ORDINARIO", "COLEGIO", "REFORZAMIENTO"],
            width=155,
            command=self.on_modalidad_change
        )
        self.cbo_modalidad.set("Todos")
        self.cbo_modalidad.pack(side="left", padx=(0, 10))

        # Filtro condicional para modalidad COLEGIO
        self.fr_filtro_colegio = ctk.CTkFrame(fr_fila2, fg_color="transparent")
        self.fr_filtro_colegio.pack(side="left", padx=(0, 10))

        ctk.CTkFrame(self.fr_filtro_colegio, width=2, height=22, fg_color="#505050").pack(side="left", padx=(0, 10))

        ctk.CTkLabel(
            self.fr_filtro_colegio,
            text="Nivel/Grado:",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(0, 2))

        self.cbo_nivel_grado = ctk.CTkComboBox(
            self.fr_filtro_colegio,
            values=["Todos"],
            width=165,
            command=lambda _: self.filtrar_tabla(),
            fg_color=TM.bg_panel(),
            border_color=TM.get_theme().border,
            button_color=TM.primary(),
            dropdown_fg_color=TM.bg_panel(),
            corner_radius=6
        )
        self.cbo_nivel_grado.set("Todos")
        self.cbo_nivel_grado.pack(side="left")
        self.fr_filtro_colegio.pack_forget()


        # Botón actualizar (extremo derecho fila 2)
        self.btn_actualizar = ctk.CTkButton(
            fr_fila2,
            text="🔄",
            width=40,
            fg_color="#404040",
            hover_color="#505050",
            command=self.cargar_datos_thread
        )
        self.btn_actualizar.pack(side="right")
        
        # ==================== TABLA ====================
        fr_tabla = ctk.CTkFrame(
            panel_izq,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        fr_tabla.pack(fill="both", expand=True)
        
        # Cabecera
        self.crear_cabecera(fr_tabla)
        
        # Loader
        self.lbl_loader = ctk.CTkLabel(
            fr_tabla,
            text="⏳ Cargando datos...",
            text_color=TM.warning()
        )
        
        # Cuerpo scrollable
        self.scroll_tabla = ctk.CTkScrollableFrame(
            fr_tabla,
            fg_color="transparent"
        )
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Hook scroll infinito
        self.scroll_tabla._parent_canvas.configure(yscrollcommand=self._hook_scroll)
        
        # ==================== PANEL DERECHO (ACCIONES) ====================
        panel_der = ctk.CTkFrame(
            self,
            width=200,
            fg_color=TM.bg_card(),
            corner_radius=15
        )
        panel_der.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)
        panel_der.grid_propagate(False)
        
        ctk.CTkLabel(
            panel_der,
            text="ACCIONES",
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(pady=(20, 15))
        
        # Botón Editar
        self.btn_editar = ctk.CTkButton(
            panel_der,
            text="✏️ Editar Datos",
            fg_color="#f39c12",
            hover_color="#d35400",
            command=self.accion_editar
        )
        self.btn_editar.pack(fill="x", padx=15, pady=8)
        
        # Botón Ficha
        self.btn_ficha = ctk.CTkButton(
            panel_der,
            text="🖨️ Ficha Matrícula",
            fg_color="#34495e",
            hover_color="#2c3e50",
            command=self.accion_imprimir
        )
        self.btn_ficha.pack(fill="x", padx=15, pady=8)
        
        # Botón Eliminar
        self.btn_eliminar = ctk.CTkButton(
            panel_der,
            text="❌ Anular Matrícula",
            fg_color=TM.danger(),
            hover_color="#c0392b",
            command=self.accion_eliminar
        )
        self.btn_eliminar.pack(fill="x", padx=15, pady=8)
        
        # Separador
        ctk.CTkFrame(
            panel_der,
            height=2,
            fg_color="#404040"
        ).pack(fill="x", padx=20, pady=20)
        
        # Total
        self.lbl_total = ctk.CTkLabel(
            panel_der,
            text="Total: 0",
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            text_color=TM.text()
        )
        self.lbl_total.pack(pady=5)

    def on_modalidad_change(self, seleccion=None):
        """Mostrar filtros condicionales según modalidad"""
        modalidad = self.cbo_modalidad.get()

        if modalidad == "COLEGIO":
            self._actualizar_opciones_nivel_grado()
            self.fr_filtro_colegio.pack(side="left", padx=(0, 10), before=self.btn_actualizar)
        else:
            self.fr_filtro_colegio.pack_forget()
            self.cbo_nivel_grado.set("Todos")

        self.filtrar_tabla()

    def _actualizar_opciones_nivel_grado(self):
        """Cargar opciones de nivel/grado para modalidad colegio"""
        opciones = {"Todos"}
        for alumno in self.alumnos_cache:
            if str(alumno.get("modalidad", "") or "").upper() != "COLEGIO":
                continue

            nivel = str(alumno.get("nivel", "") or "").strip().upper()
            grado = str(alumno.get("grado", "") or "").strip().upper()
            valor = f"{nivel} {grado}".strip()
            if valor:
                opciones.add(valor)

        opciones_ordenadas = ["Todos"] + sorted(opciones - {"Todos"})
        valor_actual = self.cbo_nivel_grado.get()
        self.cbo_nivel_grado.configure(values=opciones_ordenadas)

        if valor_actual in opciones_ordenadas:
            self.cbo_nivel_grado.set(valor_actual)
        else:
            self.cbo_nivel_grado.set("Todos")
    
    def crear_cabecera(self, parent):
        """Crear cabecera de la tabla"""
        header = ctk.CTkFrame(
            parent,
            height=40,
            fg_color=st.Colors.TABLE_HEADER,
            corner_radius=5
        )
        header.pack(fill="x", padx=5, pady=(5, 0))
        
        titulos = ["CÓDIGO", "DNI", "ALUMNO", "MODALIDAD", "GRP", "HORARIO", "CARRERA"]
        for i, titulo in enumerate(titulos):
            ctk.CTkLabel(
                header,
                text=titulo,
                font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
                text_color="white",
                width=self.ANCHOS[i]
            ).pack(side="left", padx=2)
    
    def crear_fila(self, alumno: Dict, index: int):
        """Crear una fila de la tabla"""
        bg = "#2d2d2d" if index % 2 == 0 else "#363636"
        
        row = ctk.CTkFrame(
            self.scroll_tabla,
            fg_color=bg,
            corner_radius=5,
            height=35
        )
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        
        def on_click(e):
            self.seleccionar_fila(row, alumno)
        
        row.bind("<Button-1>", on_click)
        
        def celda(texto, ancho, color=TM.text(), anchor="center"):
            lbl = ctk.CTkLabel(
                row,
                text=str(texto) if texto else "-",
                width=ancho,
                text_color=color,
                font=ctk.CTkFont(family="Roboto", size=11),
                anchor=anchor
            )
            lbl.pack(side="left", padx=2)
            lbl.bind("<Button-1>", on_click)
        
        # Columnas
        celda(alumno.get("codigo_matricula", "-"), self.ANCHOS[0])
        celda(alumno.get("dni", "-"), self.ANCHOS[1], TM.text_secondary())
        
        # Nombre completo (truncado para que no desborde)
        nombre_raw = f"{alumno.get('nombres', '')}, {alumno.get('apell_paterno', '')} {alumno.get('apell_materno', '')}"
        nombre = nombre_raw.strip()[:32] + "…" if len(nombre_raw.strip()) > 32 else nombre_raw.strip()
        celda(nombre, self.ANCHOS[2], TM.text(), "w")
        
        celda(alumno.get("modalidad", "-"), self.ANCHOS[3], TM.text_secondary())
        
        # Grupo con color
        lbl_grp = ctk.CTkLabel(
            row,
            text=alumno.get("grupo", "-") or "-",
            width=self.ANCHOS[4],
            text_color="#f1c40f",
            font=ctk.CTkFont(family="Arial", size=11, weight="bold")
        )
        lbl_grp.pack(side="left", padx=2)
        lbl_grp.bind("<Button-1>", on_click)

        # Horario
        celda(alumno.get("horario", "-"), self.ANCHOS[5], TM.text_secondary())
        
        # Carrera (truncada si es larga)
        carrera_raw = str(alumno.get("carrera", "-") or "-")
        carrera = carrera_raw[:22] + "…" if len(carrera_raw) > 22 else carrera_raw
        celda(carrera, self.ANCHOS[6], TM.text_secondary())
    
    def seleccionar_fila(self, widget: ctk.CTkFrame, datos: Dict):
        """Seleccionar una fila"""
        # Deseleccionar anterior
        if self.fila_seleccionada and self.fila_seleccionada.winfo_exists():
            try:
                self.fila_seleccionada.configure(fg_color="#2d2d2d")
            except:
                pass
        
        # Seleccionar nueva
        self.fila_seleccionada = widget
        self.datos_seleccionados = datos
        widget.configure(fg_color="#34495e")
    
    # ==================== CARGA DE DATOS ====================
    
    def cargar_datos_thread(self):
        """Iniciar carga en hilo"""
        self.lbl_total.configure(text="Cargando...")
        self.lbl_loader.pack(pady=5)
        self.btn_actualizar.configure(state="disabled")
        
        # Limpiar tabla
        self.fila_seleccionada = None
        self.datos_seleccionados = None
        self._limpiar_tabla()
        
        threading.Thread(target=self._traer_datos, daemon=True).start()
    
    def _traer_datos(self):
        """Traer datos del backend combinando alumnos + matrículas"""
        ok_a, data_a = self.alumno_client.obtener_todos(limit=1000)

        if not ok_a:
            msg = data_a.get("error", "Error al cargar alumnos") if isinstance(data_a, dict) else str(data_a)
            self.after(0, lambda: self._error_carga(msg))
            return

        # Normalizar lista de alumnos
        alumnos = data_a if isinstance(data_a, list) else data_a.get("items", []) if isinstance(data_a, dict) else []

        # Obtener matrículas (sin filtro de estado para máxima cobertura)
        ok_m, data_m = self.matricula_client.listar(limit=2000, estado=None)
        if not ok_m:
            ok_m, data_m = self.matricula_client.listar(limit=2000, estado="activo")

        # Construir índice alumno_id -> datos de matrícula (prioriza estado activo)
        matriculas_idx: Dict[int, Dict] = {}
        if ok_m:
            mats = data_m if isinstance(data_m, list) else data_m.get("items", []) if isinstance(data_m, dict) else []
            for m in mats:
                aid = m.get("alumno_id")
                if aid is not None:
                    existing = matriculas_idx.get(int(aid))
                    if not existing or m.get("estado") == "activo":
                        matriculas_idx[int(aid)] = m

        # Combinar: enriquecer cada alumno con datos de su matrícula
        combinados = []
        for alumno in alumnos:
            alumno_id = int(alumno.get("id", 0))
            mat = matriculas_idx.get(alumno_id, {})
            combinados.append({
                **alumno,
                "codigo_matricula": mat.get("codigo_matricula") or "-",
                "modalidad":        mat.get("modalidad") or "-",
                "grupo":            mat.get("grupo") or "-",
                "carrera":          mat.get("carrera") or "-",
                "horario":          mat.get("horario") or "-",
                "nivel":            mat.get("nivel") or "-",
                "grado":            mat.get("grado") or "-",
                "_matricula_id":    mat.get("id"),
            })

        self.after(0, lambda: self._finalizar_carga(combinados))
    
    def _finalizar_carga(self, datos: List[Dict]):
        """Finalizar carga y renderizar"""
        self.alumnos_cache = datos
        self._actualizar_opciones_nivel_grado()
        self.lbl_loader.pack_forget()
        self.btn_actualizar.configure(state="normal")
        self.filtrar_tabla()
    
    def _error_carga(self, error: str):
        """Manejar error de carga"""
        self.lbl_loader.configure(text=f"❌ {error}")
        self.btn_actualizar.configure(state="normal")
        self.lbl_total.configure(text="Error")
    
    def filtrar_tabla(self, event=None):
        """Filtrar alumnos en memoria"""
        texto = self.entry_buscar.get().lower()
        grupo_sel = self.cbo_grupo.get()
        estado_sel = self.cbo_estado.get()
        horario_sel = self.cbo_horario.get()
        modalidad_sel = self.cbo_modalidad.get()
        nivel_grado_sel = self.cbo_nivel_grado.get()

        # Limpiar tabla
        self._limpiar_tabla()
        
        # Filtrar
        self.alumnos_filtrados = []
        
        for alumno in self.alumnos_cache:
            # Filtro grupo
            if grupo_sel != "Todos" and alumno.get("grupo") != grupo_sel:
                continue
            
            # Filtro estado
            if estado_sel == "Activo" and not alumno.get("activo", True):
                continue
            if estado_sel == "Inactivo" and alumno.get("activo", True):
                continue

            # Filtro horario
            if horario_sel != "Todos":
                db_horario = str(alumno.get("horario", "") or "").upper()
                if db_horario != horario_sel:
                    continue

            # Filtro modalidad
            if modalidad_sel != "Todos":
                db_modalidad = str(alumno.get("modalidad", "") or "").upper()
                if db_modalidad != modalidad_sel:
                    continue

            # Filtro nivel/grado (solo cuando aplica COLEGIO)
            if modalidad_sel == "COLEGIO" and nivel_grado_sel != "Todos":
                db_nivel = str(alumno.get("nivel", "") or "").strip().upper()
                db_grado = str(alumno.get("grado", "") or "").strip().upper()
                db_nivel_grado = f"{db_nivel} {db_grado}".strip()
                if db_nivel_grado != nivel_grado_sel:
                    continue

            # Filtro texto
            nombre = f"{alumno.get('nombres', '')} {alumno.get('apell_paterno', '')} {alumno.get('apell_materno', '')}".lower()
            codigo = str(alumno.get("codigo_matricula", "")).lower()
            dni = str(alumno.get("dni", ""))
            
            if texto in nombre or texto in codigo or texto in dni:
                self.alumnos_filtrados.append(alumno)
        
        # Actualizar contador
        self.lbl_total.configure(text=f"Total: {len(self.alumnos_filtrados)}")
        self.cantidad_cargada = 0
        self.cargando_lock = False
        
        # Renderizar primer lote
        self.scroll_tabla._parent_canvas.yview_moveto(0.0)
        self._renderizar_lote()
    
    def _renderizar_lote(self):
        """Renderizar siguiente lote de filas"""
        inicio = self.cantidad_cargada
        fin = inicio + self.lote_tamano
        lote = self.alumnos_filtrados[inicio:fin]
        
        for i, alumno in enumerate(lote):
            self.crear_fila(alumno, self.cantidad_cargada + i)
        
        self.cantidad_cargada += len(lote)
        self.cargando_lock = False
    
    def _hook_scroll(self, first, last):
        """Detectar scroll para cargar más"""
        self.scroll_tabla._scrollbar.set(first, last)
        
        if self.cargando_lock:
            return
        
        try:
            if float(last) > 0.90 and self.cantidad_cargada < len(self.alumnos_filtrados):
                self.cargando_lock = True
                self.after(10, self._renderizar_lote)
        except:
            pass
    
    # ==================== ACCIONES ====================
    
    def accion_editar(self):
        """Abrir modal de edición"""
        if not self.datos_seleccionados:
            messagebox.showwarning("Aviso", "Seleccione un alumno para editar.")
            return
        
        from ui.views.alumnos.editar_alumno_dialog import EditarAlumnoDialog
        EditarAlumnoDialog(self, self.datos_seleccionados, self.auth_client, self.cargar_datos_thread)
    
    def accion_imprimir(self):
        """Imprimir ficha"""
        if not self.datos_seleccionados:
            messagebox.showwarning("Aviso", "Seleccione un alumno.")
            return
        
        nombre = self.datos_seleccionados.get("nombres", "")
        messagebox.showinfo("Info", f"Generando ficha de: {nombre}")
    
    def accion_eliminar(self):
        """Eliminar alumno"""
        if not self.datos_seleccionados:
            messagebox.showwarning("Aviso", "Seleccione un alumno para anular.")
            return
        
        alumno = self.datos_seleccionados
        nombre = f"{alumno.get('nombres', '')} {alumno.get('apellido_paterno', '')}"
        
        msg = f"¿Está SEGURO de anular la matrícula de:\n\n👤 {nombre}?\n\n⚠️ ESTA ACCIÓN ES IRREVERSIBLE."
        
        if messagebox.askyesno("Confirmar Anulación", msg, icon='warning'):
            alumno_id = alumno.get("id")
            success, data = self.alumno_client.eliminar(alumno_id)
            
            if success:
                messagebox.showinfo("Éxito", "Alumno eliminado correctamente")
                self.cargar_datos_thread()
            else:
                messagebox.showerror("Error", data.get("error", "Error al eliminar"))
    
    def refresh(self):
        """Refrescar datos"""
        self.cargar_datos_thread()

    def _limpiar_tabla(self):
        """Limpiar solo las filas del scroll."""
        for widget in self.scroll_tabla.winfo_children():
            widget.destroy()
