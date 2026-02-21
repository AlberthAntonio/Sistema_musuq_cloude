"""
Servicio de Eventos - Lógica de calendario y eventos.
"""
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session

from app.models.evento import EventoCalendario
from app.schemas.evento import EventoCreate, EventoUpdate


class EventoService:
    """Servicio para operaciones de eventos."""
    
    def listar(
        self, 
        db: Session,
        fecha_desde: Optional[date] = None,
        fecha_hasta: Optional[date] = None,
        tipo: Optional[str] = None,
        grupo: Optional[str] = None,
        activo: bool = True
    ) -> List[EventoCalendario]:
        """Listar eventos con filtros."""
        query = db.query(EventoCalendario).filter(EventoCalendario.activo == activo)
        
        if fecha_desde:
            query = query.filter(EventoCalendario.fecha >= fecha_desde)
        if fecha_hasta:
            query = query.filter(EventoCalendario.fecha <= fecha_hasta)
        if tipo:
            query = query.filter(EventoCalendario.tipo == tipo)
        if grupo:
            query = query.filter((EventoCalendario.grupo == grupo) | (EventoCalendario.grupo.is_(None)))
        
        return query.order_by(EventoCalendario.fecha).all()
    
    def crear(self, db: Session, datos: EventoCreate) -> EventoCalendario:
        """Crear nuevo evento."""
        evento = EventoCalendario(**datos.model_dump())
        db.add(evento)
        db.commit()
        db.refresh(evento)
        return evento
    
    def obtener_por_id(self, db: Session, evento_id: int) -> Optional[EventoCalendario]:
        """Obtener evento por ID."""
        return db.query(EventoCalendario).filter(EventoCalendario.id == evento_id).first()
    
    def actualizar(self, db: Session, evento_id: int, datos: EventoUpdate) -> EventoCalendario:
        """Actualizar evento."""
        evento = self.obtener_por_id(db, evento_id)
        if not evento:
            raise ValueError("Evento no encontrado")
        
        for field, value in datos.model_dump(exclude_unset=True).items():
            setattr(evento, field, value)
        
        db.commit()
        db.refresh(evento)
        return evento
    
    def eliminar(self, db: Session, evento_id: int) -> bool:
        """Eliminar evento."""
        evento = self.obtener_por_id(db, evento_id)
        if not evento:
            raise ValueError("Evento no encontrado")
        
        db.delete(evento)
        db.commit()
        return True


evento_service = EventoService()
