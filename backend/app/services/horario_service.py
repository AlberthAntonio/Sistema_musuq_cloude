"""
Servicio de Horarios - Lógica de negocio y validaciones.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.aula import Aula
from app.models.horario import Horario
from app.models.curso import Curso
from app.models.docente import Docente
from app.models.plantilla_horario import PlantillaBloque
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

    def _obtener_bloque_plantilla(self, db: Session, bloque_id: int) -> PlantillaBloque:
        bloque = db.query(PlantillaBloque).filter(PlantillaBloque.id == bloque_id).first()
        if not bloque:
            raise ValueError("Bloque de plantilla no encontrado")
        return bloque

    def _validar_consistencia_con_bloque(
        self,
        db: Session,
        valores: Dict[str, Any],
        valores_provistos: Dict[str, Any],
        bloque: PlantillaBloque,
    ) -> None:
        plantilla = bloque.plantilla
        if not plantilla:
            raise ValueError("Plantilla del bloque no encontrada")

        if bloque.tipo_bloque != "CLASE":
            raise ValueError("Solo se puede asignar horarios a bloques tipo CLASE")

        esperado = {
            "dia_semana": bloque.dia_semana,
            "hora_inicio": bloque.hora_inicio,
            "hora_fin": bloque.hora_fin,
            "grupo": plantilla.grupo,
            "periodo": plantilla.periodo,
            "turno": plantilla.turno,
            "aula_id": plantilla.aula_id,
        }

        for campo, esperado_valor in esperado.items():
            if campo in valores_provistos:
                provisto = valores_provistos.get(campo)
                if provisto is not None and provisto != esperado_valor:
                    raise ValueError(f"{campo} debe coincidir con el bloque de plantilla")

        valores["dia_semana"] = bloque.dia_semana
        valores["hora_inicio"] = bloque.hora_inicio
        valores["hora_fin"] = bloque.hora_fin
        valores["grupo"] = plantilla.grupo
        valores["periodo"] = plantilla.periodo
        valores["turno"] = plantilla.turno
        valores["aula_id"] = plantilla.aula_id

        aula_nombre = plantilla.aula.nombre if plantilla.aula else None
        if aula_nombre:
            valores["aula"] = aula_nombre
        elif plantilla.aula_id:
            aula = db.query(Aula).filter(Aula.id == plantilla.aula_id).first()
            if aula:
                valores["aula"] = aula.nombre

    def _aplicar_reglas_plantilla(
        self,
        db: Session,
        valores: Dict[str, Any],
        valores_provistos: Dict[str, Any],
    ) -> Dict[str, Any]:
        bloque_id = valores.get("plantilla_bloque_id")
        if not bloque_id:
            return valores

        bloque = self._obtener_bloque_plantilla(db, bloque_id)
        self._validar_consistencia_con_bloque(db, valores, valores_provistos, bloque)
        return valores
    
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
            ~and_(Horario.aula_id.is_(None), Horario.aula.is_(None)),
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
            ~and_(Horario.aula_id.is_(None), Horario.aula.is_(None)),
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
        datos_horario = datos.model_dump(exclude_none=True)
        datos_horario = self._aplicar_reglas_plantilla(db, datos_horario, datos_horario)

        dia_semana = datos_horario.get("dia_semana")
        hora_inicio = datos_horario.get("hora_inicio")
        hora_fin = datos_horario.get("hora_fin")

        if dia_semana is None or not hora_inicio or not hora_fin:
            raise ValueError("dia_semana, hora_inicio y hora_fin son obligatorios")

        # Validar curso existe
        if not self.validar_curso_existe(db, datos_horario["curso_id"]):
            raise ValueError("Curso no encontrado")
        
        # Validar docente existe
        if not self.validar_docente_existe(db, datos_horario.get("docente_id")):
            raise ValueError("Docente no encontrado")
        
        # Validar no hay conflicto de horario
        if not self.validar_conflicto_horario(
            db,
            datos_horario["grupo"],
            dia_semana,
            hora_inicio,
            hora_fin,
            periodo=datos_horario.get("periodo"),
        ):
            raise ValueError("Ya existe un horario en ese bloque para este grupo")

        if not self.validar_conflicto_docente(
            db,
            datos_horario.get("docente_id"),
            dia_semana,
            hora_inicio,
            hora_fin,
            periodo=datos_horario.get("periodo"),
        ):
            raise ValueError("El docente asignado ya esta en ese horario")
        
        horario = Horario(**datos_horario)
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
        snapshot = {
            "curso_id": horario.curso_id,
            "docente_id": horario.docente_id,
            "grupo": horario.grupo,
            "periodo": horario.periodo,
            "dia_semana": horario.dia_semana,
            "hora_inicio": horario.hora_inicio,
            "hora_fin": horario.hora_fin,
            "aula": horario.aula,
            "aula_id": horario.aula_id,
            "turno": horario.turno,
            "plantilla_bloque_id": horario.plantilla_bloque_id,
            "activo": horario.activo,
        }
        snapshot.update(update_data)
        snapshot = self._aplicar_reglas_plantilla(db, snapshot, update_data)
        
        # Validar curso si se cambia
        if "curso_id" in update_data and not self.validar_curso_existe(db, snapshot["curso_id"]):
            raise ValueError("Curso no encontrado")
        
        # Validar docente si se cambia
        if "docente_id" in update_data and not self.validar_docente_existe(db, snapshot.get("docente_id")):
            raise ValueError("Docente no encontrado")
        
        hay_cambio_conflicto = any(
            snapshot.get(campo) != getattr(horario, campo)
            for campo in [
                "grupo",
                "dia_semana",
                "hora_inicio",
                "hora_fin",
                "periodo",
                "docente_id",
                "plantilla_bloque_id",
            ]
        )

        if hay_cambio_conflicto:
            if not self.validar_conflicto_horario(
                db,
                snapshot["grupo"],
                snapshot["dia_semana"],
                snapshot["hora_inicio"],
                snapshot["hora_fin"],
                horario_id,
                snapshot.get("periodo"),
            ):
                raise ValueError("Ya existe un horario en ese bloque para este grupo")

            if not self.validar_conflicto_docente(
                db,
                snapshot.get("docente_id"),
                snapshot["dia_semana"],
                snapshot["hora_inicio"],
                snapshot["hora_fin"],
                horario_id,
                snapshot.get("periodo"),
            ):
                raise ValueError("El docente asignado ya esta en ese horario")
        
        for field, value in snapshot.items():
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
