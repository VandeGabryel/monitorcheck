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

