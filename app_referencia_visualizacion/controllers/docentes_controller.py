# app/controllers/docentes_controller.py

from app.database import get_session
from app.models.docente_model import Docente

class DocentesController:
    """Controlador para gestión de docentes"""
    
    def obtener_todos(self):
        """Obtiene todos los docentes activos"""
        try:
            session = get_session()
            docentes = session.query(Docente).filter(Docente.activo == True).all()
            session.close()
            
            return [{
                'id': d.id,
                'nombres': d.nombres,
                'apellidos': d.apellidos,
                'nombre_completo': d.nombre_completo,
                'dni': d.dni,
                'celular': d.celular,
                'email': d.email
            } for d in docentes]
        
        except Exception as e:
            print(f"Error: {e}")
            return []
    
    def obtener_por_id(self, id_docente):
        """Obtiene un docente por ID"""
        try:
            session = get_session()
            docente = session.query(Docente).filter(Docente.id == id_docente).first()
            session.close()
            
            if docente:
                return {
                    'id': docente.id,
                    'nombre_completo': docente.nombre_completo
                }
            return None
        
        except Exception as e:
            return None
    
    def agregar_docente(self, nombres, apellidos, dni=None, celular=None, email=None):
        """Agrega un nuevo docente"""
        try:
            session = get_session()
            
            nuevo_docente = Docente(
                nombres=nombres,
                apellidos=apellidos,
                dni=dni,
                celular=celular,
                email=email
            )
            
            session.add(nuevo_docente)
            session.commit()
            session.close()
            
            return True, "Docente agregado exitosamente"
        
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def obtener_nombres_para_combobox(self):
        """Lista de nombres para ComboBox"""
        docentes = self.obtener_todos()
        return [d['nombre_completo'] for d in docentes]
    
    def buscar_por_nombre(self, nombre_completo):
        """Busca docente por nombre completo"""
        docentes = self.obtener_todos()
        for d in docentes:
            if d['nombre_completo'] == nombre_completo:
                return d
        return None
