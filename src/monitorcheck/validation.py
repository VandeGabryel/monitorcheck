"""Validações de entrada compartilhadas pelas interfaces do MonitorCheck."""

from __future__ import annotations

import ipaddress
import math
import re
from urllib.parse import urlsplit

DEFAULT_TIMEOUT = 3.0
_HOST_LABEL = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


class ValidationError(ValueError):
    """Indica que uma entrada não atende às regras do MonitorCheck."""


def validate_host(value: str) -> str:
    """Valida um endereço IP ou nome de host sem consultar a rede."""

    host = value.strip()
    if not host:
        raise ValidationError("o host não pode estar vazio")

    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass

    if "://" in host or any(character in host for character in "/?#@:[]"):
        raise ValidationError(
            "informe somente o host ou IP, sem esquema, porta ou caminho"
        )

    hostname = host[:-1] if host.endswith(".") else host
    if not hostname or len(hostname) > 253:
        raise ValidationError("o nome de host deve ter até 253 caracteres")

    try:
        ascii_hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError as error:
        raise ValidationError("nome de host inválido") from error

    if any(not _HOST_LABEL.fullmatch(label) for label in ascii_hostname.split(".")):
        raise ValidationError("nome de host inválido")

    return host


def validate_ports(value: str) -> tuple[int, ...]:
    """Converte uma lista separada por vírgulas em portas TCP únicas."""

    if not value.strip():
        raise ValidationError("a lista de portas não pode estar vazia")

    ports: list[int] = []
    seen: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            raise ValidationError(
                "use uma lista de portas separadas por vírgulas, como 80,443"
            )
        try:
            port = int(item)
        except ValueError as error:
            raise ValidationError(f"porta inválida: {item!r}") from error
        if not 1 <= port <= 65535:
            raise ValidationError(
                f"a porta {port} está fora do intervalo de 1 a 65535"
            )
        if port not in seen:
            ports.append(port)
            seen.add(port)

    return tuple(ports)


def validate_url(value: str) -> str:
    """Valida uma URL HTTP/HTTPS sem realizar requisições."""

    url = value.strip()
    if not url or any(character.isspace() for character in url):
        raise ValidationError("informe uma URL sem espaços")

    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise ValidationError(f"URL inválida: {error}") from error

    if parsed.scheme.lower() not in {"http", "https"}:
        raise ValidationError("a URL deve usar o esquema http ou https")
    if not parsed.netloc or parsed.hostname is None:
        raise ValidationError("a URL deve conter um host")
    if parsed.username is not None or parsed.password is not None:
        raise ValidationError("credenciais na URL não são aceitas")

    validate_host(parsed.hostname)
    if port is not None and not 1 <= port <= 65535:
        raise ValidationError("a porta da URL deve estar entre 1 e 65535")

    return url


def validate_timeout(value: str) -> float:
    """Valida um timeout positivo e finito, expresso em segundos."""

    try:
        timeout = float(value)
    except ValueError as error:
        raise ValidationError("o timeout deve ser um número") from error

    if not math.isfinite(timeout) or timeout <= 0:
        raise ValidationError("o timeout deve ser positivo e finito")
    return timeout
