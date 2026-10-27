"""
routes/encuestas.py
Rutas para el Constructor de Encuestas - Modulo 2.
"""
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from extensions import db
from models import Encuesta, Pregunta, ReglaCondicional, Proyecto

bp = Blueprint("encuestas", __name__, url_prefix="/encuestas")

TIPOS_VALIDOS = {
    "texto_corto", "texto_largo", "opcion_multiple",
    "checkboxes", "likert", "desplegable"
}
ESTADOS_VALIDOS = {"borrador", "publicada", "cerrada"}


# ---------------------------------------------------------------------------
# Listado
# ---------------------------------------------------------------------------

@bp.route("/")
def listar():
    estado_filtro = request.args.get("estado", "")
    solo_plantillas = request.args.get("plantillas", "")

    query = Encuesta.query.filter_by(es_plantilla=False)

    if estado_filtro:
        query = query.filter_by(estado=estado_filtro)

    encuestas = query.order_by(Encuesta.created_at.desc()).all()
    plantillas = Encuesta.query.filter_by(es_plantilla=True).order_by(Encuesta.titulo).all()

    return render_template(
        "encuestas/list.html",
        encuestas=encuestas,
        plantillas=plantillas,
        estado_filtro=estado_filtro,
    )


# ---------------------------------------------------------------------------
# Crear (datos basicos)
# ---------------------------------------------------------------------------

@bp.route("/nueva", methods=["GET", "POST"])
def crear():
    proyectos = Proyecto.query.filter_by(estado="activo").order_by(Proyecto.nombre).all()
    plantillas = Encuesta.query.filter_by(es_plantilla=True).order_by(Encuesta.nombre_plantilla).all()

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        proyecto_id = request.form.get("proyecto_id") or None
        anonima = request.form.get("anonima") == "1"
        plantilla_origen_id = request.form.get("plantilla_origen_id") or None

        if not titulo:
            flash("El titulo de la encuesta es obligatorio.", "danger")
            return render_template("encuestas/form.html", proyectos=proyectos, plantillas=plantillas)

        encuesta = Encuesta(
            titulo=titulo,
            descripcion=descripcion,
            proyecto_id=int(proyecto_id) if proyecto_id else None,
            anonima=anonima,
            estado="borrador",
        )
        db.session.add(encuesta)
        db.session.flush()  # Obtener ID antes de commit

        # Si viene de plantilla, clonar preguntas
        if plantilla_origen_id:
            origen = Encuesta.query.get(int(plantilla_origen_id))
            if origen:
                id_map = {}  # mapa de IDs originales -> nuevos
                for p in origen.preguntas:
                    nueva = Pregunta(
                        encuesta_id=encuesta.id,
                        orden=p.orden,
                        tipo=p.tipo,
                        texto=p.texto,
                        obligatoria=p.obligatoria,
                        opciones_json=p.opciones_json,
                        escala_min=p.escala_min,
                        escala_max=p.escala_max,
                    )
                    db.session.add(nueva)
                    db.session.flush()
                    id_map[p.id] = nueva.id

                # Clonar reglas remapeando IDs
                for r in origen.reglas:
                    if r.pregunta_origen_id in id_map and r.pregunta_destino_id in id_map:
                        nueva_regla = ReglaCondicional(
                            encuesta_id=encuesta.id,
                            pregunta_origen_id=id_map[r.pregunta_origen_id],
                            valor_condicion=r.valor_condicion,
                            pregunta_destino_id=id_map[r.pregunta_destino_id],
                            accion=r.accion,
                        )
                        db.session.add(nueva_regla)

        db.session.commit()
        flash("Encuesta creada. Ahora disenala en el editor.", "success")
        return redirect(url_for("encuestas.editor", id=encuesta.id))

    return render_template("encuestas/form.html", proyectos=proyectos, plantillas=plantillas)


# ---------------------------------------------------------------------------
# Editor drag & drop
# ---------------------------------------------------------------------------

@bp.route("/<int:id>/editor")
def editor(id):
    encuesta = Encuesta.query.get_or_404(id)
    preguntas = Pregunta.query.filter_by(encuesta_id=id).order_by(Pregunta.orden).all()
    reglas = ReglaCondicional.query.filter_by(encuesta_id=id).all()
    proyectos = Proyecto.query.filter_by(estado="activo").order_by(Proyecto.nombre).all()

    # Serializar preguntas para JS
    preguntas_json = []
    for p in preguntas:
        preguntas_json.append({
            "id": p.id,
            "tipo": p.tipo,
            "texto": p.texto,
            "obligatoria": p.obligatoria,
            "opciones": json.loads(p.opciones_json) if p.opciones_json else [],
            "escala_min": p.escala_min or 1,
            "escala_max": p.escala_max or 5,
        })

    # Serializar reglas para JS
    reglas_json = []
    for r in reglas:
        reglas_json.append({
            "id": r.id,
            "pregunta_origen_id": r.pregunta_origen_id,
            "valor_condicion": r.valor_condicion,
            "pregunta_destino_id": r.pregunta_destino_id,
            "accion": r.accion,
        })

    return render_template(
        "encuestas/editor.html",
        encuesta=encuesta,
        proyectos=proyectos,
        preguntas_json=json.dumps(preguntas_json),
        reglas_json=json.dumps(reglas_json),
    )


