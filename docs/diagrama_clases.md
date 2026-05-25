# Diagrama de clases — Proyecto Mamaya Licencias

Este documento contiene el diagrama UML de clases del modelo de datos completo del proyecto.

## Modelos cubiertos

| App | Archivo físico | Modelos |
|---|---|---|
| **licencias** | `licencias/models.py` | `Tenant`, `Empresa`, `Proveedor`, `TipoLicencia`, `Licencia`, `Asignacion` |
| **empleados** | `empleados/models.py` | `GerenciaDivision`, `GerenciaArea`, `Unidad`, `Cargo`, `Empleado` |
| **user** | `user/infrastructure/models.py` | `AreaUsuario`, `PerfilUsuario` |
| **bitacora** | `bitacora/infrastructure/models.py` | `Bitacora` |
| **gestion_global** | `gestion_global/infrastructure/models.py` | *(sin modelos propios — re-exporta `Empresa`, `Tenant`, `GerenciaArea`, `GerenciaDivision`, `Unidad` desde licencias/empleados)* |
| Django builtin | `django.contrib.auth.models` | `User` (mostrado por relaciones desde `PerfilUsuario` y `Bitacora`) |

`bitacora/models.py` y `user/models.py` son re-exports de `infrastructure/models.py`; Django los necesita para autodiscovery de migraciones, pero los modelos físicos viven en `infrastructure/`.

---

## Notación

- Cada atributo se muestra como `+ nombre_campo : TipoDjango constraints`.
- **Constraints** (separados por coma, sin paréntesis para no romper el parser Mermaid):
  - `max_length=N`, `unique`, `null` (campo opcional `null=True`/`blank=True`), `default=...`, `choices=a|b|c`.
  - En relaciones: `ForeignKey`/`OneToOneField` + modelo destino + `on_delete` (`CASCADE`/`SET_NULL`/`PROTECT`) + `related_name` si aplica.
- Los **métodos y properties** llevan `()` y su tipo de retorno: `+ nombre_metodo() Tipo`.
- Las flechas muestran la **cardinalidad** y la **etiqueta del campo FK**: `"*" --> "1"` (FK obligatorio), `"*" --> "0..1"` (nullable), `"1" --> "1"` (OneToOne).

---

## Diagrama

