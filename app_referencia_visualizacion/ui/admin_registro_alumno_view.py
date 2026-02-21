import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry
from app.controllers.alumno_controller import AlumnoController
from datetime import date
import threading  # <--- HILOS AÑADIDOS

# --- IMPORTACIÓN DE ESTILOS CENTRALIZADOS ---
import app.styles.tabla_style as st

class RegistroAlumnoView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.controller = AlumnoController()
        
        self.configure(fg_color="#1a1a1a")

        # --- VARIABLES PARA SCROLL INFINITO ---
        self.lista_alumnos_cache = [] # Todos los datos en memoria
        self.cantidad_cargada = 0     # Cuántos se ven actualmente
        self.lote_tamano = 30         # Cuántos cargar por tanda
        self.cargando_lock = False    # Evitar cargas simultáneas

        # --- Configuración del Grid Principal ---
        self.grid_columnconfigure(0, weight=0) # Panel Izquierdo Fijo
        self.grid_columnconfigure(1, weight=1) # Panel Derecho (Tabla) Expandible
        self.grid_rowconfigure(0, weight=1)

        # ==================== PANEL IZQUIERDO (FORMULARIO SCROLLABLE) ====================
        # (ESTA PARTE PERMANECE EXACTAMENTE IGUAL)
        self.scroll = ctk.CTkScrollableFrame(self, width=420, label_text="Ficha de Matrícula", label_font=("Roboto", 12, "bold"))
        self.scroll.grid(row=0, column=0, padx=(10, 0), pady=10, sticky="nsew")

        # ---------------- 1. DATOS DEL ALUMNO ----------------
        self.seccion(self.scroll, "1. Datos del Alumno")

        self.entry_nombres = self.campo(self.scroll, "Nombres:")
        self.entry_ape_pat = self.campo(self.scroll, "Ap. Paterno:")
        self.entry_ape_mat = self.campo(self.scroll, "Ap. Materno:")
        self.entry_dni = self.campo(self.scroll, "DNI:", solo_numeros=True, max_char=8)
        
        fr_fecha = ctk.CTkFrame(self.scroll, fg_color="transparent")
        fr_fecha.pack(fill="x", pady=2)
        ctk.CTkLabel(fr_fecha, text="Fecha Inscripción:", width=120, anchor="w").pack(side="left", padx=5)
        self.cal_nacimiento = DateEntry(fr_fecha, width=12, background='darkblue', date_pattern='dd/mm/yyyy')
        self.cal_nacimiento.pack(side="left", padx=5)

        # ---------------- 2. DATOS ACADÉMICOS ----------------
        self.seccion(self.scroll, "2. Datos Académicos")
        self.cbo_grupo = self.combo(self.scroll, "Grupo:", ["A", "B", "C", "D"], command=self.actualizar_carreras)
        self.cbo_carrera = self.combo(self.scroll, "Carrera:", [])
        self.cbo_modalidad = self.combo(self.scroll, "Modalidad:", ["PRIMERA OPCION", "ORDINARIO", "COLEGIO", "REFORZAMIENTO"], command=self.actualizar_turnos)
        self.cbo_horario = self.combo(self.scroll, "Horario:", ["MATUTINO", "VESPERTINO", "DOBLE HORARIO"])

        # ---------------- 3. DATOS PADRES / APODERADOS ----------------
        self.seccion(self.scroll, "3. Datos Padres/Apoderados")
        self.entry_padre_nom = self.campo(self.scroll, "Nombres:")
        self.entry_padre_pat = self.campo(self.scroll, "Ap. Paterno:")
        self.entry_padre_mat = self.campo(self.scroll, "Ap. Materno:")
        
        fr_tels = ctk.CTkFrame(self.scroll, fg_color="transparent")
        fr_tels.pack(fill="x")
        self.entry_tel1 = self.campo(fr_tels, "Celular 1:", solo_numeros=True, max_char=9)
        self.entry_tel1.pack(side="left", padx=5, expand=True)
        self.entry_tel2 = self.campo(fr_tels, "Celular 2:", solo_numeros=True, max_char=9)
        self.entry_tel2.pack(side="left", padx=5, expand=True)

        self.entry_desc = self.campo(self.scroll, "Descripción:")

        # ---------------- 4. DATOS ECONÓMICOS ----------------
        self.seccion(self.scroll, "4. Importe y Pagos")
        self.entry_costo = self.campo(self.scroll, "Costo:", solo_numeros=True)
        self.entry_costo.bind("<KeyRelease>", self.calcular_deuda)
        self.entry_importe = self.campo(self.scroll, "A cuenta:", solo_numeros=True)
        self.entry_importe.bind("<KeyRelease>", self.calcular_deuda)
        
        self.entry_deuda = self.campo(self.scroll, "Deuda:")
        self.entry_deuda.configure(state="disabled", fg_color="#eee", text_color="#333")

        fr_pago = ctk.CTkFrame(self.scroll, fg_color="transparent")
        fr_pago.pack(fill="x", pady=5)
        ctk.CTkLabel(fr_pago, text="Fecha Cancelación:", width=120, anchor="w").pack(side="left", padx=5)
        self.cal_pago = DateEntry(fr_pago, width=12, background='green', date_pattern='dd/mm/yyyy')
        self.cal_pago.pack(side="left", padx=5)

        # Botón Guardar (Ahora llama a guardar_thread)
        self.btn_guardar = ctk.CTkButton(self.scroll, text="GUARDAR MATRÍCULA", command=self.guardar_thread, fg_color="#27ae60", height=40)
        self.btn_guardar.pack(fill="x", pady=20, padx=10)


        # ==================== PANEL DERECHO (TABLA CON SCROLL INFINITO) ====================
        
        self.frame_tabla = ctk.CTkFrame(self, fg_color=st.Colors.BG_PANEL)
        self.frame_tabla.grid(row=0, column=1, padx=(10, 10), pady=10, sticky="nsew")

        # Anchos fijos para las columnas
        self.ANCHOS = [80, 200, 100, 50, 200]

        # 1. Cabecera (Header Oscuro)
        self.crear_cabecera()

        # 2. Loader (Indicador de carga invisible por defecto)
        self.lbl_loader = ctk.CTkLabel(self.frame_tabla, text="Cargando...", text_color="#f39c12")
        
        # 3. Cuerpo Scrollable
        self.scroll_tabla = ctk.CTkScrollableFrame(self.frame_tabla, fg_color="transparent")
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- SCROLL INFINITO: INTERCEPTAR SCROLLBAR ---
        # Configuramos el comando del canvas para usar nuestro hook
        self.scroll_tabla._parent_canvas.configure(yscrollcommand=self._hook_scroll)

        # Cargar datos iniciales (Con Hilos)
        self.cargar_tabla_thread()

    # ==================== MÉTODOS DE LA TABLA (OPTIMIZADOS) ====================
    
    def crear_cabecera(self):
        header = ctk.CTkFrame(self.frame_tabla, height=45, fg_color=st.Colors.TABLE_HEADER, corner_radius=5)
        header.pack(fill="x", padx=5, pady=(5, 5))
        
        titulos = ["CÓDIGO", "ALUMNO", "MODALIDAD", "GRP", "CARRERA"]
        for i, t in enumerate(titulos):
            w = self.ANCHOS[i]
            ctk.CTkLabel(header, text=t, font=("Roboto", 11, "bold"), text_color="white", width=w).pack(side="left", padx=2)

    def _hook_scroll(self, first, last):
        """Detecta el movimiento del scrollbar para cargar más datos"""
        # 1. Actualizar la barra visualmente (funcionalidad original)
        self.scroll_tabla._scrollbar.set(first, last)
        
        # 2. Detectar si llegamos al final (95%)
        if self.cargando_lock: return
        try:
            if float(last) > 0.95 and self.cantidad_cargada < len(self.lista_alumnos_cache):
                self.cargando_lock = True
                self.after(10, self._renderizar_siguiente_lote)
        except: pass

    # --- LÓGICA DE HILOS ---

    def cargar_tabla_thread(self):
        """Inicia el hilo de carga de datos"""
        self.lbl_loader.pack(pady=5)
        # Limpiar tabla visual
        for widget in self.scroll_tabla.winfo_children(): widget.destroy()
        
        threading.Thread(target=self._proceso_traer_datos, daemon=True).start()

    def _proceso_traer_datos(self):
        """(Hilo) Consulta a la BD"""
        datos = self.controller.obtener_todos()
        self.after(0, lambda: self._inicializar_tabla(datos))

    def _inicializar_tabla(self, datos):
        """(Main) Recibe datos y pinta el primer lote"""
        self.lbl_loader.pack_forget()
        self.lista_alumnos_cache = datos
        self.cantidad_cargada = 0
        self.cargando_lock = False
        
        if not datos:
            ctk.CTkLabel(self.scroll_tabla, text="\nNo hay alumnos registrados", text_color="gray").pack()
            return

        self._renderizar_siguiente_lote()

    def _renderizar_siguiente_lote(self):
        """Pinta el siguiente grupo de N alumnos"""
        inicio = self.cantidad_cargada
        fin = inicio + self.lote_tamano
        lote = self.lista_alumnos_cache[inicio:fin]

        for alu in lote:
            self._dibujar_fila(alu)
        
        self.cantidad_cargada += len(lote)
        self.cargando_lock = False

    def _dibujar_fila(self, alu):
        """Dibuja una sola fila"""
        # Alternar colores
        idx = self.scroll_tabla.winfo_children().__len__()
        bg = st.Colors.ROW_ODD if idx % 2 == 0 else st.Colors.ROW_EVEN
        
        row = ctk.CTkFrame(self.scroll_tabla, fg_color=bg, corner_radius=5, height=35)
        row.pack(fill="x", pady=2)
        row.pack_propagate(False)
        
        font_row = ("Roboto", 11)

        ctk.CTkLabel(row, text=alu.codigo_matricula, width=self.ANCHOS[0], text_color="white", font=font_row).pack(side="left", padx=2)
        ctk.CTkLabel(row, text=f"{alu.nombres} {alu.apell_paterno} {alu.apell_materno}", width=self.ANCHOS[1], anchor="w", text_color="white", font=font_row).pack(side="left", padx=2)
        ctk.CTkLabel(row, text=alu.modalidad, width=self.ANCHOS[2], text_color="gray", font=font_row).pack(side="left", padx=2)
        ctk.CTkLabel(row, text=alu.grupo, width=self.ANCHOS[3], text_color="#f1c40f", font=("Arial", 11, "bold")).pack(side="left", padx=2)
        ctk.CTkLabel(row, text=alu.carrera[:20], width=self.ANCHOS[4], anchor="w", text_color="gray", font=font_row).pack(side="left", padx=2)

    # ==================== GUARDADO CON HILOS ====================

    def guardar_thread(self):
        """Valida en UI y lanza hilo para guardar"""
        datos = {
            "dni": self.entry_dni.get(),
            "nombres": self.entry_nombres.get(),
            "apell_paterno": self.entry_ape_pat.get(),
            "apell_materno": self.entry_ape_mat.get(),
            "fecha_nacimiento": self.cal_nacimiento.get_date(),
            "grupo": self.cbo_grupo.get(),
            "carrera": self.cbo_carrera.get(),
            "modalidad": self.cbo_modalidad.get(),
            "horario": self.cbo_horario.get(),
            "padre_nombres": self.entry_padre_nom.get(),
            "padre_ape_pat": self.entry_padre_pat.get(),
            "padre_ape_mat": self.entry_padre_mat.get(),
            "tel1": self.entry_tel1.get(),
            "tel2": self.entry_tel2.get(),
            "descripcion": self.entry_desc.get(),
            "costo": self.entry_costo.get() or 0,
            "importe": self.entry_importe.get() or 0,
            "deuda": self.entry_deuda.get() or 0,
            "fecha_cancel": self.cal_pago.get_date()
        }

        errores = self.validar_formulario(datos)
        if errores:
            messagebox.showwarning("Datos Incompletos", "\n".join(errores))
            return

        if not messagebox.askyesno("Confirmar", f"¿Registrar matrícula de {datos['nombres']}?"):
            return

        self.btn_guardar.configure(state="disabled", text="Guardando...")
        
        # Hilo para guardar
        threading.Thread(target=self._proceso_guardar, args=(datos,), daemon=True).start()

    def _proceso_guardar(self, datos):
        exito, mensaje = self.controller.registrar_alumno(datos)
        self.after(0, lambda: self._post_guardado(exito, mensaje))

    def _post_guardado(self, exito, mensaje):
        self.btn_guardar.configure(state="normal", text="GUARDAR MATRÍCULA")
        
        if exito:
            messagebox.showinfo("Registro Exitoso", mensaje)
            self.limpiar_campos()
            # Recargar la tabla (asíncrono) para ver el nuevo registro
            self.cargar_tabla_thread()
        else:
            messagebox.showerror("Error", mensaje)

    # ==================== UI HELPERS (ORIGINALES) ====================
    def seccion(self, parent, titulo):
        ctk.CTkLabel(parent, text=titulo, font=("Roboto", 14, "bold"), text_color="#3498db").pack(pady=(15, 5), anchor="w", padx=5)

    def campo(self, parent, label, solo_numeros=False, max_char=None):
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.pack(fill="x", pady=2)
        ctk.CTkLabel(fr, text=label, width=120, anchor="w").pack(side="left", padx=5)
        ent = ctk.CTkEntry(fr)
        if solo_numeros or max_char:
            vcmd = (self.register(lambda P: self.validar_input(P, solo_numeros, max_char)), '%P')
            ent.configure(validate="key", validatecommand=vcmd)
        ent.pack(side="left", fill="x", expand=True, padx=5)
        ent.bind("<KeyRelease>", lambda e: self.mayusculas(ent))
        return ent

    def combo(self, parent, label, valores, command=None, textoinicial="--Seleccione"):
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.pack(fill="x", pady=2)
        ctk.CTkLabel(fr, text=label, width=120, anchor="w").pack(side="left", padx=5)
        cbo = ctk.CTkComboBox(fr, values=valores, command=command, state="readonly")
        cbo.set(textoinicial)
        cbo.pack(side="left", fill="x", expand=True, padx=5)
        return cbo

    def mayusculas(self, entry):
        if entry.cget("state") != "disabled":
            pos = entry.index("insert")
            txt = entry.get().upper()
            entry.delete(0, 'end')
            entry.insert(0, txt)
            entry.icursor(pos)

    def validar_input(self, texto_nuevo, solo_numeros, max_char):
        if max_char and len(texto_nuevo) > max_char: return False
        if solo_numeros: return texto_nuevo.isdigit() or texto_nuevo == ""
        return True

    # ==================== LÓGICA ORIGINAL ====================
    def actualizar_carreras(self, seleccion):
        opciones = self.controller.obtener_carreras_por_grupo(seleccion)
        self.cbo_carrera.configure(values=opciones)
        self.cbo_carrera.set(opciones[0] if opciones else "--Seleccione")

    def actualizar_turnos(self, seleccion):
        if seleccion == "ORDINARIO":
            self.cbo_horario.set("DOBLE HORARIO")
            self.cbo_horario.configure(state="disabled")
        elif seleccion == "COLEGIO":
            self.cbo_horario.set("DOBLE HORARIO")
            self.cbo_horario.configure(state="disabled")
        else:
            self.cbo_horario.configure(state="normal")
            self.cbo_horario.set("MATUTINO")

    def calcular_deuda(self, event=None):
        try:
            costo = float(self.entry_costo.get() or 0)
            importe = float(self.entry_importe.get() or 0)
            deuda = costo - importe
            self.entry_deuda.configure(state="normal")
            self.entry_deuda.delete(0, 'end')
            self.entry_deuda.insert(0, f"{deuda:.2f}")
            self.entry_deuda.configure(state="disabled")
        except ValueError:
            pass

    def validar_formulario(self, datos):
        errores = []
        if not datos["dni"] or len(datos["dni"]) != 8: errores.append("- El DNI debe tener 8 dígitos exactos.")
        if not datos["nombres"] or not datos["apell_paterno"]: errores.append("- Falta ingresar Nombres o Apellidos.")
        if datos["grupo"] == "--Seleccione": errores.append("- Debe seleccionar un Grupo.")
        if datos["carrera"] == "--Seleccione" or not datos["carrera"]: errores.append("- Debe seleccionar una Carrera.")
        try:
            c = float(datos["costo"])
            i = float(datos["importe"])
            if i > c: errores.append("- El importe pagado no puede ser mayor al costo total.")
        except: errores.append("- Costo o Importe inválidos.")
        return errores

    def limpiar_campos(self):
        def recursive_clear(widget):
            if isinstance(widget, ctk.CTkEntry):
                if widget.cget("state") == "disabled":
                     widget.configure(state="normal")
                     widget.delete(0, "end")
                     widget.configure(state="disabled")
                else:
                    widget.delete(0, "end")
            elif isinstance(widget, ctk.CTkComboBox):
                if widget.cget("state") != "disabled": 
                    widget.set("--Seleccione")
            for child in widget.winfo_children():
                recursive_clear(child)

        recursive_clear(self.scroll)
        self.cal_nacimiento.set_date(date.today())
        self.cal_pago.set_date(date.today())













