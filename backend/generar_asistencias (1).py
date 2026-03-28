"""
📊 GENERADOR DE ASISTENCIAS - Sistema Musuq Cloud
Genera registros de asistencia realistas de los últimos 2 meses.

Usa SQLAlchemy ORM (SessionLocal + modelos oficiales) para garantizar
integridad referencial y consistencia con el resto de la aplicación.
"""

import sys
import os
import random
from datetime import datetime, timedelta
from datetime import time as dtime

# ─── Agregar el directorio /backend al path para importar los módulos de la app ──
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# ⚠️ Cambiar el CWD al directorio backend ANTES de importar la app.
# Esto garantiza que la ruta relativa "sqlite:///./musuq_dev.db" en config.py
# siempre apunte a backend/musuq_dev.db, sin importar desde dónde se ejecute el script.
os.chdir(BACKEND_DIR)

from app.db.database import SessionLocal, init_db
from app.models.alumno import Alumno
from app.models.matricula import Matricula
from app.models.asistencia import Asistencia
from app.models.periodo import PeriodoAcademico
from app.models.usuario import Usuario

# ==========================================
# CONFIGURACIÓN
# ==========================================

MESES_ATRAS = 5  # Generar asistencias de los últimos N meses

# ==========================================
# ESTADOS Y TURNOS
# Los valores deben coincidir con los usados en los servicios de la app
# ==========================================

# Estado   → valor exacto en BD
ESTADO_PUNTUAL      = "PUNTUAL"
ESTADO_TARDANZA     = "TARDANZA"
ESTADO_INASISTENCIA = "INASISTENCIA"

ESTADOS = [ESTADO_PUNTUAL, ESTADO_TARDANZA, ESTADO_INASISTENCIA]

# Probabilidades
PROB_PUNTUAL  = 0.70
PROB_TARDANZA = 0.20
# PROB_FALTA = 0.10  (el resto)

# Turnos
TURNO_MANANA = "MAÑANA"
TURNO_TARDE  = "TARDE"

# Horarios de entrada por turno
HORARIOS_ENTRADA = {
    TURNO_MANANA: {
        "inicio":       dtime(8, 0),
        "limite":       dtime(8, 15),   # hasta aquí es Puntual
        "tardanza_max": dtime(9, 0),
    },
    TURNO_TARDE: {
        "inicio":       dtime(14, 0),
        "limite":       dtime(14, 15),  # hasta aquí es Puntual
        "tardanza_max": dtime(15, 0),
    },
}

# Observaciones por estado
OBSERVACIONES = {
    ESTADO_PUNTUAL: [
        None, None, None,          # la mayoría sin observación
        "Ingreso puntual",
        "Registro normal",
    ],
    ESTADO_TARDANZA: [
        "Llegó tarde",
        "Tráfico",
        "Problemas de transporte",
        "Justificación médica",
        "Tardanza mínima",
        "Se disculpó",
    ],
    ESTADO_INASISTENCIA: [
        "No se presentó",
        "Sin justificación",
        "Enfermo",
        "Trámite personal",
        "Falta injustificada",
    ],
}

# ==========================================
# FUNCIONES AUXILIARES
# ==========================================

def generar_fechas_laborables(meses_atras: int = 2) -> list:
    """Devuelve lista de fechas laborables (lunes-sábado) de los últimos N meses."""
    fechas = []
    hoy = datetime.now().date()
    fecha_inicio = hoy - timedelta(days=30 * meses_atras)
    fecha_actual = fecha_inicio
    while fecha_actual <= hoy:
        if fecha_actual.weekday() != 6:   # excluir domingos
            fechas.append(fecha_actual)
        fecha_actual += timedelta(days=1)
    return fechas


def generar_hora_entrada(turno: str, estado: str):
    """Genera una hora de entrada realista según turno y estado."""
    if estado == ESTADO_INASISTENCIA:
        return None      # sin asistencia, no hay hora

    horario = HORARIOS_ENTRADA[turno]
    inicio_min      = horario["inicio"].hour * 60      + horario["inicio"].minute
    limite_min      = horario["limite"].hour * 60      + horario["limite"].minute
    tardanza_max_min = horario["tardanza_max"].hour * 60 + horario["tardanza_max"].minute

    if estado == ESTADO_PUNTUAL:
        minutos = random.randint(inicio_min - 5, limite_min)
    else:  # TARDANZA
        minutos = random.randint(limite_min + 1, tardanza_max_min)

    hora   = minutos // 60
    minuto = minutos % 60
    seg    = random.randint(0, 59)
    return dtime(hora, minuto, seg)