```mermaid
classDiagram
    direction LR

    %% =========================================================
    %% APP: licencias  — inventario y asignación de software
    %% =========================================================
    class Tenant {
        +nombre : CharField max_length=80, unique
        +activo : BooleanField default=True
    }

    class Empresa {
        +tenant : ForeignKey Tenant, CASCADE, related_name=empresas
        +nombre : CharField max_length=100
        +activo : BooleanField default=True
    }

    class Proveedor {
        +nombre : CharField max_length=100, unique
        +contacto : CharField max_length=100, null
        +telefono : CharField max_length=50, null
    }

    class TipoLicencia {
        +nombre : CharField max_length=50
        +fabricante : CharField max_length=100, default=Microsoft
    }

    class Licencia {
        +tenant : ForeignKey Tenant, CASCADE
        +empresa : ForeignKey Empresa, PROTECT, null
        +tipo : ForeignKey TipoLicencia, PROTECT
        +proveedor : ForeignKey Proveedor, PROTECT, null
        +fecha_compra : DateField
        +fecha_activacion : DateField null
        +fecha_vencimiento : DateField
        +usuario_activo() Asignacion
        +esta_vencida() bool
        +esta_asignada() bool
        +estado() str
    }

    class Asignacion {
        +licencia : ForeignKey Licencia, CASCADE, related_name=asignaciones
        +empleado : ForeignKey Empleado, PROTECT
        +fecha_asignacion : DateTimeField auto_now_add
        +fecha_retiro : DateTimeField null
        +activo : BooleanField default=True
        +observaciones : TextField blank
        +area_snapshot : CharField max_length=100, null
        +division_snapshot : CharField max_length=100, null
        +unidad_snapshot : CharField max_length=100, null
        +save() void
    }

    %% =========================================================
    %% APP: empleados  — estructura organizacional
    %% =========================================================
    class GerenciaDivision {
        +empresa : ForeignKey Empresa, CASCADE, related_name=divisiones
        +codigo : CharField max_length=10
        +nombre : CharField max_length=100
        +activo : BooleanField default=True
    }

    class GerenciaArea {
        +empresa : ForeignKey Empresa, CASCADE, related_name=areas
        +division : ForeignKey GerenciaDivision, CASCADE, null, related_name=areas
        +codigo : CharField max_length=10, null
        +nombre : CharField max_length=100
        +activo : BooleanField default=True
    }

    class Unidad {
        +area : ForeignKey GerenciaArea, CASCADE, related_name=unidades
        +nombre : CharField max_length=100
        +activo : BooleanField default=True
    }

    class Cargo {
        +area_usuario : ForeignKey AreaUsuario, SET_NULL, null, related_name=cargos
        +nombre : CharField max_length=120, unique
        +descripcion : CharField max_length=255, blank
        +activo : BooleanField default=True
    }

    class Empleado {
        +nombre_completo : CharField max_length=200
        +ci : CharField max_length=20, unique
        +email_principal : EmailField unique
        +empresa : ForeignKey Empresa, PROTECT
        +division : ForeignKey GerenciaDivision, SET_NULL, null
        +area : ForeignKey GerenciaArea, PROTECT
        +unidad : ForeignKey Unidad, SET_NULL, null
        +centro_de_costos : CharField max_length=20, null
        +puesto : CharField max_length=100, null
        +pais : CharField max_length=30, default=Bolivia
        +ciudad : CharField max_length=80, default=Santa_Cruz_de_la_Sierra
        +oficina : CharField max_length=80, null
        +activo : BooleanField default=True
    }

    %% =========================================================
    %% APP: user  — perfiles y áreas funcionales
    %% =========================================================
    class User {
        <<django.contrib.auth>>
        +username : CharField unique
        +email : EmailField
        +password : CharField hashed
        +is_active : BooleanField
    }

    class AreaUsuario {
        +nombre : CharField max_length=120, unique
        +descripcion : CharField max_length=255, blank
        +activo : BooleanField default=True
    }

    class PerfilUsuario {
        +user : OneToOneField User, CASCADE, related_name=perfil
        +area : CharField max_length=40, null, choices=administracion|soporte|operaciones|auditoria|sistemas|cliente
        +area_usuario : ForeignKey AreaUsuario, SET_NULL, null, related_name=perfiles
        +cargo : ForeignKey Cargo, SET_NULL, null
        +foto : FileField upload_to=perfiles/, null
        +must_change_password : BooleanField default=False
    }

    %% =========================================================
    %% APP: bitacora  — auditoría
    %% =========================================================
    class Bitacora {
        +usuario : ForeignKey User, SET_NULL, null
        +accion : CharField max_length=255
        +modulo : CharField max_length=100
        +descripcion : TextField
        +fecha : DateTimeField auto_now_add
        +ip : GenericIPAddressField null
    }

    %% =========================================================
    %% RELACIONES — licencias
    %% =========================================================
    Empresa "*" --> "1" Tenant : tenant
    Licencia "*" --> "1" Tenant : tenant
    Licencia "*" --> "0..1" Empresa : empresa
    Licencia "*" --> "1" TipoLicencia : tipo
    Licencia "*" --> "0..1" Proveedor : proveedor
    Asignacion "*" --> "1" Licencia : licencia
    Asignacion "*" --> "1" Empleado : empleado

    %% =========================================================
    %% RELACIONES — empleados
    %% =========================================================
    GerenciaDivision "*" --> "1" Empresa : empresa
    GerenciaArea "*" --> "1" Empresa : empresa
    GerenciaArea "*" --> "0..1" GerenciaDivision : division
    Unidad "*" --> "1" GerenciaArea : area
    Cargo "*" --> "0..1" AreaUsuario : area_usuario
    Empleado "*" --> "1" Empresa : empresa
    Empleado "*" --> "0..1" GerenciaDivision : division
    Empleado "*" --> "1" GerenciaArea : area
    Empleado "*" --> "0..1" Unidad : unidad

    %% =========================================================
    %% RELACIONES — user
    %% =========================================================
    PerfilUsuario "1" --> "1" User : user (OneToOne)
    PerfilUsuario "*" --> "0..1" AreaUsuario : area_usuario
    PerfilUsuario "*" --> "0..1" Cargo : cargo

    %% =========================================================
    %% RELACIONES — bitacora
    %% =========================================================
    Bitacora "*" --> "0..1" User : usuario
```

---

## Notas sobre las relaciones más importantes

### 1. `Asignacion` es la tabla pivote licencia-empleado con auditoría
Una `Asignacion` vincula **una `Licencia` con un `Empleado`** y, en su `save()`, guarda **snapshots inmutables** del área, división y unidad del empleado al momento del alta (`area_snapshot`, `division_snapshot`, `unidad_snapshot`). Esto permite mantener trazabilidad histórica aunque el empleado cambie luego de área. Además aplica una **política de retención**: máximo 5 asignaciones inactivas por licencia; las más viejas se consolidan en el campo `observaciones` de la 5ª y se borran físicamente. El `save()` también setea automáticamente `fecha_retiro` cuando `activo` pasa a `False`.

