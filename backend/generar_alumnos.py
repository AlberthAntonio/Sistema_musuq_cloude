"""
🎓 GENERADOR DE ALUMNOS - Sistema Musuq Cloud
Genera alumnos siguiendo la arquitectura multi-tenant:
  Alumno (datos personales) → Matricula (datos académicos) → ObligacionPago (financiero)
"""

import sys
import os
import random
from datetime import datetime, date, timedelta

# Asegurar que el directorio raíz del backend esté en el path
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BACKEND_DIR)

# ⚠️ Cambiar el CWD al directorio backend ANTES de importar la app.
# Esto garantiza que la ruta relativa "sqlite:///./musuq_dev.db" en config.py
# siempre apunte a backend/musuq_dev.db, sin importar desde dónde se ejecute el script.
os.chdir(BACKEND_DIR)

# ⚠️ Forzar modo SQLite antes de importar la app (PostgreSQL puede no estar activo)
os.environ.setdefault("USE_SQLITE", "true")

from sqlalchemy.orm import Session
from app.db.database import SessionLocal, engine, Base
from app.models.alumno import Alumno
from app.models.matricula import Matricula
from app.models.periodo import PeriodoAcademico
from app.models.obligacion import ObligacionPago

# Importar todos los modelos para que SQLAlchemy los registre
from app.db.database import init_db

# ==========================================
# CONFIGURACIÓN
# ==========================================

ALUMNOS_POR_GRUPO = 30  # Alumnos por cada combinación modalidad-grupo

# ==========================================
# DATOS BASE
# ==========================================

# Modalidades con sus códigos
MODALIDADES = {
    "PO": "PRIMERA OPCION",
    "OR": "ORDINARIO",
    "CO": "COLEGIO",
    "RE": "REFORZAMIENTO",
}

# Grupos
GRUPOS = ["A", "B", "C", "D"]

# Horarios
HORARIOS = [
    "MATUTINO",
    "VESPERTINO",
    "DOBLE HORARIO",
]

# Carreras
CARRERAS = [
    "MEDICINA",
    "DERECHO",
    "INGENIERÍA CIVIL",
    "ARQUITECTURA",
    "ADMINISTRACIÓN",
    "CONTABILIDAD",
    "ENFERMERÍA",
    "ING. AMBIENTAL",
    "ING. SISTEMAS",
    "ECONOMÍA",
    "PSICOLOGÍA",
    "ODONTOLOGÍA",
]

# Nombres comunes peruanos
NOMBRES = [
    "JUAN", "MARIA", "CARLOS", "ANA", "LUIS", "ROSA", "PEDRO", "CARMEN",
    "JOSE", "LAURA", "MIGUEL", "SOFIA", "DANIEL", "PATRICIA", "JORGE",
    "GABRIELA", "RICARDO", "DANIELA", "FERNANDO", "ANGELA", "ROBERTO",
    "LUCIA", "ANTONIO", "VALENTINA", "MANUEL", "CAMILA", "FRANCISCO",
    "ISABELLA", "DIEGO", "ANDREA", "PABLO", "FERNANDA", "ANDRES", "NATALIA",
    "RAFAEL", "PAULA", "EDUARDO", "CAROLINA", "ALEJANDRO", "VERONICA",
    "SERGIO", "DIANA", "MARIO", "MELISSA", "RAUL", "LORENA", "DAVID",
    "KATHERINE", "OSCAR", "VANESSA", "CESAR", "MONICA", "HUGO", "JESSICA",
    "RUBEN", "SANDRA", "IVAN", "PAMELA", "VICTOR", "RUTH", "MARCO",
    "CECILIA", "ALBERTO", "SILVIA", "ENRIQUE", "BEATRIZ", "GUSTAVO",
    "YOLANDA", "ARMANDO", "CLAUDIA", "FELIX", "ALEJANDRA",
    "MARIANA", "HECTOR", "KARINA", "ARTURO", "SUSANA", "ERNESTO", "LIDIA",
]

