"""
Diálogo Modal para Editar Alumno
Sistema Musuq Cloud
"""

import customtkinter as ctk
from tkinter import messagebox
import threading
from typing import Dict, Callable

from core.api_client import APIClient, AlumnoClient
from core.theme_manager import ThemeManager as TM


class EditarAlumnoDialog(ctk.CTkToplevel):
    """Ventana modal para editar datos de un alumno"""
    
    def __init__(self, parent, alumno_data: Dict, auth_client: APIClient, on_close: Callable):
        super().__init__(parent)
        
        self.alumno_data = alumno_data
        self.alumno_id = alumno_data.get("id")
        self.on_close = on_close
        
        self.alumno_client = AlumnoClient()
        self.alumno_client.token = auth_client.token
        
        self.entries: Dict[str, ctk.CTkEntry] = {}
        self.combos: Dict[str, ctk.CTkComboBox] = {}
        
        # Configurar ventana
        self.title("✏️ Editar Alumno")
        self.geometry("600x550")
        self.resizable(False, False)
        
        # Modal
        self.transient(parent)
        self.grab_set()
        
        # Centrar
        self.after(10, self.center_window)
        
        # Configurar fondo
        self.configure(fg_color=TM.bg_main())
        
        self.create_widgets()
        self.cargar_datos()
    
    def center_window(self):
        """Centrar ventana"""
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f'{w}x{h}+{x}+{y}')
    
    def create_widgets(self):
        """Crear widgets del formulario"""
        
        # Container principal
        main = ctk.CTkFrame(self, fg_color=TM.bg_card(), corner_radius=15)
        main.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 15))
        
        nombre = f"{self.alumno_data.get('nombres', '')} {self.alumno_data.get('apell_paterno', '')}"
        ctk.CTkLabel(
            header,
            text=f"Editando: {nombre}",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=TM.text()
        ).pack(side="left")
        
        ctk.CTkLabel(
            header,
            text=f"ID: {self.alumno_id}",
            font=ctk.CTkFont(size=11),
            text_color=TM.text_secondary()
        ).pack(side="right")
        
        # Separador
        ctk.CTkFrame(main, height=1, fg_color=TM.get_theme().border).pack(fill="x", padx=20)
        
        # Scroll para campos
        scroll = ctk.CTkScrollableFrame(main, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=10)
        
        # ==================== CAMPOS ====================
        
        # Fila 1: DNI, Nombres
        row1 = ctk.CTkFrame(scroll, fg_color="transparent")
        row1.pack(fill="x", pady=5)
        
        self.crear_campo(row1, "dni", "DNI", 100)
        self.crear_campo(row1, "nombres", "Nombres", 200)
        
        # Fila 2: Apellidos
        row2 = ctk.CTkFrame(scroll, fg_color="transparent")
        row2.pack(fill="x", pady=5)
        
        self.crear_campo(row2, "apell_paterno", "Ap. Paterno", 150)
        self.crear_campo(row2, "apell_materno", "Ap. Materno", 150)
        
        # Fila 3: Grupo, Horario, Modalidad
        row3 = ctk.CTkFrame(scroll, fg_color="transparent")
        row3.pack(fill="x", pady=5)
        
        self.crear_combo(row3, "grupo", "Grupo", ["A", "B", "C", "D"], 80)
        self.crear_combo(row3, "horario", "Horario", ["MATUTINO", "VESPERTINO", "DOBLE HORARIO"], 130)
        self.crear_combo(row3, "modalidad", "Modalidad", 
                        ["PRIMERA OPCION", "ORDINARIO", "COLEGIO", "REFORZAMIENTO"], 150,
                        on_change=self.on_modalidad_change)

        # Fila 3b: Nivel y Grado (solo COLEGIO)
        self.row_colegio = ctk.CTkFrame(scroll, fg_color="transparent")
        self.row_colegio.pack(fill="x", pady=5)
        self.crear_combo(self.row_colegio, "nivel", "Nivel", ["PRIMARIA", "SECUNDARIA"], 120,
                         on_change=self.on_nivel_change)
        self.crear_combo(self.row_colegio, "grado", "Grado", [], 100)
        self.row_colegio.pack_forget()  # Oculto por defecto
        
        # Fila 4: Carrera
        row4 = ctk.CTkFrame(scroll, fg_color="transparent")
        row4.pack(fill="x", pady=5)
        
        self.crear_campo(row4, "carrera", "Carrera", 250)
        
        # Fila 5: Celular, Email
        row5 = ctk.CTkFrame(scroll, fg_color="transparent")
        row5.pack(fill="x", pady=5)
        
        self.crear_campo(row5, "celular", "Celular", 120)
        self.crear_campo(row5, "email", "Email", 200)
        
        # Fila 6: Apoderado
        row6 = ctk.CTkFrame(scroll, fg_color="transparent")
        row6.pack(fill="x", pady=5)
        
        self.crear_campo(row6, "apoderado_nombre", "Apoderado", 200)
        self.crear_campo(row6, "apoderado_celular", "Cel. Apoderado", 120)
        
        # Fila 7: Estado
        row7 = ctk.CTkFrame(scroll, fg_color="transparent")
        row7.pack(fill="x", pady=5)
        
        self.crear_combo(row7, "activo", "Estado", ["Activo", "Inactivo"], 100)
        
        # ==================== FOOTER ====================
        footer = ctk.CTkFrame(main, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(10, 20))
        
        # Status
        self.lbl_status = ctk.CTkLabel(
            footer,
            text="",
            font=ctk.CTkFont(size=11)
        )
        self.lbl_status.pack(side="left")
        
        # Botones
        ctk.CTkButton(
            footer,
            text="Cancelar",
            fg_color="#555",
            hover_color="#666",
            width=100,
            command=self.destroy
        ).pack(side="right", padx=(10, 0))
        
        self.btn_guardar = ctk.CTkButton(
            footer,
            text="💾 Guardar",
            fg_color=TM.success(),
            hover_color="#27ae60",
            width=120,
            command=self.guardar_cambios
        )
        self.btn_guardar.pack(side="right")
    
    def crear_campo(self, parent, key: str, label: str, width: int):
        """Crear campo de entrada"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(size=10),
            text_color=TM.text_secondary()
        ).pack(anchor="w")
        
        entry = ctk.CTkEntry(
            frame,
            width=width,
            height=30,
            fg_color=TM.bg_panel()
        )
        entry.pack()
        
        self.entries[key] = entry
    
    def crear_combo(self, parent, key: str, label: str, valores: list, width: int, on_change=None):
        """Crear combobox"""
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(
            frame,
            text=label,
            font=ctk.CTkFont(size=10),
            text_color=TM.text_secondary()
        ).pack(anchor="w")
        
        combo = ctk.CTkComboBox(
            frame,
            values=valores,
            width=width,
            height=30,
            command=on_change if on_change else None
        )
        combo.pack()
        
        self.combos[key] = combo

    def on_modalidad_change(self, seleccion=None):
        """Mostrar u ocultar fila nivel/grado según modalidad"""
        modalidad = self.combos["modalidad"].get()
        if modalidad == "COLEGIO":
            self.row_colegio.pack(fill="x", pady=5)
        else:
            self.row_colegio.pack_forget()
            self.combos["nivel"].set("")
            self.combos["grado"].configure(values=[])
            self.combos["grado"].set("")

    def on_nivel_change(self, seleccion=None):
        """Actualizar opciones de grado según nivel"""
        nivel = self.combos["nivel"].get()
        if nivel == "PRIMARIA":
            grados = ["1°", "2°", "3°", "4°", "5°", "6°"]
        elif nivel == "SECUNDARIA":
            grados = ["1°", "2°", "3°", "4°", "5°"]
        else:
            grados = []
        self.combos["grado"].configure(values=grados)
        self.combos["grado"].set(grados[0] if grados else "")
    
    def cargar_datos(self):
        """Cargar datos del alumno en los campos"""
        for key, entry in self.entries.items():
            valor = self.alumno_data.get(key, "")
            if valor:
                entry.insert(0, str(valor))
        
        for key, combo in self.combos.items():
            if key == "activo":
                valor = "Activo" if self.alumno_data.get("activo", True) else "Inactivo"
            else:
                valor = self.alumno_data.get(key, "")
            
            if valor:
                combo.set(str(valor))

        # Si la modalidad es COLEGIO, mostrar la fila y cargar nivel/grado
        if self.alumno_data.get("modalidad") == "COLEGIO":
            self.row_colegio.pack(fill="x", pady=5)
            nivel = self.alumno_data.get("nivel", "")
            if nivel == "PRIMARIA":
                self.combos["grado"].configure(values=["1°", "2°", "3°", "4°", "5°", "6°"])
            elif nivel == "SECUNDARIA":
                self.combos["grado"].configure(values=["1°", "2°", "3°", "4°", "5°"])
            grado = self.alumno_data.get("grado", "")
            if grado:
                self.combos["grado"].set(grado)
    
    def obtener_datos(self) -> Dict:
        """Obtener datos del formulario"""
        datos = {}
        
        for key, entry in self.entries.items():
            valor = entry.get().strip()
            if valor:
                datos[key] = valor
        
        for key, combo in self.combos.items():
            if key == "activo":
                datos[key] = combo.get() == "Activo"
            else:
                datos[key] = combo.get()
        
        return datos
    
    def guardar_cambios(self):
        """Guardar cambios"""
        datos = self.obtener_datos()
        
        # Validar mínimo
        if not datos.get("dni") or not datos.get("nombres"):
            self.lbl_status.configure(text="❌ DNI y Nombres son requeridos", text_color=TM.danger())
            return
        
        self.btn_guardar.configure(state="disabled", text="⏳ Guardando...")
        
        def do_update():
            success, result = self.alumno_client.actualizar(self.alumno_id, datos)
            self.after(0, lambda: self.post_guardado(success, result))
        
        threading.Thread(target=do_update, daemon=True).start()
    
    def post_guardado(self, success: bool, result: Dict):
        """Callback después de guardar"""
        self.btn_guardar.configure(state="normal", text="💾 Guardar")
        
        if success:
            messagebox.showinfo("Éxito", "Alumno actualizado correctamente")
            self.on_close()  # Refrescar lista
            self.destroy()
        else:
            error = result.get("error", "Error desconocido")
            self.lbl_status.configure(text=f"❌ {error}", text_color=TM.danger())
