# app/controllers/horarios_controller.py

from app.database import get_session, SessionLocal
from app.models.horario_model import Horario
from app.models.curso_model import Curso
from app.models.docente_model import Docente

class HorariosController:
    """Controlador para gestión de horarios"""
    
    def obtener_horario_grupo(self, grupo, periodo='2026-I'):
        """Obtiene el horario completo de un grupo"""
        try:
            session = get_session()
            
            horarios = session.query(Horario).filter(
                Horario.grupo == grupo,
                Horario.periodo == periodo,
                Horario.activo == True
            ).all()
            
            # Organizar por día y hora
            horario_completo = {}
            
            for h in horarios:
                dia = h.dia_semana
                slot = f"{h.hora_inicio}-{h.hora_fin}"
                
                if dia not in horario_completo:
                    horario_completo[dia] = {}
                
                # Objeto simplificado para la vista
                horario_completo[dia][slot] = type('obj', (object,), {
                    'id': h.id,
                    'nombre_curso': h.curso.nombre if h.curso else 'Sin curso',
                    'nombre_docente': h.docente.nombre_completo if h.docente else None,
                    'aula': h.aula,
                    'hora_inicio': h.hora_inicio,
                    'hora_fin': h.hora_fin
                })()
            
            session.close()
            return True, "OK", horario_completo
        
        except Exception as e:
            return False, f"Error: {str(e)}", {}
    
    def agregar_bloque(self, curso_id, docente_id, grupo, dia_semana,
                       hora_inicio, hora_fin, aula, turno, periodo='2026-I'):
        """Agrega un nuevo bloque horario"""
        try:
            session = get_session()
            
            # Validar conflictos (implementar después)
            
            nuevo_horario = Horario(
                curso_id=curso_id,
                docente_id=docente_id,
                grupo=grupo,
                dia_semana=dia_semana,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                aula=aula,
                turno=turno,
                periodo=periodo
            )
            
            session.add(nuevo_horario)
            session.commit()
            nuevo_id = nuevo_horario.id
            session.close()
            
            return True, "Horario agregado", nuevo_id
        
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    def eliminar_bloque(self, id_horario):
        """Elimina (desactiva) un bloque"""
        try:
            session = get_session()
            
            horario = session.query(Horario).filter(Horario.id == id_horario).first()
            if horario:
                horario.activo = False
                session.commit()
            
            session.close()
            return True, "Horario eliminado"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def obtener_slots_horarios(self, turno='MAÑANA'):
        """Retorna slots de tiempo estándar"""
        if turno == 'MAÑANA':
            return [
                ('08:00', '09:30'),
                ('09:30', '11:00'),
                ('11:00', '11:30'),  # RECREO
                ('11:30', '13:00'),
                ('13:00', '14:30'),
            ]
        else:
            return [
                ('14:00', '15:30'),
                ('15:30', '17:00'),
                ('17:00', '17:30'),  # RECREO
                ('17:30', '19:00'),
            ]

    def obtener_grupos_disponibles(self):
        """Obtiene lista de grupos con horarios registrados"""
        try:
            session = SessionLocal()
            
            # Obtener grupos únicos de los horarios
            result = session.query(Horario.grupo).distinct().filter(
                Horario.activo == True
            ).all()
            
            grupos = [g[0] for g in result] if result else []
            
            session.close()
            
            # Si no hay horarios, retornar grupos por defecto
            if not grupos:
                return ['A', 'B', 'C', 'D', 'E', 'F']
            
            return sorted(grupos)
        
        except Exception as e:
            print(f"Error obteniendo grupos: {e}")
            return ['A', 'B', 'C', 'D', 'E', 'F']