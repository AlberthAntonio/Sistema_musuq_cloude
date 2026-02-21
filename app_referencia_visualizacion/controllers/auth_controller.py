from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.usuario_model import Usuario

class AuthController:
    def __init__(self):
        self.db: Session = SessionLocal()

    def login(self, usuario, password):
        """
        Verifica las credenciales.
        Retorna: (Exito: bool, Mensaje: str, UsuarioObj: Usuario|None)
        """
        # Buscamos el usuario en la BD
        user_db = self.db.query(Usuario).filter(Usuario.username == usuario).first()

        if not user_db:
            return False, "El usuario no existe", None
        
        if user_db.password != password:
            return False, "Contraseña incorrecta", None
        
        return True, "Inicio de sesión exitoso", user_db

    def inicializar_admin(self):
        """Crea un usuario admin por defecto si la BD está vacía."""
        try:
            existe = self.db.query(Usuario).filter_by(username="admin").first()
            if not existe:
                nuevo_admin = Usuario(
                    username="admin", 
                    password="123", 
                    nombre_completo="Administrador del Sistema",
                    rol="admin"
                )
                self.db.add(nuevo_admin)
                self.db.commit()
                print("✅ Usuario 'admin' creado (Pass: 123)")
        except Exception as e:
            print(f"Error al inicializar admin: {e}")
        finally:
            self.db.close()