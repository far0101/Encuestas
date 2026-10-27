"""
app.py
Punto de entrada principal de la aplicacion - Sistema de Gestion de Proyectos.
"""
from flask import Flask, render_template
from config import Config
from extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Inicializar extensiones
    db.init_app(app)

    # Registrar blueprints
    from routes.proyectos import bp as proyectos_bp
    from routes.responsables import bp as responsables_bp
    from routes.encuestas import bp as encuestas_bp
    from routes.distribucion import bp as distribucion_bp
    from routes.respuestas import bp as respuestas_bp
    from routes.dashboard import bp as dashboard_bp

    app.register_blueprint(proyectos_bp)
    app.register_blueprint(responsables_bp)
    app.register_blueprint(encuestas_bp)
    app.register_blueprint(distribucion_bp)
    app.register_blueprint(respuestas_bp)
    app.register_blueprint(dashboard_bp)

    # Ruta principal - redirige al listado de proyectos
    @app.route("/")
    def index():
        from models import Proyecto, Responsable

        total_proyectos = Proyecto.query.count()
        activos = Proyecto.query.filter_by(estado="activo").count()
        finalizados = Proyecto.query.filter_by(estado="finalizado").count()
        suspendidos = Proyecto.query.filter_by(estado="suspendido").count()
        total_responsables = Responsable.query.count()
        ultimos = Proyecto.query.order_by(Proyecto.created_at.desc()).limit(5).all()

        return render_template(
            "index.html",
            total_proyectos=total_proyectos,
            activos=activos,
            finalizados=finalizados,
            suspendidos=suspendidos,
            total_responsables=total_responsables,
            ultimos=ultimos,
        )

    # Crear tablas al iniciar
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

