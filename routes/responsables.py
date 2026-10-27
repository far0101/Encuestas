"""
routes/responsables.py
Rutas para el ABM de Responsables - Modulo 1.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Responsable

bp = Blueprint("responsables", __name__, url_prefix="/responsables")


@bp.route("/")
def listar():
    """Lista todos los responsables."""
    responsables = Responsable.query.order_by(Responsable.nombre).all()
    return render_template("responsables/list.html", responsables=responsables)


@bp.route("/nuevo", methods=["GET", "POST"])
def crear():
    """Formulario y procesamiento para crear un nuevo responsable."""
    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        rol = request.form.get("rol", "").strip()

        errores = []

        if not nombre:
            errores.append("El nombre es obligatorio.")
        if not email:
            errores.append("El email es obligatorio.")
        if not rol:
            errores.append("El rol es obligatorio.")

        # Verificar email unico
        existente = Responsable.query.filter_by(email=email).first()
        if existente:
            errores.append("Ya existe un responsable con ese email.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template(
                "responsables/form.html", accion="Crear", responsable=None
            )

        responsable = Responsable(nombre=nombre, email=email, rol=rol)
        db.session.add(responsable)
        db.session.commit()
        flash("Responsable creado correctamente.", "success")
        return redirect(url_for("responsables.listar"))

    return render_template("responsables/form.html", accion="Crear", responsable=None)


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
def editar(id):
    """Formulario y procesamiento para editar un responsable."""
    responsable = Responsable.query.get_or_404(id)

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip()
        rol = request.form.get("rol", "").strip()

        errores = []

        if not nombre:
            errores.append("El nombre es obligatorio.")
        if not email:
            errores.append("El email es obligatorio.")
        if not rol:
            errores.append("El rol es obligatorio.")

        # Verificar email unico excluyendo el actual
        existente = Responsable.query.filter(
            Responsable.email == email, Responsable.id != id
        ).first()
        if existente:
            errores.append("Ya existe otro responsable con ese email.")

        if errores:
            for e in errores:
                flash(e, "danger")
            return render_template(
                "responsables/form.html", accion="Editar", responsable=responsable
            )

        responsable.nombre = nombre
        responsable.email = email
        responsable.rol = rol
        db.session.commit()
        flash("Responsable actualizado correctamente.", "success")
        return redirect(url_for("responsables.listar"))

    return render_template(
        "responsables/form.html", accion="Editar", responsable=responsable
    )


@bp.route("/<int:id>/eliminar", methods=["POST"])
def eliminar(id):
    """Elimina un responsable si no tiene proyectos asignados."""
    responsable = Responsable.query.get_or_404(id)

    from models import Proyecto

    if (responsable.proyectos and len(responsable.proyectos) > 0) or Proyecto.query.filter_by(responsable_id=id).first():
        flash(
            "No se puede eliminar: el responsable tiene proyectos asignados. Reasigne los proyectos primero.",
            "danger",
        )
        return redirect(url_for("responsables.listar"))

    db.session.delete(responsable)
    db.session.commit()
    flash("Responsable eliminado correctamente.", "success")
    return redirect(url_for("responsables.listar"))

