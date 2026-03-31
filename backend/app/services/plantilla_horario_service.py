"""
Servicio de plantillas de horario (fase 2).
"""
from collections import defaultdict
import logging
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from app.models.aula import Aula
from app.core.logging_config import logger
from app.models.horario import Horario
from app.models.plantilla_horario import PlantillaBloque, PlantillaHorario
from app.schemas.plantilla_horario import (
    PlantillaBloqueBatchItem,
    PlantillaBloqueBatchUpsertResponse,
    PlantillaBloqueCreate,
    PlantillaBloqueUpdate,
    PlantillaGrillaFinalResponse,
    PlantillaHorarioCreate,
    PlantillaHorarioUpdate,
)


class PlantillaHorarioService:
    """Lógica de negocio para CRUD de plantillas y bloques."""

    def _log_event(self, level: int, operation: str, **context) -> None:
        logger.log(level, f"plantilla_horario.{operation}", extra={"operation": operation, **context})

    # -------------------- Validaciones --------------------
    def validar_horas(self, hora_inicio: str, hora_fin: str) -> bool:
        return bool(hora_inicio and hora_fin and hora_inicio < hora_fin)

    def validar_no_solape(
        self,
        db: Session,
        plantilla_id: int,
        dia_semana: int,
        hora_inicio: str,
        hora_fin: str,
        bloque_id_excluir: Optional[int] = None,
    ) -> bool:
        query = db.query(PlantillaBloque).filter(
            PlantillaBloque.plantilla_id == plantilla_id,
            PlantillaBloque.dia_semana == dia_semana,
            PlantillaBloque.activo == True,
        )
        if bloque_id_excluir:
            query = query.filter(PlantillaBloque.id != bloque_id_excluir)

        for bloque in query.all():
            if not (hora_fin <= bloque.hora_inicio or hora_inicio >= bloque.hora_fin):
                return False
        return True

    def _obtener_plantilla(self, db: Session, plantilla_id: int) -> PlantillaHorario:
        plantilla = db.query(PlantillaHorario).filter(PlantillaHorario.id == plantilla_id).first()
        if not plantilla:
            self._log_event(logging.WARNING, "plantilla_no_encontrada", plantilla_id=plantilla_id)
            raise ValueError("Plantilla no encontrada")
        return plantilla

    def _obtener_bloque(self, db: Session, bloque_id: int) -> PlantillaBloque:
        bloque = db.query(PlantillaBloque).filter(PlantillaBloque.id == bloque_id).first()
        if not bloque:
            self._log_event(logging.WARNING, "bloque_no_encontrado", bloque_id=bloque_id)
            raise ValueError("Bloque no encontrado")
        return bloque

    def _validar_aula_existe(self, db: Session, aula_id: int) -> None:
        if not db.query(Aula).filter(Aula.id == aula_id).first():
            self._log_event(logging.WARNING, "aula_no_encontrada", aula_id=aula_id)
            raise ValueError("Aula no encontrada")

    # -------------------- CRUD Plantillas --------------------
    def listar_plantillas(
        self,
        db: Session,
        aula_id: Optional[int] = None,
        grupo: Optional[str] = None,
        periodo: Optional[str] = None,
        turno: Optional[str] = None,
        activo: Optional[bool] = True,
    ) -> List[PlantillaHorario]:
        query = db.query(PlantillaHorario)
        if aula_id is not None:
            query = query.filter(PlantillaHorario.aula_id == aula_id)
        if grupo:
            query = query.filter(PlantillaHorario.grupo == grupo)
        if periodo:
            query = query.filter(PlantillaHorario.periodo == periodo)
        if turno:
            query = query.filter(PlantillaHorario.turno == turno)
        if activo is not None:
            query = query.filter(PlantillaHorario.activo == activo)
        items = query.order_by(PlantillaHorario.id.desc()).all()
        self._log_event(
            logging.INFO,
            "listar_plantillas",
            aula_id=aula_id,
            grupo=grupo,
            periodo=periodo,
            turno=turno,
            activo=activo,
            total=len(items),
        )
        return items

    def crear_plantilla_legacy(
        self,
        db: Session,
        aula_id: int,
        grupo: str,
        periodo: str,
        turno: str,
        version: int = 1,
        activo: bool = True,
    ) -> PlantillaHorario:
        datos = PlantillaHorarioCreate(
            aula_id=aula_id,
            grupo=grupo,
            periodo=periodo,
            turno=turno,
            version=version,
            activo=activo,
        )
        return self.crear_plantilla(db, datos)

    def crear_plantilla(
        self,
        db: Session,
        datos: Optional[PlantillaHorarioCreate] = None,
        *,
        aula_id: Optional[int] = None,
        grupo: Optional[str] = None,
        periodo: Optional[str] = None,
        turno: Optional[str] = None,
        version: int = 1,
        activo: bool = True,
    ) -> PlantillaHorario:
        # Compatibilidad: acepta schema nuevo o parámetros legacy.
        if datos is None:
            if aula_id is None or grupo is None or periodo is None or turno is None:
                raise ValueError("Datos de plantilla incompletos")
            return self.crear_plantilla_legacy(
                db,
                aula_id=aula_id,
                grupo=grupo,
                periodo=periodo,
                turno=turno,
                version=version,
                activo=activo,
            )

        self._validar_aula_existe(db, datos.aula_id)

        repetida = db.query(PlantillaHorario).filter(
            PlantillaHorario.aula_id == datos.aula_id,
            PlantillaHorario.grupo == datos.grupo,
            PlantillaHorario.periodo == datos.periodo,
            PlantillaHorario.turno == datos.turno,
            PlantillaHorario.version == datos.version,
            PlantillaHorario.activo == True,
        ).first()
        if repetida:
            self._log_event(
                logging.WARNING,
                "crear_plantilla_conflicto_version",
                aula_id=datos.aula_id,
                grupo=datos.grupo,
                periodo=datos.periodo,
                turno=datos.turno,
                version=datos.version,
            )
            raise ValueError("Ya existe una plantilla activa con la misma version para ese alcance")

        plantilla = PlantillaHorario(**datos.model_dump())
        db.add(plantilla)
        db.commit()
        db.refresh(plantilla)
        self._log_event(
            logging.INFO,
            "crear_plantilla_ok",
            plantilla_id=plantilla.id,
            aula_id=plantilla.aula_id,
            grupo=plantilla.grupo,
            periodo=plantilla.periodo,
            turno=plantilla.turno,
            version=plantilla.version,
        )
        return plantilla

    def actualizar_plantilla(
        self, db: Session, plantilla_id: int, datos: PlantillaHorarioUpdate
    ) -> PlantillaHorario:
        plantilla = self._obtener_plantilla(db, plantilla_id)
        update_data = datos.model_dump(exclude_unset=True)

        if "aula_id" in update_data and update_data["aula_id"] is not None:
            self._validar_aula_existe(db, update_data["aula_id"])

        for field, value in update_data.items():
            setattr(plantilla, field, value)

        db.commit()
        db.refresh(plantilla)
        self._log_event(
            logging.INFO,
            "actualizar_plantilla_ok",
            plantilla_id=plantilla.id,
            campos=list(update_data.keys()),
        )
        return plantilla

    def eliminar_plantilla(self, db: Session, plantilla_id: int) -> None:
        plantilla = self._obtener_plantilla(db, plantilla_id)
        db.delete(plantilla)
        db.commit()
        self._log_event(logging.INFO, "eliminar_plantilla_ok", plantilla_id=plantilla_id)

    # -------------------- CRUD Bloques --------------------
    def listar_bloques(
        self, db: Session, plantilla_id: int, activo: Optional[bool] = True
    ) -> List[PlantillaBloque]:
        self._obtener_plantilla(db, plantilla_id)
        query = db.query(PlantillaBloque).filter(PlantillaBloque.plantilla_id == plantilla_id)
        if activo is not None:
            query = query.filter(PlantillaBloque.activo == activo)
        items = query.order_by(
            PlantillaBloque.dia_semana,
            PlantillaBloque.hora_inicio,
            PlantillaBloque.orden_visual,
        ).all()
        self._log_event(
            logging.INFO,
            "listar_bloques",
            plantilla_id=plantilla_id,
            activo=activo,
            total=len(items),
        )
        return items

    def _crear_bloque_desde_schema(
        self,
        db: Session,
        plantilla_id: int,
        datos: PlantillaBloqueCreate,
    ) -> PlantillaBloque:
        self._obtener_plantilla(db, plantilla_id)
        if not self.validar_horas(datos.hora_inicio, datos.hora_fin):
            raise ValueError("Rango horario invalido")

        if not self.validar_no_solape(
            db,
            plantilla_id=plantilla_id,
            dia_semana=datos.dia_semana,
            hora_inicio=datos.hora_inicio,
            hora_fin=datos.hora_fin,
        ):
            self._log_event(
                logging.WARNING,
                "crear_bloque_solape",
                plantilla_id=plantilla_id,
                dia_semana=datos.dia_semana,
                hora_inicio=datos.hora_inicio,
                hora_fin=datos.hora_fin,
            )
            raise ValueError("Bloque superpuesto en el mismo dia")

        bloque = PlantillaBloque(plantilla_id=plantilla_id, **datos.model_dump())
        db.add(bloque)
        db.commit()
        db.refresh(bloque)
        self._log_event(
            logging.INFO,
            "crear_bloque_ok",
            plantilla_id=plantilla_id,
            bloque_id=bloque.id,
            dia_semana=bloque.dia_semana,
            hora_inicio=bloque.hora_inicio,
            hora_fin=bloque.hora_fin,
            tipo_bloque=bloque.tipo_bloque,
        )
        return bloque

    def crear_bloque(
        self,
        db: Session,
        plantilla_id: int,
        datos: Optional[PlantillaBloqueCreate] = None,
        *,
        dia_semana: Optional[int] = None,
        hora_inicio: Optional[str] = None,
        hora_fin: Optional[str] = None,
        tipo_bloque: str = "CLASE",
        etiqueta: Optional[str] = None,
        orden_visual: Optional[int] = None,
        activo: bool = True,
    ) -> PlantillaBloque:
        # Compatibilidad: acepta schema nuevo o parámetros legacy.
        if datos is None:
            if dia_semana is None or hora_inicio is None or hora_fin is None:
                raise ValueError("Datos de bloque incompletos")
            datos = PlantillaBloqueCreate(
                dia_semana=dia_semana,
                hora_inicio=hora_inicio,
                hora_fin=hora_fin,
                tipo_bloque=tipo_bloque,
                etiqueta=etiqueta,
                orden_visual=orden_visual,
                activo=activo,
            )
        return self._crear_bloque_desde_schema(db, plantilla_id, datos)

    def actualizar_bloque(
        self,
        db: Session,
        bloque_id: int,
        datos: PlantillaBloqueUpdate,
    ) -> PlantillaBloque:
        bloque = self._obtener_bloque(db, bloque_id)
        update_data = datos.model_dump(exclude_unset=True)

        dia_semana = update_data.get("dia_semana", bloque.dia_semana)
        hora_inicio = update_data.get("hora_inicio", bloque.hora_inicio)
        hora_fin = update_data.get("hora_fin", bloque.hora_fin)

        if not self.validar_horas(hora_inicio, hora_fin):
            raise ValueError("Rango horario invalido")

        if not self.validar_no_solape(
            db,
            plantilla_id=bloque.plantilla_id,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            bloque_id_excluir=bloque.id,
        ):
            raise ValueError("Bloque superpuesto en el mismo dia")

        for field, value in update_data.items():
            setattr(bloque, field, value)

        db.commit()
        db.refresh(bloque)
        self._log_event(
            logging.INFO,
            "actualizar_bloque_ok",
            bloque_id=bloque.id,
            plantilla_id=bloque.plantilla_id,
            campos=list(update_data.keys()),
        )
        return bloque

    def eliminar_bloque(self, db: Session, bloque_id: int) -> None:
        bloque = self._obtener_bloque(db, bloque_id)
        plantilla_id = bloque.plantilla_id
        db.delete(bloque)
        db.commit()
        self._log_event(
            logging.INFO,
            "eliminar_bloque_ok",
            bloque_id=bloque_id,
            plantilla_id=plantilla_id,
        )

    def batch_upsert_bloques(
        self,
        db: Session,
        plantilla_id: int,
        bloques: List[PlantillaBloqueBatchItem],
        eliminar_no_incluidos: bool = False,
    ) -> PlantillaBloqueBatchUpsertResponse:
        self._obtener_plantilla(db, plantilla_id)

        creados = 0
        actualizados = 0
        eliminados = 0
        ids_recibidos: List[int] = []

        for item in bloques:
            if item.id:
                bloque = self._obtener_bloque(db, item.id)
                if bloque.plantilla_id != plantilla_id:
                    raise ValueError("El bloque no pertenece a la plantilla indicada")

                if not self.validar_horas(item.hora_inicio, item.hora_fin):
                    raise ValueError("Rango horario invalido")

                if not self.validar_no_solape(
                    db,
                    plantilla_id=plantilla_id,
                    dia_semana=item.dia_semana,
                    hora_inicio=item.hora_inicio,
                    hora_fin=item.hora_fin,
                    bloque_id_excluir=bloque.id,
                ):
                    raise ValueError("Bloque superpuesto en el mismo dia")

                bloque.dia_semana = item.dia_semana
                bloque.hora_inicio = item.hora_inicio
                bloque.hora_fin = item.hora_fin
                bloque.tipo_bloque = item.tipo_bloque
                bloque.etiqueta = item.etiqueta
                bloque.orden_visual = item.orden_visual
                bloque.activo = item.activo
                db.flush()
                ids_recibidos.append(bloque.id)
                actualizados += 1
            else:
                if not self.validar_horas(item.hora_inicio, item.hora_fin):
                    raise ValueError("Rango horario invalido")

                if not self.validar_no_solape(
                    db,
                    plantilla_id=plantilla_id,
                    dia_semana=item.dia_semana,
                    hora_inicio=item.hora_inicio,
                    hora_fin=item.hora_fin,
                ):
                    raise ValueError("Bloque superpuesto en el mismo dia")

                nuevo = PlantillaBloque(
                    plantilla_id=plantilla_id,
                    dia_semana=item.dia_semana,
                    hora_inicio=item.hora_inicio,
                    hora_fin=item.hora_fin,
                    tipo_bloque=item.tipo_bloque,
                    etiqueta=item.etiqueta,
                    orden_visual=item.orden_visual,
                    activo=item.activo,
                )
                db.add(nuevo)
                db.flush()
                ids_recibidos.append(nuevo.id)
                creados += 1

        if eliminar_no_incluidos:
            query = db.query(PlantillaBloque).filter(PlantillaBloque.plantilla_id == plantilla_id)
            if ids_recibidos:
                query = query.filter(~PlantillaBloque.id.in_(ids_recibidos))
            for bloque in query.all():
                db.delete(bloque)
                eliminados += 1

        db.commit()
        bloques_resultado = self.listar_bloques(db, plantilla_id=plantilla_id, activo=None)
        self._log_event(
            logging.INFO,
            "batch_upsert_bloques_ok",
            plantilla_id=plantilla_id,
            creados=creados,
            actualizados=actualizados,
            eliminados=eliminados,
            total_resultante=len(bloques_resultado),
            eliminar_no_incluidos=eliminar_no_incluidos,
        )

        return PlantillaBloqueBatchUpsertResponse(
            plantilla_id=plantilla_id,
            creados=creados,
            actualizados=actualizados,
            eliminados=eliminados,
            bloques=bloques_resultado,
        )

    # -------------------- Grilla Final --------------------
    def obtener_grilla_final(
        self,
        db: Session,
        aula_id: int,
        grupo: str,
        periodo: str,
        turno: str,
    ) -> PlantillaGrillaFinalResponse:
        plantilla = db.query(PlantillaHorario).filter(
            PlantillaHorario.aula_id == aula_id,
            PlantillaHorario.grupo == grupo,
            PlantillaHorario.periodo == periodo,
            PlantillaHorario.turno == turno,
            PlantillaHorario.activo == True,
        ).order_by(PlantillaHorario.version.desc(), PlantillaHorario.id.desc()).first()

        if not plantilla:
            self._log_event(
                logging.INFO,
                "grilla_final_sin_plantilla",
                aula_id=aula_id,
                grupo=grupo,
                periodo=periodo,
                turno=turno,
            )
            return PlantillaGrillaFinalResponse(
                plantilla_id=None,
                aula_id=aula_id,
                grupo=grupo,
                periodo=periodo,
                turno=turno,
                bloques_por_dia={},
            )

        bloques = self.listar_bloques(db, plantilla.id, activo=True)
        if not bloques:
            self._log_event(
                logging.INFO,
                "grilla_final_sin_bloques",
                plantilla_id=plantilla.id,
                aula_id=aula_id,
                grupo=grupo,
                periodo=periodo,
                turno=turno,
            )
            return PlantillaGrillaFinalResponse(
                plantilla_id=plantilla.id,
                aula_id=aula_id,
                grupo=grupo,
                periodo=periodo,
                turno=turno,
                bloques_por_dia={},
            )

        bloque_ids = [b.id for b in bloques]
        horarios = db.query(Horario).filter(
            Horario.plantilla_bloque_id.in_(bloque_ids),
            Horario.grupo == grupo,
            Horario.periodo == periodo,
            Horario.activo == True,
        ).all()
        horarios_por_bloque = {h.plantilla_bloque_id: h for h in horarios}

        por_dia: Dict[str, List[Dict]] = defaultdict(list)
        for bloque in bloques:
            horario = horarios_por_bloque.get(bloque.id)
            por_dia[str(bloque.dia_semana)].append(
                {
                    "bloque_id": bloque.id,
                    "dia_semana": bloque.dia_semana,
                    "hora_inicio": bloque.hora_inicio,
                    "hora_fin": bloque.hora_fin,
                    "tipo_bloque": bloque.tipo_bloque,
                    "etiqueta": bloque.etiqueta,
                    "orden_visual": bloque.orden_visual,
                    "horario_id": horario.id if horario else None,
                    "curso_id": horario.curso_id if horario else None,
                    "curso_nombre": horario.curso.nombre if horario and horario.curso else None,
                    "docente_id": horario.docente_id if horario else None,
                    "docente_nombre": (
                        horario.docente.nombre_completo if horario and horario.docente else None
                    ),
                }
            )

        total_bloques = sum(len(items) for items in por_dia.values())
        total_horarios = len([h for h in horarios_por_bloque.values() if h])
        self._log_event(
            logging.INFO,
            "grilla_final_ok",
            plantilla_id=plantilla.id,
            aula_id=aula_id,
            grupo=grupo,
            periodo=periodo,
            turno=turno,
            total_bloques=total_bloques,
            total_horarios_asignados=total_horarios,
        )

        return PlantillaGrillaFinalResponse(
            plantilla_id=plantilla.id,
            aula_id=aula_id,
            grupo=grupo,
            periodo=periodo,
            turno=turno,
            bloques_por_dia=dict(por_dia),
        )


plantilla_horario_service = PlantillaHorarioService()