### 2. Modelo multi-tenant
`Tenant` es la raíz del aislamiento corporativo. Cada `Empresa` pertenece a un `Tenant` (`CASCADE`). Cada `Licencia` referencia explícitamente su `Tenant` (`CASCADE`) **y opcionalmente** una `Empresa` "dueña" (`PROTECT`, nullable). Esto soporta licencias que viven a nivel tenant sin asignación a empresa específica.

### 3. Estructura organizacional jerárquica (3 niveles)
`Empresa → GerenciaDivision → GerenciaArea → Unidad`. Cada nivel apunta al anterior con FK. Un `Empleado` puede colgar de cualquier combinación: `empresa` y `area` son **obligatorios**, `division` y `unidad` son opcionales (`SET_NULL`). Nota: `GerenciaArea.division` es nullable (`CASCADE` pero `null=True`), por lo que un área puede existir sin división asignada.

### 4. `on_delete` no triviales
- `PROTECT` en `Licencia.empresa`, `Licencia.tipo`, `Licencia.proveedor`, `Asignacion.empleado`, `Empleado.empresa`, `Empleado.area` — protege contra borrados accidentales que romperían historial.
- `SET_NULL` en `Empleado.division`, `Empleado.unidad`, `Cargo.area_usuario`, `PerfilUsuario.area_usuario`, `PerfilUsuario.cargo`, `Bitacora.usuario` — permite reorganizaciones sin perder el registro.
- `CASCADE` en `Empresa.tenant`, `Licencia.tenant`, `Asignacion.licencia`, `GerenciaDivision.empresa`, `GerenciaArea.empresa`, `GerenciaArea.division`, `Unidad.area`, `PerfilUsuario.user` — la entidad hija no tiene sentido sin la padre.

### 5. FK cross-app: `Cargo` (empleados) → `AreaUsuario` (user)
`Cargo` vive físicamente en la app `empleados` pero tiene una FK a `AreaUsuario` (app `user`) vía referencia lazy `'user.AreaUsuario'`. Es la única FK cruzada entre módulos no obvios. Diseño histórico: catálogo de cargos compartido entre empleados y perfiles de usuario.

### 6. `PerfilUsuario` extiende a `User` con OneToOne
La app `user` no reemplaza `AUTH_USER_MODEL`. Mantiene el `User` built-in de Django y agrega un `PerfilUsuario` 1:1 con campos extra (`foto`, `cargo`, área funcional `area`/`area_usuario`, flag `must_change_password` usado por el middleware de cambio forzado de contraseña). El campo `area` es un `CharField` con `choices` fijos (`administracion`, `soporte`, `operaciones`, `auditoria`, `sistemas`, `cliente`), distinto de la FK `area_usuario` que apunta al catálogo dinámico `AreaUsuario`.

### 7. `Bitacora.usuario` es nullable
Los eventos de auditoría sobreviven al borrado del usuario que los generó (`SET_NULL`). Importante para cumplir requisitos de trazabilidad histórica.

### 8. `gestion_global` no tiene modelos propios
`gestion_global/infrastructure/models.py` solo **re-exporta** `Empresa`, `Tenant`, `GerenciaArea`, `GerenciaDivision`, `Unidad` desde sus apps físicas. La separación es lógica (CU07/08/10/11/12 del CICLO 2), no de almacenamiento. Por eso no aparece como nodo separado en el diagrama: serían los mismos objetos.

### 9. Campo `nombre_completo` en `Empleado`
Es un único `CharField` (no separa `nombre`/`apellido`). Es el identificador legible que aparece en mensajes de UI y en los snapshots de `Asignacion.observaciones`.

### 10. Backreferences importantes (no se muestran como flechas, pero existen)
- `Tenant.empresas` (de `Empresa.tenant`)
- `Empresa.divisiones` (de `GerenciaDivision.empresa`), `Empresa.areas` (de `GerenciaArea.empresa`)
- `GerenciaDivision.areas` (de `GerenciaArea.division`)
- `GerenciaArea.unidades` (de `Unidad.area`)
- `AreaUsuario.cargos` (de `Cargo.area_usuario`), `AreaUsuario.perfiles` (de `PerfilUsuario.area_usuario`)
- `Licencia.asignaciones` (de `Asignacion.licencia`) — usado por `Licencia.usuario_activo` y `Licencia.esta_asignada`.
- `User.perfil` (OneToOne reverse de `PerfilUsuario.user`)

---

## Cómo renderizar este diagrama

- **VS Code**: instalar la extensión *Markdown Preview Mermaid Support* y abrir vista previa (`Ctrl+Shift+V`).
- **GitHub / GitLab**: el bloque Mermaid se renderiza automáticamente al ver el `.md` en la web.
- **Exportar a imagen**: usar [mermaid.live](https://mermaid.live), pegar el bloque, descargar PNG/SVG.