def generar_estado() -> str:
    """Elige un estado según probabilidades configuradas."""
    rand = random.random()
    if rand < PROB_PUNTUAL:
        return ESTADO_PUNTUAL
    elif rand < PROB_PUNTUAL + PROB_TARDANZA:
        return ESTADO_TARDANZA
    else:
        return ESTADO_INASISTENCIA


def generar_observacion(estado: str):
    return random.choice(OBSERVACIONES[estado])


def alumno_debe_asistir(horario_matricula: str, turno: str) -> bool:
    """
    Decide si el alumno asiste en el turno dado según su horario de matrícula.
    - DOBLE HORARIO : asiste en ambos turnos (100 %)
    - MATUTINO      : asiste en MAÑANA (100 %) y excepcionalmente en TARDE (5 %)
    - VESPERTINO    : asiste en TARDE  (100 %) y excepcionalmente en MAÑANA (5 %)
    - None/otro     : solo MAÑANA por defecto
    """
    if not horario_matricula:
        return turno == TURNO_MANANA

    h = horario_matricula.upper()

    if "DOBLE" in h:
        return True
    if "MATUTINO" in h or "MAÑANA" in h:
        return turno == TURNO_MANANA or random.random() < 0.05
    if "VESPERTINO" in h or "TARDE" in h:
        return turno == TURNO_TARDE or random.random() < 0.05

    # Horario desconocido → solo mañana
    return turno == TURNO_MANANA


def es_turno_incorrecto(horario_matricula: str, turno: str) -> bool:
    """True si el alumno está asistiendo en un turno que no le corresponde."""
    if not horario_matricula:
        return False
    h = horario_matricula.upper()
    if "DOBLE" in h:
        return False
    if ("MATUTINO" in h or "MAÑANA" in h) and turno == TURNO_TARDE:
        return True
    if ("VESPERTINO" in h or "TARDE" in h) and turno == TURNO_MANANA:
        return True
    return False


# ==========================================
# FUNCIÓN PRINCIPAL
# ==========================================

