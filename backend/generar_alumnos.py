"""
🎓 GENERADOR DE ALUMNOS - Sistema Musuq Cloud
Genera alumnos siguiendo el formato de la base de datos existente
"""

import sqlite3
import random
from datetime import datetime, timedelta

# ==========================================
# CONFIGURACIÓN
# ==========================================

DB_PATH = "musuq_dev.db"  # Ruta de tu base de datos

# Cantidad de alumnos a generar por modalidad-grupo
ALUMNOS_POR_GRUPO = 30  # Genera 15 alumnos por cada combinación

# ==========================================
# DATOS BASE
# ==========================================

# Modalidades con sus códigos
MODALIDADES = {
    "PO": "PRIMERA OPCION",
    "OR": "ORDINARIO",
    "CO": "COLEGIO",
    "RE": "REFORZAMIENTO"  # ← NUEVA MODALIDAD
}

# Grupos
GRUPOS = ["A", "B", "C", "D"]

# Horarios
HORARIOS = [
    "MATUTINO",
    "VESPERTINO",
    "DOBLE HORARIO"
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
    "ODONTOLOGÍA"
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
    "YOLANDA", "ARMANDO", "CLAUDIA", "FELIX", "ALEJANDRA", "CESAR",
    "MARIANA", "HECTOR", "KARINA", "ARTURO", "SUSANA", "ERNESTO", "LIDIA"
]

APELLIDOS = [
    "GARCIA", "RODRIGUEZ", "MARTINEZ", "LOPEZ", "GONZALEZ", "PEREZ",
    "SANCHEZ", "RAMIREZ", "TORRES", "FLORES", "RIVERA", "GOMEZ",
    "DIAZ", "CRUZ", "MORALES", "REYES", "GUTIERREZ", "ORTIZ",
    "JIMENEZ", "HERNANDEZ", "RUIZ", "MENDOZA", "ALVAREZ", "CASTILLO",
    "ROMERO", "HERRERA", "MEDINA", "AGUILAR", "VARGAS", "Castro",
    "RAMOS", "GUERRERO", "VAZQUEZ", "NUNEZ", "SILVA", "ROJAS",
    "SOTO", "CONTRERAS", "GUZMAN", "VEGA", "CAMPOS", "MORA",
    "PENA", "QUISPE", "MAMANI", "HUAMAN", "CHAVEZ", "TICONA",
    "CONDORI", "NINA", "FLORES", "APAZA", "CCAMA", "LAURA",
    "PACHA", "YUCRA", "ALANOCA", "CUSI", "CHOQUE", "PARI",
    "TARQUI", "SARMIENTO", "VELASQUEZ", "ARIAS", "ACOSTA", "LARA",
    "SALAZAR", "BENAVIDES", "CACERES", "CORDOVA", "ESPINOZA", "IBARRA"
]

# Nombres de padres (para el campo nombre_padre_completo)
NOMBRES_PADRES = [
    "JUAN CARLOS", "PEDRO LUIS", "JOSE ANTONIO", "MIGUEL ANGEL",
    "CARLOS ALBERTO", "ROBERTO MARIO", "FERNANDO JAVIER", "MANUEL RICARDO",
    "MARIA TERESA", "ANA MARIA", "ROSA ELENA", "CARMEN LUCIA",
    "PATRICIA ANGELICA", "LAURA BEATRIZ", "GABRIELA SOFIA"
]

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def generar_dni():
    """Genera un DNI peruano aleatorio de 8 dígitos"""
    return str(random.randint(10000000, 99999999))

def generar_celular():
    """Genera un número celular peruano (9 dígitos, empieza con 9)"""
    return f"9{random.randint(10000000, 99999999)}"

def generar_nombre_completo():
    """Genera un nombre completo aleatorio"""
    nombre = random.choice(NOMBRES)
    apellido_paterno = random.choice(APELLIDOS).upper()
    apellido_materno = random.choice(APELLIDOS).upper()
    return nombre, apellido_paterno, apellido_materno

