"""
📊 GENERADOR DE ASISTENCIAS - Sistema Musuq Cloud
Genera registros de asistencia realistas de los últimos 2 meses
"""

import sqlite3
import random
from datetime import datetime, timedelta, time
import os

# ==========================================
# CONFIGURACIÓN
# ==========================================

# La función encontrar_base_datos está aquí para detectar automáticamente
def encontrar_base_datos():
    """Busca automáticamente el archivo .db en el proyecto"""
    nombres_posibles = ["musuq_dev.db", "musuq.db", "database.db"]
    directorio_actual = os.getcwd()
    
    for nombre in nombres_posibles:
        ruta = os.path.join(directorio_actual, nombre)
        if os.path.exists(ruta):
            try:
                conn = sqlite3.connect(ruta)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='asistencias'")
                if cursor.fetchone():
                    conn.close()
                    return ruta
                conn.close()
            except:
                pass
    
    # Buscar cualquier .db con tabla asistencias
    for archivo in os.listdir(directorio_actual):
        if archivo.endswith('.db'):
            ruta = os.path.join(directorio_actual, archivo)
            try:
                conn = sqlite3.connect(ruta)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='asistencias'")
                if cursor.fetchone():
                    conn.close()
                    return ruta
                conn.close()
            except:
                pass
    
    return None

DB_PATH = encontrar_base_datos()

# Configuración de generación
MESES_ATRAS = 2  # Generar asistencias de los últimos 2 meses
DIAS_LABORABLES = [0, 1, 2, 3, 4, 5]  # Lunes a Sábado (0=Lunes, 6=Domingo)

# ==========================================
# ESTADOS Y TURNOS
# ==========================================

ESTADOS = ["PUNTUAL", "TARDANZA", "INASISTENCIA"]

# Probabilidades de cada estado (más realista)
PROB_PUNTUAL = 0.70      # 70% puntuales
PROB_TARDANZA = 0.20     # 20% tardanzas
PROB_INASISTENCIA = 0.10 # 10% inasistencias

# Turnos
TURNOS = {
    "MAÑANA": "MAÑANA",
    "TARDE": "TARDE"
}

# Horarios de entrada por turno
HORARIOS_ENTRADA = {
    "MAÑANA": {
        "inicio": time(8, 0),    # 8:00 AM
        "limite": time(8, 15),   # Hasta 8:15 es puntual
        "tardanza_max": time(9, 0)  # Después de 8:15 es tardanza
    },
    "TARDE": {
        "inicio": time(14, 0),   # 2:00 PM
        "limite": time(14, 15),  # Hasta 14:15 es puntual
        "tardanza_max": time(15, 0)  # Después de 14:15 es tardanza
    }
}

# Observaciones por estado
OBSERVACIONES = {
    "PUNTUAL": [
        None,  # La mayoría no tiene observación
        None,
        None,
        "INGRESO PUNTUAL",
        "REGISTRO NORMAL"
    ],
    "TARDANZA": [
        "LLEGO TARDE",
        "TRAFICO",
        "PROBLEMAS DE TRANSPORTE",
        "JUSTIFICACION MEDICA",
        "TARDANZA MINIMA",
        "SE DISCULPO"
    ],
    "INASISTENCIA": [
        "NO SE PRESENTO",
        "SIN JUSTIFICACION",
        "ENFERMO",
        "TRAMITE PERSONAL",
        "FALTA INJUSTIFICADA"
    ]
}

# ==========================================
# FUNCIONES DE GENERACIÓN
# ==========================================

def generar_fechas_laborables(meses_atras=2):
    """Genera lista de fechas de los últimos N meses, excluyendo domingos"""
    fechas = []
    hoy = datetime.now().date()
    fecha_inicio = hoy - timedelta(days=30 * meses_atras)
    
    fecha_actual = fecha_inicio
    while fecha_actual <= hoy:
        # Excluir domingos (weekday() == 6)
        if fecha_actual.weekday() != 6:
            fechas.append(fecha_actual)
        fecha_actual += timedelta(days=1)
    
    return fechas