# ---------------------------------------------------------------------------
# Guardar estado completo del editor (API JSON)
# ---------------------------------------------------------------------------

@bp.route("/<int:id>/guardar", methods=["POST"])
def guardar(id):
    encuesta = Encuesta.query.get_or_404(id)

    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"ok": False, "error": "JSON invalido"}), 400

    # Actualizar datos basicos de la encuesta
    if "titulo" in data:
        encuesta.titulo = data["titulo"].strip() or encuesta.titulo
    if "descripcion" in data:
        encuesta.descripcion = data.get("descripcion", "")
    if "anonima" in data:
        encuesta.anonima = bool(data["anonima"])
    if "proyecto_id" in data:
        encuesta.proyecto_id = data["proyecto_id"] or None
    if "estado" in data and data["estado"] in ESTADOS_VALIDOS:
        encuesta.estado = data["estado"]
    if "es_plantilla" in data:
        encuesta.es_plantilla = bool(data["es_plantilla"])
    if "nombre_plantilla" in data:
        encuesta.nombre_plantilla = data.get("nombre_plantilla", "")

    # Eliminar preguntas y reglas anteriores para reemplazar en bloque
    Pregunta.query.filter_by(encuesta_id=id).delete()
    ReglaCondicional.query.filter_by(encuesta_id=id).delete()
    db.session.flush()

    preguntas_data = data.get("preguntas", [])
    id_map = {}  # tempId JS -> ID real DB

    for idx, p_data in enumerate(preguntas_data):
        tipo = p_data.get("tipo", "texto_corto")
        if tipo not in TIPOS_VALIDOS:
            tipo = "texto_corto"

        opciones = p_data.get("opciones", [])
        opciones_json = json.dumps(opciones) if opciones else None

        pregunta = Pregunta(
            encuesta_id=id,
            orden=idx,
            tipo=tipo,
            texto=p_data.get("texto", "").strip() or "(Sin texto)",
            obligatoria=bool(p_data.get("obligatoria", False)),
            opciones_json=opciones_json,
            escala_min=p_data.get("escala_min", 1),
            escala_max=p_data.get("escala_max", 5),
        )
        db.session.add(pregunta)
        db.session.flush()
        id_map[str(p_data.get("tempId", idx))] = pregunta.id

    # Guardar reglas usando el mapa de IDs
    for r_data in data.get("reglas", []):
        origen_temp = str(r_data.get("pregunta_origen_tempId"))
        destino_temp = str(r_data.get("pregunta_destino_tempId"))

        if origen_temp in id_map and destino_temp in id_map:
            regla = ReglaCondicional(
                encuesta_id=id,
                pregunta_origen_id=id_map[origen_temp],
                valor_condicion=r_data.get("valor_condicion", ""),
                pregunta_destino_id=id_map[destino_temp],
                accion=r_data.get("accion", "mostrar"),
            )
            db.session.add(regla)

    db.session.commit()
    return jsonify({"ok": True, "message": "Encuesta guardada correctamente."})


# ---------------------------------------------------------------------------
# Previsualizar
# ---------------------------------------------------------------------------

@bp.route("/<int:id>/preview")
def preview(id):
    encuesta = Encuesta.query.get_or_404(id)
    preguntas = Pregunta.query.filter_by(encuesta_id=id).order_by(Pregunta.orden).all()
    reglas = ReglaCondicional.query.filter_by(encuesta_id=id).all()

    reglas_json = []
    for r in reglas:
        reglas_json.append({
            "pregunta_origen_id": r.pregunta_origen_id,
            "valor_condicion": r.valor_condicion,
            "pregunta_destino_id": r.pregunta_destino_id,
            "accion": r.accion,
        })

    for p in preguntas:
        p.opciones_parsed = json.loads(p.opciones_json) if p.opciones_json else []

    return render_template(
        "encuestas/preview.html",
        encuesta=encuesta,
        preguntas=preguntas,
        reglas_json=json.dumps(reglas_json),
    )


# ---------------------------------------------------------------------------
# Editar datos basicos
# ---------------------------------------------------------------------------

@bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    encuesta = Encuesta.query.get_or_404(id)
    proyectos = Proyecto.query.filter_by(estado="activo").order_by(Proyecto.nombre).all()

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        if not titulo:
            flash("El titulo es obligatorio.", "danger")
            return render_template("encuestas/editar_meta.html", encuesta=encuesta, proyectos=proyectos)

        encuesta.titulo = titulo
        encuesta.descripcion = request.form.get("descripcion", "")
        encuesta.proyecto_id = request.form.get("proyecto_id") or None
        encuesta.anonima = request.form.get("anonima") == "1"
        db.session.commit()
        flash("Datos de la encuesta actualizados.", "success")
        return redirect(url_for("encuestas.editor", id=encuesta.id))

    return render_template("encuestas/editar_meta.html", encuesta=encuesta, proyectos=proyectos)


# ---------------------------------------------------------------------------
# Eliminar
# ---------------------------------------------------------------------------

@bp.route("/<int:id>/eliminar", methods=["POST"])
def eliminar(id):
    encuesta = Encuesta.query.get_or_404(id)
    db.session.delete(encuesta)
    db.session.commit()
    flash("Encuesta eliminada correctamente.", "success")
    return redirect(url_for("encuestas.listar"))

