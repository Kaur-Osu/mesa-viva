"""Reglas compartidas; el servidor es la autoridad de validación."""
import re
import unicodedata
from functools import lru_cache
import dns.nameserver
import dns.resolver
from django.core.cache import cache
from django.core.exceptions import ValidationError
from email_validator import validate_email, EmailSyntaxError, EmailUndeliverableError


@lru_cache(maxsize=1)
def email_dns_resolver():
    # HTTPS evita depender de puertos DNS que algunas redes bloquean.
    # Las IP de arranque evitan una consulta DNS previa para resolver el proveedor.
    resolver = dns.resolver.Resolver(configure=False)
    resolver.nameservers = [
        dns.nameserver.DoHNameserver("https://cloudflare-dns.com/dns-query", bootstrap_address="1.1.1.1"),
        dns.nameserver.DoHNameserver("https://dns.google/dns-query", bootstrap_address="8.8.8.8"),
    ]
    resolver.timeout = 2
    resolver.lifetime = 5
    resolver.cache = dns.resolver.Cache()
    return resolver


def check_email_domain(email):
    """Verifica DNS sin contactar buzones ni enviar mensajes."""
    try:
        result = validate_email(email, check_deliverability=True, dns_resolver=email_dns_resolver())
    except EmailUndeliverableError:
        raise ValidationError("El dominio de este correo no existe o no está configurado para recibir mensajes. Revisa lo que escribiste después de @.", code="email_domain") from None
    if not getattr(result, "mx", None):
        # La biblioteca devuelve resultado indeterminado ante timeout DNS.
        # No debe interpretarse como una comprobación satisfactoria.
        raise ValidationError("No pudimos verificar el dominio del correo en este momento. Revisa tu conexión e inténtalo de nuevo.", code="email_dns_unavailable")


def validate_registration_email(value):
    try:
        result = validate_email(value, check_deliverability=False)
    except EmailSyntaxError:
        raise ValidationError("Escribe un correo válido, sin espacios ni caracteres invisibles; por ejemplo, nombre@gmail.com.", code="email_syntax") from None
    normalized = result.normalized.lower()
    domain = result.ascii_domain
    key = "email-domain-validated:" + domain
    if not cache.get(key):
        check_email_domain(normalized)
        cache.set(key, True, 3600)
    return normalized


def clean_person_name(value):
    value = unicodedata.normalize("NFC", value).replace("’", "'")
    if (not 2 <= len(value) <= 80 or not value[0].isalpha() or not value[-1].isalpha()
        or not all(c.isalpha() or c in " '-" for c in value)
        or re.search(r"[ '-]{2}", value) or sum(c.isalpha() for c in value) < 2):
        raise ValidationError("Escribe un nombre de 2 a 80 caracteres, con letras y separadores simples. No se permiten números, símbolos ni espacios repetidos.")
    return value


class StrongPasswordValidator:
    def validate(self, password, user=None):
        errors = []
        if len(password) > 128:
            errors.append("La contraseña debe tener como máximo 128 caracteres.")
        if not any(c.isupper() for c in password) or not any(c.islower() for c in password) or not re.search(r"[0-9]", password):
            errors.append("Incluye al menos una mayúscula, una minúscula y un número.")
        if any(unicodedata.category(c).startswith("C") for c in password):
            errors.append("La contraseña no puede contener caracteres invisibles ni de control.")
        if re.search(r"(.)\1{3,}", password, re.IGNORECASE):
            errors.append("Evita repetir el mismo carácter cuatro veces seguidas.")
        if any(sequence in password.lower() for sequence in ("12345", "54321", "abcde", "edcba", "qwerty", "asdfgh")):
            errors.append("Evita secuencias predecibles como 12345, abcde o qwerty.")
        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return "Usa de 12 a 128 caracteres con mayúscula, minúscula y número. Evita secuencias, repeticiones y caracteres invisibles."
