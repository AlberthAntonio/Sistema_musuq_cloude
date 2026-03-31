"""
Servicio de Asistencia - Optimizado para rendimiento.
- Eliminado N+1 queries
- Reportes usan SQL aggregation en vez de Python
- joinedload selectivo
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime, time
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case, and_

from app.models.asistencia import Asistencia
from app.models.alumno import Alumno
from app.models.matricula import Matricula
from app.schemas.asistencia import AsistenciaCreate, AsistenciaUpdate


class AsistenciaService:
    """Servicio para operaciones de asistencia."""
    
    # ==================== VALIDACIONES ====================
    
    def existe_registro(self, db: Session, alumno_id: int, fecha: date, turno: str) -> bool:
        """Verifica si ya existe asistencia para alumno en fecha y turno."""
        return db.query(Asistencia.id).filter(
            Asistencia.alumno_id == alumno_id,
            Asistencia.fecha == fecha,
            Asistencia.turno == turno
        ).first() is not None
    
    def validar_alumno_existe(self, db: Session, alumno_id: int) -> bool:
        """Verifica si el alumno existe."""
        return db.query(Alumno.id).filter(Alumno.id == alumno_id).first() is not None
    
    # ==================== OPERACIONES CRUD ====================
    
    def __init__(self, repo=None):
        from app.repositories.asistencia_repository import asistencia_repo
        self.repo = repo or asistencia_repo

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
    ) -> List[Dict[str, Any]]:
        """
        Listar asistencias con filtros, delegando a Repositorio.
        Las filas que retorna el repositorio son Row proxies, se transforman en Diccionarios planos.
        """
        from app.repositories.asistencia_repository import AsistenciaQuerySpec
        spec = AsistenciaQuerySpec(
            fecha=fecha,
            alumno_id=alumno_id,
            grupo=grupo,
            turno=turno,
            estado=estado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            periodo_id=periodo_id,
            skip=skip,
            limit=limit,
        )
        rows = self.repo.find_all(db, spec)
        
        return [
            {
                "id": r.id,
                "alumno_id": r.alumno_id,
                "fecha": r.fecha,
                "turno": r.turno,
                "estado": r.estado,
                "hora": r.hora,
                "alerta_turno": r.alerta_turno,
                "periodo_id": r.periodo_id,
                "observacion": r.observacion,
                "registrado_por": r.registrado_por,
                "fecha_registro": r.fecha_registro,
                "alumno_nombre": f"{r.alumno_apell_paterno} {r.alumno_apell_materno}, {r.alumno_nombres}",
                "alumno_dni": r.alumno_dni,
            }
            for r in rows
        ]

    def contar(
        self,
        db: Session,
        fecha: Optional[date] = None,
        alumno_id: Optional[int] = None,
        grupo: Optional[str] = None,
        turno: Optional[str] = None,
        estado: Optional[str] = None,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None,
        periodo_id: Optional[int] = None
    ) -> int:
        """Contar total de asistencias delegando a Repositorio."""
        from app.repositories.asistencia_repository import AsistenciaQuerySpec
        spec = AsistenciaQuerySpec(
            fecha=fecha,
            alumno_id=alumno_id,
            grupo=grupo,
            turno=turno,
            estado=estado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            periodo_id=periodo_id,
        )
        return self.repo.count_all(db, spec)
    
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
        
        # Pre-cargar registros existentes para evitar N queries
        existing = set()
        existing_rows = db.query(
            Asistencia.alumno_id, Asistencia.turno
        ).filter(
            Asistencia.fecha == fecha,
            Asistencia.turno == turno,
            Asistencia.alumno_id.in_([r.get("alumno_id") for r in registros if r.get("alumno_id")])
        ).all()
        for row in existing_rows:
            existing.add((row.alumno_id, row.turno))
        
        for registro in registros:
            try:
                alumno_id = registro.get("alumno_id")
                estado = registro.get("estado", "PUNTUAL")
                hora_str = registro.get("hora")
                
                # Saltar si ya existe (usando set en memoria, no query)
                if (alumno_id, turno) in existing:
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
        # Solo cargar datos del alumno, NO las matrículas (innecesario aquí)
        query = db.query(Asistencia).options(
            joinedload(Asistencia.alumno)
        ).filter(Asistencia.fecha == hoy)
        
        if grupo:
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
        """Generar reporte de asistencia por fecha usando SQL aggregation."""
        # Usar COUNT/CASE en SQL en vez de cargar todos los registros a Python
        puntual_expr = func.sum(case((Asistencia.estado == "PUNTUAL", 1), else_=0))
        tardanza_expr = func.sum(case((Asistencia.estado == "TARDANZA", 1), else_=0))
        falta_expr = func.sum(case((Asistencia.estado == "INASISTENCIA", 1), else_=0))
        
        query = db.query(
            func.count(Asistencia.id).label("total"),
            puntual_expr.label("puntual"),
            tardanza_expr.label("tardanza"),
            falta_expr.label("falta"),
        ).filter(Asistencia.fecha == fecha_reporte)
        
        if grupo:
            alumno_ids_subq = db.query(Matricula.alumno_id).filter(
                Matricula.grupo == grupo,
                Matricula.estado == "activo"
            ).scalar_subquery()
            query = query.filter(Asistencia.alumno_id.in_(alumno_ids_subq))
        if turno:
            query = query.filter(Asistencia.turno == turno)
        
        result = query.first()
        total = result.total or 0
        puntual = result.puntual or 0
        tardanza = result.tardanza or 0
        falta = result.falta or 0
        
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
        """Generar reporte de asistencia de un alumno usando SQL aggregation."""
        alumno = db.query(
            Alumno.id, Alumno.nombres, Alumno.apell_paterno, Alumno.apell_materno
        ).filter(Alumno.id == alumno_id).first()
        if not alumno:
            raise ValueError("Alumno no encontrado")
        
        nombre_completo = f"{alumno.apell_paterno} {alumno.apell_materno}, {alumno.nombres}"
        
        # Obtener código de matrícula
        mat_query = db.query(Matricula.codigo_matricula).filter(
            Matricula.alumno_id == alumno_id,
            Matricula.estado == "activo"
        )
        if periodo_id:
            mat_query = mat_query.filter(Matricula.periodo_id == periodo_id)
        mat = mat_query.first()
        codigo = mat.codigo_matricula if mat else "SIN_MATRICULA"
        
        # Aggregation SQL
        puntual_expr = func.sum(case((Asistencia.estado == "PUNTUAL", 1), else_=0))
        tardanza_expr = func.sum(case((Asistencia.estado == "TARDANZA", 1), else_=0))
        falta_expr = func.sum(case((Asistencia.estado == "INASISTENCIA", 1), else_=0))
        
        query = db.query(
            func.count(Asistencia.id).label("total"),
            puntual_expr.label("puntual"),
            tardanza_expr.label("tardanza"),
            falta_expr.label("falta"),
        ).filter(Asistencia.alumno_id == alumno_id)
        
        if periodo_id:
            query = query.filter(Asistencia.periodo_id == periodo_id)
        if fecha_inicio:
            query = query.filter(Asistencia.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Asistencia.fecha <= fecha_fin)
        
        result = query.first()
        total = result.total or 0
        puntual = result.puntual or 0
        tardanza = result.tardanza or 0
        falta = result.falta or 0
        
        return {
            "alumno_id": alumno_id,
            "codigo_matricula": codigo,
            "nombre_completo": nombre_completo,
            "total_puntual": puntual,
            "total_tardanza": tardanza,
            "total_falta": falta,
            "porcentaje_asistencia": round((puntual + tardanza) / total * 100, 2) if total > 0 else 0
        }


# Instancia global del servicio
asistencia_service = AsistenciaService()