def generar_fecha_nacimiento():
    """Genera una fecha de nacimiento (17-25 años atrás)"""
    hoy = datetime.now()
    edad_dias = random.randint(17*365, 25*365)
    fecha_nac = hoy - timedelta(days=edad_dias)
    return fecha_nac.strftime("%Y-%m-%d")

def generar_nombre_padre():
    """Genera nombre completo de padre/madre"""
    nombre = random.choice(NOMBRES_PADRES)
    apellido = random.choice(APELLIDOS).upper()
    apellido2 = random.choice(APELLIDOS).upper()
    return f"{nombre} {apellido} {apellido2}"

def generar_codigo_matricula(modalidad_codigo, grupo, numero):
    """
    Genera código de matrícula en formato: 26[MOD][GRUPO][NUM]
    Ejemplo: 26PRA0001, 26ORB0023, 26RED0005
    """
    return f"26{modalidad_codigo}{grupo}{numero:04d}"

def obtener_siguiente_numero(cursor, modalidad_codigo, grupo):
    """Obtiene el siguiente número disponible para la combinación modalidad-grupo"""
    patron = f"26{modalidad_codigo}{grupo}%"
    cursor.execute(
        "SELECT codigo_matricula FROM alumnos WHERE codigo_matricula LIKE ? ORDER BY codigo_matricula DESC LIMIT 1",
        (patron,)
    )
    resultado = cursor.fetchone()
    
    if resultado:
        # Extraer el número del código (últimos 4 dígitos)
        ultimo_codigo = resultado[0]
        ultimo_numero = int(ultimo_codigo[-4:])
        return ultimo_numero + 1
    else:
        return 1

# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================