APELLIDOS = [
    "GARCIA", "RODRIGUEZ", "MARTINEZ", "LOPEZ", "GONZALEZ", "PEREZ",
    "SANCHEZ", "RAMIREZ", "TORRES", "FLORES", "RIVERA", "GOMEZ",
    "DIAZ", "CRUZ", "MORALES", "REYES", "GUTIERREZ", "ORTIZ",
    "JIMENEZ", "HERNANDEZ", "RUIZ", "MENDOZA", "ALVAREZ", "CASTILLO",
    "ROMERO", "HERRERA", "MEDINA", "AGUILAR", "VARGAS", "CASTRO",
    "RAMOS", "GUERRERO", "VAZQUEZ", "NUNEZ", "SILVA", "ROJAS",
    "SOTO", "CONTRERAS", "GUZMAN", "VEGA", "CAMPOS", "MORA",
    "PENA", "QUISPE", "MAMANI", "HUAMAN", "CHAVEZ", "TICONA",
    "CONDORI", "NINA", "FLORES", "APAZA", "CCAMA", "LAURA",
    "PACHA", "YUCRA", "ALANOCA", "CUSI", "CHOQUE", "PARI",
    "TARQUI", "SARMIENTO", "VELASQUEZ", "ARIAS", "ACOSTA", "LARA",
    "SALAZAR", "BENAVIDES", "CACERES", "CORDOVA", "ESPINOZA", "IBARRA",
]

NOMBRES_PADRES = [
    "JUAN CARLOS", "PEDRO LUIS", "JOSE ANTONIO", "MIGUEL ANGEL",
    "CARLOS ALBERTO", "ROBERTO MARIO", "FERNANDO JAVIER", "MANUEL RICARDO",
    "MARIA TERESA", "ANA MARIA", "ROSA ELENA", "CARMEN LUCIA",
    "PATRICIA ANGELICA", "LAURA BEATRIZ", "GABRIELA SOFIA",
]

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def generar_dni():
    """Genera un DNI peruano aleatorio de 8 dígitos."""
    return str(random.randint(10000000, 99999999))

def generar_celular():
    """Genera un número celular peruano (9 dígitos, empieza con 9)."""
    return f"9{random.randint(10000000, 99999999)}"

def generar_nombre_completo():
    """Genera nombre, apellido paterno y materno."""
    nombre = random.choice(NOMBRES)
    apell_pat = random.choice(APELLIDOS)
    apell_mat = random.choice(APELLIDOS)
    return nombre, apell_pat, apell_mat

def generar_fecha_nacimiento():
    """Genera una fecha de nacimiento (17-25 años atrás)."""
    hoy = datetime.now()
    edad_dias = random.randint(17 * 365, 25 * 365)
    return (hoy - timedelta(days=edad_dias)).date()

def generar_nombre_padre():
    """Genera nombre completo de padre/madre."""
    nombre = random.choice(NOMBRES_PADRES)
    apellido1 = random.choice(APELLIDOS)
    apellido2 = random.choice(APELLIDOS)
    return f"{nombre} {apellido1} {apellido2}"


# Mapa de prefijos para código de matrícula (misma lógica que MatriculaService)
MAPA_PREFIJOS = {
    ("A", "PRIMERA OPCION"): "POA", ("A", "ORDINARIO"): "ORA", ("A", "COLEGIO"): "COA", ("A", "REFORZAMIENTO"): "REA",
    ("B", "PRIMERA OPCION"): "POB", ("B", "ORDINARIO"): "ORB", ("B", "COLEGIO"): "COB", ("B", "REFORZAMIENTO"): "REB",
    ("C", "PRIMERA OPCION"): "POC", ("C", "ORDINARIO"): "ORC", ("C", "COLEGIO"): "COC", ("C", "REFORZAMIENTO"): "REC",
    ("D", "PRIMERA OPCION"): "POD", ("D", "ORDINARIO"): "ORD", ("D", "COLEGIO"): "COD", ("D", "REFORZAMIENTO"): "RED",
}


