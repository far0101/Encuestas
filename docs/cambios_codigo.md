# Registro de Modificaciones y Componentes Base

Este archivo recopila las modificaciones basicas y el proposito de cada componente del codigo fuente para referencia tecnica y prevencion de errores.

---

## Modulo 1: Gestion de Proyectos
- **Modelos:**
  - `models.py:Responsable`: Entidad para docentes y lideres de proyecto con validacion de email unico.
  - `models.py:Proyecto`: Entidad central con relacion al responsable, estado (`activo`, `finalizado`, `suspendido`) y fechas.
- **Rutas:**
  - `routes/proyectos.py`: CRUD de proyectos, filtros por ano y estado, proteccion contra borrado accidental.
  - `routes/responsables.py`: CRUD de responsables, bloqueo de eliminacion si posee proyectos asociados.
- **Vistas:**
  - `templates/proyectos/`: `list.html`, `form.html`, `detail.html`.
  - `templates/responsables/`: `list.html`, `form.html`.

---

## Modulo 2: Constructor de Encuestas
- **Modelos:**
  - `models.py:Encuesta`: Soporte para estados (`borrador`, `publicada`, `cerrada`), bandera de anonimato y modo plantilla.
  - `models.py:Pregunta`: 6 tipos de preguntas (texto corto, texto largo, opcion multiple, checkboxes, escala Likert, desplegable) con orden y opciones serializadas en JSON.
  - `models.py:ReglaCondicional`: Motor de reglas (`pregunta_origen`, `valor_condicion`, `pregunta_destino`, `accion`).
- **Rutas:**
  - `routes/encuestas.py`: Creacion de encuestas, API `/guardar` para sincronizacion completa del estado del constructor en JSON, duplicacion desde plantilla y previsualizacion.
- **Vistas:**
  - `templates/encuestas/editor.html`: Constructor visual drag & drop (HTML5 API + SortableJS) con configuracion inline y modal de reglas.
  - `templates/encuestas/preview.html`: Evaluador de reglas condicionales en JavaScript del lado del cliente.

---

## Modulo 3: Distribucion y Recoleccion
- **Modelos:**
  - `models.py:Distribucion`: Registro de enlaces unicos tokenizados (`secrets.token_urlsafe`), destinatario, estado (`pendiente`, `respondida`), fechas de envio y contadores de recordatorios.
  - `models.py:Respuesta`: Cabecera de la sesion de respuesta. Si la encuesta es anonima, `distribucion_id` se almacena como `NULL` y el identificador se fija en `Anonimo` para garantizar el anonimato estricto.
  - `models.py:RespuestaDetalle`: Valores individuales capturados por pregunta en formato texto o JSON para selecciones multiples.
- **Servicios:**
  - `services/email_service.py`: Generador de plantillas de correo con deteccion automatica de configuracion SMTP real o registro de log local en `envios_email.log`.
- **Rutas:**
  - `routes/distribucion.py`:
    - `GET /distribucion/<id>`: Panel de control de envios, estadisticas de tasa de respuesta, enlaces publicos y lote de destinatarios.
    - `GET /distribucion/<id>/qr`: Generacion directa en streaming de codigos QR vectoriales en formato SVG.
    - `POST /distribucion/<id>/agregar`: Carga individual o por lote de emails con generacion automatica de tokens unicos.
    - `POST /distribucion/<id>/enviar_invitaciones`: Disparo masivo de correos de invitacion a destinatarios pendientes.
    - `POST /distribucion/<id>/enviar_recordatorios`: Disparo de recordatorios a pendientes incrementando contador de intentos.
  - `routes/respuestas.py`:
    - `GET/POST /responder/publica/<id>`: Formulario abierto accesible por enlace general o QR.
    - `GET/POST /responder/<token>`: Acceso controlado por token unico, validacion de un solo uso, registro de respuesta y resolucion en vivo de logica condicional.
- **Vistas:**
  - `templates/distribucion/panel.html`: Panel administrativo de distribucion y monitoreo.
  - `templates/respuestas/formulario.html`: Formulario responsivo para el participante.
  - `templates/respuestas/exito.html`: Pantalla de confirmacion de envio.
  - `templates/respuestas/error.html`: Pantalla informativa ante tokens invalidos, respondidos o encuestas cerradas.

---

## Modulo 4: Dashboard Dinamico
- **Rutas y Controladores:**
  - `routes/dashboard.py`:
    - `GET /dashboard`: Vista ejecutiva y analitica centralizada.
    - `GET /dashboard/api/datos`: Endpoint REST asincrono para consulta de metricas en tiempo real con filtros por proyecto, responsable, encuesta, fechas y participante.
- **Logica de Analitica y KPIs:**
  - Calculo de NPS (Net Promoter Score) segun segmentacion estandar (Promotores, Pasivos, Detractores).
  - Normalizacion del % de avance percibido y tasas de cumplimiento y participacion.
  - Generacion de series temporales para graficos de lineas y comparativa de barras (Chart.js).
  - Evaluacion matricial de percepcion por dimensiones para el Mapa de Calor (Heatmap).
  - Clasificacion automatica de proyectos en riesgo para el Semaforo (Verde, Amarillo, Rojo).
- **Vistas:**
  - `templates/dashboard/index.html`: Dashboard reactivo con filtros instantaneos, temporizador de refresco automatico configurable (15s, 30s, 60s) e integracion con Chart.js.

---

## Ajustes y Correcciones Transversales
- **Multiples Responsables por Proyecto:**
  - `models.py:proyecto_responsables`: Tabla intermedia muchos-a-muchos.
  - `models.py:Proyecto.responsables`: Relacion secundaria `Responsable` con soporte retrocompatible.
  - `routes/proyectos.py`: `crear()` y `editar()` reciben lista `responsable_ids` y asignan la coleccion al proyecto.
  - `templates/proyectos/form.html`: Selector con checkboxes dinamicos para seleccionar uno o multiples responsables.
  - `templates/proyectos/list.html`, `detail.html`, `index.html`: Visualizacion de multiples responsables separados por coma o lista.
- **Resolucion de Bloqueo en Drag & Drop (Cursor congelado):**
  - Desactivacion del motor nativo HTML5 (`draggable`) en los elementos de la paleta.
  - Implementacion de arrastre basado en eventos directos del mouse (`mousedown`, `mousemove`, `mouseup`) con indicador flotante e insercion tanto por arrastre como por clic directo.
- **Resolucion de Diagnosticos del Linter en Editor (templates/encuestas/editor.html):**
  - Desacoplamiento de variables de Jinja2 del bloque `<script>` de JavaScript.
  - Implementacion de contenedores `<input type="hidden">` y etiquetas `<script type="application/json">` para la inyeccion de datos iniciales (`ENCUESTA_ID`, `preguntas`, `reglas`, titulos y estados).
  - Eliminacion de sintaxis templating embebida en codigo JS, garantizando 0 errores y advertencias en el analizador estatico de codigo.



