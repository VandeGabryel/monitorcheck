"""Verificações TCP independentes da interface de apresentação."""

from __future__ import annotations

import errno
import socket
from time import perf_counter
from typing import Iterable

from monitorcheck.models import CheckResult, CheckType, ResultStatus

_WINDOWS_CONNECTION_REFUSED = 10061


def _elapsed_ms(started_at: float) -> float:
    """Retorna o tempo decorrido em milissegundos."""

    return (perf_counter() - started_at) * 1_000


def _target(host: str, port: int) -> str:
    """Monta um alvo sem tornar endereços IPv6 ambíguos."""

    return f"[{host}]:{port}" if ":" in host else f"{host}:{port}"


def _error_result(
    host: str,
    port: int,
    started_at: float,
    message: str,
    outcome: str,
    error: OSError,
) -> CheckResult:
    """Cria o resultado comum das falhas de conexão."""

    details: dict[str, object] = {
        "port": port,
        "outcome": outcome,
        "error": str(error),
    }
    if error.errno is not None:
        details["errno"] = error.errno

    return CheckResult(
        check_type=CheckType.TCP,
        target=_target(host, port),
        status=ResultStatus.ERROR,
        message=message,
        duration_ms=_elapsed_ms(started_at),
        details=details,
    )


def check_tcp_port(host: str, port: int, timeout: float) -> CheckResult:
    """Tenta estabelecer uma conexão TCP com uma única porta."""

    started_at = perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout):
            pass
    except (TimeoutError, socket.timeout) as error:
        return _error_result(
            host,
            port,
            started_at,
            "Tempo limite excedido.",
            "timeout",
            error,
        )
    except ConnectionRefusedError as error:
        return _error_result(
            host,
            port,
            started_at,
            "Conexão recusada.",
            "refused",
            error,
        )
    except OSError as error:
        if error.errno in {errno.ECONNREFUSED, _WINDOWS_CONNECTION_REFUSED}:
            return _error_result(
                host,
                port,
                started_at,
                "Conexão recusada.",
                "refused",
                error,
            )
        return _error_result(
            host,
            port,
            started_at,
            f"Erro de socket: {error}",
            "socket_error",
            error,
        )

    return CheckResult(
        check_type=CheckType.TCP,
        target=_target(host, port),
        status=ResultStatus.SUCCESS,
        message="Conexão estabelecida.",
        duration_ms=_elapsed_ms(started_at),
        details={"port": port, "outcome": "open"},
    )


def check_tcp_ports(
    host: str,
    ports: Iterable[int],
    timeout: float,
) -> tuple[CheckResult, ...]:
    """Verifica sequencialmente apenas as portas fornecidas."""

    return tuple(check_tcp_port(host, port, timeout) for port in ports)