def generar_codigo_matricula(db: Session, grupo: str, modalidad_nombre: str) -> str:
    """
    Genera código de matrícula con formato: {Año}{Prefijo}{Consecutivo}
    Ejemplo: 26POA0001 (2026, Primera Opción Grupo A, alumno #1)
    Usa la misma lógica que MatriculaService.generar_codigo().
    """
    sufijo = MAPA_PREFIJOS.get((grupo, modalidad_nombre), "GEN")
    anio = str(datetime.now().year)[-2:]
    prefijo_base = f"{anio}{sufijo}"

    # Buscar último código con este prefijo
    ultimo = db.query(Matricula.codigo_matricula).filter(
        Matricula.codigo_matricula.like(f"{prefijo_base}%")
    ).order_by(Matricula.id.desc()).first()

    if ultimo and ultimo[0]:
        consecutivo = int(ultimo[0][-4:]) + 1
    else:
        consecutivo = 1

    return f"{prefijo_base}{consecutivo:04d}"


def obtener_o_crear_periodo(db: Session) -> PeriodoAcademico:
    """Obtiene el periodo activo o crea uno nuevo si no existe."""
    periodo = db.query(PeriodoAcademico).filter(
        PeriodoAcademico.estado == "activo"
    ).first()

    if periodo:
        print(f"📅 Usando periodo existente: {periodo.nombre} (ID: {periodo.id})")
        return periodo

    # Crear periodo automáticamente
    hoy = date.today()
    anio = hoy.year
    semestre = "I" if hoy.month <= 6 else "II"
    nombre_periodo = f"{anio}-{semestre}"

    # Verificar que el nombre no exista ya (cerrado)
    existente = db.query(PeriodoAcademico).filter(
        PeriodoAcademico.nombre == nombre_periodo
    ).first()
    if existente:
        nombre_periodo = f"{anio}-{semestre}-gen"

    periodo = PeriodoAcademico(
        nombre=nombre_periodo,
        tipo="academia",
        fecha_inicio=date(anio, 1 if semestre == "I" else 7, 1),
        fecha_fin=date(anio, 6, 30) if semestre == "I" else date(anio, 12, 31),
        estado="activo",
    )
    db.add(periodo)
    db.flush()  # Para obtener el ID
    db.commit()  # Persistir el periodo inmediatamente
    print(f"📅 Periodo creado: {periodo.nombre} (ID: {periodo.id})")
    return periodo


# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================

