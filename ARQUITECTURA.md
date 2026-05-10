# Arquitectura — App `licencias`

> Documento para el equipo. Refleja el estado de la rama `refactor-piloto-licencias` después de 4 refactors piloto.

---

## 1. Resumen ejecutivo

En la rama `refactor-piloto-licencias` se hicieron 4 cambios para sacar lógica de negocio de `licencias/views.py` (que tenía ~1.250 líneas con todo mezclado) y dejar la vista solo orquestando request/response.

- **Service Layer Pattern** aplicado a 3 funciones: `asignar_licencia`, `liberar_licencia` y `dar_baja_empleado`. Las reglas de negocio (validar duplicidad, prevenir race conditions, cascada de revocación) viven en `licencias/services/`.
- **Excepciones tipadas** (`LicenciaYaAsignadaError`, `EmpleadoYaInactivoError`, etc.) en `licencias/services/exceptions.py` para que la vista traduzca cada caso a un mensaje al usuario sin reglas mezcladas.
- **Selector Pattern** en `licencias/selectors.py`: `obtener_kpis_dashboard` resuelve los 5 KPIs en **1 query agregada** en lugar del N+1 anterior (eran ~11 queries para 5 licencias).
- **Eliminación de código muerto**: `sincronizar_m365` (170 líneas que no funcionaban en producción) borrada junto con su URL, modal HTML y log handler.
- **11 tests automatizados** pasando, cubriendo los 3 services + el selector.

Resultado: `views.py` bajó a ~1.010 líneas, y todo lo nuevo se puede testear sin levantar el servidor.

---

## 2. Mapa del proyecto — ¿dónde está cada cosa?

| Necesito... | Archivo | Ejemplos reales |
|---|---|---|
| Ver/modificar los modelos | [licencias/models.py](licencias/models.py) | `Tenant`, `Empresa`, `Proveedor`, `TipoLicencia`, `Licencia`, `Asignacion` |
| Agregar una vista (HTTP) | [licencias/views.py](licencias/views.py) | `dashboard`, `asignar_licencia`, `lista_empleados`, `crear_licencia` |
| Agregar lógica de negocio (escritura) | [licencias/services/](licencias/services/) | `asignacion.asignar_licencia`, `asignacion.liberar_licencia`, `empleados.dar_baja_empleado`, `desbloqueo.enviar_token_desbloqueo` |
| Agregar una query compleja (lectura) | [licencias/selectors.py](licencias/selectors.py) | `obtener_kpis_dashboard` |
| Definir una excepción de negocio | [licencias/services/exceptions.py](licencias/services/exceptions.py) | `LicenciaYaAsignadaError`, `EmpleadoYaTieneTipoError`, `EmpleadoYaInactivoError`, `AsignacionInactivaError` |
| Agregar un formulario | [licencias/forms.py](licencias/forms.py) | `EmpleadoForm`, `LicenciaForm`, `TenantForm`, `EmpresaForm` |
| Agregar una URL | [config/urls.py](config/urls.py) | `path('licencia/<id>/asignar/', ...)`, `path('dashboard/', ...)` |
| Modificar el HTML | [licencias/templates/licencias/](licencias/templates/licencias/) | `dashboard.html`, `inicio.html`, `empleados.html` |
| Escribir tests | [licencias/tests.py](licencias/tests.py) | `AsignacionServiceTests`, `BajaEmpleadoServiceTests`, `KpisDashboardSelectorTests`, `InicioViewTests` |
| Registrar evento en bitácora | importar de [bitacora/actions/](bitacora/actions/) | `log_asignacion_licencia`, `log_liberar_licencia`, `log_baja_empleado` |

### Detalle de los archivos clave

**`licencias/models.py`** — 6 modelos:
- `Tenant`: grupo corporativo (raíz multi-tenant).
- `Empresa`: razón social vinculada a un Tenant.
- `Proveedor`: reseller/proveedor de licenciamiento.
- `TipoLicencia`: catálogo de SKUs.
- `Licencia`: activo individual de software. Propiedades calculadas: `usuario_activo`, `esta_vencida`, `esta_asignada`, `estado`.
- `Asignacion`: vínculo licencia-empleado con snapshots organizacionales y política de retención de 5 inactivos.

**`licencias/services/asignacion.py`** — operaciones transaccionales sobre asignaciones:
- `asignar_licencia(licencia_id, empleado_id, request) -> Asignacion`: vincula licencia con empleado, valida race condition + duplicidad por TipoLicencia, registra en bitácora.
- `liberar_licencia(asignacion_id, motivo, request) -> None`: revoca asignación activa, persiste motivo en `observaciones`, registra en bitácora.

