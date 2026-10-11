"""Apresentação mínima no terminal durante os gates da Etapa 1."""

from __future__ import annotations

from monitorcheck.models import CheckResult, CheckType


def format_dns_result(result: CheckResult) -> str:
    """Formata somente o resultado DNS; não constitui o relatório final."""

    if result.check_type is not CheckType.DNS:
        raise ValueError("format_dns_result aceita apenas resultados DNS")

    lines = [
        f"DNS [{result.status.name}] {result.target}",
        f"  {result.message}",
    ]
    addresses = result.details.get("addresses", ())
    if addresses:
        lines.append(f"  Endereços: {', '.join(map(str, addresses))}")
    if result.duration_ms is not None:
        lines.append(f"  Duração: {result.duration_ms:.2f} ms")
    return "\n".join(lines)


def format_tcp_results(results: tuple[CheckResult, ...]) -> str:
    """Formata resultados TCP sem constituir o relatório final."""

    lines = ["TCP"]
    for result in results:
        if result.check_type is not CheckType.TCP:
            raise ValueError("format_tcp_results aceita apenas resultados TCP")

        port = result.details.get("port", "?")
        line = f"  {port} [{result.status.name}] {result.message}"
        if result.duration_ms is not None:
            line += f" ({result.duration_ms:.2f} ms)"
        lines.append(line)
    return "\n".join(lines)


def format_http_result(result: CheckResult) -> str:
    """Formata somente o resultado HTTP; não constitui o relatório final."""

    if result.check_type is not CheckType.HTTP:
        raise ValueError("format_http_result aceita apenas resultados HTTP")

    lines = [
        f"HTTP [{result.status.name}] {result.target}",
        f"  {result.message}",
    ]
    final_url = result.details.get("final_url")
    if final_url and final_url != result.target:
        lines.append(f"  URL final: {final_url}")
    if result.duration_ms is not None:
        lines.append(f"  Duração: {result.duration_ms:.2f} ms")
    return "\n".join(lines)

