"""
routes/proyectos.py
Rutas para el ABM de Proyectos - Modulo 1.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Proyecto, Responsable
from datetime import date

bp = Blueprint("proyectos", __name__, url_prefix="/proyectos")


@bp.route("/")
def listar():
    """Lista todos los proyectos con filtro opcional por estado."""
    estado_filtro = request.args.get("estado", "")
    anio_filtro = request.args.get("anio", "")

    query = Proyecto.query

    if estado_filtro:
        query = query.filter_by(estado=estado_filtro)
    if anio_filtro:
        query = query.filter_by(anio=anio_filtro)

    proyectos = query.order_by(Proyecto.created_at.desc()).all()
    anios = db.session.query(Proyecto.anio).distinct().order_by(Proyecto.anio.desc()).all()
    anios = [a[0] for a in anios]

    return render_template(
        "proyectos/list.html",
        proyectos=proyectos,
        estado_filtro=estado_filtro,
        anio_filtro=anio_filtro,
        anios=anios,
    )


@bp.route("/nuevo", methods=["GET", "POST"])
def crear():
    """Formulario y procesamiento para crear un nuevo proyecto."""
    responsables = Responsable.query.order_by(Responsable.nombre).all()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        anio = request.form.get("anio", "").strip()
        estado = request.form.get("estado", "activo")
        fecha_inicio_str = request.form.get("fecha_inicio", "")
        fecha_fin_str = request.form.get("fecha_fin", "")
        responsable_ids = request.form.getlist("responsable_ids")

        errores = []

        if not nombre:
            errores.append("El nombre del proyecto es obligatorio.")
        if not anio or not anio.isdigit():
            errores.append("El anio debe ser un numero valido.")
        if not fecha_inicio_str:
            errores.append("La fecha de inicio es obligatoria.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template(
                "proyectos/form.html",
                responsables=responsables,
                accion="Crear",
                proyecto=None,
            )

        fecha_inicio = date.fromisoformat(fecha_inicio_str)
        fecha_fin = date.fromisoformat(fecha_fin_str) if fecha_fin_str else None

        r_ids_int = [int(rid) for rid in responsable_ids if rid.isdigit()]
        seleccionados = Responsable.query.filter(Responsable.id.in_(r_ids_int)).all() if r_ids_int else []

        proyecto = Proyecto(
            nombre=nombre,
            descripcion=descripcion,
            anio=int(anio),
            estado=estado,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            responsable_id=r_ids_int[0] if r_ids_int else None,
            responsables=seleccionados,
        )
        db.session.add(proyecto)
        db.session.commit()
        flash("Proyecto creado correctamente.", "success")
        return redirect(url_for("proyectos.listar"))

    return render_template(
        "proyectos/form.html",
        responsables=responsables,
        accion="Crear",
        proyecto=None,
    )


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    """Formulario y procesamiento para editar un proyecto existente."""
    proyecto = Proyecto.query.get_or_404(id)
    responsables = Responsable.query.order_by(Responsable.nombre).all()

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        anio = request.form.get("anio", "").strip()
        estado = request.form.get("estado", "activo")
        fecha_inicio_str = request.form.get("fecha_inicio", "")
        fecha_fin_str = request.form.get("fecha_fin", "")
        responsable_ids = request.form.getlist("responsable_ids")

        errores = []

        if not nombre:
            errores.append("El nombre del proyecto es obligatorio.")
        if not anio or not anio.isdigit():
            errores.append("El anio debe ser un numero valido.")
        if not fecha_inicio_str:
            errores.append("La fecha de inicio es obligatoria.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template(
                "proyectos/form.html",
                responsables=responsables,
                accion="Editar",
                proyecto=proyecto,
            )

        r_ids_int = [int(rid) for rid in responsable_ids if rid.isdigit()]
        seleccionados = Responsable.query.filter(Responsable.id.in_(r_ids_int)).all() if r_ids_int else []

        proyecto.nombre = nombre
        proyecto.descripcion = descripcion
        proyecto.anio = int(anio)
        proyecto.estado = estado
        proyecto.fecha_inicio = date.fromisoformat(fecha_inicio_str)
        proyecto.fecha_fin = date.fromisoformat(fecha_fin_str) if fecha_fin_str else None
        proyecto.responsable_id = r_ids_int[0] if r_ids_int else None
        proyecto.responsables = seleccionados

        db.session.commit()
        flash("Proyecto actualizado correctamente.", "success")
        return redirect(url_for("proyectos.listar"))

    return render_template(
        "proyectos/form.html",
        responsables=responsables,
        accion="Editar",
        proyecto=proyecto,
    )


@bp.route("/<int:id>/detalle")
def detalle(id):
    """Vista de detalle de un proyecto."""
    proyecto = Proyecto.query.get_or_404(id)
    return render_template("proyectos/detail.html", proyecto=proyecto)


@bp.route("/<int:id>/eliminar", methods=["POST"])
def eliminar(id):
    """Elimina un proyecto si no tiene restricciones."""
    proyecto = Proyecto.query.get_or_404(id)
    db.session.delete(proyecto)
    db.session.commit()
    flash("Proyecto eliminado correctamente.", "success")
    return redirect(url_for("proyectos.listar"))

