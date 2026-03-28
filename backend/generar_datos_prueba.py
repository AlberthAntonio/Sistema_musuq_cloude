"""
Generador de datos de prueba - Esquema nuevo (alumnos + matriculas separados)
Sistema Musuq Cloud
"""
import random
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.db.database import SessionLocal, engine, Base
from app.models.alumno import Alumno
from app.models.matricula import Matricula
from app.models.periodo import PeriodoAcademico

# ==========================================
# DATOS BASE
# ==========================================

MODALIDADES = ["PRIMERA OPCION", "ORDINARIO", "COLEGIO", "REFORZAMIENTO"]
GRUPOS = ["A", "B", "C", "D"]
HORARIOS = ["MATUTINO", "VESPERTINO", "DOBLE HORARIO"]
CARRERAS = [
    "MEDICINA", "DERECHO", "INGENIERÍA CIVIL", "ARQUITECTURA",
    "ADMINISTRACIÓN", "CONTABILIDAD", "ENFERMERÍA", "ING. SISTEMAS",
    "ECONOMÍA", "PSICOLOGÍA", "ODONTOLOGÍA", "ING. AMBIENTAL"
]
NIVELES = ["PRIMARIA", "SECUNDARIA"]
GRADOS  = ["1°", "2°", "3°", "4°", "5°"]

NOMBRES = [
    "JUAN", "MARIA", "CARLOS", "ANA", "LUIS", "ROSA", "PEDRO", "CARMEN",
    "JOSE", "LAURA", "MIGUEL", "SOFIA", "DANIEL", "PATRICIA", "JORGE",
    "GABRIELA", "RICARDO", "DANIELA", "FERNANDO", "ANGELA", "ROBERTO",
    "LUCIA", "ANTONIO", "VALENTINA", "MANUEL", "CAMILA", "FRANCISCO",
    "ISABELLA", "DIEGO", "ANDREA", "PABLO", "FERNANDA", "ANDRES", "NATALIA",
    "RAFAEL", "PAULA", "EDUARDO", "CAROLINA", "ALEJANDRO", "VERONICA"
]
APELLIDOS = [
    "GARCIA", "RODRIGUEZ", "MARTINEZ", "LOPEZ", "GONZALEZ", "PEREZ",
    "SANCHEZ", "RAMIREZ", "TORRES", "FLORES", "RIVERA", "GOMEZ",
    "DIAZ", "CRUZ", "MORALES", "REYES", "GUTIERREZ", "ORTIZ",
    "JIMENEZ", "HERNANDEZ", "RUIZ", "MENDOZA", "ALVAREZ", "CASTILLO",
    "ROMERO", "HERRERA", "MEDINA", "AGUILAR", "VARGAS", "CASTRO",
    "QUISPE", "MAMANI", "HUANCA", "CONDORI", "CCOPA", "APAZA",
    "HUAYHUA", "CUTIPA", "CALISAYA", "PARI", "LAYME", "COAQUIRA"
]

PREFIJOS = {
    ("A", "PRIMERA OPCION"): "POA", ("B", "PRIMERA OPCION"): "POB",
    ("C", "PRIMERA OPCION"): "POC", ("D", "PRIMERA OPCION"): "POD",
    ("A", "ORDINARIO"):      "ORA", ("B", "ORDINARIO"):      "ORB",
    ("C", "ORDINARIO"):      "ORC", ("D", "ORDINARIO"):      "ORD",
    ("A", "COLEGIO"):        "COA", ("B", "COLEGIO"):        "COB",
    ("C", "COLEGIO"):        "COC", ("D", "COLEGIO"):        "COD",
    ("A", "REFORZAMIENTO"):  "REA", ("B", "REFORZAMIENTO"):  "REB",
    ("C", "REFORZAMIENTO"):  "REC", ("D", "REFORZAMIENTO"):  "RED",
}

dnis_usados = set()
contadores_codigos = {}

def gen_dni():
    while True:
        d = str(random.randint(10000000, 99999999))
        if d not in dnis_usados:
            dnis_usados.add(d)
            return d

def gen_codigo(grupo, modalidad):
    prefijo = PREFIJOS.get((grupo, modalidad), "GEN")
    anio = "26"
    base = f"{anio}{prefijo}"
    contadores_codigos[base] = contadores_codigos.get(base, 0) + 1
    return f"{base}{contadores_codigos[base]:04d}"

def gen_celular():
    return f"9{random.randint(10000000, 99999999)}"


