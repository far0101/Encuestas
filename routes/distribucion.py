"""
routes/distribucion.py
Rutas para la distribucion de encuestas, generacion de QR, gestion de tokens y recordatorios - Modulo 3.
"""
import io
import secrets
from datetime import datetime
import qrcode
import qrcode.image.svg
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response,
)
from extensions import db
from models import Encuesta, Distribucion
from services.email_service import enviar_correo_encuesta, obtener_ultimos_envios

bp = Blueprint("distribucion", __name__, url_prefix="/distribucion")


@bp.route("/<int:encuesta_id>")
def panel(encuesta_id):
    """Panel principal de control de distribucion y respuestas."""
    encuesta = Encuesta.query.get_or_404(encuesta_id)
    distribuciones = (
        Distribucion.query.filter_by(encuesta_id=encuesta_id)
        .order_by(Distribucion.id.desc())
        .all()
    )

    total_destinatarios = len(distribuciones)
    respondidas = sum(1 for d in distribuciones if d.estado == "respondida")
    pendientes = sum(1 for d in distribuciones if d.estado == "pendiente")
    tasa_respuesta = (
        round((respondidas / total_destinatarios) * 100, 1)
        if total_destinatarios > 0
        else 0
    )

    base_url = request.host_url.rstrip("/")
    url_publica = f"{base_url}/responder/publica/{encuesta.id}"

    ultimos_logs = obtener_ultimos_envios(limite=5)

    return render_template(
        "distribucion/panel.html",
        encuesta=encuesta,
        distribuciones=distribuciones,
        total_destinatarios=total_destinatarios,
        respondidas=respondidas,
        pendientes=pendientes,
        tasa_respuesta=tasa_respuesta,
        url_publica=url_publica,
        base_url=base_url,
        ultimos_logs=ultimos_logs,
    )


@bp.route("/<int:encuesta_id>/qr")
def qr_code(encuesta_id):
    """Genera y sirve el codigo QR en formato vectorial SVG."""
    encuesta = Encuesta.query.get_or_404(encuesta_id)
    token = request.args.get("token")

    base_url = request.host_url.rstrip("/")
    if token:
        destino_url = f"{base_url}/responder/{token}"
    else:
        destino_url = f"{base_url}/responder/publica/{encuesta.id}"

    factory = qrcode.image.svg.SvgImage
    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=2,
        image_factory=factory,
    )
    qr.add_data(destino_url)
    qr.make(fit=True)

    img = qr.make_image()
    stream = io.BytesIO()
    img.save(stream)
    stream.seek(0)

    download = request.args.get("download")
    headers = {"Content-Type": "image/svg+xml"}
    if download:
        filename = f"qr_encuesta_{encuesta.id}.svg"
        headers["Content-Disposition"] = f"attachment; filename={filename}"

    return Response(stream.getvalue(), headers=headers)


@bp.route("/<int:encuesta_id>/agregar", methods=["POST"])
def agregar_destinatarios(encuesta_id):
    """Agrega uno o varios destinatarios y genera sus enlaces con token unico."""
    encuesta = Encuesta.query.get_or_404(encuesta_id)

    tipo_carga = request.form.get("tipo_carga", "individual")

    if tipo_carga == "lote":
        bloque = request.form.get("bloque_emails", "")
        lineas = [l.strip() for l in bloque.splitlines() if l.strip()]
        creados = 0

        for linea in lineas:
            partes = [p.strip() for p in linea.split(",") if p.strip()]
            if len(partes) >= 2:
                nombre, email = partes[0], partes[1]
            elif len(partes) == 1:
                nombre, email = partes[0].split("@")[0], partes[0]
            else:
                continue

            if "@" in email:
                token = secrets.token_urlsafe(16)
                dist = Distribucion(
                    encuesta_id=encuesta.id,
                    destinatario_nombre=nombre,
                    destinatario_email=email,
                    token=token,
                    estado="pendiente",
                )
                db.session.add(dist)
                creados += 1

        db.session.commit()
        flash(f"Se registraron {creados} destinatarios correctamente.", "success")
        return redirect(url_for("distribucion.panel", encuesta_id=encuesta.id))

    # Carga individual
    nombre = request.form.get("nombre", "").strip()
    email = request.form.get("email", "").strip()

    if not email or "@" not in email:
        flash("Debe proporcionar una direccion de correo electronico valida.", "danger")
        return redirect(url_for("distribucion.panel", encuesta_id=encuesta.id))

    token = secrets.token_urlsafe(16)
    dist = Distribucion(
        encuesta_id=encuesta.id,
        destinatario_nombre=nombre or email.split("@")[0],
        destinatario_email=email,
        token=token,
        estado="pendiente",
    )
    db.session.add(dist)
    db.session.commit()

    flash("Destinatario agregado exitosamente con enlace unico asignado.", "success")
    return redirect(url_for("distribucion.panel", encuesta_id=encuesta.id))


