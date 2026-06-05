# Programar la alarma de vencimiento en Windows (Task Scheduler)

Automatiza el envío diario del comando `python manage.py enviar_alertas`, que avisa por
email a los usuarios que tengan marcado **"Recibir alertas de vencimiento de licencias"**
en su perfil cuando hay licencias próximas a vencer (a 30, 15, 7 y 1 día — configurable en
`ALERTAS_DIAS_AVISO` dentro de `config/settings.py`).

- **Tarea:** `MamayaAlertasLicencias`
- **Frecuencia:** diaria
- **Hora:** **12:00 (mediodía)** — elegida para asegurar que la PC esté encendida.

Rutas de esta instalación (ajustar si el proyecto se mueve de carpeta):

- Python del entorno virtual: `C:\Users\Ariany\Documents\Ariany\proyecto mamaya licencias\venv\Scripts\python.exe`
- Proyecto (donde está `manage.py`): `C:\Users\Ariany\Documents\Ariany\proyecto mamaya licencias`

---

## Opción A (recomendada): wrapper `.bat` + tarea programada

Por los espacios en la ruta del proyecto, lo más robusto es usar un `.bat` que invoque al
Python del venv. Ya se incluye el archivo **`enviar_alertas.bat`** en la raíz del proyecto:

```bat
@echo off
cd /d "C:\Users\Ariany\Documents\Ariany\proyecto mamaya licencias"
"C:\Users\Ariany\Documents\Ariany\proyecto mamaya licencias\venv\Scripts\python.exe" manage.py enviar_alertas
```

### Crear la tarea (PowerShell o CMD, una sola línea)

```bat
schtasks /create /tn "MamayaAlertasLicencias" /tr "\"C:\Users\Ariany\Documents\Ariany\proyecto mamaya licencias\enviar_alertas.bat\"" /sc DAILY /st 12:00
```

> Las comillas escapadas `\"...\"` son necesarias porque la ruta del `.bat` tiene espacios.

---

## Opción B: tarea programada sin `.bat` (llamando al python del venv directo)

```bat
schtasks /create /tn "MamayaAlertasLicencias" /tr "\"C:\Users\Ariany\Documents\Ariany\proyecto mamaya licencias\venv\Scripts\python.exe\" \"C:\Users\Ariany\Documents\Ariany\proyecto mamaya licencias\manage.py\" enviar_alertas" /sc DAILY /st 12:00
```

---

## Verificar / administrar la tarea

```bat
:: Ejecutarla ahora mismo (prueba manual, sin esperar a las 12:00)
schtasks /run /tn "MamayaAlertasLicencias"

:: Ver el estado y la última ejecución
schtasks /query /tn "MamayaAlertasLicencias" /v /fo LIST

:: Eliminarla (si hay que rehacerla)
schtasks /delete /tn "MamayaAlertasLicencias" /f
```

---

## Notas

- **Permisos:** si `schtasks /create` pide privilegios, abrir la consola **como Administrador**.
- **Cuenta y "ejecutar aunque el usuario no haya iniciado sesión":** por defecto la tarea
  corre con el usuario actual y solo cuando hay sesión iniciada. Para correrla siempre,
  configurarla desde la GUI (`taskschd.msc`) con la opción *"Ejecutar tanto si el usuario
  inició sesión como si no"*.
- **Email:** el envío usa Gmail SMTP ya configurado en `config/settings.py`
  (`smtp.gmail.com:587`, TLS, app-password). Si Gmail rota el app-password o activa 2FA, el
  envío fallará — probar con `schtasks /run` antes de confiar en la automatización.
- **Sin destinatarios:** si ningún usuario tiene el checkbox marcado, el comando hace
  *fallback* a `DEFAULT_FROM_EMAIL` y deja un `warning` en el log, para no perder la alerta.
- **Logs:** el comando usa el `logging` de Python (`logger = logging.getLogger(__name__)`);
  la salida también aparece en la consola/registro de la tarea programada.
