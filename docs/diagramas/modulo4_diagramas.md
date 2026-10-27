# Modulo 4: Dashboard Dinamico - Diagramas y Especificacion Tecnica

## 1. Descripcion del Modulo

El **Modulo 4 - Dashboard Dinamico** consolida y visualiza en tiempo real los datos recopilados por las encuestas vinculadas a los proyectos de 7mo ano. Proporciona a docentes, directivos y lideres tecnicos una herramienta analitica centralizada para evaluar el desempeno, avance y percepcion de stakeholders mediante indicadores clave y alertas tempranas.

### Componentes Clave:
1. **KPIs Centrales:**
   - **NPS (Net Promoter Score):** Indice de recomendacion calculado a partir de promotores (% puntuaciones 9-10 o 5/5) menos detractores (% puntuaciones 1-6 o 1-2/5).
   - **% de Avance Percibido:** Promedio de progreso estimado por los participantes en encuestas de evaluacion continua.
   - **Tasa de Cumplimiento:** Porcentaje de encuestas respondidas frente a la meta objetivo del proyecto.
   - **Tasa de Participacion:** Porcentaje de respuestas registradas sobre el total de distribuciones enviadas.
2. **Filtros Dinamicos (Multicriterio sin recarga de pagina):**
   - Proyecto especifico o vista global.
   - Rango de fechas (desde / hasta).
   - Responsable asignado.
   - Estado de encuesta y tipo de instrumento.
3. **Visualizaciones:**
   - **Grafico de Barras:** Comparativa de avance y satisfaccion por proyecto.
   - **Grafico de Torta / Dona:** Distribucion de segmentos NPS (Promotores, Pasivos, Detractores).
   - **Grafico de Lineas de Tendencia:** Evolucion temporal de participacion y percepcion a lo largo de las semanas.
   - **Mapa de Calor (Heatmap Matriz):** Desglose de satisfaccion/percepcion por proyecto vs. dimensiones clave (comunicacion, cumplimiento tecnico, organizacion).
   - **Semaforo de Proyectos en Riesgo:** Clasificacion automatica en tres niveles (Verde: Saludable, Amarillo: Alerta, Rojo: Critico) segun umbrales de NPS, avance y respuesta.
4. **Actualizacion en Tiempo Real:**
   - Endpoint `/api/dashboard/datos` con respuesta JSON.
   - Mecanismo de refresco automatico en cliente (polling configurable) e indicador de sincronizacion en vivo.

---

## 2. Diagrama de Casos de Uso (Global y Modulo 4)

```mermaid
flowchart LR
    subgraph Actores
        Admin["Administrador / Lider"]
        Stakeholder["Participante / Evaluador"]
    end

    subgraph Modulo1["Modulo 1: Gestion de Proyectos"]
        CU01["CU01: ABM de Proyectos"]
        CU02["CU02: ABM de Responsables Multiples"]
    end

    subgraph Modulo2["Modulo 2: Constructor de Encuestas"]
        CU03["CU03: Disenar Encuesta Drag and Drop"]
        CU04["CU04: Configurar Reglas Condicionales"]
    end

    subgraph Modulo3["Modulo 3: Distribucion"]
        CU05["CU05: Envio por Link Unico, QR y Email"]
        CU06["CU06: Responder Encuesta con Anonimato"]
    end

    subgraph Modulo4["Modulo 4: Dashboard Dinamico"]
        CU07["CU07: Visualizar Dashboard Ejecutivo"]
        CU08["CU08: Filtrar por Proyecto, Fecha y Responsable"]
        CU09["CU09: Analizar KPIs (NPS, Avance, Cumplimiento, Participacion)"]
        CU10["CU10: Consultar Graficos de Tendencia, Barras y Distribucion"]
        CU11["CU11: Explorar Mapa de Calor de Satisfaccion"]
        CU12["CU12: Monitorear Semaforo de Proyectos en Riesgo"]
        CU13["CU13: Activar Actualizacion en Tiempo Real"]
    end

    Admin --> CU01
    Admin --> CU02
    Admin --> CU03
    Admin --> CU04
    Admin --> CU05
    Admin --> CU07
    Admin --> CU08
    Admin --> CU09
    Admin --> CU10
    Admin --> CU11
    Admin --> CU12
    Admin --> CU13

    Stakeholder --> CU06
    CU06 -.->|Genera datos para| CU09
```

