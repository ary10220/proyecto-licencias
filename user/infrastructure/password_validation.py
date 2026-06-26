"""Validadores de contrasena del sistema."""

from __future__ import annotations

import re
import secrets
import string

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _


class ComplexPasswordValidator:
    """Exige una clave fuerte en recuperacion, primer ingreso y cambio normal."""

    def __init__(self, min_length: int = 10):
        self.min_length = min_length

    def validate(self, password, user=None):
        errors = []
        password = password or ""

        if len(password) < self.min_length:
            errors.append(
                _("La contrasena debe tener al menos %(min_length)d caracteres.")
                % {"min_length": self.min_length}
            )
        if not re.search(r"[A-Z]", password):
            errors.append(_("La contrasena debe incluir al menos una letra mayuscula."))
        if not re.search(r"[a-z]", password):
            errors.append(_("La contrasena debe incluir al menos una letra minuscula."))
        if not re.search(r"\d", password):
            errors.append(_("La contrasena debe incluir al menos un numero."))
        if not re.search(r"[^A-Za-z0-9\s]", password):
            errors.append(_("La contrasena debe incluir al menos un caracter especial, por ejemplo @, #, $, %, !."))
        if re.search(r"\s", password):
            errors.append(_("La contrasena no debe contener espacios."))

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return _(
            "Debe tener al menos %(min_length)d caracteres, una mayuscula, "
            "una minuscula, un numero y un caracter especial. No uses espacios."
        ) % {"min_length": self.min_length}


def generate_temporary_password(length: int = 14) -> str:
    """Genera una clave temporal compatible con las politicas del sistema."""
    length = max(length, 10)
    required = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%&*?-_"),
    ]
    alphabet = string.ascii_letters + string.digits + "!@#$%&*?-_"
    required.extend(secrets.choice(alphabet) for _ in range(length - len(required)))
    secrets.SystemRandom().shuffle(required)
    return "".join(required)
