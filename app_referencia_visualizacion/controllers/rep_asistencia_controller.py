from datetime import datetime, date
from sqlalchemy import desc, func, or_
from app.database import SessionLocal
from app.models.alumno_model import Alumno
from app.models.asistencia_model import Asistencia

class ReporteAsistenciaController:
    def __init__(self):
        self.db = SessionLocal()

    def buscar_alumnos(self, texto):
        """Busca coincidencias por nombre o DNI para el autocompletado"""
        filtro = f"%{texto}%"
        resultados = self.db.query(Alumno).filter(
            or_(
                Alumno.nombres.ilike(filtro),
                Alumno.apell_paterno.ilike(filtro),
                Alumno.dni.ilike(filtro)
            )
        ).limit(10).all()
        return resultados

    def obtener_perfil_completo(self, alumno_id, f_inicio_str, f_fin_str):
        """
        Obtiene: 
        1. Datos del alumno
        2. Estadísticas (KPIs) en el rango de fechas
        3. Historial detallado
        """
        try:
            f_inicio = datetime.strptime(f_inicio_str, "%d/%m/%Y").date()
            f_fin = datetime.strptime(f_fin_str, "%d/%m/%Y").date()
        except ValueError:
            return False, "Fechas inválidas", None

        # 1. Datos Alumno
        alumno = self.db.query(Alumno).get(alumno_id)
        if not alumno:
            return False, "Alumno no encontrado", None

        # 2. Historial (Base de la pirámide)
        historial = self.db.query(Asistencia).filter(
            Asistencia.alumno_id == alumno_id,
            Asistencia.fecha >= f_inicio,
            Asistencia.fecha <= f_fin
        ).order_by(desc(Asistencia.fecha)).all()

        # 3. Calcular Estadísticas (KPIs) en Python (más rápido que 3 queries SQL para pocos datos)
        total = len(historial)
        c_puntual = sum(1 for a in historial if a.estado == "PUNTUAL")
        c_tardanza = sum(1 for a in historial if a.estado == "TARDANZA")
        c_falta = sum(1 for a in historial if a.estado == "INASISTENCIA")
        c_justificado = sum(1 for a in historial if a.estado == "JUSTIFICADO")

        # Calcular % de Asistencia Efectiva (Puntual + Tardanza + Justificado vs Total)
        # Ojo: A veces se cuenta Tardanza como 0.5 faltas, aquí lo haremos simple.
        porcentaje = 0
        if total > 0:
            asistencias_reales = c_puntual + c_tardanza + c_justificado
            porcentaje = round((asistencias_reales / total) * 100, 1)

        datos = {
            "alumno": alumno,
            "stats": {
                "total": total,
                "puntual": c_puntual,
                "tardanza": c_tardanza,
                "falta": c_falta,
                "justificado": c_justificado,
                "efectividad": porcentaje
            },
            "historial": [
                {
                    "fecha": h.fecha.strftime("%d/%m/%Y"),
                    "dia": self._obtener_dia_semana(h.fecha),
                    "hora": h.hora.strftime("%H:%M:%S"),
                    "estado": h.estado,
                    "turno": h.turno,
                    "obs": h.observacion or "-"
                } for h in historial
            ]
        }

        return True, "Datos cargados", datos

    def _obtener_dia_semana(self, fecha_obj):
        dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        return dias[fecha_obj.weekday()]