**`licencias/services/empleados.py`** — ciclo de vida del empleado:
- `dar_baja_empleado(empleado_id, request) -> dict`: inhabilita empleado, libera todas sus asignaciones activas en cascada (delegando a `liberar_licencia`), todo en una sola transacción atómica.

**`licencias/services/desbloqueo.py`** — preexiste, no se modificó:
- `enviar_token_desbloqueo(user, source) -> (ok, mensaje)`: envía token por email para desbloquear cuenta tras lockout de Axes.

**`licencias/services/exceptions.py`** — excepciones de dominio:
- Base `LicenciaServiceError`.
- Específicas: `LicenciaNoEncontradaError`, `EmpleadoNoEncontradoError`, `AsignacionNoEncontradaError`, `LicenciaYaAsignadaError`, `EmpleadoYaTieneTipoError`, `AsignacionInactivaError`, `EmpleadoYaInactivoError`.

**`licencias/selectors.py`** — queries de solo lectura optimizadas:
- `obtener_kpis_dashboard(tenant=None) -> dict`: calcula `total`, `ocupadas`, `disponibles`, `vencidas`, `por_vencer` en una sola query usando `annotate(Exists(...))` + `aggregate(Count(filter=Q(...)))`.

**`licencias/views.py`** — orquestación HTTP. Funciones notables:
- Dashboard / inicio: `inicio`, `dashboard`.
- Transacciones: `asignar_licencia`, `liberar_licencia` (delegan a services).
- Empleados: `lista_empleados`, `editar_empleado`, `baja_empleado` (delega), `reactivar_empleado`.
- AJAX cascadas: `cargar_unidades`, `cargar_areas`, `cargar_divisiones`, `cargar_empresas`.
- Configuración (catálogos): `configuracion` (sigue gigante, ver §6), más `editar_*`/`eliminar_*` por entidad (8 pares).
- Otras: `exportar_excel`, `crear_licencia`, `eliminar_licencias_masivo`, `validar_token_bloqueo`, `enviar_token_bloqueo`.

---

## 3. Patrones aplicados

### 3.1 Service Layer Pattern

**Idea:** las views solo manejan HTTP (parsear request, validar permisos, mostrar mensajes, redirigir). Las reglas de negocio viven en services puros que se pueden testear sin levantar el servidor.

**Antes** ([licencias/views.py](licencias/views.py), versión vieja de `asignar_licencia`):

```python
@login_required
def asignar_licencia(request, licencia_id):
    exigir_permiso(request, 'licencias.add_asignacion')
    if request.method == 'POST':
        licencia = get_object_or_404(Licencia, pk=licencia_id)
        empleado_id = request.POST.get('empleado_id')
        empleado = get_object_or_404(Empleado, pk=empleado_id)

        # Lógica de negocio mezclada con HTTP:
        if licencia.usuario_activo:
            messages.error(request, f"Violación de concurrencia: ...")
            return redirect(...)

        tiene_duplicada = Asignacion.objects.filter(
            empleado=empleado, licencia__tipo=licencia.tipo, activo=True
        ).exists()
        if tiene_duplicada:
            messages.warning(request, f"Regla de negocio: ...")
            return redirect(...)

        Asignacion.objects.create(...)
        log_asignacion_licencia(request, licencia, empleado)
        messages.success(request, ...)
    return redirect(...)
```

**Después** (vista delgada + service):

```python
# licencias/views.py
@login_required
def asignar_licencia(request, licencia_id):
    exigir_permiso(request, 'licencias.add_asignacion')
    if request.method != 'POST':
        return redirect(request.META.get('HTTP_REFERER', 'dashboard_general'))

    empleado_id = request.POST.get('empleado_id')
    try:
        asignacion = svc_asignar(licencia_id, empleado_id, request)
    except LicenciaYaAsignadaError as e:
        messages.error(request, f"Violación de concurrencia: ya asignada a {e.empleado_actual_nombre}.")
    except EmpleadoYaTieneTipoError as e:
        messages.warning(request, f"Regla de negocio: {e.empleado_nombre} ya posee '{e.tipo_nombre}'.")
    else:
        messages.success(request, f"Licencia asignada a {asignacion.empleado.nombre_completo}.")
    return redirect(...)
```

