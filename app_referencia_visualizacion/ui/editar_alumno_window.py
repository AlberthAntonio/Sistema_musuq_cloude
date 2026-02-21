import customtkinter as ctk
from tkcalendar import DateEntry
from tkinter import messagebox
from app.controllers.alumno_controller import AlumnoController

class EditarAlumnoWindow(ctk.CTkToplevel):
    def __init__(self, parent, alumno_id, on_close_callback):
        super().__init__(parent)
        self.controller = AlumnoController()
        self.alumno_id = alumno_id
        self.callback = on_close_callback

        # Configuración de la ventana
        self.title("Editar Alumno")
        self.geometry("500x700")
        self.resizable(False, False)
        
        # Modalidad (Bloquea la ventana de atrás)
        self.transient(parent)
        self.grab_set()

        # Título
        ctk.CTkLabel(self, text="Editar Datos del Alumno", font=("Roboto", 20, "bold")).pack(pady=20)

        # --- Formulario Scrollable ---
        self.scroll = ctk.CTkScrollableFrame(self, width=450, height=500)
        self.scroll.pack(padx=20, pady=(0, 20), fill="both", expand=True)

        # --- 1. DATOS PERSONALES (Con validación de Mayúsculas y Números) ---
        self.entry_nombres = self.crear_campo("Nombres:", mayusculas=True)
        self.entry_ape_pat = self.crear_campo("Ap. Paterno:", mayusculas=True)
        self.entry_ape_mat = self.crear_campo("Ap. Materno:", mayusculas=True)
        
        # DNI: Solo números, máx 8 dígitos
        self.entry_dni = self.crear_campo("DNI:", solo_numeros=True, max_char=8)
        
        # Fecha Nacimiento
        fr_fecha = ctk.CTkFrame(self.scroll, fg_color="transparent")
        fr_fecha.pack(fill="x", pady=5)
        ctk.CTkLabel(fr_fecha, text="Fecha Nacimiento:", width=130, anchor="w").pack(side="left", padx=5)
        self.cal_nacimiento = DateEntry(fr_fecha, width=12, background='darkblue', date_pattern='yyyy-mm-dd')
        self.cal_nacimiento.pack(side="left", padx=5)

        # --- 2. DATOS ACADÉMICOS ---
        self.cbo_grupo = self.crear_combo("Grupo:", ["A", "B", "C", "D"])
        self.cbo_modalidad = self.crear_combo("Modalidad:", ["PRIMERA OPCION", "ORDINARIO", "COLEGIO", "REFORZAMIENTO"])
        self.cbo_turno = self.crear_combo("Turno:", ["MAÑANA", "TARDE", "DOBLE HORARIO", "SIN TURNO"])
        
        self.cbo_carrera = self.crear_combo("Carrera:", [])
        # Actualizar carreras al cambiar grupo
        self.cbo_grupo.configure(command=self.actualizar_carreras_combo)

        # --- 3. APODERADO Y CONTACTO ---
        ctk.CTkLabel(self.scroll, text="Datos Apoderado", font=("Roboto", 14, "bold"), text_color="#3498db").pack(pady=(20, 5), anchor="w")
        
        self.entry_padre_completo = self.crear_campo("Nombre Completo:", mayusculas=True)
        
        # Celulares: Solo números, máx 9 dígitos
        self.entry_tel1 = self.crear_campo("Celular 1:", solo_numeros=True, max_char=9)
        self.entry_tel2 = self.crear_campo("Celular 2:", solo_numeros=True, max_char=9)
        
        self.entry_desc = self.crear_campo("Descripción:", mayusculas=True)

        # Botón Guardar
        self.btn_guardar = ctk.CTkButton(self, text="GUARDAR CAMBIOS", command=self.guardar_cambios, fg_color="#27ae60", height=45)
        self.btn_guardar.pack(fill="x", padx=20, pady=(10, 20))

        # Cargar datos al iniciar
        self.cargar_datos()

    # ================= UI HELPERS MEJORADOS =================

    def crear_campo(self, label, solo_numeros=False, max_char=None, mayusculas=False):
        """Crea un campo con etiqueta y validaciones opcionales"""
        fr = ctk.CTkFrame(self.scroll, fg_color="transparent")
        fr.pack(fill="x", pady=2)
        
        ctk.CTkLabel(fr, text=label, width=130, anchor="w").pack(side="left", padx=5)
        
        entry = ctk.CTkEntry(fr)
        
        # 1. Validación de Números y Longitud
        if solo_numeros or max_char:
            # Registramos la función de validación en Tkinter
            vcmd = (self.register(lambda P: self.validar_input(P, solo_numeros, max_char)), '%P')
            entry.configure(validate="key", validatecommand=vcmd)
        
        # 2. Conversión a Mayúsculas automática
        if mayusculas:
            entry.bind("<KeyRelease>", lambda e: self.forzar_mayusculas(entry))
            
        entry.pack(side="left", fill="x", expand=True)
        return entry

    def crear_combo(self, label, values):
        fr = ctk.CTkFrame(self.scroll, fg_color="transparent")
        fr.pack(fill="x", pady=2)
        ctk.CTkLabel(fr, text=label, width=130, anchor="w").pack(side="left", padx=5)
        cbo = ctk.CTkComboBox(fr, values=values, state="readonly")
        cbo.pack(side="left", fill="x", expand=True)
        return cbo

    # ================= LÓGICA DE VALIDACIÓN =================

    def validar_input(self, texto_nuevo, solo_numeros, max_char):
        """Función que decide si se acepta o rechaza una tecla pulsada"""
        # Si hay límite de caracteres
        if max_char and len(texto_nuevo) > max_char:
            return False
            
        # Si debe ser solo números
        if solo_numeros:
            # Permitimos vacío (para poder borrar) o si es dígito
            if texto_nuevo == "":
                return True
            return texto_nuevo.isdigit()
            
        return True

    def forzar_mayusculas(self, entry):
        """Convierte el texto a mayúsculas sin perder la posición del cursor"""
        var = entry.get()
        if var != var.upper():
            pos = entry.index("insert") # Guardamos posición del cursor
            entry.delete(0, 'end')
            entry.insert(0, var.upper())
            entry.icursor(pos) # Restauramos posición

    # ================= LÓGICA DE DATOS =================

    def cargar_datos(self):
        alumno = self.controller.obtener_por_id(self.alumno_id)
        if not alumno:
            messagebox.showerror("Error", "No se pudo cargar el alumno.")
            self.destroy()
            return

        # Llenar campos
        self.entry_nombres.insert(0, alumno.nombres)
        self.entry_ape_pat.insert(0, alumno.apell_paterno)
        self.entry_ape_mat.insert(0, alumno.apell_materno)
        self.entry_dni.insert(0, alumno.dni)
        
        if alumno.fecha_nacimiento:
            self.cal_nacimiento.set_date(alumno.fecha_nacimiento)
        
        self.cbo_grupo.set(alumno.grupo)
        self.cbo_modalidad.set(alumno.modalidad or "")
        self.cbo_turno.set(alumno.turno or "")
        
        self.actualizar_carreras_combo(alumno.grupo)
        self.cbo_carrera.set(alumno.carrera or "")

        self.entry_padre_completo.insert(0, alumno.nombre_padre_completo or "")
        self.entry_tel1.insert(0, alumno.celular_padre_1 or "")
        self.entry_tel2.insert(0, alumno.celular_padre_2 or "")
        self.entry_desc.insert(0, alumno.descripcion or "")

    def actualizar_carreras_combo(self, grupo):
        carreras = self.controller.obtener_carreras_por_grupo(grupo)
        self.cbo_carrera.configure(values=carreras)
        if carreras:
            # Si la carrera actual no está en la lista nueva, poner la primera
            current = self.cbo_carrera.get()
            if current not in carreras:
                self.cbo_carrera.set(carreras[0])

    def guardar_cambios(self):
        # Recolección de datos
        datos = {
            "nombres": self.entry_nombres.get(),
            "apell_paterno": self.entry_ape_pat.get(),
            "apell_materno": self.entry_ape_mat.get(),
            "dni": self.entry_dni.get(),
            "fecha_nacimiento": self.cal_nacimiento.get_date(),
            "grupo": self.cbo_grupo.get(),
            "modalidad": self.cbo_modalidad.get(),
            "turno": self.cbo_turno.get(),
            "carrera": self.cbo_carrera.get(),
            "nombre_padre_completo": self.entry_padre_completo.get(),
            "tel1": self.entry_tel1.get(),
            "tel2": self.entry_tel2.get(),
            "descripcion": self.entry_desc.get()
        }

        # Validaciones básicas antes de enviar
        if len(datos["dni"]) != 8:
            messagebox.showwarning("Dato Inválido", "El DNI debe tener 8 dígitos exactos.")
            return

        if messagebox.askyesno("Confirmar", "¿Guardar los cambios realizados?"):
            exito, msg = self.controller.actualizar_alumno(self.alumno_id, datos)
            if exito:
                messagebox.showinfo("Éxito", msg)
                if self.callback:
                    self.callback() # Actualiza la tabla de atrás
                self.destroy()
            else:
                messagebox.showerror("Error", msg)
























                