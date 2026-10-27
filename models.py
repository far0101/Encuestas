"""
models.py
Definicion de modelos de base de datos - Modulos 1, 2 y 3.
"""
from datetime import datetime
from extensions import db


# Tabla intermedia para relacion muchos-a-muchos entre Proyecto y Responsable
proyecto_responsables = db.Table(
    "proyecto_responsables",
    db.Column("proyecto_id", db.Integer, db.ForeignKey("proyecto.id"), primary_key=True),
    db.Column("responsable_id", db.Integer, db.ForeignKey("responsable.id"), primary_key=True),
)


class Responsable(db.Model):
    __tablename__ = "responsable"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    rol = db.Column(db.String(80), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Responsable {self.nombre}>"


class Proyecto(db.Model):
    __tablename__ = "proyecto"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    anio = db.Column(db.Integer, nullable=False)
    estado = db.Column(
        db.Enum("activo", "finalizado", "suspendido", name="estado_proyecto"),
        nullable=False,
        default="activo",
    )
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=True)
    responsable_id = db.Column(
        db.Integer, db.ForeignKey("responsable.id"), nullable=True
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relacion muchos-a-muchos con Responsable
    responsables = db.relationship(
        "Responsable",
        secondary=proyecto_responsables,
        backref=db.backref("proyectos", lazy=True),
    )
    responsable = db.relationship("Responsable", foreign_keys=[responsable_id])

    def __repr__(self):
        return f"<Proyecto {self.nombre}>"


# ---------------------------------------------------------------------------
# Modulo 2 - Constructor de Encuestas
# ---------------------------------------------------------------------------

class Encuesta(db.Model):
    __tablename__ = "encuesta"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    descripcion = db.Column(db.Text, nullable=True)
    proyecto_id = db.Column(db.Integer, db.ForeignKey("proyecto.id"), nullable=True)
    anonima = db.Column(db.Boolean, default=False, nullable=False)
    # Plantillas
    es_plantilla = db.Column(db.Boolean, default=False, nullable=False)
    nombre_plantilla = db.Column(db.String(100), nullable=True)
    # Estados: borrador / publicada / cerrada
    estado = db.Column(db.String(20), nullable=False, default="borrador")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relaciones
    proyecto = db.relationship("Proyecto", backref="encuestas")
    preguntas = db.relationship(
        "Pregunta", backref="encuesta", lazy=True,
        cascade="all, delete-orphan", order_by="Pregunta.orden"
    )
    reglas = db.relationship(
        "ReglaCondicional", backref="encuesta", lazy=True,
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Encuesta {self.titulo}>"


class Pregunta(db.Model):
    __tablename__ = "pregunta"

    id = db.Column(db.Integer, primary_key=True)
    encuesta_id = db.Column(db.Integer, db.ForeignKey("encuesta.id"), nullable=False)
    orden = db.Column(db.Integer, nullable=False, default=0)
    # Tipos: texto_corto / texto_largo / opcion_multiple / checkboxes / likert / desplegable
    tipo = db.Column(db.String(30), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    obligatoria = db.Column(db.Boolean, default=False, nullable=False)
    # JSON serializado para opciones (opcion_multiple, checkboxes, desplegable)
    opciones_json = db.Column(db.Text, nullable=True)
    # Escala Likert
    escala_min = db.Column(db.Integer, nullable=True, default=1)
    escala_max = db.Column(db.Integer, nullable=True, default=5)

    def __repr__(self):
        return f"<Pregunta {self.id} - {self.tipo}>"


class ReglaCondicional(db.Model):
    __tablename__ = "regla_condicional"

    id = db.Column(db.Integer, primary_key=True)
    encuesta_id = db.Column(db.Integer, db.ForeignKey("encuesta.id"), nullable=False)
    pregunta_origen_id = db.Column(db.Integer, db.ForeignKey("pregunta.id"), nullable=False)
    valor_condicion = db.Column(db.String(200), nullable=False)
    pregunta_destino_id = db.Column(db.Integer, db.ForeignKey("pregunta.id"), nullable=False)
    # accion: mostrar / ocultar
    accion = db.Column(db.String(10), nullable=False, default="mostrar")

    pregunta_origen = db.relationship("Pregunta", foreign_keys=[pregunta_origen_id])
    pregunta_destino = db.relationship("Pregunta", foreign_keys=[pregunta_destino_id])

    def __repr__(self):
        return f"<Regla {self.pregunta_origen_id} -> {self.pregunta_destino_id}>"


# ---------------------------------------------------------------------------
# Modulo 3 - Distribucion y Recoleccion
# ---------------------------------------------------------------------------

class Distribucion(db.Model):
    __tablename__ = "distribucion"

    id = db.Column(db.Integer, primary_key=True)
    encuesta_id = db.Column(db.Integer, db.ForeignKey("encuesta.id"), nullable=False)
    destinatario_nombre = db.Column(db.String(120), nullable=True)
    destinatario_email = db.Column(db.String(150), nullable=True)
    token = db.Column(db.String(64), unique=True, index=True, nullable=False)
    # Estados: pendiente / respondida / cancelada
    estado = db.Column(db.String(20), nullable=False, default="pendiente")
    fecha_envio = db.Column(db.DateTime, nullable=True)
    fecha_ultimo_recordatorio = db.Column(db.DateTime, nullable=True)
    intentos_recordatorio = db.Column(db.Integer, default=0, nullable=False)
    fecha_respuesta = db.Column(db.DateTime, nullable=True)

    encuesta = db.relationship("Encuesta", backref=db.backref("distribuciones", lazy=True, cascade="all, delete-orphan"))

    def __repr__(self):
        return f"<Distribucion {self.token} - {self.destinatario_email or 'Publico'}>"


class Respuesta(db.Model):
    __tablename__ = "respuesta"

    id = db.Column(db.Integer, primary_key=True)
    encuesta_id = db.Column(db.Integer, db.ForeignKey("encuesta.id"), nullable=False)
    distribucion_id = db.Column(db.Integer, db.ForeignKey("distribucion.id"), nullable=True)
    respondente_identificador = db.Column(db.String(150), nullable=False, default="Anonimo")
    fecha_completada = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    encuesta = db.relationship("Encuesta", backref=db.backref("respuestas", lazy=True, cascade="all, delete-orphan"))
    distribucion = db.relationship("Distribucion", backref=db.backref("respuesta", uselist=False))
    detalles = db.relationship("RespuestaDetalle", backref="respuesta", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Respuesta {self.id} - Encuesta {self.encuesta_id}>"


class RespuestaDetalle(db.Model):
    __tablename__ = "respuesta_detalle"

    id = db.Column(db.Integer, primary_key=True)
    respuesta_id = db.Column(db.Integer, db.ForeignKey("respuesta.id"), nullable=False)
    pregunta_id = db.Column(db.Integer, db.ForeignKey("pregunta.id"), nullable=False)
    valor_texto = db.Column(db.Text, nullable=True)
    valor_json = db.Column(db.Text, nullable=True)

    pregunta = db.relationship("Pregunta")

    def __repr__(self):
        return f"<RespuestaDetalle {self.id} - Pregunta {self.pregunta_id}>"


