from datetime import datetime, date, timedelta
from sqlalchemy import desc, func, or_
from app.database import SessionLocal
from app.models.asistencia_model import Asistencia
from app.models.alumno_model import Alumno

class ReporteInasistenciaController:
    def __init__(self):
        self.db = SessionLocal()

    def obtener_inasistencias_dia(self, fecha_str, turno, grupo, modalidad, solo_injustificadas):
        """
        Busca las inasistencias de un día específico y calcula estadísticas.
        """
        try:
            fecha_consulta = datetime.strptime(fecha_str, "%d/%m/%Y").date()
        except ValueError:
            return False, "Fecha inválida", {}, []

        # 1. Query Base: Alumnos que tienen registro de "INASISTENCIA" o "JUSTIFICADO" ese día
        #    (Asumimos que "Falta" implica cualquiera de los dos estados de ausencia)
        query = self.db.query(Asistencia, Alumno).join(Alumno).filter(
            Asistencia.fecha == fecha_consulta,
            or_(Asistencia.estado == "INASISTENCIA", Asistencia.estado == "JUSTIFICADO")
        )

        # 2. Filtros
        if turno and turno != "Todos":
            query = query.filter(Asistencia.turno == turno)
        if grupo and grupo != "Todos":
            query = query.filter(Alumno.grupo == grupo)
        if modalidad and modalidad != "Todos":
            query = query.filter(Alumno.modalidad == modalidad)
        
        # Filtro especial: Switch de "Solo Injustificadas"
        if solo_injustificadas:
            query = query.filter(Asistencia.estado == "INASISTENCIA")

        resultados = query.all()

        # 3. Calcular KPIs (Estadísticas rápidas)
        total = len(resultados)
        injustificadas = sum(1 for a, _ in resultados if a.estado == "INASISTENCIA")
        justificadas = total - injustificadas

        stats = {
            "total": total,
            "injustificadas": injustificadas,
            "justificadas": justificadas
        }

        # 4. Procesar datos y detectar REINCIDENCIA
        datos_tabla = []
        fecha_inicio_mes = fecha_consulta.replace(day=1)
        
        for asistencia, alumno in resultados:
            # Lógica de Reincidencia: ¿Cuántas faltas lleva este mes?
            # Hacemos una sub-consulta rápida
            faltas_mes = self.db.query(func.count(Asistencia.id)).filter(
                Asistencia.alumno_id == alumno.id,
                Asistencia.estado == "INASISTENCIA",
                Asistencia.fecha >= fecha_inicio_mes,
                Asistencia.fecha <= fecha_consulta
            ).scalar()

            es_reincidente = faltas_mes > 2  # Umbral: Más de 2 faltas en el mes es alerta
            
            # Formatear celular
            celular = str(alumno.celular_padre_1 or "")
            if alumno.celular_padre_2: celular += f" / {alumno.celular_padre_2}"

            datos_tabla.append({
                "id_asistencia": asistencia.id, # Necesario para justificar
                "codigo": alumno.codigo_matricula,
                "nombre": f"{alumno.apell_paterno} {alumno.apell_materno}, {alumno.nombres}",
                "turno": asistencia.turno,
                "celular": celular,
                "estado": asistencia.estado,
                "reincidente": es_reincidente, # Booleano para poner icono de fuego
                "faltas_mes": faltas_mes       # Dato extra para el tooltip
            })

        # Ordenar: Primero los reincidentes, luego por apellido
        datos_tabla.sort(key=lambda x: (not x['reincidente'], x['nombre']))

        return True, "Datos cargados", stats, datos_tabla

    def justificar_rapida(self, id_asistencia, motivo):
        """Cambia el estado de INASISTENCIA a JUSTIFICADO"""
        try:
            registro = self.db.query(Asistencia).get(id_asistencia)
            if registro:
                registro.estado = "JUSTIFICADO"
                registro.observacion = f"Justif. Rápida: {motivo}"
                self.db.commit()
                return True, "Justificado correctamente"
            return False, "Registro no encontrado"
        except Exception as e:
            self.db.rollback()
            return False, str(e)