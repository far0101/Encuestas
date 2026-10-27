"""
routes/respuestas.py
Rutas para la recepcion, validacion y almacenamiento de respuestas a encuestas - Modulo 3.
"""
import json
from datetime import datetime
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
)
from extensions import db
from models import Encuesta, Pregunta, ReglaCondicional, Distribucion, Respuesta, RespuestaDetalle

bp = Blueprint("respuestas", __name__, url_prefix="/responder")


@bp.route("/publica/<int:encuesta_id>", methods=["GET", "POST"])
def responder_publica(encuesta_id):
    """Interfaz para responder mediante enlace abierto o codigo QR."""
    encuesta = Encuesta.query.get_or_404(encuesta_id)

    if encuesta.estado != "publicada":
        return render_template(
            "respuestas/error.html",
            titulo_error="Encuesta no disponible",
            mensaje="Esta encuesta no se encuentra en estado 'Publicada' y no admite respuestas en este momento.",
        )

    preguntas = Pregunta.query.filter_by(encuesta_id=encuesta.id).order_by(Pregunta.orden).all()
    reglas = ReglaCondicional.query.filter_by(encuesta_id=encuesta.id).all()

    reglas_json = [
        {
            "pregunta_origen_id": r.pregunta_origen_id,
            "valor_condicion": r.valor_condicion,
            "pregunta_destino_id": r.pregunta_destino_id,
            "accion": r.accion,
        }
        for r in reglas
    ]

    for p in preguntas:
        p.opciones_parsed = json.loads(p.opciones_json) if p.opciones_json else []

    if request.method == "POST":
        # Control de preguntas obligatorias
        errores = []
        for p in preguntas:
            campo = f"pregunta_{p.id}"
            if p.tipo == "checkboxes":
                vals = request.form.getlist(campo)
                if p.obligatoria and not vals:
                    errores.append(f"Debe seleccionar al menos una opcion en: '{p.texto}'")
            else:
                val = request.form.get(campo, "").strip()
                if p.obligatoria and not val:
                    errores.append(f"La pregunta '{p.texto}' es obligatoria.")

        if errores:
            for err in errores:
                flash(err, "danger")
            return render_template(
                "respuestas/formulario.html",
                encuesta=encuesta,
                preguntas=preguntas,
                reglas_json=json.dumps(reglas_json),
                distribucion=None,
                es_publica=True,
            )

        identificador = "Anonimo"
        if not encuesta.anonima:
            nombre_ingresado = request.form.get("respondente_nombre", "").strip()
            email_ingresado = request.form.get("respondente_email", "").strip()
            if nombre_ingresado or email_ingresado:
                identificador = f"{nombre_ingresado} ({email_ingresado})".strip()
            else:
                identificador = "Publico No Identificado"

        respuesta = Respuesta(
            encuesta_id=encuesta.id,
            distribucion_id=None,
            respondente_identificador=identificador,
            fecha_completada=datetime.utcnow(),
        )
        db.session.add(respuesta)
        db.session.flush()

        guardar_detalles_respuesta(respuesta.id, preguntas, request.form)
        db.session.commit()

        return redirect(url_for("respuestas.exito"))

    return render_template(
        "respuestas/formulario.html",
        encuesta=encuesta,
        preguntas=preguntas,
        reglas_json=json.dumps(reglas_json),
        distribucion=None,
        es_publica=True,
    )