```python
# licencias/services/asignacion.py
@transaction.atomic
def asignar_licencia(licencia_id: int, empleado_id: int, request) -> Asignacion:
    licencia = Licencia.objects.select_related('tipo').get(pk=licencia_id)
    empleado = Empleado.objects.get(pk=empleado_id)
    if licencia.usuario_activo is not None:
        raise LicenciaYaAsignadaError(licencia.usuario_activo.empleado.nombre_completo)
    if Asignacion.objects.filter(empleado=empleado, licencia__tipo=licencia.tipo, activo=True).exists():
        raise EmpleadoYaTieneTipoError(empleado.nombre_completo, licencia.tipo.nombre)
    asignacion = Asignacion.objects.create(licencia=licencia, empleado=empleado, activo=True)
    log_asignacion_licencia(request, licencia, empleado)
    return asignacion
```

### 3.2 Excepciones tipadas

**Idea:** cada regla de negocio que puede fallar lanza una excepción específica con datos en sus atributos. La vista hace `try/except` por tipo y arma el mensaje.

```python
# licencias/services/exceptions.py
class LicenciaYaAsignadaError(LicenciaServiceError):
    def __init__(self, empleado_actual_nombre: str):
        self.empleado_actual_nombre = empleado_actual_nombre
        super().__init__(f"Licencia ya asignada a {empleado_actual_nombre}")
```

Esto permite:
- El service no conoce HTTP ni `messages`.
- La vista decide cómo presentar cada caso (ej: `messages.error` vs `messages.warning`).
- Tests pueden assertir excepción específica + datos: `self.assertEqual(ctx.exception.empleado_nombre, 'Juan')`.

### 3.3 Selector + Command-Query Separation

**Idea:** las **escrituras** (commands) van a `services/`, las **lecturas complejas** (queries) van a `selectors.py`. Separar deja explícito qué tiene side-effects y qué no.

**Antes** ([licencias/views.py](licencias/views.py), `dashboard` viejo): loop en Python con N+1.

```python
for lic in licencias:
    if lic.usuario_activo:   # ← 1 query por iteración
        ocupadas += 1
    if lic.fecha_vencimiento < hoy:
        vencidas += 1
    elif lic.fecha_vencimiento <= limite_30_dias:
        por_vencer += 1
    if not lic.usuario_activo and lic.fecha_vencimiento >= hoy:  # ← otra query
        disponibles += 1
```

Para 5 licencias: ~11 queries. Para 500: ~1.001.

**Después** ([licencias/selectors.py](licencias/selectors.py)):

```python
def obtener_kpis_dashboard(tenant=None) -> dict:
    hoy = timezone.now().date()
    limite_30_dias = hoy + timedelta(days=30)
    qs = Licencia.objects.all()
    if tenant is not None:
        qs = qs.filter(tenant=tenant)
    active_subq = Asignacion.objects.filter(licencia=OuterRef('pk'), activo=True)
    return qs.annotate(tiene_activa=Exists(active_subq)).aggregate(
        total=Count('id'),
        ocupadas=Count('id', filter=Q(tiene_activa=True)),
        disponibles=Count('id', filter=Q(tiene_activa=False, fecha_vencimiento__gte=hoy)),
        vencidas=Count('id', filter=Q(fecha_vencimiento__lt=hoy)),
        por_vencer=Count('id', filter=Q(fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=limite_30_dias)),
    )
```

**1 query** sin importar cuántas licencias haya. La vista solo hace `kpis = obtener_kpis_dashboard(tenant=tenant_seleccionado)` y mapea al context.

---

## 4. Cómo agregar una nueva feature siguiendo estos patrones

### 4.1 Quiero agregar una nueva regla de negocio

**Ejemplo:** "no se puede asignar una licencia a un empleado de una empresa distinta a la dueña de la licencia".

1. **Agregá la excepción** en [licencias/services/exceptions.py](licencias/services/exceptions.py):
   ```python
   class EmpresaNoCoincideError(LicenciaServiceError):
       def __init__(self, empleado_empresa: str, licencia_empresa: str):
           self.empleado_empresa = empleado_empresa
           self.licencia_empresa = licencia_empresa
           super().__init__(f"Empleado de '{empleado_empresa}' no puede recibir licencia de '{licencia_empresa}'")
   ```

2. **Agregá la validación** dentro de `asignar_licencia` en [licencias/services/asignacion.py](licencias/services/asignacion.py) (antes del `Asignacion.objects.create`):
   ```python
   if licencia.empresa and licencia.empresa != empleado.empresa:
       raise EmpresaNoCoincideError(empleado.empresa.nombre, licencia.empresa.nombre)
   ```

3. **Capturala en la vista** [licencias/views.py](licencias/views.py) en `asignar_licencia`:
   ```python
   except EmpresaNoCoincideError as e:
       messages.error(request, f"No se puede asignar: {e}")
   ```

