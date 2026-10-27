# Modulo 2 - Constructor de Encuestas: Diagramas Previos

> [!IMPORTANT]
> Confirmar este documento antes de iniciar el desarrollo del Modulo 2.

---

## 1. Diagrama de Casos de Uso - Acumulado (Modulos 1 y 2)

```mermaid
graph TD
    Admin(["Administrador"])

    subgraph M1["Modulo 1 - Gestion de Proyectos"]
        UC1["Crear Proyecto"]
        UC2["Listar Proyectos"]
        UC3["Editar Proyecto"]
        UC4["Eliminar Proyecto"]
        UC5["Ver detalle de Proyecto"]
        UC6["Crear Responsable"]
        UC7["Listar Responsables"]
        UC8["Editar Responsable"]
        UC9["Eliminar Responsable"]
        UC10["Asignar Responsable a Proyecto"]
    end

    subgraph M2["Modulo 2 - Constructor de Encuestas"]
        UC11["Crear Encuesta"]
        UC12["Agregar Pregunta via Drag and Drop"]
        UC13["Configurar logica condicional"]
        UC14["Guardar como plantilla"]
        UC15["Usar plantilla existente"]
        UC16["Editar Encuesta"]
        UC17["Eliminar Encuesta"]
        UC18["Vincular Encuesta a Proyecto"]
        UC19["Previsualizar Encuesta"]
        UC20["Configurar anonimato"]
    end

    Admin --> UC1
    Admin --> UC2
    Admin --> UC3
    Admin --> UC4
    Admin --> UC5
    Admin --> UC6
    Admin --> UC7
    Admin --> UC8
    Admin --> UC9
    Admin --> UC10

    Admin --> UC11
    Admin --> UC12
    Admin --> UC13
    Admin --> UC14
    Admin --> UC15
    Admin --> UC16
    Admin --> UC17
    Admin --> UC18
    Admin --> UC19
    Admin --> UC20

    UC11 -.->|include| UC12
    UC11 -.->|include| UC18
    UC11 -.->|include| UC20
    UC15 -.->|extends| UC11
    UC12 -.->|extends| UC13
    UC19 -.->|include| UC11
```

---

## 2. Diagrama de Flujo - Crear Encuesta

```mermaid
flowchart TD
    START([Inicio]) --> PANEL[Panel de Encuestas]
    PANEL --> ACCION{Accion}

    ACCION -->|Nueva encuesta desde cero| FORM_E[Formulario: datos basicos\nTitulo, Descripcion, Proyecto, Anonimato]
    ACCION -->|Usar plantilla| SEL_PLANTILLA[Seleccionar plantilla]
    SEL_PLANTILLA --> CLONAR[Clonar plantilla como nueva encuesta]
    CLONAR --> EDITOR

    FORM_E --> VALID_E{Datos validos?}
    VALID_E -->|No| ERR_E[Mostrar errores]
    ERR_E --> FORM_E
    VALID_E -->|Si| GUARDAR_BASE[Guardar encuesta base en DB]
    GUARDAR_BASE --> EDITOR

    EDITOR["Editor visual\n(lista de preguntas + panel lateral de tipos)"]

    EDITOR --> DRAG[Arrastrar tipo de pregunta al area]
    DRAG --> CONFIG_P[Configurar pregunta:\nTexto, opciones, obligatoria?]
    CONFIG_P --> COND{Agregar logica condicional?}
    COND -->|Si| CONF_COND[Definir regla:\nSi respuesta X -> mostrar/ocultar pregunta Y]
    CONF_COND --> GUARDAR_P[Guardar pregunta]
    COND -->|No| GUARDAR_P
    GUARDAR_P --> MAS{Agregar mas preguntas?}
    MAS -->|Si| DRAG
    MAS -->|No| OPCIONES

    OPCIONES{Que hacer?}
    OPCIONES -->|Previsualizar| PREVIEW[Vista previa de la encuesta]
    PREVIEW --> OPCIONES
    OPCIONES -->|Guardar como plantilla| GUARDAR_TPL[Guardar como plantilla reutilizable]
    GUARDAR_TPL --> OPCIONES
    OPCIONES -->|Finalizar| PANEL
```