@bp.route("/<string:token>", methods=["GET", "POST"])
def responder_token(token):
    """Interfaz para responder mediante enlace unico individual."""
    dist = Distribucion.query.filter_by(token=token).first()

    if not dist:
        return render_template(
            "respuestas/error.html",
            titulo_error="Enlace invalido o expirado",
            mensaje="El token proporcionado no corresponde a ninguna distribucion activa.",
        )

    if dist.estado == "respondida":
        return render_template(
            "respuestas/error.html",
            titulo_error="Encuesta ya respondida",
            mensaje=f"Esta encuesta ya fue completada exitosamente el {dist.fecha_respuesta.strftime('%d/%m/%Y a las %H:%M') if dist.fecha_respuesta else ''}. Muchas gracias por su participacion.",
        )

    encuesta = dist.encuesta
    if encuesta.estado != "publicada":
        return render_template(
            "respuestas/error.html",
            titulo_error="Encuesta pausada",
            mensaje="La encuesta ha sido pausada o cerrada por el equipo de administracion.",
        )

    preguntas = Pregunta.query.filter_by(encuesta_id=encuesta.id).order_by(Pregunta.orden).all()
    reglas = ReglaCondicional.query.filter_by(encuesta_id=encuesta.id).all()

    reglas_json = [
        {
            "pregunta_origen_id": r.pregunta_origen_id,
            "valor_condicion": r.valor_condicion,
            "pregunta_destino_id": r.pregunta_destino_id,
            "accion": r.accion,
        }
        for r in reglas
    ]

    for p in preguntas:
        p.opciones_parsed = json.loads(p.opciones_json) if p.opciones_json else []

    if request.method == "POST":
        errores = []
        for p in preguntas:
            campo = f"pregunta_{p.id}"
            if p.tipo == "checkboxes":
                vals = request.form.getlist(campo)
                if p.obligatoria and not vals:
                    errores.append(f"Debe marcar al menos una opcion en: '{p.texto}'")
            else:
                val = request.form.get(campo, "").strip()
                if p.obligatoria and not val:
                    errores.append(f"La pregunta '{p.texto}' es obligatoria.")

        if errores:
            for err in errores:
                flash(err, "danger")
            return render_template(
                "respuestas/formulario.html",
                encuesta=encuesta,
                preguntas=preguntas,
                reglas_json=json.dumps(reglas_json),
                distribucion=dist,
                es_publica=False,
            )

        # Regla de anonimato: si es anonima, no se vincula distribucion_id a la respuesta
        if encuesta.anonima:
            distribucion_fk = None
            identificador = "Anonimo"
        else:
            distribucion_fk = dist.id
            identificador = dist.destinatario_nombre or dist.destinatario_email or "Identificado"

        respuesta = Respuesta(
            encuesta_id=encuesta.id,
            distribucion_id=distribucion_fk,
            respondente_identificador=identificador,
            fecha_completada=datetime.utcnow(),
        )
        db.session.add(respuesta)
        db.session.flush()

        guardar_detalles_respuesta(respuesta.id, preguntas, request.form)

        # Marcar la distribucion como respondida para cerrar el token
        dist.estado = "respondida"
        dist.fecha_respuesta = datetime.utcnow()

        db.session.commit()
        return redirect(url_for("respuestas.exito"))

    return render_template(
        "respuestas/formulario.html",
        encuesta=encuesta,
        preguntas=preguntas,
        reglas_json=json.dumps(reglas_json),
        distribucion=dist,
        es_publica=False,
    )


@bp.route("/exito")
def exito():
    """Pantalla final de confirmacion tras enviar las respuestas."""
    return render_template("respuestas/exito.html")


def guardar_detalles_respuesta(respuesta_id, preguntas, form_data):
    """Guarda cada respuesta individual segun el tipo de componente."""
    for p in preguntas:
        campo = f"pregunta_{p.id}"
        if p.tipo == "checkboxes":
            valores = form_data.getlist(campo)
            detalle = RespuestaDetalle(
                respuesta_id=respuesta_id,
                pregunta_id=p.id,
                valor_texto=", ".join(valores),
                valor_json=json.dumps(valores),
            )
        else:
            val = form_data.get(campo, "").strip()
            detalle = RespuestaDetalle(
                respuesta_id=respuesta_id,
                pregunta_id=p.id,
                valor_texto=val,
                valor_json=None,
            )
        db.session.add(detalle)