def generar_hora_entrada(turno, estado):
    """Genera una hora realista según el turno y estado"""
    horario = HORARIOS_ENTRADA[turno]
    
    if estado == "PUNTUAL":
        # Entre hora inicio y límite puntual
        inicio_min = horario["inicio"].hour * 60 + horario["inicio"].minute
        limite_min = horario["limite"].hour * 60 + horario["limite"].minute
        minutos = random.randint(inicio_min - 5, limite_min)  # Puede llegar 5 min antes
        
    elif estado == "TARDANZA":
        # Entre límite puntual y tardanza máxima
        limite_min = horario["limite"].hour * 60 + horario["limite"].minute
        tardanza_max_min = horario["tardanza_max"].hour * 60 + horario["tardanza_max"].minute
        minutos = random.randint(limite_min + 1, tardanza_max_min)
        
    else:  # INASISTENCIA
        return None  # No hay hora de entrada
    
    hora = minutos // 60
    minuto = minutos % 60
    segundo = random.randint(0, 59)
    
    return time(hora, minuto, segundo)

def generar_estado():
    """Genera un estado aleatorio con probabilidades realistas"""
    rand = random.random()
    
    if rand < PROB_PUNTUAL:
        return "PUNTUAL"
    elif rand < PROB_PUNTUAL + PROB_TARDANZA:
        return "TARDANZA"
    else:
        return "INASISTENCIA"

def generar_observacion(estado):
    """Genera una observación según el estado"""
    opciones = OBSERVACIONES[estado]
    return random.choice(opciones)

def alumno_debe_asistir(alumno_horario, turno, fecha):
    """Determina si un alumno debe asistir en un turno específico"""
    
    # DOBLE HORARIO: asiste en ambos turnos
    if alumno_horario == "DOBLE HORARIO":
        return True
    
    # MATUTINO: principalmente en MAÑANA
    if alumno_horario == "MATUTINO":
        if turno == "MAÑANA":
            return True
        else:
            # 5% de probabilidad de asistir en TARDE (horario incorrecto)
            return random.random() < 0.05
    
    # VESPERTINO: principalmente en TARDE
    if alumno_horario == "VESPERTINO":
        if turno == "TARDE":
            return True
        else:
            # 5% de probabilidad de asistir en MAÑANA (horario incorrecto)
            return random.random() < 0.05
    
    return False

# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================