def generar_alumnos():
    """Genera alumnos para todas las combinaciones de modalidad y grupo"""
    
    print("="*70)
    print("🎓 GENERADOR DE ALUMNOS - MUSUQ CLOUD")
    print("="*70)
    
    # Conectar a la base de datos
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print(f"✅ Conexión exitosa a: {DB_PATH}")
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        return
    
    # Obtener DNIs existentes para evitar duplicados
    cursor.execute("SELECT dni FROM alumnos")
    dnis_existentes = set(dni[0] for dni in cursor.fetchall())
    
    print(f"📊 DNIs existentes en BD: {len(dnis_existentes)}")
    print(f"📝 Generando {ALUMNOS_POR_GRUPO} alumnos por cada grupo/modalidad...")
    print()
    
    total_generados = 0
    errores = 0
    
    # Iterar por cada combinación de modalidad y grupo
    for mod_codigo, mod_nombre in MODALIDADES.items():
        for grupo in GRUPOS:
            
            print(f"📌 Procesando: {mod_nombre} - Grupo {grupo}")
            
            # Obtener el siguiente número disponible
            numero_inicial = obtener_siguiente_numero(cursor, mod_codigo, grupo)
            
            for i in range(ALUMNOS_POR_GRUPO):
                numero_actual = numero_inicial + i
                
                # Generar datos del alumno
                codigo = generar_codigo_matricula(mod_codigo, grupo, numero_actual)
                
                # Generar DNI único
                dni = generar_dni()
                while dni in dnis_existentes:
                    dni = generar_dni()
                dnis_existentes.add(dni)
                
                nombre, apell_pat, apell_mat = generar_nombre_completo()
                fecha_nac = generar_fecha_nacimiento()
                carrera = random.choice(CARRERAS)
                horario = random.choice(HORARIOS)
                nombre_padre = generar_nombre_padre()
                celular1 = generar_celular()
                celular2 = generar_celular() if random.random() > 0.3 else None
                
                # Costo de matrícula variable
                costo = random.choice([400.0, 450.0, 500.0, 550.0, 600.0])
                
                # Insertar en la base de datos
                try:
                    cursor.execute("""
                        INSERT INTO alumnos (
                            codigo_matricula, dni, nombres, apell_paterno, apell_materno,
                            fecha_nacimiento, grupo, carrera, modalidad, horario,
                            nombre_padre_completo, celular_padre_1, celular_padre_2,
                            costo_matricula, activo
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        codigo, dni, nombre, apell_pat, apell_mat,
                        fecha_nac, grupo, carrera, mod_nombre, horario,
                        nombre_padre, celular1, celular2,
                        costo, 1
                    ))
                    total_generados += 1
                    
                except sqlite3.IntegrityError as e:
                    errores += 1
                    print(f"   ⚠️ Error al insertar {codigo}: {e}")
            
            print(f"   ✅ Generados: {ALUMNOS_POR_GRUPO} alumnos")
    
    # Guardar cambios
    conn.commit()
    print()
    print("="*70)
    print(f"✅ PROCESO COMPLETADO")
    print(f"📊 Total alumnos generados: {total_generados}")
    print(f"❌ Errores: {errores}")
    print("="*70)
    
    # Mostrar resumen por modalidad y grupo
    print("\n📈 RESUMEN POR MODALIDAD Y GRUPO:")
    print("-"*70)
    
    for mod_codigo, mod_nombre in MODALIDADES.items():
        print(f"\n{mod_nombre}:")
        for grupo in GRUPOS:
            cursor.execute(
                "SELECT COUNT(*) FROM alumnos WHERE modalidad = ? AND grupo = ?",
                (mod_nombre, grupo)
            )
            count = cursor.fetchone()[0]
            print(f"  Grupo {grupo}: {count} alumnos")
    
    # Mostrar total general
    cursor.execute("SELECT COUNT(*) FROM alumnos")
    total_bd = cursor.fetchone()[0]
    print(f"\n📊 TOTAL EN BASE DE DATOS: {total_bd} alumnos")
    
    conn.close()
    print("\n✅ Base de datos cerrada correctamente")

# ==========================================
# FUNCIÓN PARA VER ESTADÍSTICAS
# ==========================================

def mostrar_estadisticas():
    """Muestra estadísticas de la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*70)
    print("📊 ESTADÍSTICAS DE LA BASE DE DATOS")
    print("="*70)
    
    # Total de alumnos
    cursor.execute("SELECT COUNT(*) FROM alumnos")
    total = cursor.fetchone()[0]
    print(f"\n👥 Total de alumnos: {total}")
    
    # Por modalidad
    print("\n📋 Por Modalidad:")
    cursor.execute("""
        SELECT modalidad, COUNT(*) as total 
        FROM alumnos 
        GROUP BY modalidad 
        ORDER BY modalidad
    """)
    for modalidad, count in cursor.fetchall():
        print(f"  {modalidad:25} {count:5} alumnos")
    
    # Por grupo
    print("\n📋 Por Grupo:")
    cursor.execute("""
        SELECT grupo, COUNT(*) as total 
        FROM alumnos 
        GROUP BY grupo 
        ORDER BY grupo
    """)
    for grupo, count in cursor.fetchall():
        print(f"  Grupo {grupo}:                {count:5} alumnos")
    
    # Por horario
    print("\n⏰ Por Horario:")
    cursor.execute("""
        SELECT horario, COUNT(*) as total 
        FROM alumnos 
        GROUP BY horario 
        ORDER BY horario
    """)
    for horario, count in cursor.fetchall():
        print(f"  {horario:25} {count:5} alumnos")
    
    # Por carrera (top 10)
    print("\n🎓 Top 10 Carreras:")
    cursor.execute("""
        SELECT carrera, COUNT(*) as total 
        FROM alumnos 
        GROUP BY carrera 
        ORDER BY total DESC 
        LIMIT 10
    """)
    for carrera, count in cursor.fetchall():
        print(f"  {carrera:25} {count:5} alumnos")
    
    conn.close()

# ==========================================
# EJECUTAR
# ==========================================

if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("🎓 GENERADOR DE ALUMNOS - SISTEMA MUSUQ CLOUD")
    print("="*70)
    print("\nOpciones:")
    print("1. Generar nuevos alumnos")
    print("2. Ver estadísticas actuales")
    print("3. Salir")
    print()
    
    try:
        opcion = input("Selecciona una opción (1-3): ").strip()
        
        if opcion == "1":
            confirmacion = input(f"\n⚠️ Se generarán aproximadamente {len(MODALIDADES) * len(GRUPOS) * ALUMNOS_POR_GRUPO} alumnos. ¿Continuar? (s/n): ").strip().lower()
            if confirmacion == 's':
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