def generar_asistencias():
    """
    Genera registros de asistencia para todas las matrículas activas del
    periodo académico activo, usando el ORM de SQLAlchemy.
    """
    print("=" * 80)
    print("📊 GENERADOR DE ASISTENCIAS - MUSUQ CLOUD")
    print("=" * 80)

    db = SessionLocal()
    try:
        # ── 1. Verificar que la BD tiene las tablas necesarias ───────────────
        init_db()

        # ── 2. Obtener usuario admin (registrado_por) ─────────────────────────
        admin = db.query(Usuario).filter(
            Usuario.activo == True
        ).order_by(Usuario.id).first()

        if not admin:
            print("❌ No hay usuarios en la base de datos. Crea primero un usuario admin.")
            return
        print(f"👤 Registrado por: {admin.username} (id={admin.id})")

        # ── 3. Obtener periodo académico activo ───────────────────────────────
        periodo = db.query(PeriodoAcademico).filter(
            PeriodoAcademico.estado == "activo"
        ).order_by(PeriodoAcademico.id.desc()).first()

        if not periodo:
            print("❌ No hay periodos académicos activos.")
            print("   Crea uno desde la interfaz o con init_database.py")
            return
        print(f"📅 Periodo académico: {periodo.nombre} (id={periodo.id})")

        # ── 4. Obtener matrículas activas del periodo ─────────────────────────
        matriculas = (
            db.query(Matricula)
            .filter(
                Matricula.periodo_id == periodo.id,
                Matricula.estado == "activo",
            )
            .all()
        )

        if not matriculas:
            print("❌ No hay matrículas activas en este periodo.")
            print("   Ejecuta primero: python generar_datos_prueba.py")
            return
        print(f"👥 Matrículas activas: {len(matriculas)}")

        # ── 5. Generar fechas laborables ──────────────────────────────────────
        fechas = generar_fechas_laborables(MESES_ATRAS)
        print(f"\n📊 Días laborables a generar: {len(fechas)}")
        print(f"📆 Desde: {fechas[0]}  →  Hasta: {fechas[-1]}")

        # Estimación
        total_estimado = len(matriculas) * len(fechas) * 1.5
        print(f"\n⚠️  Se generarán ~{int(total_estimado)} registros de asistencia")
        print("💾 Esto puede tardar 1-2 minutos…")

        confirmacion = input("\n¿Continuar? (s/n): ").strip().lower()
        if confirmacion != "s":
            print("❌ Operación cancelada.")
            return

        # ── 6. Obtener registros existentes para evitar duplicados ─────────────
        print("\n🔍 Cargando registros existentes (deduplicación)…")
        existentes: set[tuple] = set(
            db.query(Asistencia.alumno_id, Asistencia.fecha, Asistencia.turno)
            .filter(Asistencia.periodo_id == periodo.id)
            .all()
        )
        print(f"   Registros ya existentes: {len(existentes)}")

        # ── 7. Generar e insertar ─────────────────────────────────────────────
        print("\n" + "=" * 80)
        print("🔄 GENERANDO ASISTENCIAS…")
        print("=" * 80)

        total_registros = 0
        omitidos        = 0
        contador_estados = {ESTADO_PUNTUAL: 0, ESTADO_TARDANZA: 0, ESTADO_INASISTENCIA: 0}
        contador_turnos  = {TURNO_MANANA: 0, TURNO_TARDE: 0}
        alertas_turno    = 0

        lote: list[Asistencia] = []
        TAMANIO_LOTE = 500   # flush cada N objetos para controlar memoria

        total_matriculas = len(matriculas)

        for idx, matricula in enumerate(matriculas, 1):
            alumno_id    = matricula.alumno_id
            horario_mat  = matricula.horario or "MATUTINO"

            if idx % 20 == 0 or idx == 1:
                print(
                    f"📌 Procesando matrícula {idx}/{total_matriculas}: "
                    f"{matricula.codigo_matricula}  horario={horario_mat}"
                )

            for fecha in fechas:
                for turno in [TURNO_MANANA, TURNO_TARDE]:

                    # ¿Debe asistir?
                    if not alumno_debe_asistir(horario_mat, turno):
                        continue

                    # ¿Ya existe el registro?
                    if (alumno_id, fecha, turno) in existentes:
                        omitidos += 1
                        continue

                    # Generar datos
                    estado      = generar_estado()
                    hora        = generar_hora_entrada(turno, estado)
                    observacion = generar_observacion(estado)
                    alerta      = es_turno_incorrecto(horario_mat, turno)

                    asistencia = Asistencia(
                        alumno_id      = alumno_id,
                        periodo_id     = periodo.id,
                        registrado_por = admin.id,
                        fecha          = fecha,
                        hora           = hora,
                        estado         = estado,
                        turno          = turno,
                        alerta_turno   = alerta,
                        observacion    = observacion,
                    )
                    lote.append(asistencia)

                    # Registrar para deduplicación en memoria
                    existentes.add((alumno_id, fecha, turno))

                    total_registros          += 1
                    contador_estados[estado] += 1
                    contador_turnos[turno]   += 1
                    if alerta:
                        alertas_turno += 1

                    # Flush por lotes para no acumular demasiados objetos en RAM
                    if len(lote) >= TAMANIO_LOTE:
                        db.bulk_save_objects(lote)
                        db.commit()
                        lote.clear()

        # Insertar el último lote parcial
        if lote:
            db.bulk_save_objects(lote)
            db.commit()
            lote.clear()

        # ── 8. Resumen ────────────────────────────────────────────────────────
        print("\n" + "=" * 80)
        print("✅ PROCESO COMPLETADO")
        print("=" * 80)
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"  Nuevos registros generados : {total_registros}")
        print(f"  Registros omitidos (ya existían): {omitidos}")

        print(f"\n📈 Por Estado:")
        for estado, count in contador_estados.items():
            pct = (count / total_registros * 100) if total_registros else 0
            print(f"  {estado:12} {count:7}  ({pct:.1f}%)")

        print(f"\n⏰ Por Turno:")
        for turno, count in contador_turnos.items():
            pct = (count / total_registros * 100) if total_registros else 0
            print(f"  {turno:10} {count:7}  ({pct:.1f}%)")

        print(f"\n⚠️  Alertas de turno cruzado : {alertas_turno}")

        total_bd = db.query(Asistencia).count()
        print(f"\n💾 Total de asistencias en BD: {total_bd}")

    except Exception as exc:
        db.rollback()
        print(f"\n❌ Error durante la generación: {exc}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("\n✅ Sesión de BD cerrada correctamente.")


def mostrar_estadisticas():
    """Muestra estadísticas de asistencias usando ORM."""
    db = SessionLocal()
    try:
        print("\n" + "=" * 80)
        print("📊 ESTADÍSTICAS DE ASISTENCIAS")
        print("=" * 80)

        total = db.query(Asistencia).count()
        print(f"\n📋 Total de registros: {total}")

        if total == 0:
            print("\n⚠️  No hay registros de asistencia.")
            return

        from sqlalchemy import func

        # Por estado
        print("\n📈 Por Estado:")
        filas = (
            db.query(Asistencia.estado, func.count(Asistencia.id))
            .group_by(Asistencia.estado)
            .order_by(func.count(Asistencia.id).desc())
            .all()
        )
        for estado, count in filas:
            pct = count / total * 100
            print(f"  {estado:20} {count:8}  ({pct:.1f}%)")

        # Por turno
        print("\n⏰ Por Turno:")
        filas = (
            db.query(Asistencia.turno, func.count(Asistencia.id))
            .group_by(Asistencia.turno)
            .order_by(Asistencia.turno)
            .all()
        )
        for turno, count in filas:
            pct = count / total * 100
            print(f"  {turno:20} {count:8}  ({pct:.1f}%)")

        # Alertas
        alertas = db.query(Asistencia).filter(Asistencia.alerta_turno == True).count()
        print(f"\n⚠️  Alertas de turno: {alertas} ({alertas / total * 100:.1f}%)")

        # Rango de fechas
        fecha_min = db.query(func.min(Asistencia.fecha)).scalar()
        fecha_max = db.query(func.max(Asistencia.fecha)).scalar()
        print(f"\n📅 Rango de fechas:")
        print(f"  Desde: {fecha_min}")
        print(f"  Hasta: {fecha_max}")

        # Top 10 alumnos
        print(f"\n👥 Top 10 alumnos con más registros:")
        filas = (
            db.query(
                Alumno.nombres,
                Alumno.apell_paterno,
                func.count(Asistencia.id).label("total"),
            )
            .join(Asistencia, Asistencia.alumno_id == Alumno.id)
            .group_by(Alumno.id)
            .order_by(func.count(Asistencia.id).desc())
            .limit(10)
            .all()
        )
        for nombres, apellido, count in filas:
            print(f"  {nombres:20} {apellido:20} {count:4} registros")

    finally:
        db.close()


# ==========================================
# EJECUTAR
# ==========================================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("📊 GENERADOR DE ASISTENCIAS - SISTEMA MUSUQ CLOUD")
    print("=" * 80)
    print("\nOpciones:")
    print("  1. Generar registros de asistencia (últimos 2 meses)")
    print("  2. Ver estadísticas actuales")
    print("  3. Salir")
    print()

    try:
        opcion = input("Selecciona una opción (1-3): ").strip()

        if opcion == "1":
            generar_asistencias()
            input("\nPresiona Enter para ver estadísticas…")
            mostrar_estadisticas()
        elif opcion == "2":
            mostrar_estadisticas()
        elif opcion == "3":
            print("👋 Hasta luego!")
        else:
            print("❌ Opción inválida.")

    except KeyboardInterrupt:
        print("\n\n❌ Proceso interrumpido por el usuario.")
    except Exception as exc:
        print(f"\n❌ Error: {exc}")
        import traceback
        traceback.print_exc()
