"""
PRUEBA DE CTkTable - Estilo Asistencia View
Ejecutar: python prueba_ctktable.py
"""

import customtkinter as ctk
from datetime import datetime
import random

# Instalar si no tienes: pip install CTkTable
try:
    from CTkTable import CTkTable
except ImportError:
    print("⚠️ ERROR: Necesitas instalar CTkTable")
    print("Ejecuta: pip install CTkTable")
    exit()


class PruebaTablaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Configuración ventana
        self.title("🧪 PRUEBA CTkTable - Estilo Dark")
        self.geometry("1200x700")
        
        # Tema dark (igual que tu app)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Colores (copiados de tu código)
        self.COLORS = {
            "bg_card": "#1e1e1e",
            "bg_panel": "#252525",
            "table_header": "#34495e",
            "text": "#e0e0e0",
            "text_secondary": "#a0a0a0",
            "primary": "#3498db",
            "warning": "#f39c12",
            "puntual": "#27ae60",
            "tardanza": "#e67e22",
            "falta": "#e74c3c",
            "hover": "#2c3e50",
            "row_even": "#2d2d2d",
            "row_odd": "#363636"
        }
        
        # Datos de prueba
        self.datos_ejemplo = self.generar_datos_ejemplo(50)
        self.datos_filtrados = self.datos_ejemplo.copy()
        
        self.create_widgets()
        
    def generar_datos_ejemplo(self, cantidad):
        """Genera datos de ejemplo realistas"""
        nombres = [
            "Juan Pérez García", "María López Ruiz", "Carlos Mendoza Silva",
            "Ana Torres Vega", "Luis Ramírez Cruz", "Carmen Flores Díaz",
            "Roberto Sánchez Morales", "Patricia Vargas Romero", "José Castro Herrera",
            "Laura Gutiérrez Ortiz", "Miguel Ángel Rojas", "Sofia Moreno Campos",
            "Diego Fernández Luna", "Valentina Jiménez Ríos", "Sebastián Reyes Mora",
            "Isabella Núñez Vargas", "Mateo Castillo Ponce", "Camila Ramos Aguirre",
            "Santiago Domínguez León", "Martina Guerrero Soto"
        ]
        
        estados = ["PUNTUAL", "TARDANZA", "FALTA"]
        turnos = ["MAÑANA", "TARDE"]
        
        datos = []
        for i in range(cantidad):
            nombre = random.choice(nombres)
            dni = f"{random.randint(10000000, 99999999)}"
            turno = random.choice(turnos)
            estado = random.choices(estados, weights=[70, 20, 10])[0]  # Más puntualidad
            
            # Hora según turno
            if turno == "MAÑANA":
                hora = f"{random.randint(7, 12):02d}:{random.randint(0, 59):02d}:00"
            else:
                hora = f"{random.randint(13, 18):02d}:{random.randint(0, 59):02d}:00"
            
            datos.append({
                "codigo": dni,
                "nombre": nombre,
                "turno": turno,
                "estado": estado,
                "hora": hora
            })
        
        return datos
    
    def create_widgets(self):
        # Grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Frame principal
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # ========== HEADER ==========
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        
        ctk.CTkLabel(
            header_frame,
            text="📋 PRUEBA DE TABLA - CTkTable",
            font=ctk.CTkFont(family="Roboto", size=20, weight="bold"),
            text_color=self.COLORS["text"]
        ).pack(side="left")
        
        ctk.CTkLabel(
            header_frame,
            text="50 registros de ejemplo",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=self.COLORS["text_secondary"]
        ).pack(side="right")
        
        # ========== BARRA DE BÚSQUEDA ==========
        search_frame = ctk.CTkFrame(
            main_frame,
            height=50,
            fg_color=self.COLORS["bg_card"],
            corner_radius=10
        )
        search_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(
            search_frame,
            text="🔍",
            font=ctk.CTkFont(size=14),
            text_color=self.COLORS["text_secondary"]
        ).pack(side="left", padx=(15, 5))
        
        self.entry_busqueda = ctk.CTkEntry(
            search_frame,
            placeholder_text="Buscar por nombre, DNI...",
            height=35,
            border_width=0,
            fg_color=self.COLORS["bg_panel"],
            text_color=self.COLORS["text"],
            corner_radius=8
        )
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=5, pady=8)
        self.entry_busqueda.bind("<KeyRelease>", self.buscar)
        
        ctk.CTkButton(
            search_frame,
            text="Limpiar",
            width=100,
            command=self.limpiar_busqueda,
            fg_color=self.COLORS["bg_panel"],
            hover_color=self.COLORS["hover"]
        ).pack(side="right", padx=5)
        
        # ========== INFO TABLA ==========
        info_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        info_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(
            info_frame,
            text="HISTORIAL DE HOY",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=self.COLORS["text_secondary"]
        ).pack(side="left")
        
        self.lbl_contador = ctk.CTkLabel(
            info_frame,
            text=f"({len(self.datos_ejemplo)}/{len(self.datos_ejemplo)})",
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=self.COLORS["primary"],
            fg_color=self.COLORS["bg_panel"],
            corner_radius=5,
            padx=8, pady=2
        )
        self.lbl_contador.pack(side="left", padx=10)
        
        # ========== CONTENEDOR TABLA ==========
        table_container = ctk.CTkFrame(
            main_frame,
            fg_color=self.COLORS["bg_card"],
            corner_radius=10
        )
        table_container.grid(row=3, column=0, sticky="nsew")
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # ========== TABLA CTkTable ==========
        self.crear_tabla(table_container)
        
        # ========== BOTONES ACCIÓN ==========
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        
        ctk.CTkButton(
            btn_frame,
            text="🔄 Recargar Datos",
            command=self.recargar_datos,
            fg_color=self.COLORS["primary"],
            hover_color="#2980b9",
            height=40
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="➕ Agregar 10 más",
            command=self.agregar_datos,
            fg_color="#27ae60",
            hover_color="#229954",
            height=40
        ).pack(side="left", padx=5)
        
        self.btn_info = ctk.CTkButton(
            btn_frame,
            text="ℹ️ Info de selección",
            command=self.mostrar_seleccion,
            fg_color=self.COLORS["warning"],
            hover_color="#d68910",
            height=40,
            state="disabled"
        )
        self.btn_info.pack(side="right", padx=5)
        
    def crear_tabla(self, parent):
        """Crea la tabla con CTkTable"""
        
        # Preparar datos para CTkTable (formato matriz)
        valores = self.preparar_valores(self.datos_filtrados)
        
        # Crear tabla (solo parámetros compatibles)
        self.tabla = CTkTable(
            parent,
            values=valores,
            colors=[self.COLORS["row_even"], self.COLORS["row_odd"]],
            header_color=self.COLORS["table_header"],
            hover_color=self.COLORS["hover"],
            text_color=self.COLORS["text"],
            corner_radius=5,
            command=self.tabla_click
        )
        self.tabla.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
    
    def preparar_valores(self, datos):
        """Convierte los datos al formato de CTkTable"""
        # Header
        valores = [["CÓDIGO", "ALUMNO", "TURNO", "ESTADO", "HORA"]]
        
        # Filas
        for d in datos:
            turno_icono = "🌅 M" if d["turno"] == "MAÑANA" else "🌆 T"
            
            # Formatear estado con color (simulado con emoji)
            if d["estado"] == "PUNTUAL":
                estado_texto = "✅ PUNTUAL"
            elif d["estado"] == "TARDANZA":
                estado_texto = "⚠️ TARDANZA"
            else:
                estado_texto = "❌ FALTA"
            
            valores.append([
                d["codigo"],
                d["nombre"],
                turno_icono,
                estado_texto,
                d["hora"]
            ])
        
        return valores
    
    def tabla_click(self, info):
        """Maneja el click en la tabla"""
        fila = info["row"]
        columna = info["column"]
        valor = info["value"]
        
        # Ignorar header (fila 0)
        if fila == 0:
            return
        
        # Habilitar botón de info
        self.btn_info.configure(state="normal")
        
        print(f"📍 Click en Fila {fila}, Columna {columna}: {valor}")
    
    def buscar(self, event):
        """Filtra la tabla según búsqueda"""
        texto = self.entry_busqueda.get().strip().lower()
        
        if not texto:
            self.datos_filtrados = self.datos_ejemplo.copy()
        else:
            self.datos_filtrados = [
                d for d in self.datos_ejemplo
                if texto in d["nombre"].lower() or texto in d["codigo"]
            ]
        
        # Actualizar tabla
        self.actualizar_tabla()
    
    def limpiar_busqueda(self):
        """Limpia la búsqueda"""
        self.entry_busqueda.delete(0, 'end')
        self.datos_filtrados = self.datos_ejemplo.copy()
        self.actualizar_tabla()
    
    def actualizar_tabla(self):
        """Actualiza los valores de la tabla"""
        nuevos_valores = self.preparar_valores(self.datos_filtrados)
        
        # Actualizar CTkTable
        self.tabla.update_values(nuevos_valores)
        
        # Actualizar contador
        self.lbl_contador.configure(
            text=f"({len(self.datos_filtrados)}/{len(self.datos_ejemplo)})"
        )
        
        # Cambiar color contador si está filtrado
        if len(self.datos_filtrados) < len(self.datos_ejemplo):
            self.lbl_contador.configure(text_color=self.COLORS["warning"])
        else:
            self.lbl_contador.configure(text_color=self.COLORS["primary"])
    
    def recargar_datos(self):
        """Recarga los datos de ejemplo"""
        self.datos_ejemplo = self.generar_datos_ejemplo(50)
        self.datos_filtrados = self.datos_ejemplo.copy()
        self.actualizar_tabla()
        print("✅ Datos recargados")
    
    def agregar_datos(self):
        """Agrega 10 registros más"""
        nuevos = self.generar_datos_ejemplo(10)
        self.datos_ejemplo.extend(nuevos)
        self.datos_filtrados = self.datos_ejemplo.copy()
        self.actualizar_tabla()
        print(f"✅ Agregados 10 registros. Total: {len(self.datos_ejemplo)}")
    
    def mostrar_seleccion(self):
        """Muestra info de la fila seleccionada"""
        # CTkTable no tiene selección persistente por defecto
        # Esta es una funcionalidad limitada
        print("ℹ️ Funcionalidad de selección limitada en CTkTable")
        print("   Considera usar Treeview para selección avanzada")


if __name__ == "__main__":
    print("🚀 Iniciando prueba de CTkTable...")
    print("=" * 50)
    print("Características:")
    print("✓ Estilo dark (igual a tu app)")
    print("✓ 50 registros de ejemplo")
    print("✓ Búsqueda en tiempo real")
    print("✓ Colores alternados")
    print("✓ Hover effect")
    print("=" * 50)
    
    app = PruebaTablaApp()
    app.mainloop()