def main():
    db = SessionLocal()
    try:
        # ========== 1. PERIODO ACADÉMICO ==========
        periodo = db.query(PeriodoAcademico).filter(PeriodoAcademico.estado == "activo").first()
        if not periodo:
            from datetime import date
            periodo = PeriodoAcademico(
                nombre="CICLO VERANO 2026",
                tipo="academia",
                fecha_inicio=date(2026, 1, 6),
                fecha_fin=date(2026, 3, 31),
                estado="activo",
            )
            db.add(periodo)
            db.commit()
            db.refresh(periodo)
            print(f"✅ Periodo creado: {periodo.nombre} (id={periodo.id})")
        else:
            print(f"ℹ️  Periodo existente: {periodo.nombre} (id={periodo.id})")

        # Cargar DNIs ya registrados
        existentes = db.query(Alumno.dni).all()
        for (d,) in existentes:
            dnis_usados.add(d)

        # ========== 2. GENERAR ALUMNOS + MATRÍCULAS ==========
        ALUMNOS_POR_COMBINACION = 10  # 10 por cada grupo+modalidad = ~480 total
        total_creados = 0
        errores = 0

        for modalidad in MODALIDADES:
            for grupo in GRUPOS:
                for _ in range(ALUMNOS_POR_COMBINACION):
                    try:
                        # Datos personales
                        nombre = random.choice(NOMBRES) + " " + random.choice(NOMBRES)
                        apell_pat = random.choice(APELLIDOS)
                        apell_mat = random.choice(APELLIDOS)
                        dni = gen_dni()

                        alumno = Alumno(
                            dni=dni,
                            nombres=nombre,
                            apell_paterno=apell_pat,
                            apell_materno=apell_mat,
                            nombre_padre_completo=f"{random.choice(NOMBRES)} {apell_pat} {random.choice(APELLIDOS)}",
                            celular_padre_1=gen_celular(),
                            activo=True,
                        )
                        db.add(alumno)
                        db.flush()  # Obtener id sin commit

                        # Carrera o nivel/grado según modalidad
                        carrera = None
                        nivel = None
                        grado = None
                        if modalidad == "COLEGIO":
                            nivel = random.choice(NIVELES)
                            grado = random.choice(GRADOS)
                        else:
                            carrera = random.choice(CARRERAS)

                        codigo = gen_codigo(grupo, modalidad)
                        matricula = Matricula(
                            alumno_id=alumno.id,
                            periodo_id=periodo.id,
                            codigo_matricula=codigo,
                            grupo=grupo,
                            modalidad=modalidad,
                            horario=random.choice(HORARIOS),
                            carrera=carrera,
                            nivel=nivel,
                            grado=grado,
                            estado="activo",
                        )
                        db.add(matricula)
                        total_creados += 1

                    except Exception as e:
                        errores += 1
                        db.rollback()
                        print(f"  ⚠️ Error: {e}")
                        continue

                db.commit()
                print(f"  ✅ {modalidad} - Grupo {grupo}: {ALUMNOS_POR_COMBINACION} alumnos")

        # ========== 3. TAMBIÉN CREAR MATRÍCULA PARA ALUMNO EXISTENTE ==========
        alumno_sin_mat = db.query(Alumno).outerjoin(
            Matricula, Matricula.alumno_id == Alumno.id
        ).filter(Matricula.id == None).all()

        for alumno in alumno_sin_mat:
            grupo = random.choice(GRUPOS)
            modalidad = random.choice(["PRIMERA OPCION", "ORDINARIO"])
            codigo = gen_codigo(grupo, modalidad)
            mat = Matricula(
                alumno_id=alumno.id,
                periodo_id=periodo.id,
                codigo_matricula=codigo,
                grupo=grupo,
                modalidad=modalidad,
                horario=random.choice(HORARIOS),
                carrera=random.choice(CARRERAS),
                estado="activo",
            )
            db.add(mat)
            print(f"  ➕ Matrícula creada para alumno existente: {alumno.nombres} → {codigo}")

        db.commit()

        total_al = db.query(Alumno).count()
        total_mat = db.query(Matricula).count()
        print(f"\n{'='*60}")
        print(f"✅ COMPLETADO")
        print(f"   Alumnos en BD:    {total_al}")
        print(f"   Matrículas en BD: {total_mat}")
        print(f"   Errores:          {errores}")
        print(f"{'='*60}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