@bp.route("/<int:encuesta_id>/enviar_invitaciones", methods=["POST"])
def enviar_invitaciones(encuesta_id):
    """Envia el correo de invitacion a todos los destinatarios con estado pendiente."""
    encuesta = Encuesta.query.get_or_404(encuesta_id)
    pendientes = Distribucion.query.filter_by(
        encuesta_id=encuesta_id, estado="pendiente"
    ).all()

    if not pendientes:
        flash("No existen destinatarios pendientes de envio.", "warning")
        return redirect(url_for("distribucion.panel", encuesta_id=encuesta.id))

    base_url = request.host_url.rstrip("/")
    enviados = 0

    for dist in pendientes:
        url_encuesta = f"{base_url}/responder/{dist.token}"
        ok, _ = enviar_correo_encuesta(
            destinatario_email=dist.destinatario_email,
            destinatario_nombre=dist.destinatario_nombre,
            encuesta_titulo=encuesta.titulo,
            url_encuesta=url_encuesta,
            es_recordatorio=False,
        )
        if ok:
            dist.fecha_envio = datetime.utcnow()
            enviados += 1

    db.session.commit()
    flash(f"Se procesaron {enviados} invitaciones por correo electronico.", "success")
    return redirect(url_for("distribucion.panel", encuesta_id=encuesta.id))


@bp.route("/<int:encuesta_id>/enviar_recordatorios", methods=["POST"])
def enviar_recordatorios(encuesta_id):
    """Envia recordatorios a todos los destinatarios que aun no hayan respondido."""
    encuesta = Encuesta.query.get_or_404(encuesta_id)
    pendientes = Distribucion.query.filter_by(
        encuesta_id=encuesta_id, estado="pendiente"
    ).all()

    if not pendientes:
        flash("Todos los destinatarios registrados ya completaron la encuesta o no hay pendientes.", "info")
        return redirect(url_for("distribucion.panel", encuesta_id=encuesta.id))

    base_url = request.host_url.rstrip("/")
    recordatorios = 0

    for dist in pendientes:
        url_encuesta = f"{base_url}/responder/{dist.token}"
        ok, _ = enviar_correo_encuesta(
            destinatario_email=dist.destinatario_email,
            destinatario_nombre=dist.destinatario_nombre,
            encuesta_titulo=encuesta.titulo,
            url_encuesta=url_encuesta,
            es_recordatorio=True,
        )
        if ok:
            dist.intentos_recordatorio += 1
            dist.fecha_ultimo_recordatorio = datetime.utcnow()
            recordatorios += 1

    db.session.commit()
    flash(f"Se emitieron {recordatorios} recordatorios a respondentes pendientes.", "success")
    return redirect(url_for("distribucion.panel", encuesta_id=encuesta.id))


@bp.route("/<int:encuesta_id>/recordatorio_individual/<int:distribucion_id>", methods=["POST"])
def recordatorio_individual(encuesta_id, distribucion_id):
    """Envia recordatorio a un unico destinatario especifico."""
    encuesta = Encuesta.query.get_or_404(encuesta_id)
    dist = Distribucion.query.get_or_404(distribucion_id)

    if dist.estado != "pendiente":
        flash("El destinatario ya ha respondido o no se encuentra pendiente.", "warning")
        return redirect(url_for("distribucion.panel", encuesta_id=encuesta.id))

    base_url = request.host_url.rstrip("/")
    url_encuesta = f"{base_url}/responder/{dist.token}"

    ok, msg = enviar_correo_encuesta(
        destinatario_email=dist.destinatario_email,
        destinatario_nombre=dist.destinatario_nombre,
        encuesta_titulo=encuesta.titulo,
        url_encuesta=url_encuesta,
        es_recordatorio=True,
    )

    if ok:
        dist.intentos_recordatorio += 1
        dist.fecha_ultimo_recordatorio = datetime.utcnow()
        db.session.commit()
        flash(f"Recordatorio enviado a {dist.destinatario_email}.", "success")
    else:
        flash(f"Error al enviar recordatorio: {msg}", "danger")

    return redirect(url_for("distribucion.panel", encuesta_id=encuesta.id))


@bp.route("/<int:encuesta_id>/eliminar_destinatario/<int:distribucion_id>", methods=["POST"])
def eliminar_destinatario(encuesta_id, distribucion_id):
    """Elimina un destinatario si todavia se encuentra pendiente."""
    dist = Distribucion.query.get_or_404(distribucion_id)
    if dist.estado == "respondida":
        flash("No es posible eliminar un registro que ya cuenta con respuesta registrada.", "danger")
        return redirect(url_for("distribucion.panel", encuesta_id=encuesta_id))

    db.session.delete(dist)
    db.session.commit()
    flash("Destinatario eliminado de la lista de distribucion.", "success")
    return redirect(url_for("distribucion.panel", encuesta_id=encuesta_id))

