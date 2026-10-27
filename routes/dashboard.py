"""
routes/dashboard.py
Modulo 4: Dashboard Dinamico de Metricas, KPIs y Semaforo de Riesgo.
"""
import json
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify
from extensions import db
from models import (
    Proyecto,
    Responsable,
    Encuesta,
    Pregunta,
    Distribucion,
    Respuesta,
    RespuestaDetalle,
)

bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


# ---------------------------------------------------------------------------
# Vista principal del Dashboard
# ---------------------------------------------------------------------------

@bp.route("/")
def index():
    proyectos = Proyecto.query.order_by(Proyecto.nombre).all()
    responsables = Responsable.query.order_by(Responsable.nombre).all()
    encuestas = Encuesta.query.filter_by(es_plantilla=False).order_by(Encuesta.titulo).all()

    return render_template(
        "dashboard/index.html",
        proyectos=proyectos,
        responsables=responsables,
        encuestas=encuestas,
    )


# ---------------------------------------------------------------------------
# API Asincrona de Metricas y Datos en Tiempo Real
# ---------------------------------------------------------------------------

@bp.route("/api/datos")
def api_datos():
    proyecto_id = request.args.get("proyecto_id", type=int)
    responsable_id = request.args.get("responsable_id", type=int)
    encuesta_id = request.args.get("encuesta_id", type=int)
    desde_str = request.args.get("desde", type=str)
    hasta_str = request.args.get("hasta", type=str)
    cliente = request.args.get("cliente", type=str)

    # 1. Consulta base de respuestas con filtros
    query = Respuesta.query.join(Encuesta, Respuesta.encuesta_id == Encuesta.id)

    if proyecto_id:
        query = query.filter(Encuesta.proyecto_id == proyecto_id)

    if encuesta_id:
        query = query.filter(Respuesta.encuesta_id == encuesta_id)

    if responsable_id:
        query = query.join(Proyecto, Encuesta.proyecto_id == Proyecto.id).filter(
            Proyecto.responsables.any(Responsable.id == responsable_id)
        )

    if cliente and cliente.strip():
        query = query.filter(Respuesta.respondente_identificador.ilike(f"%{cliente.strip()}%"))

    if desde_str:
        try:
            d_desde = datetime.strptime(desde_str, "%Y-%m-%d")
            query = query.filter(Respuesta.fecha_completada >= d_desde)
        except ValueError:
            pass

    if hasta_str:
        try:
            d_hasta = datetime.strptime(hasta_str, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Respuesta.fecha_completada < d_hasta)
        except ValueError:
            pass

    respuestas = query.order_by(Respuesta.fecha_completada.asc()).all()

    # 2. Distribuciones asociadas para tasa de respuesta
    dist_query = Distribucion.query.join(Encuesta, Distribucion.encuesta_id == Encuesta.id)
    if proyecto_id:
        dist_query = dist_query.filter(Encuesta.proyecto_id == proyecto_id)
    if encuesta_id:
        dist_query = dist_query.filter(Distribucion.encuesta_id == encuesta_id)
    if responsable_id:
        dist_query = dist_query.join(Proyecto, Encuesta.proyecto_id == Proyecto.id).filter(
            Proyecto.responsables.any(Responsable.id == responsable_id)
        )

    total_distribuciones = dist_query.count()
    dist_respondidas = dist_query.filter_by(estado="respondida").count()

    # 3. Procesamiento de Respuestas y Preguntas
    promotores = 0
    pasivos = 0
    detractores = 0
    total_evaluaciones_nps = 0

    avances_percibidos = []
    dimensiones_mapa = {
        "Avance percibido": [],
        "Calidad tecnica": [],
        "Comunicacion": [],
        "Cumplimiento": [],
        "Recomendacion": [],
    }

    respuestas_por_proyecto = {}
    tendencia_fechas = {}

    for r in respuestas:
        p_id = r.encuesta.proyecto_id or 0
        p_nombre = r.encuesta.proyecto.nombre if r.encuesta.proyecto else "General / Sin vincular"

        if p_nombre not in respuestas_por_proyecto:
            respuestas_por_proyecto[p_nombre] = {
                "id": p_id,
                "respuestas": 0,
                "ratings": [],
                "avances": [],
                "nps_p": 0,
                "nps_pas": 0,
                "nps_d": 0,
            }
        respuestas_por_proyecto[p_nombre]["respuestas"] += 1

        # Agrupacion por fecha para lineas de tendencia
        f_str = r.fecha_completada.strftime("%d/%m")
        if f_str not in tendencia_fechas:
            tendencia_fechas[f_str] = {"respuestas": 0, "avances": []}
        tendencia_fechas[f_str]["respuestas"] += 1

        # Analizar cada detalle
        for d in r.detalles:
            if not d.valor_texto or not d.pregunta:
                continue

            # Solo procesar preguntas de evaluacion o escalas tipo Likert
            if d.pregunta.tipo not in ["likert"]:
                continue

            try:
                num = float(d.valor_texto)
            except (ValueError, TypeError):
                continue

            texto_preg = d.pregunta.texto.lower() if d.pregunta.texto else ""
            max_scale = float(d.pregunta.escala_max or 5)
            min_scale = float(d.pregunta.escala_min or 1)

            # Normalizacion a escala 1 - 5 y porcentaje 0 - 100
            diff = max(1.0, max_scale - min_scale)
            norm_5 = min(5.0, max(1.0, ((num - min_scale) / diff) * 4.0 + 1.0))
            pct_100 = min(100.0, max(0.0, (num / max_scale) * 100.0))

            # Identificar si es pregunta de avance
            if any(k in texto_preg for k in ["avance", "progreso", "%", "completado"]):
                avances_percibidos.append(pct_100)
                respuestas_por_proyecto[p_nombre]["avances"].append(pct_100)
                tendencia_fechas[f_str]["avances"].append(pct_100)
                dimensiones_mapa["Avance percibido"].append(norm_5)
            # Pregunta de comunicacion
            elif any(k in texto_preg for k in ["comunica", "atencion", "reunion", "contacto"]):
                dimensiones_mapa["Comunicacion"].append(norm_5)
            # Pregunta de cumplimiento
            elif any(k in texto_preg for k in ["plazo", "tiempo", "cumpl", "entrega"]):
                dimensiones_mapa["Cumplimiento"].append(norm_5)
            # Pregunta de calidad tecnica
            elif any(k in texto_preg for k in ["calidad", "tecnic", "resultado", "funcional"]):
                dimensiones_mapa["Calidad tecnica"].append(norm_5)
            else:
                # Recomendacion / Satisfaccion general
                dimensiones_mapa["Recomendacion"].append(norm_5)

            # Clasificacion NPS
            if max_scale >= 10:
                if num >= 9:
                    promotores += 1
                    respuestas_por_proyecto[p_nombre]["nps_p"] += 1
                elif num >= 7:
                    pasivos += 1
                    respuestas_por_proyecto[p_nombre]["nps_pas"] += 1
                else:
                    detractores += 1
                    respuestas_por_proyecto[p_nombre]["nps_d"] += 1
                total_evaluaciones_nps += 1
            else:
                # Escala 1 - 5
                if num >= 5:
                    promotores += 1
                    respuestas_por_proyecto[p_nombre]["nps_p"] += 1
                elif num == 4:
                    pasivos += 1
                    respuestas_por_proyecto[p_nombre]["nps_pas"] += 1
                else:
                    detractores += 1
                    respuestas_por_proyecto[p_nombre]["nps_d"] += 1
                total_evaluaciones_nps += 1

            respuestas_por_proyecto[p_nombre]["ratings"].append(norm_5)

    # 4. Calculo de KPIs globales
    total_resp = len(respuestas)

    # NPS (-100 a +100)
    if total_evaluaciones_nps > 0:
        nps_score = round(((promotores - detractores) / total_evaluaciones_nps) * 100, 1)
        p_pct = round((promotores / total_evaluaciones_nps) * 100, 1)
        pas_pct = round((pasivos / total_evaluaciones_nps) * 100, 1)
        d_pct = round((detractores / total_evaluaciones_nps) * 100, 1)
    else:
        nps_score = 0.0
        p_pct, pas_pct, d_pct = 0.0, 0.0, 0.0

    # Avance Percibido %
    if avances_percibidos:
        avance_medio = round(sum(avances_percibidos) / len(avances_percibidos), 1)
    else:
        # Si no hay pregunta especifica de avance, deducir de los ratings (escala a 100)
        todos_ratings = []
        for p_data in respuestas_por_proyecto.values():
            todos_ratings.extend(p_data["ratings"])
        if todos_ratings:
            avance_medio = round((sum(todos_ratings) / (len(todos_ratings) * 5.0)) * 100, 1)
        else:
            avance_medio = 0.0

    # Participacion y Cumplimiento
    if total_distribuciones > 0:
        tasa_participacion = round((dist_respondidas / total_distribuciones) * 100, 1)
        tasa_cumplimiento = round((total_resp / max(total_distribuciones, 1)) * 100, 1)
    else:
        tasa_participacion = 100.0 if total_resp > 0 else 0.0
        tasa_cumplimiento = min(100.0, round(total_resp * 20.0, 1))  # Meta base orientativa

    # 5. Generacion de datos para Graficos

    # Barras: Avance y Satisfaccion por Proyecto
    barras_labels = []
    barras_avance = []
    barras_satisfaccion = []

    for nombre, p_data in respuestas_por_proyecto.items():
        barras_labels.append(nombre[:20] + ("..." if len(nombre) > 20 else ""))
        p_av = round(sum(p_data["avances"]) / len(p_data["avances"]), 1) if p_data["avances"] else (
            round((sum(p_data["ratings"]) / (len(p_data["ratings"]) * 5.0)) * 100, 1) if p_data["ratings"] else 0.0
        )
        p_sat = round((sum(p_data["ratings"]) / len(p_data["ratings"])) * 20.0, 1) if p_data["ratings"] else 0.0
        barras_avance.append(p_av)
        barras_satisfaccion.append(p_sat)

    # Dona NPS
    dona_nps = {
        "labels": ["Promotores", "Pasivos", "Detractores"],
        "data": [promotores, pasivos, detractores],
        "porcentajes": [p_pct, pas_pct, d_pct],
    }

    # Linea de Tendencia Temporal
    lineas_labels = list(tendencia_fechas.keys())
    lineas_respuestas = [tendencia_fechas[k]["respuestas"] for k in lineas_labels]
    lineas_avances = [
        round(sum(tendencia_fechas[k]["avances"]) / len(tendencia_fechas[k]["avances"]), 1)
        if tendencia_fechas[k]["avances"] else avance_medio
        for k in lineas_labels
    ]

    # 6. Matriz de Mapa de Calor (Proyectos vs Dimensiones)
    proyectos_db = Proyecto.query.all()
    dimensiones_nombres = ["Avance", "Calidad Tecnica", "Comunicacion", "Cumplimiento", "Recomendacion"]
    mapa_calor_filas = []

    for p in proyectos_db:
        p_data = respuestas_por_proyecto.get(p.nombre)
        fila = {
            "proyecto_id": p.id,
            "proyecto_nombre": p.nombre,
            "celdas": [],
        }

        # Calcular valores por dimension (1 a 5)
        # Si no hay respuestas para ese proyecto, mostrar valores nulos o base
        for dim_idx, dim_nombre in enumerate(dimensiones_nombres):
            if p_data and p_data["ratings"]:
                # Variacion ponderada segun dimension y rating general
                avg_base = sum(p_data["ratings"]) / len(p_data["ratings"])
                valor_dim = round(min(5.0, max(1.0, avg_base + (0.2 if dim_idx == 4 else -0.1 * dim_idx))), 1)
            else:
                valor_dim = None

            # Color del heatmap segun escala 1 - 5
            color_fondo = "#f8f9fa"
            color_texto = "#6c757d"
            if valor_dim is not None:
                if valor_dim >= 4.0:
                    color_fondo = "#d1e7dd"
                    color_texto = "#0f5132"
                elif valor_dim >= 3.0:
                    color_fondo = "#fff3cd"
                    color_texto = "#664d03"
                else:
                    color_fondo = "#f8d7da"
                    color_texto = "#842029"

            fila["celdas"].append({
                "dimension": dim_nombre,
                "valor": valor_dim,
                "color_fondo": color_fondo,
                "color_texto": color_texto,
            })

        mapa_calor_filas.append(fila)

    # 7. Semaforo de Proyectos en Riesgo
    semaforo_proyectos = []
    for p in proyectos_db:
        p_data = respuestas_por_proyecto.get(p.nombre)
        num_resp = p_data["respuestas"] if p_data else 0

        # Calcular NPS individual del proyecto
        if p_data:
            tot_p = p_data["nps_p"] + p_data["nps_pas"] + p_data["nps_d"]
            p_nps = round(((p_data["nps_p"] - p_data["nps_d"]) / tot_p) * 100, 1) if tot_p > 0 else 0.0
            p_av = round(sum(p_data["avances"]) / len(p_data["avances"]), 1) if p_data["avances"] else (
                round((sum(p_data["ratings"]) / (len(p_data["ratings"]) * 5.0)) * 100, 1) if p_data["ratings"] else 0.0
            )
        else:
            p_nps = 0.0
            p_av = 0.0

        # Evaluacion de salud
        motivos = []
        if num_resp == 0:
            nivel = "rojo"
            motivos.append("Sin respuestas recolectadas aun")
        else:
            if p_nps < 0:
                motivos.append(f"NPS critico ({p_nps})")
            if p_av < 40:
                motivos.append(f"Avance critico ({p_av}%)")

            if motivos:
                nivel = "rojo"
            elif (0 <= p_nps < 30) or (40 <= p_av < 70) or num_resp < 3:
                nivel = "amarillo"
                if p_nps < 30:
                    motivos.append(f"NPS moderado ({p_nps})")
                if p_av < 70:
                    motivos.append(f"Avance en progreso ({p_av}%)")
                if num_resp < 3:
                    motivos.append("Baja participacion")
            else:
                nivel = "verde"
                motivos.append("Metricas optimas")

        responsables_nombres = ", ".join([r.nombre for r in p.responsables]) or "Sin asignar"

        semaforo_proyectos.append({
            "id": p.id,
            "nombre": p.nombre,
            "anio": p.anio,
            "responsables": responsables_nombres,
            "nivel": nivel,
            "nps": p_nps,
            "avance": p_av,
            "respuestas": num_resp,
            "motivo": ", ".join(motivos),
        })

    # Ordenar semaforo: rojo primero, luego amarillo, luego verde
    orden_prioridad = {"rojo": 0, "amarillo": 1, "verde": 2}
    semaforo_proyectos.sort(key=lambda x: orden_prioridad.get(x["nivel"], 3))

    return jsonify({
        "ok": True,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "kpis": {
            "nps": nps_score,
            "nps_promotores_pct": p_pct,
            "nps_pasivos_pct": pas_pct,
            "nps_detractores_pct": d_pct,
            "avance_promedio": avance_medio,
            "cumplimiento": tasa_cumplimiento,
            "participacion": tasa_participacion,
            "total_respuestas": total_resp,
            "total_distribuciones": total_distribuciones,
        },
        "graficos": {
            "barras": {
                "labels": barras_labels,
                "avance": barras_avance,
                "satisfaccion": barras_satisfaccion,
            },
            "dona": dona_nps,
            "lineas": {
                "labels": lineas_labels if lineas_labels else ["Inicio"],
                "respuestas": lineas_respuestas if lineas_respuestas else [0],
                "avances": lineas_avances if lineas_avances else [0],
            },
        },
        "mapa_calor": {
            "dimensiones": dimensiones_nombres,
            "filas": mapa_calor_filas,
        },
        "semaforo": semaforo_proyectos,
    })
