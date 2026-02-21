"""

Vista de Control de Asistencia (Modo Kiosco) - ESTILO MEJORADO

Sistema Musuq Cloud

"""

import customtkinter as ctk
from tkinter import messagebox
import threading
import locale
from datetime import datetime, time as dt_time
from core.api_client import APIClient
from controllers.asistencia_controller import AsistenciaController
from utils.audio_helper import AudioHelper
from styles import tabla_style as st
from core.theme_manager import ThemeManager as TM
from mixins.infinite_scroll_mixin import InfiniteScrollMixin

# Intentar poner fechas en español
try:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
except:
    pass

class AsistenciaView(ctk.CTkFrame, InfiniteScrollMixin):
    """
    Vista principal de asistencia con diseño tipo Kiosco.
    Permite escaneo de códigos, búsqueda y visualización de historial.
    """

    def __init__(self, parent, auth_client: APIClient):
        super().__init__(parent, fg_color="transparent")
        self.controller = AsistenciaController(auth_client.token)
        self.audio = AudioHelper()
        print("DEBUG: AsistenciaView INIT")

        # Variables de estado
        self.fila_seleccionada = None
        self.datos_seleccionados = None
        self.color_original_seleccion = None
        self._reloj_after = None
        self.turno_actual_cache = self._obtener_turno_actual()
        self.filtro_turno_activo = True
        self._monitor_turno_after = None
        self.primer_widget_fila = None
        self.cargando = False
        self.registros_cache = []
        self._debounce_timer = None  # Timer para debounce

        # Anchos de columnas
        self.ANCHOS = [0, 100, 300, 80, 100, 100]

        self.create_widgets()

        # Iniciar procesos que no dependen de datos
        self.actualizar_reloj()
        self.actualizar_turno_display()
        self._verificar_cambio_turno()

        # Cargar cache de nombres PRIMERO, luego tabla
        threading.Thread(target=self._iniciar_carga_datos, daemon=True).start()

        # Foco inicial
        self.after(500, lambda: self.entry_codigo.focus())

    def create_widgets(self):
        # Grid Principal
        self.grid_columnconfigure(0, weight=7)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # ==================== COLUMNA IZQUIERDA (INPUT + TABLA) ====================
        self.card_izq = ctk.CTkFrame(self, fg_color="transparent", corner_radius=10)
        self.card_izq.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=20)
        self.card_izq.grid_rowconfigure(4, weight=1)
        self.card_izq.grid_columnconfigure(0, weight=1)

        # 1. Encabezado con mejor diseño
        header_frame = ctk.CTkFrame(self.card_izq, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 15))

        self.lbl_titulo = ctk.CTkLabel(
            header_frame,
            text="📋 CONTROL DE ASISTENCIA",
            font=ctk.CTkFont(family="Roboto", size=20, weight="bold"),
            text_color=TM.text()
        )
        self.lbl_titulo.pack(side="left")

        self.lbl_instr = ctk.CTkLabel(
            header_frame,
            text="Ingrese CÓDIGO o escanee carnet ➝",
            font=ctk.CTkFont(family="Roboto", size=11),
            text_color=TM.text_secondary()
        )
        self.lbl_instr.pack(side="right")

        # 2. Input Principal con mejor diseño
        self.fr_input = ctk.CTkFrame(self.card_izq, fg_color="transparent")
        self.fr_input.grid(row=1, column=0, sticky="ew", padx=0, pady=(0, 10))

        self.entry_codigo = ctk.CTkEntry(
            self.fr_input,
            placeholder_text="📷 Código aquí...",
            height=50,
            font=ctk.CTkFont(family="Roboto", size=24, weight="bold"),
            border_width=0,
            fg_color=TM.bg_panel(),
            text_color=TM.text(),
            justify="center",
            corner_radius=10
        )
        self.entry_codigo.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_codigo.bind("<Return>", self.registrar_asistencia)

        self.btn_marcar = ctk.CTkButton(
            self.fr_input,
            text="MARCAR",
            width=120,
            height=50,
            fg_color=st.Colors.ASISTENCIA,
            hover_color="#2980b9",
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            corner_radius=10,
            command=self.registrar_asistencia
        )
        self.btn_marcar.pack(side="right")

        # 3. Barra de Búsqueda mejorada (estilo alumnos_list)
        self.fr_busqueda = ctk.CTkFrame(
            self.card_izq,
            height=50,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.fr_busqueda.grid(row=2, column=0, sticky="ew", padx=0, pady=(5, 10))

        ctk.CTkLabel(
            self.fr_busqueda,
            text="🔍",
            font=ctk.CTkFont(size=14),
            text_color=TM.text_secondary()
        ).pack(side="left", padx=(15, 5))

        self.entry_busqueda = ctk.CTkEntry(
            self.fr_busqueda,
            placeholder_text="Buscar por Nombre, DNI o Código...",
            height=35,
            border_width=0,
            fg_color=TM.bg_panel(),
            text_color=TM.text(),
            corner_radius=8
        )
        self.entry_busqueda.pack(side="left", fill="x", expand=True, padx=5, pady=8)
        self.entry_busqueda.bind("<KeyRelease>", self.evento_buscar_alumno)

        # 4. Lista de Resultados Búsqueda
        self.wrapper_resultados = ctk.CTkFrame(self.card_izq, fg_color="transparent", height=0)
        self.fr_resultados = ctk.CTkScrollableFrame(
            self.wrapper_resultados,
            fg_color=TM.bg_card(),
            height=100
        )
        self.fr_resultados.pack(fill="both", expand=True)

        # 5. Tabla Historial con diseño mejorado
        self.fr_tabla = ctk.CTkFrame(self.card_izq, fg_color="transparent")
        self.fr_tabla.grid(row=4, column=0, sticky="nsew", padx=0, pady=(5, 0))

        # Header Tabla mejorado
        self.fr_header_tabla = ctk.CTkFrame(self.fr_tabla, fg_color="transparent")
        self.fr_header_tabla.pack(fill="x", pady=(0, 10))

        fr_info_izq = ctk.CTkFrame(self.fr_header_tabla, fg_color="transparent")
        fr_info_izq.pack(side="left")

        ctk.CTkLabel(
            fr_info_izq,
            text="HISTORIAL DE HOY",
            font=ctk.CTkFont(family="Roboto", size=12, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(side="left")

        self.lbl_contador = ctk.CTkLabel(
            fr_info_izq,
            text="(0/0)",
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.primary(),
            fg_color=TM.bg_panel(),
            corner_radius=5,
            padx=8, pady=2
        )
        self.lbl_contador.pack(side="left", padx=10)

        self.switch_filtro = ctk.CTkSwitch(
            fr_info_izq,
            text="Filtrar turno",
            font=ctk.CTkFont(family="Roboto", size=9),
            command=self.toggle_filtro_turno,
            width=80, height=20, switch_width=35, switch_height=18
        )
        self.switch_filtro.pack(side="left", padx=10)
        self.switch_filtro.select()

        self.lbl_loader = ctk.CTkLabel(
            self.fr_header_tabla,
            text="⏳ Cargando...",
            text_color=TM.warning()
        )

        # Contenedor tabla con estilo alumnos_list
        self.container_list = ctk.CTkFrame(
            self.fr_tabla,
            fg_color=TM.bg_card(),
            corner_radius=10
        )
        self.container_list.pack(fill="both", expand=True)

        self.crear_cabecera()

        self.scroll_tabla = ctk.CTkScrollableFrame(
            self.container_list,
            fg_color="transparent"
        )
        self.scroll_tabla.pack(fill="both", expand=True, padx=5, pady=5)

        # Inicializar Mixin
        self.init_infinite_scroll(self.scroll_tabla, lote_tamano=25)

        # ==================== COLUMNA DERECHA (ESTADO + RELOJ) ====================
        self.card_der = ctk.CTkFrame(
            self,
            width=250,
            fg_color=TM.bg_card(),
            corner_radius=15
        )
        self.card_der.grid(row=0, column=1, sticky="nsew", padx=(0, 20), pady=20)

        # Reloj
        self.fr_reloj = ctk.CTkFrame(self.card_der, fg_color="transparent")
        self.fr_reloj.pack(pady=(40, 10), fill="x")

        self.lbl_reloj = ctk.CTkLabel(
            self.fr_reloj,
            text="00:00:00",
            font=ctk.CTkFont(family="Roboto", size=42, weight="bold"),
            text_color=TM.text()
        )
        self.lbl_reloj.pack()

        self.lbl_fecha = ctk.CTkLabel(
            self.fr_reloj,
            text="--/--/----",
            font=ctk.CTkFont(family="Roboto", size=13),
            text_color=TM.warning()
        )
        self.lbl_fecha.pack()

        # Turno
        self.lbl_turno_activo = ctk.CTkLabel(
            self.card_der,
            text=self._obtener_turno_actual(),
            font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
            text_color=TM.primary(),
            fg_color=TM.bg_panel(),
            corner_radius=8,
            height=35
        )
        self.lbl_turno_activo.pack(pady=(10, 5), padx=20, fill="x")

        # Estado (Grande)
        self.lbl_estado = ctk.CTkLabel(
            self.card_der,
            text="ESPERANDO...",
            width=200,
            height=70,
            corner_radius=15,
            fg_color=TM.bg_panel(),
            text_color=TM.text_secondary(),
            font=ctk.CTkFont(family="Roboto", size=18, weight="bold")
        )
        self.lbl_estado.pack(pady=(20, 30), padx=20)

        # Botones Acción con estilo mejorado
        ctk.CTkLabel(
            self.card_der,
            text="ACCIONES",
            font=ctk.CTkFont(family="Roboto", size=14, weight="bold"),
            text_color=TM.text_secondary()
        ).pack(pady=(20, 15))

        self.fr_botones = ctk.CTkFrame(self.card_der, fg_color="transparent")
        self.fr_botones.pack(fill="both", expand=True, padx=20, pady=5)

        self.btn_limpiar = ctk.CTkButton(
            self.fr_botones,
            text="🧹 REFRESCAR TABLA",
            height=40,
            fg_color="#404040",
            hover_color="#505050",
            command=self.cargar_tabla_thread
        )
        self.btn_limpiar.pack(fill="x", pady=5)

        self.btn_eliminar = ctk.CTkButton(
            self.fr_botones,
            text="🗑️ ELIMINAR",
            height=40,
            fg_color=TM.danger(),
            hover_color="#c0392b",
            state="disabled",
            command=self.eliminar_seleccion
        )
        self.btn_eliminar.pack(fill="x", pady=5)

    # ================= MÉTODOS VISUALES =================

    def crear_cabecera(self):
        header = ctk.CTkFrame(
            self.container_list,
            height=40,
            fg_color=st.Colors.TABLE_HEADER,
            corner_radius=5
        )
        header.pack(fill="x", padx=5, pady=(5, 0))

        fr_columnas = ctk.CTkFrame(header, fg_color="transparent")
        fr_columnas.pack(side="left", padx=5)

        cols = ["", "CÓDIGO", "ALUMNO", "TURNO", "ESTADO", "HORA"]

        for i, t in enumerate(cols):
            if i == 0:
                continue
            w = self.ANCHOS[i]
            ctk.CTkLabel(
                fr_columnas,
                text=t,
                font=ctk.CTkFont(family="Roboto", size=11, weight="bold"),
                text_color="white",
                width=w
            ).pack(side="left", padx=2)

    def actualizar_reloj(self):
        if not self.winfo_exists():
            return

        now = datetime.now()
        self.lbl_reloj.configure(text=now.strftime("%H:%M:%S"))
        self.lbl_fecha.configure(text=now.strftime("%A, %d de %B del %Y").upper())

        self._reloj_after = self.after(1000, self.actualizar_reloj)

    def _obtener_turno_actual(self):
        hora_actual = datetime.now().time()
        if dt_time(6, 0, 0) <= hora_actual < dt_time(13, 0, 0):
            return "🌅 TURNO MAÑANA ACTIVO"
        elif dt_time(13, 0, 0) <= hora_actual <= dt_time(23, 59, 59):
            return "🌆 TURNO TARDE ACTIVO"
        else:
            return "⏸️ FUERA DE HORARIO"

    def actualizar_turno_display(self):
        if not self.winfo_exists():
            return

        self.lbl_turno_activo.configure(text=self._obtener_turno_actual())
        self.after(60000, self.actualizar_turno_display)

    def toggle_filtro_turno(self):
        self.filtro_turno_activo = self.switch_filtro.get()
        self.switch_filtro.configure(
            text="🔍 Solo turno actual" if self.filtro_turno_activo else "📋 Viendo todos"
        )
        self.cargar_tabla_thread()

    # ================= LÓGICA DE DATOS =================

    def cargar_tabla_thread(self):
        print("[DEBUG] cargar_tabla_thread llamado")
        self.lbl_loader.pack(side="right", padx=10)
        self.btn_limpiar.configure(state="disabled")
        self.limpiar_scroll()
        print(f"[DEBUG] Scroll limpiado, widgets restantes: {len(self.scroll_tabla.winfo_children())}")
        threading.Thread(target=self._cargar_datos, daemon=True).start()

    def _cargar_datos(self):
        success, result = self.controller.asistencia_client.obtener_hoy()

        if success:
            registros = result if isinstance(result, list) else result.get("items", [])

            if self.filtro_turno_activo:
                turno_actual_short = "MAÑANA" if "MAÑANA" in self._obtener_turno_actual() else "TARDE"
                registros = [r for r in registros if r.get("turno") == turno_actual_short]

            registros.sort(key=lambda x: x.get("hora") or "", reverse=True)
            self.after(0, lambda: self._inicializar_tabla(registros))
        else:
            self.after(0, lambda: self._error_carga())

    def _inicializar_tabla(self, registros):
        print(f"[DEBUG] _inicializar_tabla con {len(registros)} registros")
        self.lbl_loader.pack_forget()
        self.btn_limpiar.configure(state="normal")

        self.cargar_datos_scroll(registros)
        print(f"[DEBUG] Datos cargados en scroll, cache tiene {len(self._cache_datos_scroll)} items")

        # Actualizar contador con lógica de color
        actual = len(registros)

        if self.filtro_turno_activo:
            turno_actual_str = self._obtener_turno_actual()
            if "MAÑANA" in turno_actual_str:
                turno = "MAÑANA"
            elif "TARDE" in turno_actual_str:
                turno = "TARDE"
            else:
                turno = None

            if turno:
                total = self._calcular_total_esperado(turno)
            else:
                total = self.controller.contar_todos_alumnos()
        else:
            total = self.controller.contar_todos_alumnos()

        # Determinar color según si excede el total
        if actual > total:
            color = TM.danger()
            icono = "⚠️"
        elif actual == total:
            color = TM.success()
            icono = "✅"
        else:
            color = TM.primary()
            icono = "📊"

        self.lbl_contador.configure(
            text=f"{icono} {actual}/{total}",
            text_color=color
        )

    def _verificar_cambio_turno(self):
        """Verifica cambio de turno y recarga automáticamente si está filtrado"""
        if not self.winfo_exists():
            return

        turno_nuevo = self._obtener_turno_actual()

        if turno_nuevo != self.turno_actual_cache:
            if self.filtro_turno_activo:
                self.cargar_tabla_thread()

            self.lbl_estado.configure(
                text=f"🔄 {turno_nuevo}",
                fg_color=TM.primary(),
                text_color="white"
            )

            self.after(4000, lambda: self.lbl_estado.configure(
                text="ESPERANDO...",
                fg_color=TM.bg_panel(),
                text_color=TM.text_secondary()
            ) if self.winfo_exists() else None)

            self.turno_actual_cache = turno_nuevo
            self.actualizar_turno_display()

        if self.winfo_exists():
            self._monitor_turno_after = self.after(60000, self._verificar_cambio_turno)

    def _calcular_total_esperado(self, turno):
        """
        Calcula cuántos alumnos DEBEN asistir al turno especificado.
        El turno (MAÑANA/TARDE) determina qué horarios (MATUTINO/VESPERTINO/DOBLE HORARIO)
        se deben contabilizar.
        Args:
            turno: "MAÑANA" o "TARDE"
        """
        try:
            if turno == "MAÑANA":
                return self.controller.contar_alumnos_por_horario("MATUTINO", "DOBLE HORARIO")
            elif turno == "TARDE":
                return self.controller.contar_alumnos_por_horario("VESPERTINO", "DOBLE HORARIO")
            else:
                return self.controller.contar_todos_alumnos()
        except Exception:
            return 0

    def _error_carga(self):
        self.lbl_loader.pack_forget()
        self.btn_limpiar.configure(state="normal")
        messagebox.showerror("Error", "No se pudieron cargar los registros")

    # ================= REGISTRO DE ASISTENCIA =================

    def registrar_asistencia(self, event=None):
        codigo = self.entry_codigo.get().strip()
        if not codigo:
            return

        self.entry_codigo.configure(state="disabled")
        self.btn_marcar.configure(state="disabled")
        self.lbl_estado.configure(
            text="PROCESANDO...",
            fg_color=TM.warning(),
            text_color="white"
        )

        threading.Thread(target=self._hilo_registrar, args=(codigo,), daemon=True).start()

    def _hilo_registrar(self, codigo):
        exito, mensaje, datos, alerta_turno = self.controller.registrar_por_dni(codigo)
        self.after(0, lambda: self._post_registro(exito, mensaje, datos, alerta_turno))

    def _post_registro(self, exito, mensaje, datos, alerta_turno):
        self.entry_codigo.configure(state="normal")
        self.entry_codigo.delete(0, 'end')
        self.entry_codigo.focus()
        self.btn_marcar.configure(state="normal")

        if not exito:
            self.lbl_estado.configure(
                text="❌ ERROR",
                fg_color=st.Colors.FALTA,
                text_color="white"
            )
            self.audio.reproducir_alerta_error()
            messagebox.showerror("Error", mensaje)
            self._reset_estado()
        else:
            nombre = datos.get("alumno", {}).get("nombres", "Alumno")

            if alerta_turno:
                self.lbl_estado.configure(
                    text=f"⚠️ TURNO CRUZADO\n{nombre}",
                    fg_color=st.Colors.TARDANZA,
                    text_color="white"
                )
                self.audio.reproducir_alerta_turno_cruzado()
            else:
                self.lbl_estado.configure(
                    text=f"✅ REGISTRADO\n{nombre}",
                    fg_color=st.Colors.PUNTUAL,
                    text_color="white"
                )

            self.cargar_tabla_thread()
            self._reset_estado(delay=3000)

    def _reset_estado(self, delay=3000):
        self.after(delay, lambda: self.lbl_estado.configure(
            text="ESPERANDO...",
            fg_color=TM.bg_panel(),
            text_color=TM.text_secondary()
        ) if self.winfo_exists() else None)

    def eliminar_seleccion(self):
        if not self.fila_seleccionada or not self.datos_seleccionados:
            return

        id_asist = self.datos_seleccionados.get("id")
        alumno_id = self.datos_seleccionados.get("alumno_id")
        nombre = f"Alumno {alumno_id}"

        if hasattr(self.controller, 'mapa_alumnos') and alumno_id in self.controller.mapa_alumnos:
            a = self.controller.mapa_alumnos[alumno_id]
            nombre = f"{a.get('nombres', '')} {a.get('apell_paterno', '')} {a.get('apell_materno', '')}".strip()

        confirm = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro de eliminar la asistencia de:\n\n{nombre}?\n\nEsta acción no se puede deshacer."
        )

        if confirm:
            success, msg = self.controller.eliminar_asistencia(id_asist)

            if success:
                self.lbl_estado.configure(
                    text="🗑️ ELIMINADO",
                    fg_color=TM.danger(),
                    text_color="white"
                )
                self.cargar_tabla_thread()
                self._reset_estado()

                self.fila_seleccionada = None
                self.datos_seleccionados = None
                self.btn_eliminar.configure(state="disabled")
            else:
                messagebox.showerror("Error", msg)

    # ================= BÚSQUEDA =================

    def evento_buscar_alumno(self, event):
        """Evento al escribir en la barra de búsqueda con debounce"""
        # Cancelar timer anterior si existe
        if self._debounce_timer:
            self.after_cancel(self._debounce_timer)
        
        # Programar nueva búsqueda en 500ms
        self._debounce_timer = self.after(500, self._ejecutar_busqueda_alumno)

    def _ejecutar_busqueda_alumno(self):
        """Ejecuta la búsqueda real después del debounce"""
        texto = self.entry_busqueda.get().strip()
        print(f"[DEBUG View] Búsqueda solicitada: '{texto}'")

        for w in self.fr_resultados.winfo_children():
            w.destroy()

        if len(texto) < 2:
            print(f"[DEBUG View] Texto insuficiente ({len(texto)} chars) -> Ocultar panel")
            self.wrapper_resultados.grid_forget()
            return

        self.wrapper_resultados.grid(row=3, column=0, sticky="ew", padx=0, pady=(0, 10))

        loading_label = ctk.CTkLabel(
            self.fr_resultados,
            text="🔍 Buscando...",
            text_color=TM.text_secondary()
        )
        loading_label.pack(pady=10)

        threading.Thread(target=self._buscar_hilo, args=(texto,), daemon=True).start()

    def _buscar_hilo(self, texto):
        print(f"[DEBUG View] Iniciando búsqueda en hilo para: '{texto}'")
        resultados = self.controller.buscar_alumnos_general(texto)
        print(f"[DEBUG View] Búsqueda completada: {len(resultados)} resultados")
        self.after(0, lambda: self._mostrar_resultados(resultados))

    def _mostrar_resultados(self, resultados):
        """Mostrar resultados de búsqueda en la UI"""
        print(f"[DEBUG View] _mostrar_resultados llamado con {len(resultados)} items")

        for w in self.fr_resultados.winfo_children():
            w.destroy()

        self.wrapper_resultados.grid(row=3, column=0, sticky="ew", padx=0, pady=(0, 10))
        self.wrapper_resultados.lift()

        if not resultados:
            btn = ctk.CTkButton(
                self.fr_resultados,
                text="⚠️ No se encontraron coincidencias",
                anchor="w",
                fg_color="transparent",
                text_color=TM.text_secondary(),
                hover_color=TM.bg_panel(),
                state="disabled",
                height=35
            )
            btn.pack(fill="x", pady=2, padx=5)
            return

        print(f"[DEBUG View] Renderizando {len(resultados)} resultados")

        for i, res in enumerate(resultados[:10]):
            nombre_completo = res.get('nombre_completo', '')
            if not nombre_completo:
                nombre = res.get('nombres', '')
                paterno = res.get('apell_paterno', '')
                materno = res.get('apell_materno', '')
                nombre_completo = f"{nombre} {paterno} {materno}".strip()

            dni = res.get('dni', 'Sin DNI')
            codigo = res.get('codigo_matricula', '')
            grupo = res.get('grupo', '')

            texto_btn = f"👤 {nombre_completo}"
            if dni != 'Sin DNI':
                texto_btn += f" | DNI: {dni}"
            if codigo:
                texto_btn += f" | Cód: {codigo}"
            if grupo:
                texto_btn += f" | [{grupo}]"

            btn = ctk.CTkButton(
                self.fr_resultados,
                text=texto_btn,
                anchor="w",
                fg_color="transparent",
                text_color=TM.text(),
                hover_color=st.Colors.HOVER,
                height=35,
                command=lambda r=res: self._seleccionar_busqueda(r)
            )
            btn.pack(fill="x", pady=1, padx=5)

        if len(resultados) > 10:
            info = ctk.CTkLabel(
                self.fr_resultados,
                text=f"ℹ️ Mostrando 10 de {len(resultados)} resultados. Refina tu búsqueda.",
                text_color=TM.warning(),
                font=ctk.CTkFont(family="Roboto", size=9)
            )
            info.pack(pady=5)

    def _seleccionar_busqueda(self, alumno):
        print(f"[DEBUG] Seleccionado: {alumno.get('nombres')}")
        self.entry_codigo.delete(0, 'end')
        self.entry_codigo.insert(0, alumno.get("dni"))
        self.registrar_asistencia()

        self.entry_busqueda.delete(0, 'end')
        self.wrapper_resultados.grid_forget()
        for w in self.fr_resultados.winfo_children():
            w.destroy()

    # ================= IMPLEMENTACIÓN MIXIN =================

    def render_fila_scroll(self, reg, index):
        """Renderiza una fila de asistencia usando el mixin"""
        if not self.winfo_exists():
            return

        id_asistencia = reg.get("id")
        alumno_id = reg.get("alumno_id")
        nombre = f"Alumno {alumno_id}"
        codigo = str(alumno_id)

        if hasattr(self.controller, 'mapa_alumnos') and alumno_id in self.controller.mapa_alumnos:
            a = self.controller.mapa_alumnos[alumno_id]
            nombre = f"{a.get('nombres', '')} {a.get('apell_paterno', '')} {a.get('apell_materno', '')}".strip()
            codigo = a.get("dni")
        elif not hasattr(self.controller, 'mapa_alumnos'):
            threading.Thread(target=self._cargar_cache_nombres, daemon=True).start()

        turno = reg.get("turno", "MAÑANA")
        estado = reg.get("estado", "Puntual")
        hora = reg.get("hora", "")
        if isinstance(hora, str):
            hora = hora[:8]

        # Colores de fila mejorados (estilo alumnos_list)
        bg = "#2d2d2d" if index % 2 == 0 else "#363636"

        row = ctk.CTkFrame(
            self._scroll_widget_inf,
            fg_color=bg,
            corner_radius=5,
            height=35
        )
        row.bind("<Button-1>", lambda e, r=row, d=reg: self._seleccionar_fila(e, r, d))
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)

        font_row = ctk.CTkFont(family="Roboto", size=11)

        def lbl(txt, w, col, anchor="center"):
            l = ctk.CTkLabel(
                row,
                text=str(txt),
                width=w,
                text_color=col,
                font=font_row,
                anchor=anchor
            )
            l.pack(side="left", padx=2)
            l.bind("<Button-1>", lambda e, r=row, d=reg: self._seleccionar_fila(e, r, d))

        lbl(codigo, self.ANCHOS[1], TM.text_secondary())
        lbl(nombre, self.ANCHOS[2], TM.text(), "w")

        turno_icono = "🌅" if turno == "MAÑANA" else "🌆"
        lbl(f"{turno_icono} {turno[0]}", self.ANCHOS[3], TM.primary())

        # Badge Estado
        bg_st = TM.bg_panel()
        if "PUNTUAL" in estado:
            bg_st = st.Colors.PUNTUAL
        elif "TARDANZA" in estado:
            bg_st = st.Colors.TARDANZA
        elif "FALTA" in estado:
            bg_st = st.Colors.FALTA

        f_st = ctk.CTkFrame(row, fg_color="transparent", width=self.ANCHOS[4], height=35)
        f_st.pack(side="left", padx=2)
        ctk.CTkLabel(
            f_st,
            text=estado,
            fg_color=bg_st,
            text_color="white",
            width=80,
            height=20,
            corner_radius=5
        ).place(relx=0.5, rely=0.5, anchor="center")

        lbl(hora, self.ANCHOS[5], TM.text_secondary())

    def _iniciar_carga_datos(self):
        """Carga cache de nombres PRIMERO, luego la tabla"""
        print("[DEBUG] _iniciar_carga_datos: cargando cache...")
        self._cargar_cache_nombres()
        print("[DEBUG] _iniciar_carga_datos: cache listo, cargando tabla...")
        self.after(0, self.cargar_tabla_thread)

    def _cargar_cache_nombres(self):
        """Helper para traer lista de alumnos y poder mostrar nombres"""
        print("[DEBUG] _cargar_cache_nombres iniciando...")
        success, res = self.controller.alumno_client.obtener_todos(limit=2000)

        if success:
            items = res if isinstance(res, list) else res.get("items", [])
            self.controller.mapa_alumnos = {a['id']: a for a in items}
            print(f"[DEBUG] Cache de nombres cargado: {len(self.controller.mapa_alumnos)} alumnos")

    def _seleccionar_fila(self, event, row_widget, data):
        """Maneja la selección visual de una fila"""
        if self.fila_seleccionada and self.fila_seleccionada.winfo_exists():
            try:
                self.fila_seleccionada.configure(fg_color=self.color_original_seleccion)
            except:
                pass

        self.fila_seleccionada = row_widget
        self.datos_seleccionados = data
        self.color_original_seleccion = row_widget._fg_color

        # Color de selección consistente con alumnos_list
        row_widget.configure(fg_color="#34495e")

        self.btn_eliminar.configure(state="normal")