def generar_alumnos():
    """Genera alumnos con sus matrículas y obligaciones de pago."""

    print("=" * 70)
    print("🎓 GENERADOR DE ALUMNOS - MUSUQ CLOUD")
    print("   Arquitectura: Alumno → Matrícula → ObligaciónPago")
    print("=" * 70)

    # Crear tablas si no existen
    init_db()

    # Abrir sesión de BD
    db: Session = SessionLocal()
    try:
        # Obtener DNIs existentes para evitar duplicados
        dnis_existentes = set(
            dni[0] for dni in db.query(Alumno.dni).all()
        )

        print(f"📊 DNIs existentes en BD: {len(dnis_existentes)}")
        print(f"📝 Generando {ALUMNOS_POR_GRUPO} alumnos por cada grupo/modalidad...")
        print()

        # Obtener o crear periodo académico activo
        periodo = obtener_o_crear_periodo(db)
        periodo_id = periodo.id  # Guardar ID por si el objeto queda detached

        total_alumnos = 0
        total_matriculas = 0
        total_obligaciones = 0
        errores = 0

        # Iterar por cada combinación de modalidad y grupo
        for mod_codigo, mod_nombre in MODALIDADES.items():
            for grupo in GRUPOS:

                print(f"📌 Procesando: {mod_nombre} - Grupo {grupo}")

                for i in range(ALUMNOS_POR_GRUPO):

                    # --- 1. Crear ALUMNO (datos personales) ---
                    dni = generar_dni()
                    while dni in dnis_existentes:
                        dni = generar_dni()
                    dnis_existentes.add(dni)

                    nombre, apell_pat, apell_mat = generar_nombre_completo()
                    fecha_nac = generar_fecha_nacimiento()
                    celular1 = generar_celular()
                    celular2 = generar_celular() if random.random() > 0.3 else None

                    try:
                        alumno = Alumno(
                            dni=dni,
                            nombres=nombre,
                            apell_paterno=apell_pat,
                            apell_materno=apell_mat,
                            fecha_nacimiento=fecha_nac,
                            nombre_padre_completo=generar_nombre_padre(),
                            celular_padre_1=celular1,
                            celular_padre_2=celular2,
                            activo=True,
                        )
                        db.add(alumno)
                        db.flush()  # Para obtener alumno.id
                        total_alumnos += 1

                        # --- 2. Crear MATRÍCULA (datos académicos) ---
                        codigo = generar_codigo_matricula(db, grupo, mod_nombre)
                        carrera = random.choice(CARRERAS)
                        horario = random.choice(HORARIOS)

                        matricula = Matricula(
                            codigo_matricula=codigo,
                            alumno_id=alumno.id,
                            periodo_id=periodo_id,
                            grupo=grupo,
                            carrera=carrera,
                            modalidad=mod_nombre,
                            horario=horario,
                            estado="activo",
                        )
                        db.add(matricula)
                        db.flush()  # Para obtener matricula.id
                        total_matriculas += 1

                        # --- 3. Crear OBLIGACIÓN DE PAGO (financiero) ---
                        costo = random.choice([400.0, 450.0, 500.0, 550.0, 600.0])

                        obligacion = ObligacionPago(
                            matricula_id=matricula.id,
                            concepto="Matrícula",
                            monto_total=costo,
                            monto_pagado=0.0,
                            estado="pendiente",
                        )
                        db.add(obligacion)
                        total_obligaciones += 1

                        # Commit individual: garantiza que un error posterior
                        # no revierta este alumno ya guardado correctamente
                        db.commit()

                    except Exception as e:
                        errores += 1
                        db.rollback()  # Solo revierte el alumno actual
                        print(f"   ⚠️ Error al insertar alumno {dni}: {e}")

                print(f"   ✅ Generados: {ALUMNOS_POR_GRUPO} alumnos")

        # Los commits ya se hicieron individualmente en el loop
        print()
        print("=" * 70)
        print("✅ PROCESO COMPLETADO")
        print(f"� Alumnos creados: {total_alumnos}")
        print(f"📋 Matrículas creadas: {total_matriculas}")
        print(f"💰 Obligaciones de pago creadas: {total_obligaciones}")
        print(f"❌ Errores: {errores}")
        print("=" * 70)

        # Resumen por modalidad y grupo
        print("\n📈 RESUMEN POR MODALIDAD Y GRUPO:")
        print("-" * 70)

        for mod_codigo, mod_nombre in MODALIDADES.items():
            print(f"\n{mod_nombre}:")
            for grupo in GRUPOS:
                count = db.query(Matricula).filter(
                    Matricula.modalidad == mod_nombre,
                    Matricula.grupo == grupo,
                    Matricula.periodo_id == periodo_id,
                ).count()
                print(f"  Grupo {grupo}: {count} alumnos")

        # Total general
        total_alumnos_bd = db.query(Alumno).count()
        total_matriculas_bd = db.query(Matricula).filter(
            Matricula.periodo_id == periodo_id
        ).count()
        periodo_nombre = db.query(PeriodoAcademico.nombre).filter(
            PeriodoAcademico.id == periodo_id
        ).scalar()
        print(f"\n📊 TOTAL EN BD: {total_alumnos_bd} alumnos, {total_matriculas_bd} matrículas en periodo {periodo_nombre}")

    except Exception as e:
        db.rollback()
        print(f"\n❌ Error general: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\n✅ Sesión de base de datos cerrada correctamente")


# ==========================================
# FUNCIÓN PARA VER ESTADÍSTICAS
# ==========================================

