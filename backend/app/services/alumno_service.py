"""
Servicio de Alumnos - Lógica de negocio y validaciones.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.alumno import Alumno
from app.schemas.alumno import AlumnoCreate, AlumnoUpdate


class AlumnoService:
    """Servicio para operaciones de alumnos."""
    
    # ==================== VALIDACIONES ====================
    
    def validar_dni_unico(self, db: Session, dni: str, alumno_id: Optional[int] = None) -> bool:
        """Verifica si el DNI ya existe. Retorna True si está disponible."""
        query = db.query(Alumno).filter(Alumno.dni == dni)
        if alumno_id:
            query = query.filter(Alumno.id != alumno_id)
        return query.first() is None
    
    def validar_codigo_unico(self, db: Session, codigo: str, alumno_id: Optional[int] = None) -> bool:
        """Verifica si el código de matrícula ya existe. Retorna True si está disponible."""
        query = db.query(Alumno).filter(Alumno.codigo_matricula == codigo)
        if alumno_id:
            query = query.filter(Alumno.id != alumno_id)
        return query.first() is None
    
    def generar_codigo(self, db: Session, grupo: str, modalidad: str) -> str:
        """
        Generar código de matrícula con formato: {Año}{Prefijo}{Consecutivo}
        Ejemplo: 26POA0001 (2026, Primera Opción Grupo A, alumno #1)
        """
        from datetime import datetime
        
        # Mapa de prefijos (Modalidad + Grupo)
        mapa_prefijos = {
            ("A", "PRIMERA OPCION"): "POA", ("A", "ORDINARIO"): "ORA", ("A", "COLEGIO"): "COA", ("A", "REFORZAMIENTO"): "REA",
            ("B", "PRIMERA OPCION"): "POB", ("B", "ORDINARIO"): "ORB", ("B", "COLEGIO"): "COB", ("B", "REFORZAMIENTO"): "REB",
            ("C", "PRIMERA OPCION"): "POC", ("C", "ORDINARIO"): "ORC", ("C", "COLEGIO"): "COC", ("C", "REFORZAMIENTO"): "REC",
            ("D", "PRIMERA OPCION"): "POD", ("D", "ORDINARIO"): "ORD", ("D", "COLEGIO"): "COD", ("D", "REFORZAMIENTO"): "RED",
        }
        
        # Obtener prefijo
        sufijo = mapa_prefijos.get((grupo, modalidad), "GEN")
        
        # Año actual (2 dígitos)
        anio = str(datetime.now().year)[-2:]
        
        # Prefijo completo: AñoSufijo (ej: 26POA)
        prefijo_base = f"{anio}{sufijo}"
        
        # Buscar último código con este prefijo
        ultimo = db.query(Alumno.codigo_matricula).filter(
            Alumno.codigo_matricula.like(f"{prefijo_base}%")
        ).order_by(Alumno.id.desc()).first()
        
        # Extraer consecutivo y sumar 1
        if ultimo and ultimo[0]:
            consecutivo = int(ultimo[0][-4:]) + 1
        else:
            consecutivo = 1
        
        # Formato final: {Año}{Sufijo}{Consecutivo:4digits}
        return f"{prefijo_base}{consecutivo:04d}"
    
    # ==================== OPERACIONES CRUD ====================
    
    def listar(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        grupo: Optional[str] = None,
        carrera: Optional[str] = None,
        modalidad: Optional[str] = None,
        horario: Optional[str] = None,
        activo: Optional[bool] = True
    ) -> List[Alumno]:
        """Listar alumnos con filtros opcionales."""
        query = db.query(Alumno)
        
        if grupo:
            query = query.filter(Alumno.grupo == grupo)
        if carrera:
            query = query.filter(Alumno.carrera.ilike(f"%{carrera}%"))
        if modalidad:
            query = query.filter(Alumno.modalidad == modalidad)
        if horario:
            query = query.filter(Alumno.horario == horario)
        if activo is not None:
            query = query.filter(Alumno.activo == activo)
        
        return query.order_by(Alumno.apell_paterno, Alumno.apell_materno).offset(skip).limit(limit).all()
    
    def crear(self, db: Session, datos: AlumnoCreate) -> Alumno:
        """Crear nuevo alumno con validaciones y generación automática de código."""
        # Validar DNI único
        if not self.validar_dni_unico(db, datos.dni):
            raise ValueError("El DNI ya está registrado")
        
        # Generar código automáticamente si no viene
        if not datos.codigo_matricula or datos.codigo_matricula.startswith("TMP-"):
            datos.codigo_matricula = self.generar_codigo(db, datos.grupo, datos.modalidad)
        
        # Validar código único
        if not self.validar_codigo_unico(db, datos.codigo_matricula):
            raise ValueError("El código de matrícula ya existe")
        
        alumno = Alumno(**datos.model_dump())
        db.add(alumno)
        db.commit()
        db.refresh(alumno)
        return alumno
    
    def obtener_por_id(self, db: Session, alumno_id: int) -> Optional[Alumno]:
        """Obtener alumno por ID."""
        return db.query(Alumno).filter(Alumno.id == alumno_id).first()
    
    def obtener_por_dni(self, db: Session, dni: str) -> Optional[Alumno]:
        """Obtener alumno por DNI."""
        return db.query(Alumno).filter(Alumno.dni == dni).first()
    
    def obtener_por_codigo(self, db: Session, codigo: str) -> Optional[Alumno]:
        """Obtener alumno por código de matrícula."""
        return db.query(Alumno).filter(Alumno.codigo_matricula == codigo).first()
    
    def buscar(self, db: Session, termino: str, limite: int = 20) -> List[Alumno]:
        """Buscar alumnos por nombre, apellido, DNI o código."""
        return db.query(Alumno).filter(
            or_(
                Alumno.nombres.ilike(f"%{termino}%"),
                Alumno.apell_paterno.ilike(f"%{termino}%"),
                Alumno.apell_materno.ilike(f"%{termino}%"),
                Alumno.dni.ilike(f"%{termino}%"),
                Alumno.codigo_matricula.ilike(f"%{termino}%")
            ),
            Alumno.activo == True
        ).limit(limite).all()
    
    def listar_por_grupo(self, db: Session, grupo: str) -> List[Alumno]:
        """Listar alumnos activos de un grupo."""
        return db.query(Alumno).filter(
            Alumno.grupo == grupo,
            Alumno.activo == True
        ).order_by(Alumno.apell_paterno, Alumno.apell_materno).all()
    
    def actualizar(self, db: Session, alumno_id: int, datos: AlumnoUpdate) -> Alumno:
        """Actualizar alumno."""
        alumno = self.obtener_por_id(db, alumno_id)
        if not alumno:
            raise ValueError("Alumno no encontrado")
        
        update_data = datos.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(alumno, field, value)
        
        db.commit()
        db.refresh(alumno)
        return alumno
    
    def eliminar(self, db: Session, alumno_id: int) -> bool:
        """Eliminar alumno permanentemente."""
        alumno = self.obtener_por_id(db, alumno_id)
        if not alumno:
            raise ValueError("Alumno no encontrado")
        
        db.delete(alumno)
        db.commit()
        return True
    
    def desactivar(self, db: Session, alumno_id: int) -> Alumno:
        """Desactivar alumno (soft delete)."""
        alumno = self.obtener_por_id(db, alumno_id)
        if not alumno:
            raise ValueError("Alumno no encontrado")
        
        alumno.activo = False
        db.commit()
        db.refresh(alumno)
        return alumno


# Instancia global del servicio
alumno_service = AlumnoService()
