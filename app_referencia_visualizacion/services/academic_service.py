# Ubicación: app/services/academic_service.py
from app.database import SessionLocal

def obtener_cursos(grupo):
    """
    Servicio que consulta la Malla Curricular activa en la base de datos.
    Retorna la lista de nombres de cursos para un grupo dado.
    """
    # Importación local para evitar ciclos
    from app.models.curso_model import Curso, MallaCurricular
    
    session = SessionLocal()
    try:
        # Query optimizada: Join entre Curso y Malla
        resultados = session.query(Curso.nombre)\
                            .join(MallaCurricular)\
                            .filter(MallaCurricular.grupo == grupo)\
                            .all()
        
        # Convertir lista de tuplas [('Mate',), ('Lenguaje',)] a lista simple ['Mate', 'Lenguaje']
        lista_cursos = [r[0] for r in resultados]
        return lista_cursos
    except Exception as e:
        print(f"Error en academic_service: {e}")
        return []
    finally:
        session.close()