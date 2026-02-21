from app.database import SessionLocal
from app.models.alumno_model import Alumno
from app.models.pago_model import Pago
from sqlalchemy import func, or_
from datetime import date

class TesoreriaController:
    def __init__(self):
        self.db = SessionLocal()

    def buscar_alumno(self, criterio):
        """
        Busca alumnos por DNI, Código, Nombre o Apellidos.
        Se usa ilike (si fuera postgres) o like con % para coincidencia parcial.
        """
        if not criterio:
            return []
            
        # Buscamos coincidencias en cualquiera de los campos principales
        busqueda = f"%{criterio}%"
        
        return self.db.query(Alumno).filter(
            or_(
                Alumno.dni.like(busqueda),
                Alumno.codigo_matricula.like(busqueda),
                Alumno.apell_paterno.like(busqueda),
                Alumno.apell_materno.like(busqueda),
                Alumno.nombres.like(busqueda)
            )
        ).limit(20).all()

    def obtener_estado_cuenta(self, alumno_id):
        """
        Calcula la situación financiera y devuelve DATOS COMPLETOS del alumno.
        """
        alumno = self.db.query(Alumno).filter(Alumno.id == alumno_id).first()
        if not alumno:
            return None
            
        total_pagado = self.db.query(func.sum(Pago.monto)).filter(Pago.alumno_id == alumno_id).scalar() or 0.0
        deuda = alumno.costo_matricula - total_pagado
        historial = self.db.query(Pago).filter(Pago.alumno_id == alumno_id).order_by(Pago.fecha.desc()).all()
        
        return {
            # Datos Identificación
            "nombre_completo": f"{alumno.apell_paterno} {alumno.apell_materno}, {alumno.nombres}",
            "dni": alumno.dni,
            "codigo": alumno.codigo_matricula,
            "info_extra": f"{alumno.grupo or '-'} / {alumno.horario or '-'}", # Ejemplo: Grado A / Mañana
            
            # Datos Financieros
            "costo": alumno.costo_matricula,
            "pagado": total_pagado,
            "deuda": deuda,
            "historial": historial
        }

    def registrar_pago(self, alumno_id, monto, concepto):
        try:
            monto = float(monto)
            # 1. Validación: Monto negativo
            if monto <= 0:
                return False, "El monto debe ser mayor a 0."

            # 2. Validación: Exceso de pago
            deuda_actual = self.obtener_deuda_actual(alumno_id)
            
            # Usamos una pequeña tolerancia (0.01) por si hay errores de redondeo en flotantes
            if monto > (deuda_actual + 0.01):
                return False, f"Error: El monto (S/. {monto}) supera la deuda actual (S/. {deuda_actual:.2f})."

            # 3. Registrar si todo está OK
            nuevo_pago = Pago(
                alumno_id=alumno_id,
                monto=monto,
                concepto=concepto,
                fecha=date.today()
            )
            self.db.add(nuevo_pago)
            self.db.commit()
            return True, "Pago registrado correctamente."
            
        except ValueError:
            return False, "El monto debe ser un número válido."
        except Exception as e:
            self.db.rollback()
            return False, f"Error de base de datos: {str(e)}"
    
    def obtener_deuda_actual(self, alumno_id):
        """Método auxiliar para calcular deuda precisa"""
        alumno = self.db.query(Alumno).filter(Alumno.id == alumno_id).first()
        if not alumno: return 0.0
        
        total_pagado = self.db.query(func.sum(Pago.monto)).filter(Pago.alumno_id == alumno_id).scalar() or 0.0
        return alumno.costo_matricula - total_pagado

    