import customtkinter as ctk
from tkinter import messagebox
from datetime import date
from sqlalchemy import or_
from app.database import SessionLocal
from app.models.alumno_model import Alumno
from app.models.sesion_model import SesionExamen
from app.models.nota_model import Nota
from app.services.academic_service import obtener_cursos

# --- IMPORTACIÓN DE ESTILOS ---
import app.styles.tabla_style as st

class RegistrarNotasView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        
        self.session_db = SessionLocal()
        self.sesion_actual = None 
        self.lista_filas_alumnos = [] 
        
        # --- VARIABLES DE PAGINACIÓN ---
        self.pagina_actual = 1
        self.items_por_pagina = 30 
        self.total_paginas = 1
        self.alumnos_filtrados_cache = [] 

        # Configuración Visual General
        self.configure(fg_color=st.Colors.BG_MAIN)

        # ==========================================
        # PANEL IZQUIERDO: LISTA DE EXÁMENES
        # ==========================================
        self.panel_izq = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color=st.Colors.BG_MAIN)
        self.panel_izq.pack(side="left", fill="y", padx=(0, 2), pady=0)
        self.panel_izq.pack_propagate(False)

        ctk.CTkLabel(self.panel_izq, text="HISTORIAL EXÁMENES", font=st.Fonts.TITLE, text_color="white").pack(pady=(30, 15))
        
        self.btn_nuevo = ctk.CTkButton(self.panel_izq, text="+ NUEVO EXAMEN", 
                                     fg_color="#2980b9", hover_color="#3498db", height=40,
                                     font=("Roboto", 12, "bold"),
                                     command=self.abrir_popup_crear_examen)
        self.btn_nuevo.pack(pady=(0, 15), padx=20, fill="x")

        ctk.CTkLabel(self.panel_izq, text="Seleccione para editar:", text_color="gray", font=("Roboto", 11)).pack(anchor="w", padx=20)

        self.scroll_sesiones = ctk.CTkScrollableFrame(self.panel_izq, fg_color=st.Colors.BG_PANEL)
        self.scroll_sesiones.pack(fill="both", expand=True, padx=10, pady=(5, 20))

        # ==========================================
        # PANEL DERECHO: FILTROS Y SÁBANA
        # ==========================================
        self.panel_der = ctk.CTkFrame(self, fg_color="transparent") # Transparente para ver el fondo principal
        self.panel_der.pack(side="right", fill="both", expand=True, padx=(0,20), pady=20)

        # Título Dinámico
        self.lbl_titulo_sesion = ctk.CTkLabel(self.panel_der, text="Selecciona un examen", 
                                              font=("Roboto", 24, "bold"), text_color="white")
        self.lbl_titulo_sesion.pack(pady=(0, 15), anchor="w")

        # Barra de Herramientas (Filtros)
        self.frame_tools = ctk.CTkFrame(self.panel_der, fg_color=st.Colors.BG_PANEL, corner_radius=10, height=60)
        self.frame_tools.pack(fill="x", pady=5)
        self.frame_tools.pack_propagate(False)

        # Filtros
        ctk.CTkLabel(self.frame_tools, text="Grupo:", text_color="silver").pack(side="left", padx=(20, 5))
        self.combo_grupo = ctk.CTkComboBox(self.frame_tools, values=["Todos", "A", "B", "C", "D"], width=70)
        self.combo_grupo.set("Todos")
        self.combo_grupo.pack(side="left", padx=5)

        ctk.CTkLabel(self.frame_tools, text="Modalidad:", text_color="silver").pack(side="left", padx=(15, 5))
        self.combo_modalidad = ctk.CTkComboBox(self.frame_tools, 
                                               values=["Todos", "ORDINARIO", "PRIMERA OPCION", "COLEGIO", "REFORZAMIENTO"], 
                                               width=140)
        self.combo_modalidad.set("Todos")
        self.combo_modalidad.pack(side="left", padx=5)

        # Buscador
        self.bg_search = ctk.CTkFrame(self.frame_tools, fg_color="#383838", corner_radius=15, height=30, width=150)
        self.bg_search.pack(side="left", padx=15)
        self.bg_search.pack_propagate(False)
        
        self.entry_busqueda = ctk.CTkEntry(self.bg_search, placeholder_text="Buscar alumno...", 
                                         border_width=0, fg_color="transparent", text_color="white")
        self.entry_busqueda.pack(fill="both", padx=5)
        self.entry_busqueda.bind("<Return>", lambda event: self.buscar_y_reiniciar())

        self.btn_filtrar = ctk.CTkButton(self.frame_tools, text="Filtrar", width=80, fg_color="#DB6403", hover_color="#505050", command=self.buscar_y_reiniciar)
        self.btn_filtrar.pack(side="left", padx=5)

        # Paginación (Derecha)
        self.btn_siguiente = ctk.CTkButton(self.frame_tools, text=">", width=30, fg_color="#34495e", command=self.pagina_siguiente)
        self.btn_siguiente.pack(side="right", padx=10)
        
        self.lbl_paginacion = ctk.CTkLabel(self.frame_tools, text="Pag 0/0", font=("Arial", 12, "bold"), text_color="silver")
        self.lbl_paginacion.pack(side="right", padx=5)

        self.btn_anterior = ctk.CTkButton(self.frame_tools, text="<", width=30, fg_color="#34495e", command=self.pagina_anterior)
        self.btn_anterior.pack(side="right", padx=10)

        # Tabla (Sábana de notas)
        # Usamos un frame contenedor para darle fondo oscuro
        self.fr_tabla_container = ctk.CTkFrame(self.panel_der, fg_color=st.Colors.BG_PANEL, corner_radius=10)
        self.fr_tabla_container.pack(fill="both", expand=True, pady=10)

        self.scroll_tabla = ctk.CTkScrollableFrame(self.fr_tabla_container, fg_color="transparent", orientation="vertical")
        self.scroll_tabla.pack(fill="both", expand=True, padx=10, pady=10)
        
        
        self.grid_frame = ctk.CTkFrame(self.scroll_tabla, fg_color="transparent")
        self.grid_frame.pack(fill="both", expand=True)

        # Botón Guardar
        self.btn_guardar = ctk.CTkButton(self.panel_der, text="💾 GUARDAR NOTAS (Página Actual)", 
                                         fg_color="#27ae60", hover_color="#2ecc71",
                                         font=("Roboto", 13, "bold"),
                                         state="disabled", height=45, command=self.guardar_notas)
        self.btn_guardar.pack(fill="x", pady=5)

        self.cargar_lista_sesiones()

    # --- DEFINICIÓN DE MÉTODOS ---

    def cargar_lista_sesiones(self):
        for w in self.scroll_sesiones.winfo_children(): w.destroy()
        sesiones = self.session_db.query(SesionExamen).order_by(SesionExamen.fecha.desc()).all()
        
        if not sesiones:
            ctk.CTkLabel(self.scroll_sesiones, text="Sin exámenes registrados", text_color="gray").pack(pady=20)
            return
            
        for sesion in sesiones:
            texto = f"{sesion.fecha}\n{sesion.nombre}"
            # Colores para estados
            bg_color = "#34495e" if sesion.estado == "Abierto" else "#2c2c2c"
            txt_color = "white" if sesion.estado == "Abierto" else "gray"
            
            btn = ctk.CTkButton(self.scroll_sesiones, text=texto, fg_color=bg_color, hover_color="#2c3e50",
                                height=50, anchor="w", text_color=txt_color,
                                font=("Roboto", 12),
                                command=lambda s=sesion: self.seleccionar_sesion(s))
            btn.pack(fill="x", pady=2)

    def abrir_popup_crear_examen(self):
        self.popup = ctk.CTkToplevel(self)
        self.popup.title("Nuevo Examen")
        self.popup.geometry("350x300")
        self.popup.attributes("-topmost", True)
        self.popup.configure(fg_color="#2b2b2b") # Fondo oscuro para popup
        
        ctk.CTkLabel(self.popup, text="Nombre del Examen:", font=("Arial", 14, "bold"), text_color="white").pack(pady=(20, 5))
        self.entry_nombre_popup = ctk.CTkEntry(self.popup, width=250, placeholder_text="Ej. Examen Semanal 5")
        self.entry_nombre_popup.pack(pady=5)
        
        ctk.CTkLabel(self.popup, text="Fecha del Examen:", font=("Arial", 14, "bold"), text_color="white").pack(pady=(15, 5))
        frame_fecha = ctk.CTkFrame(self.popup, fg_color="transparent")
        frame_fecha.pack(pady=5)
        
        dias = [str(i) for i in range(1, 32)]
        self.combo_dia = ctk.CTkComboBox(frame_fecha, values=dias, width=60)
        self.combo_dia.set(str(date.today().day))
        self.combo_dia.pack(side="left", padx=2)
        
        meses = [str(i) for i in range(1, 13)]
        self.combo_mes = ctk.CTkComboBox(frame_fecha, values=meses, width=60)
        self.combo_mes.set(str(date.today().month))
        self.combo_mes.pack(side="left", padx=2)
        
        anio_actual = date.today().year
        anios = [str(anio_actual), str(anio_actual + 1)]
        self.combo_anio = ctk.CTkComboBox(frame_fecha, values=anios, width=80)
        self.combo_anio.set(str(anio_actual))
        self.combo_anio.pack(side="left", padx=2)
        
        ctk.CTkButton(self.popup, text="Crear Examen", fg_color="#2980b9", command=self.confirmar_creacion_examen).pack(pady=30)

    def confirmar_creacion_examen(self):
        nombre = self.entry_nombre_popup.get().strip()
        if not nombre: return
        try:
            d, m, a = int(self.combo_dia.get()), int(self.combo_mes.get()), int(self.combo_anio.get())
            fecha = date(a, m, d)
            nueva = SesionExamen(nombre=nombre, fecha=fecha)
            self.session_db.add(nueva)
            self.session_db.commit()
            self.popup.destroy()
            self.cargar_lista_sesiones()
            self.seleccionar_sesion(nueva)
            messagebox.showinfo("Éxito", "Examen creado.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def seleccionar_sesion(self, sesion):
        self.sesion_actual = sesion
        self.lbl_titulo_sesion.configure(text=f"📝 {sesion.nombre} ({sesion.fecha})", text_color="white")
        if sesion.estado == "Cerrado":
            self.btn_guardar.configure(state="disabled", text="🔒 Examen Cerrado", fg_color="gray")
        else:
            self.btn_guardar.configure(state="normal", text="💾 Guardar Notas (Pág. Actual)", fg_color="#27ae60")
        
        self.buscar_y_reiniciar()

    def buscar_y_reiniciar(self, *args):
        if not self.sesion_actual: 
            messagebox.showwarning("Falta Información", "Por favor, seleccione una sección antes de buscar.")
            return
        
        grupo_sel = self.combo_grupo.get()
        modalidad_sel = self.combo_modalidad.get()
        busqueda_txt = self.entry_busqueda.get().strip()

        # Iniciamos la query base
        query = self.session_db.query(Alumno)

        # --- LÓGICA CORREGIDA PARA GRUPO ---
        if grupo_sel != "Todos":
            query = query.filter(Alumno.grupo == grupo_sel)
        # -----------------------------------

        # Lógica de Modalidad (Ya la tenías bien, pero asegúrate que esté así)
        if modalidad_sel != "Todos":
            query = query.filter(Alumno.modalidad == modalidad_sel)

        # Filtro de texto (Buscador)
        if busqueda_txt:
            filtro = or_(Alumno.nombres.ilike(f"%{busqueda_txt}%"),
                         Alumno.apell_paterno.ilike(f"%{busqueda_txt}%"),
                         Alumno.apell_materno.ilike(f"%{busqueda_txt}%"))
            query = query.filter(filtro)

        self.alumnos_filtrados_cache = query.order_by(Alumno.apell_paterno).all()
        
        # Calcular total páginas
        total_items = len(self.alumnos_filtrados_cache)
        if total_items == 0:
            self.total_paginas = 1
        else:
            self.total_paginas = (total_items + self.items_por_pagina - 1) // self.items_por_pagina

        self.pagina_actual = 1
        self.renderizar_pagina_actual()

    def pagina_siguiente(self):
        if self.pagina_actual < self.total_paginas:
            self.pagina_actual += 1
            self.renderizar_pagina_actual()

    def pagina_anterior(self):
        if self.pagina_actual > 1:
            self.pagina_actual -= 1
            self.renderizar_pagina_actual()

    def renderizar_pagina_actual(self):
        grupo_sel = self.combo_grupo.get()
        cursos = obtener_cursos(grupo_sel)

        # Limpiar Grid
        for w in self.grid_frame.winfo_children(): w.destroy()
        self.lista_filas_alumnos = []
        
        # Calcular Slice
        inicio = (self.pagina_actual - 1) * self.items_por_pagina
        fin = inicio + self.items_por_pagina
        alumnos_pagina = self.alumnos_filtrados_cache[inicio:fin]

        self.lbl_paginacion.configure(text=f"Pag {self.pagina_actual}/{self.total_paginas} ({len(self.alumnos_filtrados_cache)} alum.)")

        if not alumnos_pagina:
            ctk.CTkLabel(self.grid_frame, text="No hay alumnos en este grupo.", text_color="gray").pack(pady=20)
            return

        # BATCH FETCHING
        ids_visibles = [a.id for a in alumnos_pagina]
        notas_lote = self.session_db.query(Nota).filter(
            Nota.sesion_id == self.sesion_actual.id,
            Nota.alumno_id.in_(ids_visibles)
        ).all()
        mapa_notas = { (n.alumno_id, n.curso_nombre): n for n in notas_lote }

        # --- CABECERA DE LA SABANA ---
        # Fila 0
        ctk.CTkLabel(self.grid_frame, text="ESTUDIANTE", font=("Arial", 12, "bold"), width=200, anchor="w", text_color="#f1c40f").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        col_idx = 1
        for curso in cursos:
            # Abreviar nombres de cursos largos
            nom_corto = curso[:4].upper()
            ctk.CTkLabel(self.grid_frame, text=nom_corto, font=("Arial", 11, "bold"), width=50, text_color="silver").grid(row=0, column=col_idx)
            col_idx += 1
        ctk.CTkLabel(self.grid_frame, text="PROM", font=("Arial", 12, "bold"), text_color="#2ecc71").grid(row=0, column=col_idx, padx=10)

        # --- FILAS ---
        row_idx = 1
        for i, alumno in enumerate(alumnos_pagina):
            # Fondo alternado para filas (aunque en grid es difícil de aplicar a toda la fila, lo aplicamos a los widgets o un frame contenedor)
            # Para simplificar en grid, dejamos fondo transparente pero usamos separadores si es necesario.
            
            fila_data = {"alumno_id": alumno.id, "nombre": f"{alumno.apell_paterno} {alumno.apell_materno} {alumno.nombres}", "inputs": {}}
            
            # Nombre Alumno
            ctk.CTkLabel(self.grid_frame, text=fila_data["nombre"], anchor="w", text_color="white").grid(row=row_idx, column=0, sticky="w", padx=10, pady=2)

            col_c = 1
            for curso in cursos:
                nota_obj = mapa_notas.get( (alumno.id, curso) )
                val_str = str(nota_obj.valor) if nota_obj else ""

                # Entry Estilizado
                entry = ctk.CTkEntry(self.grid_frame, width=45, height=28, border_width=0, 
                                     fg_color="#3a3a3a", text_color="white", justify="center")
                entry.insert(0, val_str)
                
                if self.sesion_actual.estado == "Cerrado": entry.configure(state="disabled")

                # Bind para calcular promedio en vivo
                entry.bind("<KeyRelease>", lambda e, f=fila_data, c=cursos: self.calcular_promedio_fila(f, c))
                
                entry.grid(row=row_idx, column=col_c, padx=2, pady=2)
                fila_data["inputs"][curso] = entry
                col_c += 1

            # Label Promedio
            lbl_prom = ctk.CTkLabel(self.grid_frame, text="-", width=40, font=("Arial", 12, "bold"))
            lbl_prom.grid(row=row_idx, column=col_c)
            fila_data["lbl_promedio"] = lbl_prom
            
            self.calcular_promedio_fila(fila_data, cursos)
            self.lista_filas_alumnos.append(fila_data)
            row_idx += 1

    def calcular_promedio_fila(self, fila_data, cursos):
        suma, cant = 0.0, 0
        for c in cursos:
            t = fila_data["inputs"][c].get()
            if t.strip():
                try: suma += float(t); cant += 1
                except: pass
        if cant > 0:
            p = suma / cant
            fila_data["lbl_promedio"].configure(text=f"{p:.1f}", text_color="#2ecc71" if p >= 11 else "#e74c3c")
        else:
            fila_data["lbl_promedio"].configure(text="-", text_color="gray")

    def guardar_notas(self):
        if not self.sesion_actual: return
        try:
            c = 0
            for f in self.lista_filas_alumnos:
                aid = f["alumno_id"]
                for cur, ent in f["inputs"].items():
                    txt = ent.get().strip()
                    if txt:
                        try:
                            val = float(txt)
                            nota = self.session_db.query(Nota).filter_by(alumno_id=aid, curso_nombre=cur, sesion_id=self.sesion_actual.id).first()
                            if nota: nota.valor = val
                            else: self.session_db.add(Nota(alumno_id=aid, curso_nombre=cur, sesion_id=self.sesion_actual.id, valor=val))
                            c += 1
                        except: pass
            self.session_db.commit()
            messagebox.showinfo("Guardado", f"Se guardaron las notas de esta página correctamente.")
        except Exception as e:
            self.session_db.rollback()
            messagebox.showerror("Error", str(e))