"""Interface de linha de comando do MonitorCheck."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Sequence

from monitorcheck.presenters.terminal import (
    format_report,
    summarize_results,
    supports_color,
)
from monitorcheck.runner import run_checks
from monitorcheck.validation import (
    DEFAULT_TIMEOUT,
    ValidationError,
    validate_host,
    validate_ports,
    validate_timeout,
    validate_url,
)


@dataclass(frozen=True, slots=True)
class CliConfig:
    """Entradas já validadas fornecidas pela CLI."""

    host: str
    ports: tuple[int, ...]
    url: str | None
    timeout: float
    use_color: bool


def parse_host(value: str) -> str:
    """Adapta a validação compartilhada ao contrato do argparse."""
    try:
        return validate_host(value)
    except ValidationError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def parse_ports(value: str) -> tuple[int, ...]:
    """Adapta a validação compartilhada ao contrato do argparse."""
    try:
        return validate_ports(value)
    except ValidationError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def parse_url(value: str) -> str:
    """Adapta a validação compartilhada ao contrato do argparse."""
    try:
        return validate_url(value)
    except ValidationError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


def parse_timeout(value: str) -> float:
    """Adapta a validação compartilhada ao contrato do argparse."""
    try:
        return validate_timeout(value)
    except ValidationError as error:
        raise argparse.ArgumentTypeError(str(error)) from error


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
        help="desativa cores na saída",
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
    """Executa as verificações solicitadas e apresenta o relatório final."""

    config = parse_args(argv)
    execution = run_checks(
        config.host,
        config.ports,
        config.url,
        config.timeout,
    )

    print(
        format_report(
            target=config.host,
            timeout=config.timeout,
            dns_result=execution.dns_result,
            tcp_results=execution.tcp_results,
            http_result=execution.http_result,
            use_color=config.use_color and supports_color(),
        )
    )

    return 1 if summarize_results(execution.all_results).failures else 0

