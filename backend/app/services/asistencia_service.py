"""
Servicio de Asistencia - Lógica de negocio y validaciones.
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime, time
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.asistencia import Asistencia
from app.models.alumno import Alumno
from app.models.matricula import Matricula
from app.schemas.asistencia import AsistenciaCreate, AsistenciaUpdate


class AsistenciaService:
    """Servicio para operaciones de asistencia."""
    
    # ==================== VALIDACIONES ====================
    
    def existe_registro(self, db: Session, alumno_id: int, fecha: date, turno: str) -> bool:
        """Verifica si ya existe asistencia para alumno en fecha y turno."""
        return db.query(Asistencia).filter(
            Asistencia.alumno_id == alumno_id,
            Asistencia.fecha == fecha,
            Asistencia.turno == turno
        ).first() is not None
    
    def validar_alumno_existe(self, db: Session, alumno_id: int) -> bool:
        """Verifica si el alumno existe."""
        return db.query(Alumno).filter(Alumno.id == alumno_id).first() is not None
    
    # ==================== OPERACIONES CRUD ====================
    
    def listar(
        self,
        db: Session,
        skip: int = 0,
        limit: int = 100,
        fecha: Optional[date] = None,
        alumno_id: Optional[int] = None,
        grupo: Optional[str] = None,
        turno: Optional[str] = None,
        estado: Optional[str] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        periodo_id: Optional[int] = None
    ) -> List[Asistencia]:
        """Listar asistencias con filtros. Soporta fecha exacta o rango fecha_inicio/fecha_fin."""
        query = db.query(Asistencia).options(joinedload(Asistencia.alumno))
        
        if fecha:
            query = query.filter(Asistencia.fecha == fecha)
        elif fecha_inicio or fecha_fin:
            if fecha_inicio:
                query = query.filter(Asistencia.fecha >= fecha_inicio)
            if fecha_fin:
                query = query.filter(Asistencia.fecha <= fecha_fin)
        if alumno_id:
            query = query.filter(Asistencia.alumno_id == alumno_id)
        if periodo_id:
            query = query.filter(Asistencia.periodo_id == periodo_id)
        if grupo:
            # FIX: grupo vive en Matricula, no en Alumno
            alumno_ids_subq = db.query(Matricula.alumno_id).filter(
                Matricula.grupo == grupo,
                Matricula.estado == "activo"
            ).scalar_subquery()
            query = query.filter(Asistencia.alumno_id.in_(alumno_ids_subq))
        if turno:
            query = query.filter(Asistencia.turno == turno)
        if estado:
            query = query.filter(Asistencia.estado == estado)
        
        return query.order_by(Asistencia.fecha.desc()).offset(skip).limit(limit).all()
    
    def registrar(self, db: Session, datos: AsistenciaCreate, usuario_id: int) -> Asistencia:
        """Registrar asistencia de un alumno."""
        # Validar alumno existe
        if not self.validar_alumno_existe(db, datos.alumno_id):
            raise ValueError("Alumno no encontrado")
        
        # Validar no existe registro duplicado
        if self.existe_registro(db, datos.alumno_id, datos.fecha, datos.turno):
            raise ValueError(f"Ya existe registro de asistencia para el turno {datos.turno}")
        
        asistencia = Asistencia(
            **datos.model_dump(),
            registrado_por=usuario_id
        )
        db.add(asistencia)
        db.commit()
        db.refresh(asistencia)
        return asistencia
    
    def registrar_masivo(
        self, 
        db: Session, 
        fecha: date, 
        turno: str, 
        registros: List[Dict[str, Any]], 
        usuario_id: int
    ) -> Dict[str, Any]:
        """Registrar asistencia de múltiples alumnos."""
        creados = 0
        errores = []
        
        for registro in registros:
            try:
                alumno_id = registro.get("alumno_id")
                estado = registro.get("estado", "PUNTUAL")
                hora_str = registro.get("hora")
                
                # Saltar si ya existe
                if self.existe_registro(db, alumno_id, fecha, turno):
                    continue
                
                asistencia = Asistencia(
                    alumno_id=alumno_id,
                    fecha=fecha,
                    turno=turno,
                    estado=estado,
                    hora=time.fromisoformat(hora_str) if hora_str else datetime.now().time(),
                    registrado_por=usuario_id
                )
                db.add(asistencia)
                creados += 1
                
            except Exception as e:
                errores.append({"alumno_id": alumno_id, "error": str(e)})
        
        db.commit()
        
        return {
            "mensaje": f"Se registraron {creados} asistencias",
            "fecha": fecha,
            "turno": turno,
            "errores": errores if errores else None
        }
    
    def obtener_hoy(
        self, 
        db: Session, 
        grupo: Optional[str] = None, 
        turno: Optional[str] = None
    ) -> List[Asistencia]:
        """Obtener asistencias del día de hoy."""
        hoy = date.today()
        query = db.query(Asistencia).options(
            joinedload(Asistencia.alumno).joinedload(Alumno.matriculas)
        ).filter(Asistencia.fecha == hoy)
        
        if grupo:
            # FIX: grupo vive en Matricula, no en Alumno
            alumno_ids_subq = db.query(Matricula.alumno_id).filter(
                Matricula.grupo == grupo,
                Matricula.estado == "activo"
            ).scalar_subquery()
            query = query.filter(Asistencia.alumno_id.in_(alumno_ids_subq))
        if turno:
            query = query.filter(Asistencia.turno == turno)
        
        return query.all()
    
    def obtener_por_id(self, db: Session, asistencia_id: int) -> Optional[Asistencia]:
        """Obtener asistencia por ID."""
        return db.query(Asistencia).filter(Asistencia.id == asistencia_id).first()
    
    def actualizar(self, db: Session, asistencia_id: int, datos: AsistenciaUpdate) -> Asistencia:
        """Actualizar registro de asistencia."""
        asistencia = self.obtener_por_id(db, asistencia_id)
        if not asistencia:
            raise ValueError("Asistencia no encontrada")
        
        update_data = datos.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(asistencia, field, value)
        
        db.commit()
        db.refresh(asistencia)
        return asistencia
    
    def eliminar(self, db: Session, asistencia_id: int) -> bool:
        """Eliminar registro de asistencia."""
        asistencia = self.obtener_por_id(db, asistencia_id)
        if not asistencia:
            raise ValueError("Asistencia no encontrada")
        
        db.delete(asistencia)
        db.commit()
        return True
    
    # ==================== REPORTES ====================
    
    def reporte_por_fecha(
        self, 
        db: Session, 
        fecha_reporte: date, 
        grupo: Optional[str] = None,
        turno: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generar reporte de asistencia por fecha."""
        query = db.query(Asistencia).filter(Asistencia.fecha == fecha_reporte)
        
        if grupo:
            # FIX: grupo vive en Matricula, no en Alumno
            alumno_ids_subq = db.query(Matricula.alumno_id).filter(
                Matricula.grupo == grupo,
                Matricula.estado == "activo"
            ).scalar_subquery()
            query = query.filter(Asistencia.alumno_id.in_(alumno_ids_subq))
        if turno:
            query = query.filter(Asistencia.turno == turno)
        
        asistencias = query.all()
        total = len(asistencias)
        
        puntual = sum(1 for a in asistencias if a.estado == "PUNTUAL")
        tardanza = sum(1 for a in asistencias if a.estado == "TARDANZA")
        falta = sum(1 for a in asistencias if a.estado == "INASISTENCIA")
        
        return {
            "fecha": fecha_reporte,
            "grupo": grupo,
            "turno": turno,
            "total": total,
            "puntual": puntual,
            "tardanza": tardanza,
            "falta": falta,
            "porcentaje_asistencia": round((puntual + tardanza) / total * 100, 2) if total > 0 else 0
        }
    
    def reporte_alumno(
        self, 
        db: Session, 
        alumno_id: int,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        periodo_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generar reporte de asistencia de un alumno."""
        alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
        if not alumno:
            raise ValueError("Alumno no encontrado")
        
        # FIX: codigo_matricula vive en Matricula, no en Alumno
        mat_query = db.query(Matricula).filter(
            Matricula.alumno_id == alumno_id,
            Matricula.estado == "activo"
        )
        if periodo_id:
            mat_query = mat_query.filter(Matricula.periodo_id == periodo_id)
        matricula = mat_query.first()
        codigo = matricula.codigo_matricula if matricula else "SIN_MATRICULA"
        
        query = db.query(Asistencia).filter(Asistencia.alumno_id == alumno_id)
        
        if periodo_id:
            query = query.filter(Asistencia.periodo_id == periodo_id)
        if fecha_inicio:
            query = query.filter(Asistencia.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Asistencia.fecha <= fecha_fin)
        
        asistencias = query.all()
        total = len(asistencias)
        
        puntual = sum(1 for a in asistencias if a.estado == "PUNTUAL")
        tardanza = sum(1 for a in asistencias if a.estado == "TARDANZA")
        falta = sum(1 for a in asistencias if a.estado == "INASISTENCIA")
        
        return {
            "alumno_id": alumno_id,
            "codigo_matricula": codigo,
            "nombre_completo": alumno.nombre_completo,
            "total_puntual": puntual,
            "total_tardanza": tardanza,
            "total_falta": falta,
            "porcentaje_asistencia": round((puntual + tardanza) / total * 100, 2) if total > 0 else 0
        }


# Instancia global del servicio
asistencia_service = AsistenciaService()
