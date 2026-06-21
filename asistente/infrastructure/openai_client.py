"""
Cliente REST minimo para la API de OpenAI (chat/completions).

Sigue el mismo enfoque que el sistema CUP (FICCT): NO usa el SDK oficial para
no agregar dependencias a requirements.txt; habla con la API REST usando
`urllib` de la libreria estandar de Python.

Configuracion (variables de entorno, con `settings` como fallback):
  - OPENAI_API_KEY : clave de la API (obligatoria).
  - OPENAI_MODEL   : modelo a usar. Por defecto: gpt-4o-mini.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from django.conf import settings

ENDPOINT = 'https://api.openai.com/v1/chat/completions'
MODELO_DEFECTO = 'gpt-4o-mini'


class AsistenteNoConfigurado(Exception):
    """Se lanza cuando falta la clave OPENAI_API_KEY."""


class AsistenteError(Exception):
    """Error de red o de la API al consultar el modelo."""


def _api_key() -> str:
    return (os.environ.get('OPENAI_API_KEY') or getattr(settings, 'OPENAI_API_KEY', '') or '').strip()


def _modelo() -> str:
    return (os.environ.get('OPENAI_MODEL') or getattr(settings, 'OPENAI_MODEL', '') or MODELO_DEFECTO).strip()


def chat(
    *,
    system: str,
    user: str,
    schema: dict | None = None,
    schema_name: str = 'respuesta',
    temperature: float = 0.0,
    max_tokens: int = 400,
    timeout: int = 20,
) -> str:
    """
    Envia un par de mensajes system+user al modelo y devuelve el texto de la
    respuesta. Si `schema` (un JSON Schema) se provee, fuerza salida
    estructurada en modo `strict`.

    Lanza `AsistenteNoConfigurado` si falta la clave y `AsistenteError` ante
    cualquier fallo de red o de la API.
    """
    api_key = _api_key()
    if not api_key:
        raise AsistenteNoConfigurado('Falta la clave OPENAI_API_KEY.')

    payload: dict = {
        'model': _modelo(),
        'temperature': temperature,
        'max_tokens': max_tokens,
        'messages': [
            {'role': 'system', 'content': system},
            {'role': 'user', 'content': user},
        ],
    }
    if schema is not None:
        payload['response_format'] = {
            'type': 'json_schema',
            'json_schema': {'name': schema_name, 'strict': True, 'schema': schema},
        }

    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        ENDPOINT,
        data=data,
        method='POST',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as exc:
        raise AsistenteError(f'OpenAI respondio {exc.code}.') from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise AsistenteError('No se pudo conectar con OpenAI.') from exc
    except json.JSONDecodeError as exc:
        raise AsistenteError('Respuesta invalida de OpenAI.') from exc

    choices = body.get('choices') or [{}]
    return (choices[0].get('message') or {}).get('content') or ''