---

## 3. Diagrama de Flujo - Tipos de Pregunta y Logica Condicional

```mermaid
flowchart LR
    TIPOS["Tipos de pregunta disponibles"]

    TIPOS --> T1["Texto corto\n(input texto)"]
    TIPOS --> T2["Texto largo\n(textarea)"]
    TIPOS --> T3["Opcion multiple\n(radio buttons)"]
    TIPOS --> T4["Casillas de verificacion\n(checkboxes)"]
    TIPOS --> T5["Escala Likert\n(1 a 5 / 1 a 10)"]
    TIPOS --> T6["Desplegable\n(select)"]

    T3 --> COND_POSIBLE["Puede tener\nlogica condicional"]
    T4 --> COND_POSIBLE
    T6 --> COND_POSIBLE

    COND_POSIBLE --> REGLA["Regla:\nSi [pregunta X]\ntiene valor [opcion Y]\nentonces [mostrar / ocultar]\n[pregunta Z]"]
```

---

## 4. Modelo de Datos - Modulo 2

### Nuevas entidades

**`Encuesta`**
| Campo | Tipo | Descripcion |
|---|---|---|
| id | INT PK | Identificador |
| titulo | VARCHAR(200) | Titulo de la encuesta |
| descripcion | TEXT | Descripcion opcional |
| proyecto_id | INT FK | Proyecto al que pertenece |
| anonima | BOOLEAN | Si las respuestas son anonimas |
| es_plantilla | BOOLEAN | Si puede usarse como plantilla |
| nombre_plantilla | VARCHAR(100) | Nombre al guardar como plantilla |
| estado | ENUM | borrador / publicada / cerrada |
| created_at | DATETIME | |
| updated_at | DATETIME | |

**`Pregunta`**
| Campo | Tipo | Descripcion |
|---|---|---|
| id | INT PK | Identificador |
| encuesta_id | INT FK | Encuesta a la que pertenece |
| orden | INT | Posicion en el formulario |
| tipo | ENUM | texto_corto / texto_largo / opcion_multiple / checkboxes / likert / desplegable |
| texto | TEXT | Texto de la pregunta |
| obligatoria | BOOLEAN | Si es requerida |
| opciones | TEXT | JSON con las opciones (para tipos multiple/check/desplegable) |
| escala_min | INT | Para Likert: valor minimo |
| escala_max | INT | Para Likert: valor maximo |

**`ReglaCondicional`**
| Campo | Tipo | Descripcion |
|---|---|---|
| id | INT PK | Identificador |
| encuesta_id | INT FK | Encuesta contenedora |
| pregunta_origen_id | INT FK | Pregunta que dispara la regla |
| valor_condicion | VARCHAR(200) | Valor que activa la regla |
| pregunta_destino_id | INT FK | Pregunta afectada |
| accion | ENUM | mostrar / ocultar |

---

## 5. Decisiones de Diseno

| Aspecto | Decision | Justificacion |
|---|---|---|
| Drag and Drop | HTML5 Drag and Drop API nativa | Sin dependencias extra, compatible con Bootstrap |
| Almacenamiento de opciones | JSON en columna TEXT | Flexible, evita tabla extra para opciones |
| Previa de encuesta | Renderizado en la misma pagina en modal | Rapido, sin ruta extra |
| Plantillas | Flag `es_plantilla` en la misma tabla `Encuesta` | Simple, evita duplicar estructura |
| Logica condicional | Tabla separada `ReglaCondicional` | Limpio, extensible, facil de consultar |

---

> [!NOTE]
> El diagrama de casos de uso se seguira actualizando con los Modulos 3 al 5.
> Confirmar este documento para iniciar el desarrollo del Modulo 2.
