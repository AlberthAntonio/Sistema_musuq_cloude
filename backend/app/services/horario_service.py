"""
Servicio de Horarios - Lógica de negocio y validaciones.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.horario import Horario
from app.models.curso import Curso
from app.models.docente import Docente
from app.schemas.horario import HorarioCreate, HorarioUpdate


class HorarioService:
    """Servicio para operaciones de horarios."""
    
    # ==================== VALIDACIONES ====================
    
    def validar_curso_existe(self, db: Session, curso_id: int) -> bool:
        """Verifica si el curso existe."""
        return db.query(Curso).filter(Curso.id == curso_id).first() is not None
    
    def validar_docente_existe(self, db: Session, docente_id: int) -> bool:
        """Verifica si el docente existe."""
        if not docente_id:
            return True  # Docente es opcional
        return db.query(Docente).filter(Docente.id == docente_id).first() is not None
    
    def validar_conflicto_horario(
        self,
        db: Session,
        grupo: str,
        dia_semana: int,
        hora_inicio: str,
        hora_fin: str,
        horario_id: Optional[int] = None,
        periodo: Optional[str] = None,
    ) -> bool:
        """Verifica conflicto de horario para el grupo. Retorna True si NO hay conflicto."""
        query = db.query(Horario).filter(
            Horario.grupo == grupo,
            Horario.dia_semana == dia_semana,
            Horario.activo == True,
        )
        if periodo:
            query = query.filter(Horario.periodo == periodo)
        if horario_id:
            query = query.filter(Horario.id != horario_id)

        # Verificar superposición de horas
        for h in query.all():
            if not (hora_fin <= h.hora_inicio or hora_inicio >= h.hora_fin):
                return False
        return True

    def validar_conflicto_docente(
        self,
        db: Session,
        docente_id: Optional[int],
        dia_semana: int,
        hora_inicio: str,
        hora_fin: str,
        horario_id: Optional[int] = None,
        periodo: Optional[str] = None,
    ) -> bool:
        """Verifica conflicto de horario para el docente. Retorna True si NO hay conflicto."""
        if not docente_id:
            return True

        query = db.query(Horario).filter(
            Horario.docente_id == docente_id,
            Horario.dia_semana == dia_semana,
            Horario.activo == True,
        )
        if periodo:
            query = query.filter(Horario.periodo == periodo)
        if horario_id:
            query = query.filter(Horario.id != horario_id)

        for h in query.all():
            if not (hora_fin <= h.hora_inicio or hora_inicio >= h.hora_fin):
                return False
        return True
    
    # ==================== OPERACIONES CRUD ====================
    
    def listar(
        self, 
        db: Session,
        grupo: Optional[str] = None,
        dia_semana: Optional[int] = None,
        curso_id: Optional[int] = None,
        docente_id: Optional[int] = None,
        activo: Optional[bool] = True
    ) -> List[Horario]:
        """Listar horarios con filtros."""
        query = db.query(Horario)
        
        if grupo:
            query = query.filter(Horario.grupo == grupo)
        if dia_semana:
            query = query.filter(Horario.dia_semana == dia_semana)
        if curso_id:
            query = query.filter(Horario.curso_id == curso_id)
        if docente_id:
            query = query.filter(Horario.docente_id == docente_id)
        if activo is not None:
            query = query.filter(Horario.activo == activo)
        
        return query.order_by(Horario.dia_semana, Horario.hora_inicio).all()
    
    def crear(self, db: Session, datos: HorarioCreate) -> Horario:
        """Crear nuevo horario."""
        # Validar curso existe
        if not self.validar_curso_existe(db, datos.curso_id):
            raise ValueError("Curso no encontrado")
        
        # Validar docente existe
        if not self.validar_docente_existe(db, datos.docente_id):
            raise ValueError("Docente no encontrado")
        
        # Validar no hay conflicto de horario
        if not self.validar_conflicto_horario(
            db,
            datos.grupo,
            datos.dia_semana,
            datos.hora_inicio,
            datos.hora_fin,
            periodo=datos.periodo,
        ):
            raise ValueError("Ya existe un horario en ese bloque para este grupo")

        if not self.validar_conflicto_docente(
            db,
            datos.docente_id,
            datos.dia_semana,
            datos.hora_inicio,
            datos.hora_fin,
            periodo=datos.periodo,
        ):
            raise ValueError("El docente asignado ya esta en ese horario")
        
        horario = Horario(**datos.model_dump())
        db.add(horario)
        db.commit()
        db.refresh(horario)
        return horario
    
    def obtener_por_id(self, db: Session, horario_id: int) -> Optional[Horario]:
        """Obtener horario por ID."""
        return db.query(Horario).filter(Horario.id == horario_id).first()
    
    def obtener_por_grupo(self, db: Session, grupo: str) -> List[Dict[str, Any]]:
        """Obtener horarios de un grupo con información completa."""
        horarios = db.query(Horario).filter(
            Horario.grupo == grupo,
            Horario.activo == True
        ).order_by(Horario.dia_semana, Horario.hora_inicio).all()
        
        resultado = []
        for h in horarios:
            resultado.append({
                "id": h.id,
                "dia_semana": h.dia_semana,
                "dia_nombre": h.dia_nombre,
                "hora_inicio": h.hora_inicio,
                "hora_fin": h.hora_fin,
                "aula": h.aula,
                "turno": h.turno,
                "curso_id": h.curso_id,
                "curso_nombre": h.curso.nombre if h.curso else None,
                "docente_id": h.docente_id,
                "docente_nombre": h.docente.nombre_completo if h.docente else None
            })
        return resultado
    
    def obtener_por_docente(self, db: Session, docente_id: int) -> List[Horario]:
        """Obtener horarios de un docente."""
        return db.query(Horario).filter(
            Horario.docente_id == docente_id,
            Horario.activo == True
        ).order_by(Horario.dia_semana, Horario.hora_inicio).all()
    
    def actualizar(self, db: Session, horario_id: int, datos: HorarioUpdate) -> Horario:
        """Actualizar horario."""
        horario = self.obtener_por_id(db, horario_id)
        if not horario:
            raise ValueError("Horario no encontrado")
        
        update_data = datos.model_dump(exclude_unset=True)
        
        # Validar curso si se cambia
        if "curso_id" in update_data and not self.validar_curso_existe(db, update_data["curso_id"]):
            raise ValueError("Curso no encontrado")
        
        # Validar docente si se cambia
        if "docente_id" in update_data and not self.validar_docente_existe(db, update_data["docente_id"]):
            raise ValueError("Docente no encontrado")
        
        # Validar conflicto si se cambian día/hora
        if any(k in update_data for k in ["grupo", "dia_semana", "hora_inicio", "hora_fin", "periodo"]):
            grupo = update_data.get("grupo", horario.grupo)
            dia = update_data.get("dia_semana", horario.dia_semana)
            inicio = update_data.get("hora_inicio", horario.hora_inicio)
            fin = update_data.get("hora_fin", horario.hora_fin)
            periodo = update_data.get("periodo", horario.periodo)

            if not self.validar_conflicto_horario(db, grupo, dia, inicio, fin, horario_id, periodo):
                raise ValueError("Ya existe un horario en ese bloque para este grupo")

            docente_id = update_data.get("docente_id", horario.docente_id)
            if not self.validar_conflicto_docente(db, docente_id, dia, inicio, fin, horario_id, periodo):
                raise ValueError("El docente asignado ya esta en ese horario")
        
        for field, value in update_data.items():
            setattr(horario, field, value)
        
        db.commit()
        db.refresh(horario)
        return horario
    
    def eliminar(self, db: Session, horario_id: int) -> bool:
        """Eliminar horario."""
        horario = self.obtener_por_id(db, horario_id)
        if not horario:
            raise ValueError("Horario no encontrado")
        
        db.delete(horario)
        db.commit()
        return True
    
    def desactivar(self, db: Session, horario_id: int) -> Horario:
        """Desactivar horario."""
        horario = self.obtener_por_id(db, horario_id)
        if not horario:
            raise ValueError("Horario no encontrado")
        
        horario.activo = False
        db.commit()
        db.refresh(horario)
        return horario


# Instancia global del servicio
horario_service = HorarioService()
