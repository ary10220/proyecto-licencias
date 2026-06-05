# Pull Request — Fase 1 (Dashboard con graficos) + Fase 2 (Alarma automatizada)

> Documento de apoyo para crear el PR en GitHub. Copiar/pegar la seccion correspondiente.
> Rama: `ariany/cierre-proyecto` -> `main`
> Link directo: https://github.com/ary10220/proyecto-licencias/pull/new/ariany/cierre-proyecto

---

## Titulo sugerido del PR

```
feat: Dashboard con graficos analiticos (Chart.js) y alarma de vencimiento automatizada (CU14)
```

---

## Descripcion del PR (pegar en el cuerpo)

### Resumen

Este PR cierra dos features pendientes del proyecto Mamaya Licencias para la presentacion academica:

- **Fase 1 — Dashboard con graficos analiticos:** se agregan 5 graficos interactivos (Chart.js) al dashboard ejecutivo, sin alterar los KPIs ni las barras CSS existentes.
- **Fase 2 — Alarma de vencimiento automatizada (CU14):** los destinatarios de las alertas se gestionan con un checkbox por usuario; el comando `enviar_alertas` se refactoriza con formato de resumen ejecutivo escalable y se automatiza con Windows Task Scheduler.

### Fase 1 — Dashboard con graficos (Chart.js)

- Se incorpora **Chart.js v4 por CDN** en `templates/base.html` (no se agregan dependencias de backend).
- La vista `dashboard()` calcula una estructura `chart_data` (serializada con `json_script`, sin riesgo de XSS) reutilizando los conteos existentes y agregando dos series nuevas: **licencias por empresa** y **vencimientos por mes** (`TruncMonth`).
- Se agregan 5 graficos: **estado** (doughnut), **tipo** (barras), **origen** (pie), **empresa** (barras horizontales) y **vencimientos por mes** (linea).
- Los graficos **respetan los filtros** existentes del dashboard (tenant, empresa, tipo, origen).
- La inicializacion se hace en `DOMContentLoaded` para garantizar que el CDN ya este cargado.
- **No se modifican** los KPIs numericos, las barras CSS originales ni `exportar_excel()`.

### Fase 2 — Alarma de vencimiento automatizada (CU14)

- Nuevo campo **`recibir_alertas_vencimiento`** (`BooleanField`, `default=False`) en `PerfilUsuario` (opt-in).
- El **formulario de Usuario** (`UserForm`) gestiona el campo siguiendo el patron de los campos de perfil existentes (`area_usuario`, `cargo`): declaracion, `initial` en `__init__`, persistencia en `save()`. Visible al crear y editar.
- Refactor de `enviar_alertas.py`:
  - Destinatarios dinamicos: usuarios activos con el checkbox marcado (`perfil__recibir_alertas_vencimiento=True`), con **fallback** a `DEFAULT_FROM_EMAIL` si no hay nadie suscrito.
  - **Multiples offsets de aviso** configurables (`ALERTAS_DIAS_AVISO = [30, 15, 7, 1]`).
  - **Formato de resumen ejecutivo escalable** (resumen general, distribucion por urgencia, top 5 empresas, top 5 tipos, criticas limitadas a 10), sin emojis.
  - Agregaciones en memoria con `collections.Counter` (1 sola lectura de BD).
  - **Optimizacion N+1** con `select_related` + `prefetch_related`.
  - **Logging estructurado** (inicio, conteos, exito/error).
- **Automatizacion** con Windows Task Scheduler documentada en `docs/programar_alarma_windows.md` (+ wrapper `enviar_alertas.bat`). Tarea `MamayaAlertasLicencias`, diaria 12:00.

Cierra: **CU14 — Notificar vencimiento de licencias.**

---

## Archivos modificados

### Fase 1
- `templates/base.html` — CDN de Chart.js v4.
- `licencias/views.py` — `chart_data` y series para los graficos (import de `TruncMonth`).
- `licencias/templates/licencias/dashboard_reportes.html` — canvases + inicializacion de Chart.js.

### Fase 2
- `user/infrastructure/models.py` — campo `recibir_alertas_vencimiento` en `PerfilUsuario`.
- `user/interfaces/forms/usuarios.py` — campo en `UserForm` (declaracion + initial + save).
- `user/templates/user/usuarios/form.html` — checkbox en "Estado y privilegios de cuenta".
- `licencias/management/commands/enviar_alertas.py` — refactor completo del comando.
- `config/settings.py` — `ALERTAS_DIAS_AVISO = [30, 15, 7, 1]`.

## Archivos nuevos

### Fase 2
- `user/migrations/0008_perfilusuario_recibir_alertas_vencimiento.py` — migracion del campo.
- `docs/programar_alarma_windows.md` — guia de automatizacion (schtasks).
- `enviar_alertas.bat` — wrapper para la tarea programada.

---

## Tests manuales realizados

### Fase 1 — Dashboard
- [x] `python manage.py check` sin errores.
- [x] `/dashboard/` renderiza los 5 graficos correctamente.
- [x] `/dashboard/<tenant_id>/` y los filtros (`?empresa=`, `?tipo=`, `?origen=`) actualizan los graficos.
- [x] Sin errores de Chart.js en la consola del navegador (init en `DOMContentLoaded`).
- [x] KPIs, barras CSS originales y exportacion a Excel siguen funcionando igual.

### Fase 2 — Alarma
- [x] Migracion `0008` generada y aplicada (`migrate user` OK).
- [x] Checkbox visible y persistente en crear/editar usuario (marcado en `admin2`).
- [x] Verificacion en seco: la query de destinatarios detecta solo a los suscritos (`perfil__...`).
- [x] Envio real de prueba: email recibido en `arianyclaure@gmail.com` con el formato de resumen ejecutivo.
- [x] Subject sin emojis: `Alerta: N licencia(s) por vencer (X critica/s)`.
- [x] Fallback a `DEFAULT_FROM_EMAIL` validado por codigo (logger.warning si no hay suscritos).
- [x] Licencia de prueba (id 714) eliminada tras la validacion.
- [x] Tarea `MamayaAlertasLicencias` creada y verificada (`schtasks /query`), proxima ejecucion 12:00.

---

## Evidencia recomendada para adjuntar al PR

- Captura del **dashboard** con los 5 graficos visibles.
- Captura del **dashboard filtrado** por un tenant/empresa (mostrando que los graficos cambian).
- Captura del **formulario de Usuario** con el checkbox "Recibir alertas de vencimiento de licencias".
- Captura del **email recibido** con el formato de resumen ejecutivo.
- Captura de la salida de `schtasks /query /tn "MamayaAlertasLicencias"` mostrando la tarea habilitada.
- (Opcional) Captura del log del comando `enviar_alertas` mostrando los conteos.

---

## Notas para el revisor

- Chart.js se carga por **CDN**; no se agregaron dependencias de Python.
- El campo `recibir_alertas_vencimiento` es **opt-in** (`default=False`): ningun usuario recibe alertas hasta marcar el checkbox.
- La tarea de Windows quedo en modo **"Solo interactivo"** y con condiciones de energia por defecto (no inicia en bateria). Para produccion conviene reconfigurarla como "Ejecutar aunque el usuario no inicie sesion" y revisar la pestania Condiciones.
- Recordatorio de seguridad (fuera del alcance de este PR): las credenciales SMTP estan en texto plano en `config/settings.py`; se recomienda moverlas a variables de entorno (`.env`).
