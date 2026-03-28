"""
Servicio de Aulas - gestión de aulas, grupos, cursos y horarios asociados.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.aula import Aula, AulaGrupo, AulaCurso
from app.models.curso import Curso
from app.models.docente import Docente
from app.models.horario import Horario
from app.schemas.aula import AulaCreate, AulaUpdate


class AulaService:
    """Servicio para operaciones de aulas."""

    def _normalizar_lista(self, valores: List[str]) -> List[str]:
        resultado: List[str] = []
        for valor in valores:
            valor_limpio = valor.strip().upper()
            if valor_limpio and valor_limpio not in resultado:
                resultado.append(valor_limpio)
        return resultado

    def _sin_conflicto_horario(
        self,
        db: Session,
        grupo: str,
        dia_semana: int,
        hora_inicio: str,
        hora_fin: str,
    ) -> bool:
        query = db.query(Horario).filter(
            Horario.grupo == grupo,
            Horario.dia_semana == dia_semana,
            Horario.activo == True,
        )
        for horario in query.all():
            if not (hora_fin <= horario.hora_inicio or hora_inicio >= horario.hora_fin):
                return False
        return True

    def _mapear_aula_response(self, aula: Aula) -> dict:
        return {
            "id": aula.id,
            "nombre": aula.nombre,
            "modalidad": aula.modalidad,
            "descripcion": aula.descripcion,
            "activo": aula.activo,
            "fecha_creacion": aula.fecha_creacion,
            "grupos": [g.grupo for g in aula.grupos_asignados],
            "cursos_ids": [c.curso_id for c in aula.cursos_asignados],
        }

    def listar(self, db: Session, modalidad: Optional[str] = None, activo: Optional[bool] = True) -> List[dict]:
        query = db.query(Aula)
        if modalidad:
            query = query.filter(Aula.modalidad == modalidad)
        if activo is not None:
            query = query.filter(Aula.activo == activo)

        aulas = query.order_by(Aula.nombre).all()
        return [self._mapear_aula_response(aula) for aula in aulas]

    def obtener_por_id(self, db: Session, aula_id: int) -> Optional[dict]:
        aula = db.query(Aula).filter(Aula.id == aula_id).first()
        if not aula:
            return None
        return self._mapear_aula_response(aula)

    def crear(self, db: Session, datos: AulaCreate) -> dict:
        existe = db.query(Aula).filter(Aula.nombre == datos.nombre).first()
        if existe:
            raise ValueError("Ya existe un aula con ese nombre")

        grupos = self._normalizar_lista(datos.grupos)
        cursos_ids = list(dict.fromkeys(datos.cursos_ids))

        for curso_id in cursos_ids:
            if not db.query(Curso).filter(Curso.id == curso_id).first():
                raise ValueError(f"Curso no encontrado: {curso_id}")

        aula = Aula(
            nombre=datos.nombre.strip(),
            modalidad=datos.modalidad.strip().upper(),
            descripcion=datos.descripcion,
        )
        db.add(aula)
        db.flush()

        for grupo in grupos:
            db.add(AulaGrupo(aula_id=aula.id, grupo=grupo))

        for curso_id in cursos_ids:
            db.add(AulaCurso(aula_id=aula.id, curso_id=curso_id))

        for bloque in datos.horarios:
            grupo_bloque = bloque.grupo.strip().upper()

            if grupos and grupo_bloque not in grupos:
                raise ValueError(f"El grupo {grupo_bloque} no está asignado al aula")

            if cursos_ids and bloque.curso_id not in cursos_ids:
                raise ValueError(f"El curso {bloque.curso_id} no está asignado al aula")

            if not db.query(Curso).filter(Curso.id == bloque.curso_id).first():
                raise ValueError(f"Curso no encontrado: {bloque.curso_id}")

            if bloque.docente_id and not db.query(Docente).filter(Docente.id == bloque.docente_id).first():
                raise ValueError(f"Docente no encontrado: {bloque.docente_id}")

            if not self._sin_conflicto_horario(
                db,
                grupo_bloque,
                bloque.dia_semana,
                bloque.hora_inicio,
                bloque.hora_fin,
            ):
                raise ValueError(
                    f"Conflicto horario para grupo {grupo_bloque} en día {bloque.dia_semana}"
                )

            db.add(
                Horario(
                    curso_id=bloque.curso_id,
                    docente_id=bloque.docente_id,
                    grupo=grupo_bloque,
                    periodo=bloque.periodo,
                    dia_semana=bloque.dia_semana,
                    hora_inicio=bloque.hora_inicio,
                    hora_fin=bloque.hora_fin,
                    aula_id=aula.id,
                    aula=aula.nombre,
                    turno=bloque.turno,
                )
            )

        db.commit()
        db.refresh(aula)
        return self._mapear_aula_response(aula)

    def obtener_horarios_aula(self, db: Session, aula_id: int, periodo: Optional[str] = None) -> List[dict]:
        aula = db.query(Aula).filter(Aula.id == aula_id).first()
        if not aula:
            raise ValueError("Aula no encontrada")

        # Buscar por aula_id (registros nuevos) O por nombre de aula (registros legacy sin FK)
        from sqlalchemy import or_
        query = db.query(Horario).filter(
            or_(
                Horario.aula_id == aula_id,
                (Horario.aula_id == None) & (Horario.aula == aula.nombre)
            ),
            Horario.activo == True,
        )

        if periodo:
            query = query.filter(Horario.periodo == periodo)

        horarios = query.order_by(Horario.dia_semana, Horario.hora_inicio).all()

        # Reparar silenciosamente los registros legacy asignándoles el aula_id correcto
        reparados = False
        for h in horarios:
            if h.aula_id is None:
                h.aula_id = aula_id
                reparados = True
        if reparados:
            db.commit()

        return [
            {
                "id": h.id,
                "aula": h.aula,
                "grupo": h.grupo,
                "periodo": h.periodo,
                "dia_semana": h.dia_semana,
                "dia_nombre": h.dia_nombre,
                "hora_inicio": h.hora_inicio,
                "hora_fin": h.hora_fin,
                "turno": h.turno,
                "curso_id": h.curso_id,
                "curso_nombre": h.curso.nombre if h.curso else None,
                "docente_id": h.docente_id,
                "docente_nombre": h.docente.nombre_completo if h.docente else None,
            }
            for h in horarios
        ]

    def actualizar(self, db: Session, aula_id: int, datos: AulaUpdate) -> dict:
        aula = db.query(Aula).filter(Aula.id == aula_id).first()
        if not aula:
            raise ValueError("Aula no encontrada")

        cambios = datos.model_dump(exclude_unset=True)

        if "nombre" in cambios:
            nuevo_nombre = cambios["nombre"].strip()
            existe = db.query(Aula).filter(Aula.nombre == nuevo_nombre, Aula.id != aula_id).first()
            if existe:
                raise ValueError("Ya existe un aula con ese nombre")

            if nuevo_nombre != aula.nombre:
                # Actualiza el campo display por FK (no por coincidencia de nombre)
                db.query(Horario).filter(Horario.aula_id == aula.id).update({"aula": nuevo_nombre})
                aula.nombre = nuevo_nombre

        if "modalidad" in cambios:
            aula.modalidad = cambios["modalidad"].strip().upper()
        if "descripcion" in cambios:
            aula.descripcion = cambios["descripcion"]
        if "activo" in cambios:
            aula.activo = cambios["activo"]

        if "grupos" in cambios:
            nuevos_grupos = self._normalizar_lista(cambios["grupos"])
            db.query(AulaGrupo).filter(AulaGrupo.aula_id == aula.id).delete()
            for grupo in nuevos_grupos:
                db.add(AulaGrupo(aula_id=aula.id, grupo=grupo))

        if "cursos_ids" in cambios:
            nuevos_cursos = list(dict.fromkeys(cambios["cursos_ids"]))
            for curso_id in nuevos_cursos:
                if not db.query(Curso).filter(Curso.id == curso_id).first():
                    raise ValueError(f"Curso no encontrado: {curso_id}")

            db.query(AulaCurso).filter(AulaCurso.aula_id == aula.id).delete()
            for curso_id in nuevos_cursos:
                db.add(AulaCurso(aula_id=aula.id, curso_id=curso_id))

        db.commit()
        db.refresh(aula)
        return self._mapear_aula_response(aula)

    def eliminar(self, db: Session, aula_id: int) -> bool:
        aula = db.query(Aula).filter(Aula.id == aula_id).first()
        if not aula:
            raise ValueError("Aula no encontrada")

        # Desvincula los horarios antes de borrar (limpia FK y campo display)
        db.query(Horario).filter(Horario.aula_id == aula.id).update({"aula_id": None, "aula": None})
        db.delete(aula)
        db.commit()
        return True


aula_service = AulaService()