4. **Test del service** en [licencias/tests.py](licencias/tests.py):
   ```python
   def test_asignar_falla_si_empresas_no_coinciden(self):
       otra_empresa = Empresa.objects.create(tenant=self.tenant, nombre='Otra SA')
       otro_empleado = Empleado.objects.create(..., empresa=otra_empresa, area=...)
       with self.assertRaises(EmpresaNoCoincideError) as ctx:
           svc_asignar(self.licencia.id, otro_empleado.id, self._request())
       self.assertEqual(ctx.exception.empleado_empresa, 'Otra SA')
   ```

### 4.2 Quiero agregar un KPI nuevo al dashboard

**Ejemplo:** "cantidad de licencias por empresa".

Va al **selector**, NO a la vista. Modificá `obtener_kpis_dashboard` en [licencias/selectors.py](licencias/selectors.py) o creá un selector nuevo si la query es independiente.

Si es un agregado más sobre las mismas licencias, sumá una key al `aggregate`:
```python
return qs.annotate(...).aggregate(
    total=Count('id'),
    # ... existentes
    sin_empresa=Count('id', filter=Q(empresa__isnull=True)),
)
```

Si requiere `group by empresa`, hacé un selector nuevo:
```python
def obtener_licencias_por_empresa(tenant=None) -> list[dict]:
    qs = Licencia.objects.all()
    if tenant is not None:
        qs = qs.filter(tenant=tenant)
    return list(qs.values('empresa__nombre').annotate(total=Count('id')).order_by('-total'))
```

Después en la vista: `context['licencias_por_empresa'] = obtener_licencias_por_empresa(...)`. **No hagas el group by en Python.**

### 4.3 Quiero eliminar código viejo

Patrón usado en el piloto #4 (`sincronizar_m365`):

1. **Identificá todas las referencias** con grep (función, log handler, URL name, IDs de modal HTML):
   ```powershell
   # ejemplo, reemplazá nombre_funcion
   ```
   Usá la herramienta Grep sobre el repo. Buscá: nombre de función, nombre de URL (`'mi_url'`), IDs de elementos HTML asociados, imports re-exportados.

2. **Verificá imports huérfanos** que solo usaba esa función. Antes de quitar `import X` chequeá que nadie más lo usa:
   ```powershell
   # buscar X. en todo el repo
   ```
   Si está compartido → no lo toques. Si solo lo usaba el código muerto → quitalo.

3. **Borrá en este orden**:
   - Función / método.
   - URL en `config/urls.py` (sin esto, `manage.py check` falla por referencia rota).
   - Botón / modal en templates.
   - Imports muertos.

4. **Validá**:
   ```powershell
   python manage.py check
   python manage.py test licencias
   ```
   + greps de cero matches sobre las cadenas borradas.

5. **Commit explicando el porqué**, no solo el qué:
   `remove: eliminar X (no se usa desde Y, reemplazado por Z)`.

---

## 5. Tests automatizados — cómo correrlos

```powershell
python manage.py test licencias
```

Salida esperada: **`Ran 11 tests in ~5s — OK`**.

Para verlos uno por uno: `python manage.py test licencias --verbosity=2`.

Las **4 clases** y qué cubre cada una:

| Clase | Archivo | Qué cubre |
|---|---|---|
| `InicioViewTests` | tests.py | Que la vista `inicio` renderice OK para usuario autenticado. (Test único, preexistente.) |
| `AsignacionServiceTests` | tests.py | Service `asignar_licencia` (happy path + duplicidad por TipoLicencia) y `liberar_licencia` (marca inactiva + lanza error si ya inactiva). 3 tests. |
| `BajaEmpleadoServiceTests` | tests.py | Service `dar_baja_empleado`: cascada con 2 licencias, caso sin licencias, error `EmpleadoYaInactivoError`. 3 tests. |
| `KpisDashboardSelectorTests` | tests.py | Selector `obtener_kpis_dashboard`: cuenta correcta, filtro por tenant, fechas borde (vencer vs vencida), no duplicación con múltiples asignaciones. 4 tests. |

Patrón de los tests de service: usan `RequestFactory` para construir un request fake con `request.user` autenticado (la bitácora lo necesita), construyen Tenant + Empresa + Empleado + TipoLicencia + Licencia en `setUp`, y testean el service directamente — **sin** levantar servidor ni cliente HTTP.

---

## 6. Deuda técnica pendiente

Orden por prioridad:

