"""
services/email_service.py
Servicio para envio y simulacion de correos electronicos y recordatorios.
"""
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

LOG_ENVIOS_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "envios_email.log")


def enviar_correo_encuesta(destinatario_email, destinatario_nombre, encuesta_titulo, url_encuesta, es_recordatorio=False):
    """
    Envia un correo de invitacion o recordatorio para responder una encuesta.
    Si hay configuracion SMTP en variables de entorno, intenta el envio real.
    De lo contrario, registra el envio en el archivo envios_email.log.
    """
    nombre = destinatario_nombre or "Estimado/a participante"
    tipo_texto = "Recordatorio:" if es_recordatorio else "Invitacion:"
    asunto = f"{tipo_texto} Encuesta sobre {encuesta_titulo}"

    cuerpo_texto = f"""Hola {nombre},

{"Le enviamos este recordatorio porque aun no hemos recibido su respuesta para la encuesta:" if es_recordatorio else "Ha sido invitado/a a responder la siguiente encuesta:"}
{encuesta_titulo}

Para completarla, por favor acceda al siguiente enlace unico y seguro:
{url_encuesta}

Su colaboracion es fundamental para la evaluacion y mejora continua de los proyectos.

Atentamente,
Equipo de Gestion de Proyectos
"""

    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")

    if smtp_host and smtp_port and smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = destinatario_email
            msg["Subject"] = asunto
            msg.attach(MIMEText(cuerpo_texto, "plain", "utf-8"))

            with smtplib.SMTP(smtp_host, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, destinatario_email, msg.as_string())

            registrar_log(destinatario_email, asunto, url_encuesta, "ENVIADO_SMTP")
            return True, "Correo enviado mediante servidor SMTP."
        except Exception as exc:
            registrar_log(destinatario_email, asunto, url_encuesta, f"ERROR_SMTP: {str(exc)}")
            return False, f"Fallo envio SMTP: {str(exc)}"

    # Modo simulado: se registra localmente
    registrar_log(destinatario_email, asunto, url_encuesta, "SIMULADO_LOCAL")
    return True, "Envio simulado registrado correctamente en el log del sistema."


def registrar_log(email, asunto, url, estado):
    """Guarda un registro legible del envio en el archivo de log."""
    linea = (
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
        f"ESTADO: {estado} | DESTINO: {email} | ASUNTO: {asunto} | LINK: {url}\n"
    )
    try:
        with open(LOG_ENVIOS_PATH, "a", encoding="utf-8") as f:
            f.write(linea)
    except Exception:
        pass


def obtener_ultimos_envios(limite=10):
    """Recupera los ultimos envios registrados para visualizacion rapida."""
    if not os.path.exists(LOG_ENVIOS_PATH):
        return []

    try:
        with open(LOG_ENVIOS_PATH, "r", encoding="utf-8") as f:
            lineas = f.readlines()
        return [l.strip() for l in lineas[-limite:] if l.strip()]
    except Exception:
        return []

