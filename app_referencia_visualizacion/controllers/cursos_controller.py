# app/controllers/cursos_controller.py

from app.database import get_session
from app.models.curso_model import Curso

class CursosController:
    """Controlador para gestión de cursos"""
    
    def obtener_todos(self):
        """Obtiene todos los cursos"""
        try:
            session = get_session()
            cursos = session.query(Curso).all()
            session.close()
            
            return [{'id': c.id, 'nombre': c.nombre} for c in cursos]
        
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def obtener_por_id(self, id_curso):
        """Obtiene un curso por ID"""
        try:
            session = get_session()
            curso = session.query(Curso).filter(Curso.id == id_curso).first()
            session.close()
            
            if curso:
                return {'id': curso.id, 'nombre': curso.nombre}
            return None
        
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def agregar_curso(self, nombre):
        """Agrega un nuevo curso"""
        try:
            session = get_session()
            
            # Verificar duplicados
            existe = session.query(Curso).filter(Curso.nombre == nombre).first()
            if existe:
                session.close()
                return False, "Ya existe un curso con ese nombre"
            
            # Crear nuevo
            nuevo_curso = Curso(nombre=nombre)
            session.add(nuevo_curso)
            session.commit()
            session.close()
            
            return True, "Curso agregado exitosamente"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def obtener_nombres_para_combobox(self):
        """Lista de nombres para ComboBox"""
        cursos = self.obtener_todos()
        return [c['nombre'] for c in cursos]
    
    def buscar_por_nombre(self, nombre):
        """Busca curso por nombre"""
        try:
            session = get_session()
            curso = session.query(Curso).filter(Curso.nombre == nombre).first()
            session.close()
            
            if curso:
                return {'id': curso.id, 'nombre': curso.nombre}
            return None
        
        except Exception as e:
            return None