| # | Item | Prioridad | Esfuerzo | Por qué se postergó |
|---|---|---|---|---|
| 1 | `configuracion()` ([views.py:590](licencias/views.py#L590)) — gestiona 8 entidades en una sola vista (~125 líneas) | **Alta** | 1-2 días | Es el próximo candidato natural de refactor pero requiere decidir antes si conviene partirla en 8 vistas distintas o convertirla en un FormSet/ViewSet. Cualquiera de las dos es un cambio mayor. |
| 2 | `inicio()` ([views.py:306](licencias/views.py#L306)) hace 4 counts separados con la misma definición de KPIs que `dashboard` | **Media** | 30 min | Trivial reusar `obtener_kpis_dashboard` del selector. Quedó fuera del piloto #3 porque la spec era solo el dashboard. |
| 3 | Funciones repetitivas `editar_*` y `eliminar_*` (8 pares en views.py L721-928) — patrón CRUD casi idéntico | Media | 2-4 horas | Se podrían generalizar con un dict `{entidad → (Form, redirect)}` o CBVs. Trade-off: el código actual es repetitivo pero **legible**; abstraerlo lo hace más corto pero menos directo. Decisión de equipo. |
| 4 | Apps `bitacora/` y `user/` con Clean Architecture sobre-ingenierizada (5 capas) | Baja | 3-5 días | Funciona bien, no rompe nada. Refactorizarla es trabajo grande sin valor visible para el usuario. Vale la pena solo si se piensa agregar muchas features ahí. Por ahora, "deuda fría". |
| 5 | Decidir si `pandas` se quita de `requirements.txt` (ya no lo importa nadie tras el piloto #4) | Baja | 5 min + redeploy | Quitarlo es una línea, pero hay que confirmar que no entra de vuelta en una feature futura de import de Excel. Si nadie tiene planes a 30-60 días, sacarlo y bajar el tamaño del venv. |

---

## 7. Commits de esta rama

| Hash | Mensaje | Resumen |
|---|---|---|
| `d989625` | `refactor: extraer asignar_licencia y liberar_licencia a service layer` | Piloto #1: nace `services/asignacion.py` y `services/exceptions.py`, las dos vistas de transacción quedan delgadas. Cubierto por 3 tests. |
| `7d8e613` | `refactor: extraer baja_empleado a service layer con cascada de revocación` | Piloto #2: nuevo `services/empleados.py::dar_baja_empleado` reutiliza `liberar_licencia` para la cascada, todo `@transaction.atomic`. +1 excepción `EmpleadoYaInactivoError`, +3 tests. |
| `2f918aa` | `refactor: dashboard usa selector con query agregada (resuelve N+1)` | Piloto #3: nace `selectors.py::obtener_kpis_dashboard`. 5 KPIs en 1 query (antes ~11). Snapshot 5/2/3/2/3 preservado. +4 tests. |
| `7bd88f7` | `remove: eliminar sincronizar_m365 y dead code asociado (178 líneas)` | Piloto #4: borrado quirúrgico de la función, su URL, modal HTML, log handler en bitácora, imports `pandas` y `transaction`. Ningún test agregado/quitado. |

---

## 8. Convenciones del equipo

Reglas mínimas para que los 6 que tocamos el repo no nos pisemos:

1. **Lógica de negocio NO va en `views.py`.** Va en [licencias/services/](licencias/services/). La vista solo: parsea request, valida permisos, llama al service, captura excepciones, muestra `messages`, redirige.
2. **Queries complejas (joins, agregados, subqueries) NO van en `views.py`.** Van en [licencias/selectors.py](licencias/selectors.py). Si necesitás un loop en Python para calcular algo a partir de queries, casi seguro hay una `aggregate` que lo resuelve mejor.
3. **Cada nueva regla de negocio que pueda fallar → excepción tipada** en [licencias/services/exceptions.py](licencias/services/exceptions.py), heredando de `LicenciaServiceError`. Pasale los datos que la vista necesita para armar el mensaje (nombres, IDs, etc.) como atributos de la excepción.
4. **Cada nuevo service → al menos 1 test que lo cubra.** Mínimo: happy path. Ideal: happy path + un caso que dispare cada excepción tipada que el service pueda lanzar.
5. **Antes de cada commit:** correr `python manage.py test licencias` y `python manage.py check`. Ambos deben pasar. Si rompés tests con un cambio intencional, actualizalos en el mismo commit.
6. **Cada feature/refactor en su propia rama.** Nunca directo a `main`. Nombre sugerido: `feat/<corto>`, `refactor/<corto>`, `fix/<corto>`. PR con descripción del *por qué*, no solo del *qué*.
7. **Servicios reciben `request` (no `user_actor`)** por convención del proyecto, porque `bitacora.actions.log_*` lo necesita para extraer IP. Si en el futuro queremos pureza, se migra el módulo bitácora primero.

---

*Última actualización: rama `refactor-piloto-licencias`, después del commit `7bd88f7`.*
