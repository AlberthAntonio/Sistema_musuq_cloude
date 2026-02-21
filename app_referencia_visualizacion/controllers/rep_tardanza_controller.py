from datetime import datetime
from app.database import SessionLocal
from app.models.asistencia_model import Asistencia
from app.models.alumno_model import Alumno
from sqlalchemy import desc

class ReporteTardanzaController:
    def __init__(self):
        self.db = SessionLocal()

    def filtrar_tardanzas(self, desde_str, hasta_str, turno, grupo, modalidad):
        """
        Filtra las tardanzas cruzando datos de Asistencia y Alumno.
        Recibe fechas en formato texto 'DD/MM/YYYY' y las convierte.
        """
        try:
            # 1. Convertir texto a objetos fecha (date)
            fecha_inicio = datetime.strptime(desde_str, "%d/%m/%Y").date()
            fecha_fin = datetime.strptime(hasta_str, "%d/%m/%Y").date()
        except ValueError:
            return False, "Formato de fecha inválido. Use DD/MM/YYYY (ej. 15/01/2026)", []

        # 2. Construir la consulta base (JOIN entre Asistencia y Alumno)
        # Queremos SOLO las tardanzas
        query = self.db.query(Asistencia, Alumno).join(Alumno).filter(
            Asistencia.estado == "TARDANZA",
            Asistencia.fecha >= fecha_inicio,
            Asistencia.fecha <= fecha_fin
        )

        # 3. Aplicar filtros dinámicos si no dicen "Todos"
        if turno and turno != "Todos":
            query = query.filter(Alumno.horario == turno)
        
        if grupo and grupo != "Todos":
            query = query.filter(Alumno.grupo == grupo)
            
        if modalidad and modalidad != "Todos":
            query = query.filter(Alumno.modalidad == modalidad)

        # 4. Ordenar: Lo más reciente primero
        resultados = query.order_by(desc(Asistencia.fecha), desc(Asistencia.hora)).all()

        # 5. Formatear datos para la tabla (Lista de diccionarios)
        datos_tabla = []
        for asistencia, alumno in resultados:
            # Concatenamos celulares si tiene dos
            celulares = str(alumno.celular_padre_1 or "")
            if alumno.celular_padre_2:
                celulares += f" / {alumno.celular_padre_2}"

            datos_tabla.append({
                "codigo": alumno.codigo_matricula,
                "nombre": f"{alumno.apell_paterno} {alumno.apell_materno}, {alumno.nombres}",
                "estado": asistencia.estado,
                "horario": alumno.horario,
                "fecha": f"{asistencia.fecha.strftime('%d/%m/%Y')} {asistencia.hora.strftime('%H:%M')}",
                "celular": celulares
            })

        return True, "Búsqueda exitosa", datos_tabla