---

## 3. Diagrama de Flujo: Operacion del Dashboard Dinamico

```mermaid
flowchart TD
    Inicio([Acceso a /dashboard]) --> CargarEstructura[Cargar vista HTML del Dashboard]
    CargarEstructura --> IniciarFiltros[Poblar filtros: Proyectos, Responsables, Rangos]
    IniciarFiltros --> SolicitarDatos[Peticion AJAX a /api/dashboard/datos]

    subgraph BackendAPI["Backend: routes/dashboard.py"]
        SolicitarDatos --> LeerParametros[Leer parametros de filtro: proyecto_id, responsable_id, fechas]
        LeerParametros --> ConsultaDB[Consultar Respuestas y Proyectos en DB]
        ConsultaDB --> CalcKPIs[Calcular KPIs: NPS, Avance Promedio, Tasa Respuesta, Cumplimiento]
        CalcKPIs --> CalcSeries[Generar series de datos para graficos temporales y categorias]
        CalcSeries --> GenerarMatriz[Calcular matriz para Mapa de Calor]
        GenerarMatriz --> EvaluarRiesgo[Evaluar reglas de riesgo para Semaforo]
        EvaluarRiesgo --> RetornarJSON[Responder payload JSON con estado 200]
    end

    RetornarJSON --> RenderCliente[Frontend: procesar JSON recibido]

    subgraph FrontendRender["Renderizado Reactivo"]
        RenderCliente --> ActualizarKPIs[Pintar tarjetas de KPI con variacion]
        ActualizarKPIs --> RenderGraficos[Actualizar instancias de Chart.js: Barras, Torta, Lineas]
        RenderGraficos --> RenderHeatmap[Pintar celdas de matriz Mapa de Calor con gradiente CSS]
        RenderHeatmap --> RenderSemaforo[Pintar lista y badges de proyectos en Verde/Amarillo/Rojo]
    end

    RenderSemaforo --> EsperarAccion{Evento del Usuario}

    EsperarAccion -->|Cambia filtro en formulario| SolicitarDatos
    EsperarAccion -->|Disparo de temporizador automatico| SolicitarDatos
    EsperarAccion -->|Clic en tarjeta de proyecto en riesgo| FiltrarProyectoDirecto[Aplicar filtro del proyecto y actualizar]
    FiltrarProyectoDirecto --> SolicitarDatos
    EsperarAccion -->|Salir| Fin([Fin de sesion])
```

---

## 4. Matriz de Clasificacion de Riesgo (Semaforo de Proyectos)

El sistema evaluara automaticamente la salud de cada proyecto activo segun la siguiente logica:

| Nivel de Riesgo | Color | Criterios de Evaluacion | Accion Sugerida |
| :--- | :--- | :--- | :--- |
| **Normal / Saludable** | Verde | NPS >= +30, Avance percibido >= 70%, Tasa respuesta >= 60% | Mantener plan de trabajo habitual. |
| **Atencion / Alerta** | Amarillo | NPS entre 0 y +29, Avance entre 40% y 69%, o Respuesta 35%-59% | Enviar recordatorios y revisar desvio con responsables. |
| **Critico / En Riesgo** | Rojo | NPS < 0, Avance percibido < 40%, o Tasa respuesta < 35% | Reunion urgente con lideres de proyecto y docentes. |

---

## 5. Endpoints y Estructura a Desarrollar

- **Vista Principal:** `routes/dashboard.py` -> `GET /dashboard` (plantilla `templates/dashboard/index.html`).
- **API de Metricas:** `GET /api/dashboard/datos` (soporta query params: `proyecto_id`, `responsable_id`, `desde`, `hasta`, `tipo_encuesta`).
- **Librerias Frontend:** `Chart.js` (cargado via CDN oficial, sin dependencias pesadas adicionales).

