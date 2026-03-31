"""
Servicio de Matrículas - CRUD y generación de código.
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.matricula import Matricula
from app.models.alumno import Alumno
from app.models.periodo import PeriodoAcademico
from app.schemas.matricula import MatriculaCreate, MatriculaUpdate


class MatriculaService:
    """Servicio para operaciones de matrículas."""
    
    def generar_codigo(self, db: Session, grupo: str, modalidad: str) -> str:
        """
        Generar código de matrícula con formato: {Año}{Prefijo}{Consecutivo}
        Ejemplo: 26POA0001 (2026, Primera Opción Grupo A, alumno #1)
        """
        mapa_prefijos = {
            ("A", "PRIMERA OPCION"): "POA", ("A", "ORDINARIO"): "ORA", ("A", "COLEGIO"): "COA", ("A", "REFORZAMIENTO"): "REA",
            ("B", "PRIMERA OPCION"): "POB", ("B", "ORDINARIO"): "ORB", ("B", "COLEGIO"): "COB", ("B", "REFORZAMIENTO"): "REB",
            ("C", "PRIMERA OPCION"): "POC", ("C", "ORDINARIO"): "ORC", ("C", "COLEGIO"): "COC", ("C", "REFORZAMIENTO"): "REC",
            ("D", "PRIMERA OPCION"): "POD", ("D", "ORDINARIO"): "ORD", ("D", "COLEGIO"): "COD", ("D", "REFORZAMIENTO"): "RED",
        }
        
        sufijo = mapa_prefijos.get((grupo, modalidad), "GEN")
        anio = str(datetime.now().year)[-2:]
        prefijo_base = f"{anio}{sufijo}"
        
        # Buscar último código con este prefijo
        ultimo = db.query(Matricula.codigo_matricula).filter(
            Matricula.codigo_matricula.like(f"{prefijo_base}%")
        ).order_by(Matricula.id.desc()).first()
        
        if ultimo and ultimo[0]:
            consecutivo = int(ultimo[0][-4:]) + 1
        else:
            consecutivo = 1
        
        return f"{prefijo_base}{consecutivo:04d}"
    
    def __init__(self, repo=None):
        from app.repositories.matricula_repository import matricula_repo
        self.repo = repo or matricula_repo

    def listar(
        self,
        db: Session,
        periodo_id: Optional[int] = None,
        alumno_id: Optional[int] = None,
        grupo: Optional[str] = None,
        estado: Optional[str] = "activo",
        skip: int = 0,
        limit: int = 100
    ) -> List[Matricula]:
        """Listar matrículas delegando a Repositorio."""
        from app.repositories.matricula_repository import MatriculaQuerySpec
        spec = MatriculaQuerySpec(
            periodo_id=periodo_id,
            alumno_id=alumno_id,
            grupo=grupo,
            estado=estado,
            skip=skip,
            limit=limit,
        )
        return self.repo.find_all(db, spec)

    def contar(
        self,
        db: Session,
        periodo_id: Optional[int] = None,
        alumno_id: Optional[int] = None,
        grupo: Optional[str] = None,
        estado: Optional[str] = "activo",
    ) -> int:
        """Contar matrículas delegando a Repositorio."""
        from app.repositories.matricula_repository import MatriculaQuerySpec
        spec = MatriculaQuerySpec(
            periodo_id=periodo_id,
            alumno_id=alumno_id,
            grupo=grupo,
            estado=estado,
        )
        return self.repo.count_all(db, spec)
    
    def crear(self, db: Session, datos: MatriculaCreate, usuario_actual_id: Optional[int] = None) -> Matricula:
        """Crear nueva matrícula con generación automática de código."""
        # Validar que el alumno existe
        alumno = db.query(Alumno).filter(Alumno.id == datos.alumno_id).first()
        if not alumno:
            raise ValueError("Alumno no encontrado")
        
        # Validar que el periodo existe y está activo
        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.id == datos.periodo_id
        ).first()
        if not periodo:
            raise ValueError("Periodo académico no encontrado")
        if periodo.estado != "activo":
            raise ValueError("No se puede matricular en un periodo cerrado")
        
        # Validar que el alumno no tenga una matrícula activa en el mismo periodo
        existente = db.query(Matricula).filter(
            Matricula.alumno_id == datos.alumno_id,
            Matricula.periodo_id == datos.periodo_id,
            Matricula.estado == "activo"
        ).first()
        if existente:
            raise ValueError("El alumno ya tiene una matrícula activa en este periodo")
        
        # Generar código automáticamente si no viene
        if not datos.codigo_matricula or datos.codigo_matricula.startswith("TMP-"):
            datos.codigo_matricula = self.generar_codigo(
                db, datos.grupo or "A", datos.modalidad or "ORDINARIO"
            )
        
        # Validar código único
        codigo_existente = db.query(Matricula).filter(
            Matricula.codigo_matricula == datos.codigo_matricula
        ).first()
        if codigo_existente:
            raise ValueError("El código de matrícula ya existe")
        
        matricula = Matricula(**datos.model_dump())
        if usuario_actual_id:
            matricula.creado_por = usuario_actual_id
        db.add(matricula)
        db.commit()
        db.refresh(matricula)
        return matricula
    
    def obtener_por_id(self, db: Session, matricula_id: int) -> Optional[Matricula]:
        """Obtener matrícula por ID."""
        return db.query(Matricula).filter(Matricula.id == matricula_id).first()
    
    def obtener_por_codigo(self, db: Session, codigo: str) -> Optional[Matricula]:
        """Obtener matrícula por código."""
        return db.query(Matricula).filter(Matricula.codigo_matricula == codigo).first()
    
    def actualizar(self, db: Session, matricula_id: int, datos: MatriculaUpdate) -> Matricula:
        """Actualizar matrícula."""
        matricula = self.obtener_por_id(db, matricula_id)
        if not matricula:
            raise ValueError("Matrícula no encontrada")
        
        for field, value in datos.model_dump(exclude_unset=True).items():
            setattr(matricula, field, value)
        
        db.commit()
        db.refresh(matricula)
        return matricula
    
    def retirar(self, db: Session, matricula_id: int) -> Matricula:
        """Marcar matrícula como retirada."""
        matricula = self.obtener_por_id(db, matricula_id)
        if not matricula:
            raise ValueError("Matrícula no encontrada")
        
        matricula.estado = "retirado"
        db.commit()
        db.refresh(matricula)
        return matricula
    
    def eliminar(self, db: Session, matricula_id: int) -> bool:
        """Eliminar matrícula permanentemente."""
        matricula = self.obtener_por_id(db, matricula_id)
        if not matricula:
            raise ValueError("Matrícula no encontrada")
        
        db.delete(matricula)
        db.commit()
        return True


matricula_service = MatriculaService()
