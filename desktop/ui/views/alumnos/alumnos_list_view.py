"""
Panel de Lista de Alumnos
Sistema Musuq Cloud
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
from typing import Dict, List, Optional, Callable

from core.api_client import APIClient, AlumnoClient
from core.theme_manager import ThemeManager as TM
from styles import tabla_style as st


class AlumnosListPanel(ctk.CTkFrame):
    """Panel con tabla de alumnos, filtros y acciones"""
    
    def __init__(self, parent, auth_client: APIClient):
        super().__init__(parent, fg_color="transparent")
        
        self.auth_client = auth_client
        self.alumno_client = AlumnoClient()
        self.alumno_client.token = auth_client.token
        
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
        self.ANCHOS = [80, 90, 280, 120, 50, 110]
        
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
        
        # ==================== BARRA DE FILTROS ====================
        fr_filtros = ctk.CTkFrame(
            panel_izq,
            height=50,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        fr_filtros.pack(fill="x", pady=(0, 10))
        
        # Icono búsqueda
        ctk.CTkLabel(
            fr_filtros,
            text="🔍",
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(15, 5))
        
        # Entry búsqueda
        self.entry_buscar = ctk.CTkEntry(
            fr_filtros,
            placeholder_text="Buscar por DNI, Nombre...",
            width=220,
            height=35,
            border_width=0,
            fg_color=TM.bg_panel(),
            text_color=TM.text()
        )
        self.entry_buscar.pack(side="left", padx=5, pady=8)
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_tabla)
        
        # Separador
        ctk.CTkFrame(fr_filtros, width=2, height=25, fg_color="#505050").pack(side="left", padx=10)
        
        # Filtro Grupo
        ctk.CTkLabel(
            fr_filtros,
            text="Grupo:",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(5, 2))
        
        self.cbo_grupo = ctk.CTkComboBox(
            fr_filtros,
            values=["Todos", "A", "B", "C", "D"],
            width=80,
            command=lambda _: self.filtrar_tabla()
        )
        self.cbo_grupo.set("Todos")
        self.cbo_grupo.pack(side="left", padx=5)
        
        # Filtro Estado
        ctk.CTkLabel(
            fr_filtros,
            text="Estado:",
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(size=11)
        ).pack(side="left", padx=(10, 2))
        
        self.cbo_estado = ctk.CTkComboBox(
            fr_filtros,
            values=["Todos", "Activo", "Inactivo"],
            width=100,
            command=lambda _: self.filtrar_tabla()
        )
        self.cbo_estado.set("Todos")
        self.cbo_estado.pack(side="left", padx=5)
        
        # Botón actualizar
        self.btn_actualizar = ctk.CTkButton(
            fr_filtros,
            text="🔄",
            width=40,
            fg_color="#404040",
            hover_color="#505050",
            command=self.cargar_datos_thread
        )
        self.btn_actualizar.pack(side="right", padx=10)
        
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
    
    def crear_cabecera(self, parent):
        """Crear cabecera de la tabla"""
        header = ctk.CTkFrame(
            parent,
            height=40,
            fg_color=st.Colors.TABLE_HEADER,
            corner_radius=5
        )
        header.pack(fill="x", padx=5, pady=(5, 0))
        
        titulos = ["CÓDIGO", "DNI", "ALUMNO", "MODALIDAD", "GRP", "CELULAR"]
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
        
        # Nombre completo
        nombre = f"{alumno.get('nombres', '')}, {alumno.get('apell_paterno', '')} {alumno.get('apell_materno', '')}"
        celda(nombre.strip(), self.ANCHOS[2], TM.text(), "w")
        
        celda(alumno.get("modalidad", "-"), self.ANCHOS[3], TM.text_secondary())
        
        # Grupo con color
        lbl_grp = ctk.CTkLabel(
            row,
            text=alumno.get("grupo", "-"),
            width=self.ANCHOS[4],
            text_color="#f1c40f",
            font=ctk.CTkFont(family="Arial", size=11, weight="bold")
        )
        lbl_grp.pack(side="left", padx=2)
        lbl_grp.bind("<Button-1>", on_click)
        
        celda(alumno.get("celular", "-"), self.ANCHOS[5], TM.text_secondary())
    
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
        for widget in self.scroll_tabla.winfo_children():
            widget.destroy()
        
        threading.Thread(target=self._traer_datos, daemon=True).start()
    
    def _traer_datos(self):
        """Traer datos del backend"""
        success, data = self.alumno_client.obtener_todos(limit=1000)
        
        if success:
            # El backend puede devolver lista u objeto con items
            if isinstance(data, list):
                alumnos = data
            else:
                alumnos = data.get("items", []) if isinstance(data, dict) else []
            
            self.after(0, lambda: self._finalizar_carga(alumnos))
        else:
            self.after(0, lambda: self._error_carga(data.get("error", "Error desconocido")))
    
    def _finalizar_carga(self, datos: List[Dict]):
        """Finalizar carga y renderizar"""
        self.alumnos_cache = datos
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
        
        # Limpiar tabla
        for widget in self.scroll_tabla.winfo_children():
            widget.destroy()
        
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
