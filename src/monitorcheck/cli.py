"""Interface de linha de comando e validação de entradas."""

from __future__ import annotations

import argparse
import ipaddress
import math
import re
from dataclasses import dataclass
from typing import Sequence
from urllib.parse import urlsplit

from monitorcheck.checks.dns import resolve_host
from monitorcheck.checks.tcp import check_tcp_ports
from monitorcheck.models import ResultStatus
from monitorcheck.presenters.terminal import format_dns_result, format_tcp_results

DEFAULT_TIMEOUT = 3.0
_HOST_LABEL = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$")


@dataclass(frozen=True, slots=True)
class CliConfig:
    """Entradas já validadas fornecidas pela CLI."""

    host: str
    ports: tuple[int, ...]
    url: str | None
    timeout: float
    use_color: bool


def parse_host(value: str) -> str:
    """Valida um endereço IP ou nome de host sem consultar a rede."""

    host = value.strip()
    if not host:
        raise argparse.ArgumentTypeError("o host não pode estar vazio")

    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        pass

    if "://" in host or any(character in host for character in "/?#@:[]"):
        raise argparse.ArgumentTypeError(
            "informe somente o host ou IP, sem esquema, porta ou caminho"
        )

    hostname = host[:-1] if host.endswith(".") else host
    if not hostname or len(hostname) > 253:
        raise argparse.ArgumentTypeError("o nome de host deve ter até 253 caracteres")

    try:
        ascii_hostname = hostname.encode("idna").decode("ascii")
    except UnicodeError as error:
        raise argparse.ArgumentTypeError("nome de host inválido") from error

    if any(not _HOST_LABEL.fullmatch(label) for label in ascii_hostname.split(".")):
        raise argparse.ArgumentTypeError("nome de host inválido")

    return host


def parse_ports(value: str) -> tuple[int, ...]:
    """Converte uma lista separada por vírgulas em portas TCP únicas."""

    if not value.strip():
        raise argparse.ArgumentTypeError("a lista de portas não pode estar vazia")

    ports: list[int] = []
    seen: set[int] = set()
    for item in value.split(","):
        item = item.strip()
        if not item:
            raise argparse.ArgumentTypeError(
                "use uma lista de portas separadas por vírgulas, como 80,443"
            )
        try:
            port = int(item)
        except ValueError as error:
            raise argparse.ArgumentTypeError(f"porta inválida: {item!r}") from error
        if not 1 <= port <= 65535:
            raise argparse.ArgumentTypeError(
                f"a porta {port} está fora do intervalo de 1 a 65535"
            )
        if port not in seen:
            ports.append(port)
            seen.add(port)

    return tuple(ports)


def parse_url(value: str) -> str:
    """Valida uma URL HTTP/HTTPS sem realizar requisições."""

    url = value.strip()
    if not url or any(character.isspace() for character in url):
        raise argparse.ArgumentTypeError("informe uma URL sem espaços")

    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError as error:
        raise argparse.ArgumentTypeError(f"URL inválida: {error}") from error

    if parsed.scheme.lower() not in {"http", "https"}:
        raise argparse.ArgumentTypeError("a URL deve usar o esquema http ou https")
    if not parsed.netloc or parsed.hostname is None:
        raise argparse.ArgumentTypeError("a URL deve conter um host")
    if parsed.username is not None or parsed.password is not None:
        raise argparse.ArgumentTypeError("credenciais na URL não são aceitas")

    parse_host(parsed.hostname)
    if port is not None and not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("a porta da URL deve estar entre 1 e 65535")

    return url


def parse_timeout(value: str) -> float:
    """Valida um timeout positivo e finito, expresso em segundos."""

    try:
        timeout = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("o timeout deve ser um número") from error

    if not math.isfinite(timeout) or timeout <= 0:
        raise argparse.ArgumentTypeError("o timeout deve ser positivo e finito")
    return timeout


def build_parser() -> argparse.ArgumentParser:
    """Cria o parser público da CLI."""

    parser = argparse.ArgumentParser(
        prog="monitorcheck",
        description="Verificações básicas de conectividade de hosts e serviços.",
    )
    parser.add_argument("host", type=parse_host, help="nome do host ou endereço IP")
    parser.add_argument(
        "--ports",
        type=parse_ports,
        default=(),
        metavar="PORTA,...",
        help="portas TCP separadas por vírgulas (ex.: 80,443)",
    )
    parser.add_argument(
        "--url",
        type=parse_url,
        help="URL HTTP ou HTTPS a verificar",
    )
    parser.add_argument(
        "--timeout",
        type=parse_timeout,
        default=DEFAULT_TIMEOUT,
        metavar="SEGUNDOS",
        help=f"timeout de cada operação (padrão: {DEFAULT_TIMEOUT:g}s)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="desativa cores na saída futura",
    )
    return parser


def parse_args(argv: Sequence[str] | None = None) -> CliConfig:
    """Interpreta argumentos e retorna uma configuração validada."""

    arguments = build_parser().parse_args(argv)
    return CliConfig(
        host=arguments.host,
        ports=arguments.ports,
        url=arguments.url,
        timeout=arguments.timeout,
        use_color=not arguments.no_color,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """Executa e apresenta as verificações DNS e TCP disponíveis."""

    config = parse_args(argv)
    dns_result = resolve_host(config.host)
    print(format_dns_result(dns_result))

    tcp_results = ()
    if config.ports:
        tcp_results = check_tcp_ports(config.host, config.ports, config.timeout)
        print(format_tcp_results(tcp_results))
    if config.url:
        print("HTTP/HTTPS ainda não implementado; --url não foi executado.")

    results = (dns_result, *tcp_results)
    return 0 if all(result.status is ResultStatus.SUCCESS for result in results) else 1

