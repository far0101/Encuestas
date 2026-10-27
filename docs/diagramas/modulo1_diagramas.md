# Modulo 1 - Gestion de Proyectos: Diagramas Previos

> [!IMPORTANT]
> Estos diagramas deben ser confirmados por el usuario antes de iniciar el desarrollo del modulo.

---

## 1. Diagrama de Casos de Uso - Modulo 1

```mermaid
graph TD
    Admin(["Administrador"])
    
    subgraph Sistema["Sistema - Gestion de Proyectos"]
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

    UC1 -.->|include| UC10
    UC5 -.->|include| UC2
```

---

## 2. Diagrama de Flujo - ABM Proyectos

```mermaid
flowchart TD
    START([Inicio]) --> LOGIN[Usuario accede al sistema]
    LOGIN --> DASH[Dashboard / Lista de Proyectos]

    DASH --> ACCION{Accion seleccionada}

    %% ALTA
    ACCION -->|Nuevo Proyecto| FORM_CREAR[Formulario: Crear Proyecto]
    FORM_CREAR --> VALID_C{Datos validos?}
    VALID_C -->|No| ERR_C[Mostrar errores de validacion]
    ERR_C --> FORM_CREAR
    VALID_C -->|Si| GUARDAR[Guardar en base de datos]
    GUARDAR --> OK_C[Mensaje: Proyecto creado correctamente]
    OK_C --> DASH

    %% BAJA
    ACCION -->|Eliminar Proyecto| CONFIRM{Confirmar eliminacion?}
    CONFIRM -->|No| DASH
    CONFIRM -->|Si| VERIFICAR{Tiene encuestas asociadas?}
    VERIFICAR -->|Si| BLOQUEO[Advertencia: No se puede eliminar]
    BLOQUEO --> DASH
    VERIFICAR -->|No| ELIMINAR[Eliminar de base de datos]
    ELIMINAR --> OK_D[Mensaje: Proyecto eliminado]
    OK_D --> DASH

    %% MODIFICACION
    ACCION -->|Editar Proyecto| FORM_EDITAR[Formulario: Editar Proyecto pre-cargado]
    FORM_EDITAR --> VALID_E{Datos validos?}
    VALID_E -->|No| ERR_E[Mostrar errores de validacion]
    ERR_E --> FORM_EDITAR
    VALID_E -->|Si| ACTUALIZAR[Actualizar en base de datos]
    ACTUALIZAR --> OK_E[Mensaje: Proyecto actualizado]
    OK_E --> DASH

    %% VER DETALLE
    ACCION -->|Ver detalle| DETALLE[Pantalla de detalle del Proyecto]
    DETALLE --> DASH
```

---

## 3. Diagrama de Flujo - ABM Responsables

```mermaid
flowchart TD
    START([Inicio]) --> PANEL[Panel de Responsables]

    PANEL --> ACCION{Accion seleccionada}

    %% ALTA
    ACCION -->|Nuevo Responsable| FORM_R[Formulario: Crear Responsable]
    FORM_R --> VALID_R{Datos validos?}
    VALID_R -->|No| ERR_R[Mostrar errores de validacion]
    ERR_R --> FORM_R
    VALID_R -->|Si| GUARD_R[Guardar en base de datos]
    GUARD_R --> OK_R[Mensaje: Responsable creado]
    OK_R --> PANEL

    %% BAJA
    ACCION -->|Eliminar Responsable| CONF_R{Confirmar eliminacion?}
    CONF_R -->|No| PANEL
    CONF_R -->|Si| CHECK_R{Tiene proyectos asignados?}
    CHECK_R -->|Si| BLOCK_R[Advertencia: Reasignar antes de eliminar]
    BLOCK_R --> PANEL
    CHECK_R -->|No| ELIM_R[Eliminar de base de datos]
    ELIM_R --> OK_DR[Mensaje: Responsable eliminado]
    OK_DR --> PANEL

    %% MODIFICACION
    ACCION -->|Editar Responsable| FORM_ER[Formulario: Editar Responsable pre-cargado]
    FORM_ER --> VALID_ER{Datos validos?}
    VALID_ER -->|No| ERR_ER[Mostrar errores de validacion]
    ERR_ER --> FORM_ER
    VALID_ER -->|Si| ACT_R[Actualizar en base de datos]
    ACT_R --> OK_ER[Mensaje: Responsable actualizado]
    OK_ER --> PANEL
```

---

## 4. Modelo de Datos - Modulo 1

### Entidad: `Proyecto`
| Campo | Tipo | Descripcion |
|---|---|---|
| `id` | INT PK | Identificador unico |
| `nombre` | VARCHAR(150) | Nombre del proyecto |
| `descripcion` | TEXT | Descripcion general |
| `anio` | INT | Año lectivo (ej: 2026) |
| `estado` | ENUM | `activo`, `finalizado`, `suspendido` |
| `fecha_inicio` | DATE | Fecha de inicio |
| `fecha_fin` | DATE | Fecha estimada de fin |
| `responsable_id` | INT FK | Referencia a Responsable |
| `created_at` | DATETIME | Registro de creacion |
| `updated_at` | DATETIME | Ultima modificacion |

### Entidad: `Responsable`
| Campo | Tipo | Descripcion |
|---|---|---|
| `id` | INT PK | Identificador unico |
| `nombre` | VARCHAR(100) | Nombre completo |
| `email` | VARCHAR(150) | Correo electronico (unico) |
| `rol` | VARCHAR(80) | Rol dentro del proyecto |
| `created_at` | DATETIME | Registro de creacion |

---

## 5. Stack Tecnologico Propuesto

| Capa | Tecnologia | Justificacion |
|---|---|---|
| Frontend | HTML5 + CSS3 (Vanilla) + JavaScript | Simple, sin dependencias de framework pesado |
| Backend | Python + Flask | Ligero, facil de desplegar, ideal para prototipo |
| Base de datos | SQLite (desarrollo) | Sin servidor adicional requerido |
| ORM | SQLAlchemy | Abstraccion de base de datos, migraciones sencillas |
| UI Componentes | Bootstrap 5 | Diseno responsivo profesional sin esfuerzo extra |

---

> [!NOTE]
> El diagrama de casos de uso se actualizara a medida que se integren los modulos 2 al 5.
> Confirmar este documento para proceder con el desarrollo del Modulo 1.
