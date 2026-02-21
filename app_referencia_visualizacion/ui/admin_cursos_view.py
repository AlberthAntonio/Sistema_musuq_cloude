import customtkinter as ctk
from tkinter import messagebox
from app.database import SessionLocal
from app.models.curso_model import Curso, MallaCurricular

# --- IMPORTACIÓN DE ESTILOS ---
import app.styles.tabla_style as st

class GestionCursosView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.session_db = SessionLocal()
        
        # Cache de datos para filtrado rápido
        self.todos_los_cursos = []
        
        # Configuración Visual General
        self.configure(fg_color=st.Colors.BG_MAIN)

        # Layout: Dos columnas (30% Izq - 70% Der)
        self.grid_columnconfigure(0, weight=3) # Catálogo
        self.grid_columnconfigure(1, weight=7) # Malla
        self.grid_rowconfigure(0, weight=1)

        # ============================================================
        #           PANEL IZQUIERDO: CATÁLOGO INTELIGENTE
        # ============================================================
        self.panel_izq = ctk.CTkFrame(self, fg_color=st.Colors.BG_PANEL, corner_radius=0)
        self.panel_izq.grid(row=0, column=0, sticky="nsew", padx=(0, 2), pady=0)
        
        # Título
        ctk.CTkLabel(self.panel_izq, text="CATÁLOGO", font=st.Fonts.TITLE, text_color="white").pack(pady=(20, 5))
        
        # --- 1. BARRA DE CREACIÓN (Compacta) ---
        self.frame_nuevo = ctk.CTkFrame(self.panel_izq, fg_color="#383838", height=35, corner_radius=5)
        self.frame_nuevo.pack(fill="x", padx=15, pady=10)
        
        self.entry_nuevo_curso = ctk.CTkEntry(self.frame_nuevo, placeholder_text="Nuevo curso...", 
                                              border_width=0, fg_color="transparent", text_color="white", height=35)
        self.entry_nuevo_curso.pack(side="left", fill="x", expand=True, padx=5)
        
        btn_add = ctk.CTkButton(self.frame_nuevo, text="CREAR", width=60, height=25, 
                                fg_color="#2980b9", hover_color="#3498db", 
                                font=("Arial", 10, "bold"),
                                command=self.crear_curso_global)
        btn_add.pack(side="right", padx=5)

        # --- 2. BUSCADOR EN TIEMPO REAL ---
        ctk.CTkLabel(self.panel_izq, text="🔍 Buscar materia:", anchor="w", text_color="gray", font=("Roboto", 11)).pack(fill="x", padx=15, pady=(10, 2))
        
        self.entry_buscar = ctk.CTkEntry(self.panel_izq, placeholder_text="Filtrar lista...", height=30)
        self.entry_buscar.pack(fill="x", padx=15, pady=(0, 10))
        self.entry_buscar.bind("<KeyRelease>", self.filtrar_catalogo)

        # --- 3. LISTA SCROLLABLE ---
        self.scroll_cursos = ctk.CTkScrollableFrame(self.panel_izq, fg_color="transparent")
        self.scroll_cursos.pack(fill="both", expand=True, padx=10, pady=5)

        # ============================================================
        #           PANEL DERECHO: MALLA TIPO "CHIPS"
        # ============================================================
        self.panel_der = ctk.CTkFrame(self, fg_color="transparent")
        self.panel_der.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        # Header Derecho
        h_der = ctk.CTkFrame(self.panel_der, fg_color="transparent")
        h_der.pack(fill="x", pady=(0, 10))
        ctk.CTkLabel(h_der, text="MALLA CURRICULAR", font=("Roboto", 24, "bold"), text_color="white").pack(side="left")
        ctk.CTkLabel(h_der, text="Selecciona un grupo para gestionar sus materias", text_color="gray").pack(side="left", padx=20, pady=5)

        # Pestañas de Grupos
        self.tab_grupos = ctk.CTkTabview(self.panel_der, 
                                         fg_color=st.Colors.BG_PANEL,
                                         segmented_button_fg_color="#2b2b2b",
                                         segmented_button_selected_color="#e67e22",
                                         segmented_button_unselected_color="#2b2b2b",
                                         text_color="white",
                                         corner_radius=10)
        self.tab_grupos.pack(fill="both", expand=True)
        
        self.tabs_data = {} # Guardaremos referencias a los widgets de cada tab
        for grupo in ["A", "B", "C", "D", "Único"]:
            tab = self.tab_grupos.add(grupo)
            
            # Scroll container para los CHIPS
            scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
            scroll.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Guardamos la referencia para poder repintar luego
            self.tabs_data[grupo] = scroll

        # Carga Inicial
        self.cargar_catalogo_bd()
        self.cargar_mallas()

    # ============================================================
    #                  LÓGICA DEL CATÁLOGO
    # ============================================================

    def crear_curso_global(self):
        nombre = self.entry_nuevo_curso.get().strip()
        if not nombre: return
        
        try:
            nuevo = Curso(nombre=nombre)
            self.session_db.add(nuevo)
            self.session_db.commit()
            self.entry_nuevo_curso.delete(0, 'end')
            self.cargar_catalogo_bd() # Recargar BD
            messagebox.showinfo("Éxito", f"Curso '{nombre}' creado.")
        except Exception:
            self.session_db.rollback()
            messagebox.showerror("Error", "El curso ya existe.")

    def cargar_catalogo_bd(self):
        """Trae datos de BD a memoria y pinta la lista."""
        cursos = self.session_db.query(Curso).order_by(Curso.nombre).all()
        self.todos_los_cursos = cursos # Cache
        self.filtrar_catalogo() # Pintar

    def filtrar_catalogo(self, event=None):
        """Filtra la lista visualmente sin ir a la BD."""
        texto = self.entry_buscar.get().lower()
        
        # Limpiar UI
        for w in self.scroll_cursos.winfo_children(): w.destroy()
        
        # Filtrar
        filtrados = [c for c in self.todos_los_cursos if texto in c.nombre.lower()]
        
        for c in filtrados:
            self.dibujar_item_catalogo(c)

    def dibujar_item_catalogo(self, curso):
        """Dibuja una fila en el panel izquierdo."""
        frame = ctk.CTkFrame(self.scroll_cursos, fg_color="#2b2b2b", corner_radius=5)
        frame.pack(fill="x", pady=2)
        
        # Nombre
        ctk.CTkLabel(frame, text=curso.nombre, anchor="w", text_color="silver", font=("Roboto", 12)).pack(side="left", padx=10, pady=8)
        
        # Botón "Quick Add" (Flecha o Más)
        btn = ctk.CTkButton(frame, text="➕", width=30, height=20, 
                            fg_color="#27ae60", hover_color="#2ecc71",
                            font=("Arial", 12),
                            command=lambda c=curso: self.agregar_al_grupo_actual(c))
        btn.pack(side="right", padx=5)

    # ============================================================
    #                  LÓGICA DE MALLAS (CHIPS)
    # ============================================================

    def cargar_mallas(self):
        """Recarga los chips de todos los grupos."""
        for grupo, scroll_widget in self.tabs_data.items():
            # Limpiar
            for w in scroll_widget.winfo_children(): w.destroy()
            
            # Obtener cursos del grupo
            asignaciones = self.session_db.query(MallaCurricular, Curso)\
                .join(Curso).filter(MallaCurricular.grupo == grupo).all()
            
            if not asignaciones:
                ctk.CTkLabel(scroll_widget, text="Arrastra o añade cursos desde el catálogo", text_color="gray").pack(pady=20)
                continue

            # --- DIBUJAR CHIPS EN GRID (3 COLUMNAS) ---
            # Usamos un frame interno para el grid
            grid_frame = ctk.CTkFrame(scroll_widget, fg_color="transparent")
            grid_frame.pack(fill="x")
            
            col_count = 3
            for i, (malla, curso) in enumerate(asignaciones):
                row = i // col_count
                col = i % col_count
                
                self.dibujar_chip(grid_frame, curso, malla, row, col)

    def dibujar_chip(self, parent, curso, malla, r, c):
        """Crea una tarjeta pequeña (Chip) para el curso."""
        chip = ctk.CTkFrame(parent, fg_color="#34495e", corner_radius=15, border_width=1, border_color="#4ecdc4")
        chip.grid(row=r, column=c, padx=5, pady=5, sticky="ew")
        
        # Nombre Curso
        # Cortamos el nombre si es muy largo
        nom_display = (curso.nombre[:20] + '..') if len(curso.nombre) > 20 else curso.nombre
        
        ctk.CTkLabel(chip, text=nom_display, font=("Roboto", 12, "bold"), text_color="white").pack(side="left", padx=(15, 5), pady=8)
        
        # Botón Eliminar (X pequeña)
        btn_del = ctk.CTkButton(chip, text="✕", width=25, height=25, 
                                fg_color="transparent", hover_color="#c0392b", text_color="#e74c3c",
                                corner_radius=10,
                                command=lambda m=malla: self.quitar_curso(m))
        btn_del.pack(side="right", padx=5)

        # Configurar peso de columna para que se expandan bien
        parent.grid_columnconfigure(c, weight=1)

    # ============================================================
    #                  ACCIONES
    # ============================================================

    def agregar_al_grupo_actual(self, curso):
        """Añade el curso seleccionado al tab que esté visible."""
        grupo_activo = self.tab_grupos.get() # Retorna "A", "B", etc.
        
        # Validar duplicados
        existe = self.session_db.query(MallaCurricular).filter_by(grupo=grupo_activo, curso_id=curso.id).first()
        if existe:
            # Feedback visual sutil en lugar de popup molesto
            messagebox.showwarning("Aviso", f"'{curso.nombre}' ya está en el Grupo {grupo_activo}.")
            return

        try:
            nueva = MallaCurricular(grupo=grupo_activo, curso_id=curso.id)
            self.session_db.add(nueva)
            self.session_db.commit()
            
            # Recargar SOLO la vista
            self.cargar_mallas()
            
        except Exception as e:
            self.session_db.rollback()
            messagebox.showerror("Error", str(e))

    def quitar_curso(self, malla_obj):
        if messagebox.askyesno("Confirmar", "¿Quitar materia del grupo?"):
            try:
                self.session_db.delete(malla_obj)
                self.session_db.commit()
                self.cargar_mallas()
            except Exception as e:
                self.session_db.rollback()
                messagebox.showerror("Error", str(e))