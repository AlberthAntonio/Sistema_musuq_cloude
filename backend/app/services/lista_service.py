"""
Servicio de Listas Guardadas - Lógica de listas de alumnos.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.lista import ListaGuardada
from app.models.alumno import Alumno
from app.schemas.lista import ListaCreate, ListaUpdate


class ListaService:
    """Servicio para operaciones de listas guardadas."""
    
    def listar(self, db: Session) -> List[Dict[str, Any]]:
        """Listar todas las listas con conteo de alumnos."""
        listas = db.query(ListaGuardada).all()
        resultado = []
        for lista in listas:
            resultado.append({
                "id": lista.id,
                "nombre": lista.nombre,
                "descripcion": lista.descripcion,
                "fecha_creacion": lista.fecha_creacion,
                "cantidad_alumnos": len(lista.alumnos) if lista.alumnos else 0
            })
        return resultado
    
    def crear(self, db: Session, datos: ListaCreate) -> ListaGuardada:
        """Crear nueva lista con alumnos opcionales."""
        lista = ListaGuardada(nombre=datos.nombre, descripcion=datos.descripcion)
        
        # Agregar alumnos si se proporcionan
        if datos.alumno_ids:
            alumnos = db.query(Alumno).filter(Alumno.id.in_(datos.alumno_ids)).all()
            lista.alumnos = alumnos
        
        db.add(lista)
        db.commit()
        db.refresh(lista)
        return lista
    
    def obtener_por_id(self, db: Session, lista_id: int) -> Optional[ListaGuardada]:
        """Obtener lista por ID."""
        return db.query(ListaGuardada).filter(ListaGuardada.id == lista_id).first()
    
    def obtener_con_alumnos(self, db: Session, lista_id: int) -> Optional[Dict[str, Any]]:
        """Obtener lista con sus alumnos."""
        lista = self.obtener_por_id(db, lista_id)
        if not lista:
            return None
        
        return {
            "id": lista.id,
            "nombre": lista.nombre,
            "descripcion": lista.descripcion,
            "fecha_creacion": lista.fecha_creacion,
            "cantidad_alumnos": len(lista.alumnos),
            "alumnos": [{"id": a.id, "nombres": a.nombres, "apell_paterno": a.apell_paterno, "dni": a.dni} for a in lista.alumnos]
        }
    
    def actualizar(self, db: Session, lista_id: int, datos: ListaUpdate) -> ListaGuardada:
        """Actualizar lista."""
        lista = self.obtener_por_id(db, lista_id)
        if not lista:
            raise ValueError("Lista no encontrada")
        
        for field, value in datos.model_dump(exclude_unset=True).items():
            setattr(lista, field, value)
        
        db.commit()
        db.refresh(lista)
        return lista
    
    def agregar_alumnos(self, db: Session, lista_id: int, alumno_ids: List[int]) -> ListaGuardada:
        """Agregar alumnos a una lista."""
        lista = self.obtener_por_id(db, lista_id)
        if not lista:
            raise ValueError("Lista no encontrada")
        
        alumnos = db.query(Alumno).filter(Alumno.id.in_(alumno_ids)).all()
        for alumno in alumnos:
            if alumno not in lista.alumnos:
                lista.alumnos.append(alumno)
        
        db.commit()
        db.refresh(lista)
        return lista
    
    def quitar_alumno(self, db: Session, lista_id: int, alumno_id: int) -> bool:
        """Quitar un alumno específico de una lista."""
        lista = self.obtener_por_id(db, lista_id)
        if not lista:
            raise ValueError("Lista no encontrada")

        alumno = db.query(Alumno).filter(Alumno.id == alumno_id).first()
        if not alumno:
            raise ValueError("Alumno no encontrado")

        if alumno not in lista.alumnos:
            raise ValueError("El alumno no pertenece a esta lista")

        lista.alumnos.remove(alumno)
        db.commit()
        return True

    def eliminar(self, db: Session, lista_id: int) -> bool:
        """Eliminar lista."""
        lista = self.obtener_por_id(db, lista_id)
        if not lista:
            raise ValueError("Lista no encontrada")

        db.delete(lista)
        db.commit()
        return True


lista_service = ListaService()