def mostrar_estadisticas():
    """Muestra estadísticas de la base de datos."""
    init_db()
    db: Session = SessionLocal()

    try:
        print("\n" + "=" * 70)
        print("📊 ESTADÍSTICAS DE LA BASE DE DATOS")
        print("=" * 70)

        # Total de alumnos
        total = db.query(Alumno).count()
        print(f"\n👥 Total de alumnos: {total}")

        # Periodos
        periodos = db.query(PeriodoAcademico).all()
        print(f"\n� Periodos académicos: {len(periodos)}")
        for p in periodos:
            mat_count = db.query(Matricula).filter(Matricula.periodo_id == p.id).count()
            print(f"  {p.nombre} ({p.estado}): {mat_count} matrículas")

        # Total de matrículas
        total_mat = db.query(Matricula).count()
        print(f"\n📋 Total de matrículas: {total_mat}")

        # Por modalidad
        print("\n📋 Matrículas por Modalidad:")
        from sqlalchemy import func
        resultados = db.query(
            Matricula.modalidad, func.count(Matricula.id)
        ).group_by(Matricula.modalidad).order_by(Matricula.modalidad).all()
        for modalidad, count in resultados:
            print(f"  {modalidad or 'Sin modalidad':25} {count:5} matrículas")

        # Por grupo
        print("\n📋 Matrículas por Grupo:")
        resultados = db.query(
            Matricula.grupo, func.count(Matricula.id)
        ).group_by(Matricula.grupo).order_by(Matricula.grupo).all()
        for grupo, count in resultados:
            print(f"  Grupo {grupo or '?':20} {count:5} matrículas")

        # Por horario
        print("\n⏰ Matrículas por Horario:")
        resultados = db.query(
            Matricula.horario, func.count(Matricula.id)
        ).group_by(Matricula.horario).order_by(Matricula.horario).all()
        for horario, count in resultados:
            print(f"  {horario or 'Sin horario':25} {count:5} matrículas")

        # Top 10 carreras
        print("\n🎓 Top 10 Carreras:")
        resultados = db.query(
            Matricula.carrera, func.count(Matricula.id)
        ).group_by(Matricula.carrera).order_by(func.count(Matricula.id).desc()).limit(10).all()
        for carrera, count in resultados:
            print(f"  {carrera or 'Sin carrera':25} {count:5} matrículas")

        # Obligaciones de pago
        total_oblig = db.query(ObligacionPago).count()
        print(f"\n💰 Total obligaciones de pago: {total_oblig}")
        if total_oblig > 0:
            monto_total = db.query(func.sum(ObligacionPago.monto_total)).scalar() or 0
            monto_pagado = db.query(func.sum(ObligacionPago.monto_pagado)).scalar() or 0
            print(f"  Monto total: S/ {monto_total:,.2f}")
            print(f"  Monto pagado: S/ {monto_pagado:,.2f}")
            print(f"  Saldo pendiente: S/ {monto_total - monto_pagado:,.2f}")

    finally:
        db.close()


# ==========================================
# EJECUTAR
# ==========================================

if __name__ == "__main__":

    print("\n" + "=" * 70)
    print("🎓 GENERADOR DE ALUMNOS - SISTEMA MUSUQ CLOUD")
    print("   Arquitectura: Alumno → Matrícula → ObligaciónPago")
    print("=" * 70)
    print("\nOpciones:")
    print("1. Generar nuevos alumnos (con matrículas y obligaciones)")
    print("2. Ver estadísticas actuales")
    print("3. Salir")
    print()

    try:
        opcion = input("Selecciona una opción (1-3): ").strip()

        if opcion == "1":
            total_esperado = len(MODALIDADES) * len(GRUPOS) * ALUMNOS_POR_GRUPO
            confirmacion = input(
                f"\n⚠️ Se generarán ~{total_esperado} alumnos "
                f"(con sus matrículas y obligaciones de pago). ¿Continuar? (s/n): "
            ).strip().lower()
            if confirmacion == "s":
                generar_alumnos()
                mostrar_estadisticas()
            else:
                print("❌ Operación cancelada")

        elif opcion == "2":
            mostrar_estadisticas()

        elif opcion == "3":
            print("👋 Hasta luego!")

        else:
            print("❌ Opción inválida")

    except KeyboardInterrupt:
        print("\n\n❌ Proceso interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
