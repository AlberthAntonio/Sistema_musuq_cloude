"""
Mixin para agregar funcionalidad de Scroll Infinito a cualquier vista
con CustomTkinter ScrollableFrame.

Autor: Sistema de Asistencia Pro
Fecha: Enero 2026
"""

import customtkinter as ctk

class InfiniteScrollMixin:
    """
    Mixin que proporciona scroll infinito para tablas con CustomTkinter.
    """
    
    def init_infinite_scroll(self, scroll_widget, lote_tamano=20):
        """
        Inicializa el sistema de scroll infinito.
        
        Args:
            scroll_widget: El CTkScrollableFrame donde se mostrarán los datos
            lote_tamano: Cuántos registros cargar por lote (default: 20)
        """
        # Referencias
        self._scroll_widget_inf = scroll_widget
        self.lote_tamano = lote_tamano
        
        # Variables de control
        self._cache_datos_scroll = []
        self._registros_cargados_scroll = 0
        self._cargando_mas_scroll = False
        
        # Hook del scroll
        try:
            self._scroll_widget_inf._parent_canvas.configure(
                yscrollcommand=self._hook_scroll_infinito
            )
        except Exception as e:
            print(f"⚠️ Error configurando hook de scroll: {e}")
        
        # Label indicador de "Cargando más..."
        self._lbl_cargando_mas = ctk.CTkLabel(
            self._scroll_widget_inf,
            text="⏳ Cargando más registros...",
            text_color="#3498db",
            font=("Roboto", 10, "italic")
        )
    
    def cargar_datos_scroll(self, lista_datos):
        """
        Carga datos en el cache y renderiza el primer lote.
        
        Args:
            lista_datos: Lista de objetos/diccionarios a mostrar
        """
        # Guardar en cache
        self._cache_datos_scroll = lista_datos
        self._registros_cargados_scroll = 0
        self._cargando_mas_scroll = False
        
        # Validar si hay datos
        if not lista_datos:
            return
        
        # Renderizar primer lote
        self._renderizar_siguiente_lote_scroll()
    
    def limpiar_scroll(self):
        """Limpia todos los widgets del scroll y resetea variables"""
        if not self._scroll_widget_inf.winfo_exists():
            return

        for widget in self._scroll_widget_inf.winfo_children():
            try:
                widget.destroy()
            except:
                pass
        
        self._cache_datos_scroll = []
        self._registros_cargados_scroll = 0
        self._cargando_mas_scroll = False
    
    def resetear_scroll(self):
        """Vuelve al inicio del scroll"""
        try:
            if self._scroll_widget_inf.winfo_exists():
                self._scroll_widget_inf._parent_canvas.yview_moveto(0.0)
        except:
            pass
    
    def _hook_scroll_infinito(self, first, last):
        """
        Hook que detecta cuando el usuario hace scroll.
        Carga más datos automáticamente al llegar al 90%.
        """
        if not self._scroll_widget_inf.winfo_exists():
            return

        # 1. Actualizar scrollbar visual
        try:
            self._scroll_widget_inf._scrollbar.set(first, last)
        except:
            pass
        
        # 2. Validaciones
        if self._cargando_mas_scroll:
            return
        if not self._cache_datos_scroll:
            return
        
        # 3. Detectar si llegamos al 90% del scroll
        try:
            posicion_actual = float(last)
            
            if (posicion_actual >= 0.90 and 
                self._registros_cargados_scroll < len(self._cache_datos_scroll)):
                
                # Activar lock
                self._cargando_mas_scroll = True
                
                # Mostrar indicador
                try:
                    if self._lbl_cargando_mas.winfo_exists():
                        self._lbl_cargando_mas.pack(pady=10)
                except:
                    pass
                
                # Cargar siguiente lote con delay
                if self._scroll_widget_inf.winfo_exists():
                    self._scroll_widget_inf.after(200, self._renderizar_siguiente_lote_scroll)
        
        except Exception as e:
            if "bad window path" not in str(e):
                print(f"Error en _hook_scroll_infinito: {e}")
            self._cargando_mas_scroll = False
    
    def _renderizar_siguiente_lote_scroll(self):
        """
        Renderiza el siguiente lote de registros.
        Llama a render_fila_scroll() para cada item.
        """
        if not self._scroll_widget_inf.winfo_exists():
            return

        # Calcular rango del lote
        inicio = self._registros_cargados_scroll
        fin = inicio + self.lote_tamano
        
        # Extraer lote
        lote = self._cache_datos_scroll[inicio:fin]
        
        # Renderizar cada item
        for item in lote:
            # Validar existencia antes de cada render (por si cierran durante el loop)
            if not self._scroll_widget_inf.winfo_exists():
                break

            # Llamar al método abstracto (debe ser implementado por la vista)
            try:
                self.render_fila_scroll(item, self._registros_cargados_scroll)
            except AttributeError:
                print("⚠️ Error: Debes implementar el método render_fila_scroll(item, index) en tu vista")
                break
            except Exception as e:
                # Si falla el render de una fila (ej. widget destruido), paramos
                break
            
            self._registros_cargados_scroll += 1
        
        # Ocultar indicador
        try:
            if self._lbl_cargando_mas.winfo_exists():
                self._lbl_cargando_mas.pack_forget()
        except:
            pass
        
        # Liberar lock
        self._cargando_mas_scroll = False
    
    def render_fila_scroll(self, item, index):
        """
        Método abstracto que DEBE ser implementado por cada vista.
        """
        raise NotImplementedError(
            "Debes implementar el método render_fila_scroll(item, index) en tu vista"
        )

    def get_total_registros(self):
        """Retorna el total de registros en el cache"""
        return len(self._cache_datos_scroll)
