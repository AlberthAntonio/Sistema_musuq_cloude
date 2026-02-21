from app.database import SessionLocal
from app.models.alumno_model import Alumno
from app.models.pago_model import Pago
from sqlalchemy import func

class RepDeudoresController:
    def __init__(self):
        self.db = SessionLocal()

    def obtener_filtros_disponibles(self):
        """Retorna grupos y modalidades únicas de la BD"""
        grupos = [g[0] for g in self.db.query(Alumno.grupo).distinct().all() if g[0]]
        modalidades = [m[0] for m in self.db.query(Alumno.modalidad).distinct().all() if m[0]]
        return sorted(grupos), sorted(modalidades)

    def obtener_lista_deudores(self, grupo_filtro="Todos", modalidad_filtro="Todas"):
        """
        Busca deudores aplicando filtros de Grupo y Modalidad.
        Calcula el semáforo (Rojo/Naranja/Amarillo).
        """
        query = self.db.query(Alumno)
        
        # 1. Aplicar Filtros
        if grupo_filtro != "Todos":
            query = query.filter(Alumno.grupo == grupo_filtro)
        if modalidad_filtro != "Todas":
            query = query.filter(Alumno.modalidad == modalidad_filtro)
            
        alumnos = query.order_by(Alumno.apell_paterno).all()
        
        lista_reporte = []

        for alu in alumnos:
            # Calcular Deuda
            costo_total = alu.costo_matricula
            
            # Ignorar si el costo es 0 (Becado completo)
            if costo_total <= 0: continue

            total_pagado = self.db.query(func.sum(Pago.monto)).filter(Pago.alumno_id == alu.id).scalar() or 0.0
            deuda = costo_total - total_pagado

            # Consideramos deudor si debe más de 50 céntimos (por redondeos)
            if deuda > 0.50:
                pct_deuda = (deuda / costo_total) * 100
                
                # Regla de Negocio (Semáforo)
                if pct_deuda > 50:
                    icono = "🔴"
                    desc = f"Debe {pct_deuda:.0f}% (>50%)"
                    tag = "CRITICO"
                elif pct_deuda == 50:
                    icono = "🟠"
                    desc = "Debe 50%"
                    tag = "MEDIO"
                else:
                    icono = "🟡"
                    desc = f"Debe {pct_deuda:.0f}% (<50%)"
                    tag = "LEVE"

                lista_reporte.append({
                    "icono": icono,
                    "nombre": f"{alu.apell_paterno} {alu.apell_materno}, {alu.nombres}",
                    "modalidad": alu.modalidad, # Para mostrar en tabla
                    "contacto": alu.celular_padre_1 or "-",
                    "costo": costo_total,
                    "pagado": total_pagado,
                    "deuda": deuda,
                    "estado_desc": desc,
                    "tag": tag,
                    "pct_raw": pct_deuda # Para ordenar
                })

        # Ordenar: Los más críticos arriba
        lista_reporte.sort(key=lambda x: x["pct_raw"], reverse=True)
        
        return lista_reporte