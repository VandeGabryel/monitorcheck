"""Verificação HTTP/HTTPS independente da interface de apresentação."""

from __future__ import annotations

import socket
import ssl
import urllib.error
import urllib.request
from time import perf_counter

from monitorcheck.models import CheckResult, CheckType, ResultStatus


def _elapsed_ms(started_at: float) -> float:
    """Retorna o tempo decorrido em milissegundos."""

    return (perf_counter() - started_at) * 1_000


def _error_result(
    url: str,
    started_at: float,
    message: str,
    outcome: str,
    error: BaseException,
    *,
    final_url: str | None = None,
    status_code: int | None = None,
) -> CheckResult:
    """Cria um resultado controlado para uma falha HTTP ou de transporte."""

    return CheckResult(
        check_type=CheckType.HTTP,
        target=url,
        status=ResultStatus.ERROR,
        message=message,
        duration_ms=_elapsed_ms(started_at),
        details={
            "requested_url": url,
            "final_url": final_url,
            "status_code": status_code,
            "outcome": outcome,
            "error": str(error),
        },
    )


def _url_error_result(
    url: str,
    started_at: float,
    error: urllib.error.URLError,
) -> CheckResult:
    """Classifica o motivo encapsulado por ``URLError``."""

    reason = error.reason
    if isinstance(reason, (TimeoutError, socket.timeout)):
        return _error_result(
            url,
            started_at,
            "Tempo limite excedido.",
            "timeout",
            error,
        )
    if isinstance(reason, (ssl.SSLError, ssl.CertificateError)):
        return _error_result(
            url,
            started_at,
            f"Erro TLS: {reason}",
            "tls_error",
            error,
        )
    return _error_result(
        url,
        started_at,
        f"Erro de conexão/rede: {reason}",
        "network_error",
        error,
    )


def check_http(url: str, timeout: float) -> CheckResult:
    """Executa um GET e retorna metadados, sem consumir o corpo da resposta."""

    started_at = perf_counter()
    request = urllib.request.Request(url, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            final_url = response.geturl()
    except urllib.error.HTTPError as error:
        try:
            final_url = error.geturl()
            return _error_result(
                url,
                started_at,
                f"Erro HTTP {error.code}: {error.reason}.",
                "http_error",
                error,
                final_url=final_url,
                status_code=error.code,
            )
        finally:
            error.close()
    except (TimeoutError, socket.timeout) as error:
        return _error_result(
            url,
            started_at,
            "Tempo limite excedido.",
            "timeout",
            error,
        )
    except (ssl.SSLError, ssl.CertificateError) as error:
        return _error_result(
            url,
            started_at,
            f"Erro TLS: {error}",
            "tls_error",
            error,
        )
    except urllib.error.URLError as error:
        return _url_error_result(url, started_at, error)
    except OSError as error:
        return _error_result(
            url,
            started_at,
            f"Erro de conexão/rede: {error}",
            "network_error",
            error,
        )

    status = (
        ResultStatus.SUCCESS
        if status_code is not None and 200 <= status_code < 400
        else ResultStatus.WARNING
    )
    message = (
        f"Resposta HTTP recebida: {status_code}."
        if status_code is not None
        else "Resposta HTTP recebida sem código de status."
    )
    return CheckResult(
        check_type=CheckType.HTTP,
        target=url,
        status=status,
        message=message,
        duration_ms=_elapsed_ms(started_at),
        details={
            "requested_url": url,
            "final_url": final_url,
            "status_code": status_code,
            "outcome": "response",
        },
    )

