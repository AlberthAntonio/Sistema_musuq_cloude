from app.database import SessionLocal
from app.models.alumno_model import Alumno
from app.models.pago_model import Pago 
from sqlalchemy.exc import IntegrityError
from datetime import datetime, date

class AlumnoController:
    def __init__(self):
        self.db = SessionLocal()

    def generar_codigo(self, grupo, modalidad):

        mapa_prefijos = {
            ("A", "PRIMERA OPCION"): "POA", ("A", "ORDINARIO"): "ORA", ("A", "COLEGIO"): "COA", ("A", "REFORZAMIENTO"): "REA",
            ("B", "PRIMERA OPCION"): "POB", ("B", "ORDINARIO"): "ORB", ("B", "COLEGIO"): "COB", ("B", "REFORZAMIENTO"): "REB",
            ("C", "PRIMERA OPCION"): "POC", ("C", "ORDINARIO"): "ORC", ("C", "COLEGIO"): "COC", ("C", "REFORZAMIENTO"): "REC",            
            ("D", "PRIMERA OPCION"): "POD", ("D", "ORDINARIO"): "ORD", ("D", "COLEGIO"): "COD", ("D", "REFORZAMIENTO"): "RED",
        }
        sufijo = mapa_prefijos.get((grupo, modalidad)) or "GEN"
        anio = str(datetime.now().year)[-2:]
        prefijo_base = f"{anio}{sufijo}"
        
        ultimo = self.db.query(Alumno.codigo_matricula).filter(
            Alumno.codigo_matricula.like(f"{prefijo_base}%")
        ).order_by(Alumno.id.desc()).first()

        consecutivo = int(ultimo[0][-4:]) + 1 if ultimo else 1
        return f"{prefijo_base}{consecutivo:04d}"

    def obtener_carreras_por_grupo(self, grupo):
        data = {
            "A": ["ARQUITECTURA", "ING. CIVIL", "ING. DE MINAS", "ING. INFORMÁTICA Y SISTEMAS", "ING. MECÁNICA", "ING. ELÉCTRICA", "ING. ELECTRÓNICA", "ING. GEOLÓGICA", "ING. METALURGICA", "ING. QUÍMICA", "ING. PETROQUÍMICA", "QUÍMICA", "FÍSICA", "MATEMÁTICA"],
            "B": ["MEDICINA HUMANA", "ENFERMERIA", "FARMACIA Y BIOQUIMICA", "ODONTOLOGIA", "BIOLOGIA", "AGRONOMÍA", "ZOOTECNIA"],
            "C": ["CONTABILIDAD", "ECONOMIA", "ADMINISTRACION", "TURISMO"],
            "D": ["DERECHO", "EDUCACION", "CIENCIAS DE LA COMUNICACION", "ARQUEOLOGIA", "ANTROPOLOGIA", "HISTORIA", "SOCIOLOGIA", "PSICOLOGIA", "FILOSOFIA", "ARTE"]
        }
        return data.get(grupo, [])

    def registrar_alumno(self, datos):
        try:
            nuevo_codigo = self.generar_codigo(datos['grupo'], datos['modalidad'])
            nom_padre = f"{datos['padre_nombres']} {datos['padre_ape_pat']} {datos['padre_ape_mat']}"

            
            nuevo_alumno = Alumno(
                codigo_matricula=nuevo_codigo,
                dni=datos['dni'],
                nombres=datos['nombres'],
                apell_paterno=datos['apell_paterno'],
                apell_materno=datos['apell_materno'],
                fecha_nacimiento=datos['fecha_nacimiento'],
                grupo=datos['grupo'],
                carrera=datos['carrera'],
                modalidad=datos['modalidad'],
                horario=datos['horario'],
                nombre_padre_completo=nom_padre,
                celular_padre_1=datos['tel1'],
                celular_padre_2=datos['tel2'],
                descripcion=datos['descripcion'],
                
                costo_matricula=float(datos['costo']) 
            )
            self.db.add(nuevo_alumno)
            self.db.flush() 

            # 2. Registrar el PRIMER PAGO si ingresaron un monto "A cuenta"
            importe_inicial = float(datos['importe'])
            if importe_inicial > 0:
                primer_pago = Pago(
                    alumno_id=nuevo_alumno.id,
                    monto=importe_inicial,
                    fecha=date.today(),
                    concepto="Pago Inicial / Matrícula"
                )
                self.db.add(primer_pago)

            self.db.commit()
            return True, f"Matrícula Exitosa.\nCódigo: {nuevo_codigo}"
            
        except IntegrityError:
            self.db.rollback()
            return False, "El DNI ya está registrado."
        except Exception as e:
            self.db.rollback()
            return False, f"Error: {str(e)}"

    def obtener_todos(self):
        self.db.expire_all()
        return self.db.query(Alumno).all()

    def obtener_por_id(self, alumno_id):
        return self.db.query(Alumno).filter(Alumno.id == alumno_id).first()

    def actualizar_alumno(self, alumno_id, datos):
        """Actualiza los datos de un alumno existente"""
        try:
            alumno = self.db.query(Alumno).filter(Alumno.id == alumno_id).first()
            if not alumno:
                return False, "Alumno no encontrado."

            # Actualizamos campos básicos
            alumno.dni = datos['dni']
            alumno.nombres = datos['nombres']
            alumno.apell_paterno = datos['apell_paterno']
            alumno.apell_materno = datos['apell_materno']
            alumno.fecha_nacimiento = datos['fecha_nacimiento']
            
            alumno.grupo = datos['grupo']
            alumno.carrera = datos['carrera']
            alumno.modalidad = datos['modalidad']
            alumno.horario = datos['horario']
            
            # Actualizamos datos del apoderado
            # Nota: Recibimos el nombre completo
            alumno.nombre_padre_completo = datos['nombre_padre_completo']
            alumno.celular_padre_1 = datos['tel1']
            alumno.celular_padre_2 = datos['tel2']
            alumno.descripcion = datos['descripcion']

            self.db.commit()
            return True, "Datos actualizados correctamente."
        except Exception as e:
            self.db.rollback()
            return False, f"Error al actualizar: {str(e)}"

    def eliminar_alumno(self, alumno_id):
        """Elimina un alumno y todos sus datos relacionados (pagos, asistencias)"""
        try:
            # Buscamos al alumno
            alumno = self.db.query(Alumno).filter(Alumno.id == alumno_id).first()
            if not alumno:
                return False, "Alumno no encontrado."

            self.db.delete(alumno)
            self.db.commit()
            return True, "Matrícula anulada y registros eliminados correctamente."
            
        except Exception as e:
            self.db.rollback()
            return False, f"Error al eliminar: {str(e)}"