def generar_asistencias():
    """Genera registros de asistencia para todos los alumnos"""
    
    if not DB_PATH:
        print("\n❌ ERROR: No se encontró la base de datos")
        print("Ejecuta primero: python diagnostico_completo.py")
        return
    
    print("="*80)
    print("📊 GENERADOR DE ASISTENCIAS - MUSUQ CLOUD")
    print("="*80)
    print(f"📁 Base de datos: {os.path.basename(DB_PATH)}")
    print(f"📍 Ruta: {DB_PATH}")
    
    # Conectar a BD
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print("✅ Conexión exitosa")
    except Exception as e:
        print(f"❌ Error al conectar: {e}")
        return
    
    # Obtener todos los alumnos con sus horarios
    print("\n📋 Cargando alumnos...")
    cursor.execute("""
        SELECT id, codigo_matricula, nombres, apell_paterno, horario 
        FROM alumnos 
        WHERE activo = 1
        ORDER BY id
    """)
    alumnos = cursor.fetchall()
    
    if not alumnos:
        print("❌ No hay alumnos en la base de datos")
        print("Ejecuta primero: python generar_alumnos.py")
        conn.close()
        return
    
    print(f"👥 Alumnos encontrados: {len(alumnos)}")
    
    # Generar fechas laborables
    print(f"\n📅 Generando fechas de los últimos {MESES_ATRAS} meses (sin domingos)...")
    fechas = generar_fechas_laborables(MESES_ATRAS)
    print(f"📊 Días laborables: {len(fechas)}")
    print(f"📆 Desde: {fechas[0]} hasta: {fechas[-1]}")
    
    # Confirmar generación
    total_estimado = len(alumnos) * len(fechas) * 1.5  # Promedio considerando turnos
    print(f"\n⚠️ Se generarán aproximadamente {int(total_estimado)} registros de asistencia")
    print(f"💾 Esto puede tomar 1-2 minutos...")
    
    confirmacion = input("\n¿Continuar? (s/n): ").strip().lower()
    if confirmacion != 's':
        print("❌ Operación cancelada")
        conn.close()
        return
    
    # Variables de conteo
    total_registros = 0
    contador_estados = {"PUNTUAL": 0, "TARDANZA": 0, "INASISTENCIA": 0}
    contador_turnos = {"MAÑANA": 0, "TARDE": 0}
    alertas_turno = 0
    
    # Usuario que registra (asumimos usuario admin con id=1)
    REGISTRADO_POR = 1
    
    print("\n" + "="*80)
    print("🔄 GENERANDO ASISTENCIAS...")
    print("="*80)
    
    # Procesar por lotes para mostrar progreso
    total_alumnos = len(alumnos)
    
    for idx, alumno in enumerate(alumnos, 1):
        alumno_id, codigo, nombres, apellido, horario = alumno
        
        # Mostrar progreso cada 10 alumnos
        if idx % 10 == 0 or idx == 1:
            print(f"📌 Procesando alumno {idx}/{total_alumnos}: {codigo} - {nombres} {apellido}")
        
        # Para cada fecha
        for fecha in fechas:
            
            # Determinar en qué turnos debe asistir este alumno
            for turno in ["MAÑANA", "TARDE"]:
                
                # ¿Debe asistir en este turno?
                if not alumno_debe_asistir(horario, turno, fecha):
                    continue
                
                # Generar estado (PUNTUAL, TARDANZA, INASISTENCIA)
                estado = generar_estado()
                
                # Generar hora según estado y turno
                hora = generar_hora_entrada(turno, estado)
                
                # Generar observación
                observacion = generar_observacion(estado)
                
                # Detectar alerta de turno (asiste en horario incorrecto)
                alerta = False
                if horario == "MATUTINO" and turno == "TARDE":
                    alerta = True
                    alertas_turno += 1
                elif horario == "VESPERTINO" and turno == "MAÑANA":
                    alerta = True
                    alertas_turno += 1
                
                # Insertar registro
                try:
                    cursor.execute("""
                        INSERT INTO asistencias (
                            alumno_id, registrado_por, fecha, hora, estado, 
                            turno, alerta_turno, observacion
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        alumno_id, REGISTRADO_POR, fecha, hora, estado,
                        turno, alerta, observacion
                    ))
                    
                    total_registros += 1
                    contador_estados[estado] += 1
                    contador_turnos[turno] += 1
                    
                except sqlite3.IntegrityError as e:
                    print(f"⚠️ Error al insertar: {e}")
        
        # Commit cada 10 alumnos para no perder progreso
        if idx % 10 == 0:
            conn.commit()
    
    # Commit final
    conn.commit()
    
    print("\n" + "="*80)
    print("✅ PROCESO COMPLETADO")
    print("="*80)
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"  Total registros generados: {total_registros}")
    print(f"\n📈 Por Estado:")
    for estado, count in contador_estados.items():
        porcentaje = (count / total_registros * 100) if total_registros > 0 else 0
        print(f"  {estado:15} {count:6} ({porcentaje:.1f}%)")
    
    print(f"\n⏰ Por Turno:")
    for turno, count in contador_turnos.items():
        porcentaje = (count / total_registros * 100) if total_registros > 0 else 0
        print(f"  {turno:15} {count:6} ({porcentaje:.1f}%)")
    
    print(f"\n⚠️ Alertas de turno (horario incorrecto): {alertas_turno}")
    
    # Verificar total en BD
    cursor.execute("SELECT COUNT(*) FROM asistencias")
    total_bd = cursor.fetchone()[0]
    print(f"\n💾 Total de asistencias en BD: {total_bd}")
    
    conn.close()
    print("\n✅ Base de datos cerrada correctamente")

def mostrar_estadisticas():
    """Muestra estadísticas de asistencias"""
    
    if not DB_PATH or not os.path.exists(DB_PATH):
        print("❌ No hay base de datos configurada")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("📊 ESTADÍSTICAS DE ASISTENCIAS")
    print("="*80)
    
    # Total
    cursor.execute("SELECT COUNT(*) FROM asistencias")
    total = cursor.fetchone()[0]
    print(f"\n📋 Total de registros: {total}")
    
    if total == 0:
        print("\n⚠️ No hay registros de asistencia")
        conn.close()
        return
    
    # Por estado
    print("\n📈 Por Estado:")
    cursor.execute("""
        SELECT estado, COUNT(*) as total 
        FROM asistencias 
        GROUP BY estado 
        ORDER BY total DESC
    """)
    for estado, count in cursor.fetchall():
        porcentaje = (count / total * 100)
        print(f"  {estado:20} {count:8} ({porcentaje:.1f}%)")
    
    # Por turno
    print("\n⏰ Por Turno:")
    cursor.execute("""
        SELECT turno, COUNT(*) as total 
        FROM asistencias 
        GROUP BY turno 
        ORDER BY turno
    """)
    for turno, count in cursor.fetchall():
        porcentaje = (count / total * 100)
        print(f"  {turno:20} {count:8} ({porcentaje:.1f}%)")
    
    # Alertas de turno
    cursor.execute("SELECT COUNT(*) FROM asistencias WHERE alerta_turno = 1")
    alertas = cursor.fetchone()[0]
    porcentaje_alertas = (alertas / total * 100)
    print(f"\n⚠️ Alertas de turno: {alertas} ({porcentaje_alertas:.1f}%)")
    
    # Rango de fechas
    cursor.execute("SELECT MIN(fecha), MAX(fecha) FROM asistencias")
    fecha_min, fecha_max = cursor.fetchone()
    print(f"\n📅 Rango de fechas:")
    print(f"  Desde: {fecha_min}")
    print(f"  Hasta: {fecha_max}")
    
    # Top 10 alumnos con más asistencias
    print(f"\n👥 Top 10 alumnos con más registros:")
    cursor.execute("""
        SELECT a.codigo_matricula, al.nombres, al.apell_paterno, COUNT(*) as total
        FROM asistencias a
        JOIN alumnos al ON a.alumno_id = al.id
        GROUP BY a.alumno_id
        ORDER BY total DESC
        LIMIT 10
    """)
    for codigo, nombre, apellido, count in cursor.fetchall():
        print(f"  {codigo:12} {nombre:15} {apellido:15} {count:4} registros")
    
    conn.close()

# ==========================================
# EJECUTAR
# ==========================================

if __name__ == "__main__":
    import sys
    
    if not DB_PATH:
        print("\n❌ No se puede ejecutar sin una base de datos")
        print("Coloca el archivo .db en el mismo directorio que este script")
        print("O ejecuta: python diagnostico_completo.py")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("📊 GENERADOR DE ASISTENCIAS - SISTEMA MUSUQ CLOUD")
    print("="*80)
    print("\nOpciones:")
    print("1. Generar registros de asistencia (2 meses)")
    print("2. Ver estadísticas actuales")
    print("3. Salir")
    print()
    
    try:
        opcion = input("Selecciona una opción (1-3): ").strip()
        
        if opcion == "1":
            generar_asistencias()
            # Mostrar estadísticas después de generar
            input("\nPresiona Enter para ver estadísticas...")
            mostrar_estadisticas()
        
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
