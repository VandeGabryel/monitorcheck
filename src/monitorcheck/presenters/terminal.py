"""Consolidação e apresentação dos resultados no terminal."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Sequence, TextIO

from monitorcheck.models import CheckResult, CheckType, ResultStatus

_RESET = "\033[0m"
_STATUS_COLORS = {
    ResultStatus.SUCCESS: "\033[32m",
    ResultStatus.WARNING: "\033[33m",
    ResultStatus.ERROR: "\033[31m",
    ResultStatus.INFO: "\033[36m",
    ResultStatus.SKIPPED: "\033[90m",
}
_OUTCOME_LABELS = {
    "open": "aberta",
    "refused": "recusada",
    "timeout": "timeout",
    "socket_error": "erro de socket",
    "response": "resposta recebida",
    "http_error": "erro HTTP",
    "network_error": "erro de rede",
    "tls_error": "erro TLS",
}


@dataclass(frozen=True, slots=True)
class ReportSummary:
    """Contagens e estado geral calculados a partir dos resultados."""

    total: int
    successes: int
    warnings: int
    failures: int
    informational: int
    skipped: int

    @property
    def overall_status(self) -> ResultStatus:
        if self.failures:
            return ResultStatus.ERROR
        if self.warnings:
            return ResultStatus.WARNING
        if self.successes:
            return ResultStatus.SUCCESS
        if self.informational:
            return ResultStatus.INFO
        return ResultStatus.SKIPPED


def summarize_results(results: Sequence[CheckResult]) -> ReportSummary:
    """Calcula as contagens usadas no resumo e no código de saída."""

    return ReportSummary(
        total=len(results),
        successes=sum(result.status is ResultStatus.SUCCESS for result in results),
        warnings=sum(result.status is ResultStatus.WARNING for result in results),
        failures=sum(result.status is ResultStatus.ERROR for result in results),
        informational=sum(result.status is ResultStatus.INFO for result in results),
        skipped=sum(result.status is ResultStatus.SKIPPED for result in results),
    )


def supports_color(stream: TextIO | None = None) -> bool:
    """Indica se o fluxo de saída se apresenta como um terminal interativo."""

    output = stream if stream is not None else sys.stdout
    return bool(getattr(output, "isatty", lambda: False)())


def _status_label(status: ResultStatus, use_color: bool) -> str:
    label = f"[{status.name}]"
    if not use_color:
        return label
    return f"{_STATUS_COLORS[status]}{label}{_RESET}"


def _duration_label(result: CheckResult) -> str:
    if result.duration_ms is None:
        return "não disponível"
    return f"{result.duration_ms:.2f} ms"


def _format_dns(result: CheckResult, use_color: bool) -> list[str]:
    if result.check_type is not CheckType.DNS:
        raise ValueError("a seção DNS aceita apenas resultados DNS")

    lines = [
        "DNS",
        f"  Status: {_status_label(result.status, use_color)}",
        f"  Alvo: {result.target}",
        f"  Mensagem: {result.message}",
        f"  Duração: {_duration_label(result)}",
    ]
    addresses = result.details.get("addresses", ())
    if addresses:
        lines.append(f"  Endereços: {', '.join(map(str, addresses))}")
    return lines


def _format_tcp(results: Sequence[CheckResult], use_color: bool) -> list[str]:
    lines = ["TCP"]
    for result in results:
        if result.check_type is not CheckType.TCP:
            raise ValueError("a seção TCP aceita apenas resultados TCP")

        port = result.details.get("port", "?")
        outcome = result.details.get("outcome")
        lines.extend(
            [
                f"  Porta {port} {_status_label(result.status, use_color)}",
                f"    Alvo: {result.target}",
                f"    Mensagem: {result.message}",
                f"    Duração: {_duration_label(result)}",
            ]
        )
        if outcome:
            lines.append(f"    Resultado: {_OUTCOME_LABELS.get(str(outcome), outcome)}")
    return lines


def _format_http(result: CheckResult, use_color: bool) -> list[str]:
    if result.check_type is not CheckType.HTTP:
        raise ValueError("a seção HTTP aceita apenas resultados HTTP")

    lines = [
        "HTTP/HTTPS",
        f"  Status: {_status_label(result.status, use_color)}",
        f"  Mensagem: {result.message}",
        f"  Duração: {_duration_label(result)}",
    ]
    requested_url = result.details.get("requested_url", result.target)
    final_url = result.details.get("final_url")
    status_code = result.details.get("status_code")
    outcome = result.details.get("outcome")
    lines.append(f"  URL solicitada: {requested_url}")
    if final_url:
        lines.append(f"  URL final: {final_url}")
    if status_code is not None:
        lines.append(f"  Código HTTP: {status_code}")
    if outcome:
        lines.append(f"  Resultado: {_OUTCOME_LABELS.get(str(outcome), outcome)}")
    return lines


def _format_summary(summary: ReportSummary, use_color: bool) -> list[str]:
    lines = [
        "Resumo",
        f"  Total de verificações: {summary.total}",
        f"  Sucessos: {summary.successes}",
        f"  Avisos: {summary.warnings}",
        f"  Falhas: {summary.failures}",
    ]
    if summary.informational:
        lines.append(f"  Informativas: {summary.informational}")
    if summary.skipped:
        lines.append(f"  Não executadas: {summary.skipped}")
    lines.append(
        f"  Resultado geral: {_status_label(summary.overall_status, use_color)}"
    )
    return lines


def _format_legend(use_color: bool) -> str:
    entries = (
        (ResultStatus.SUCCESS, "sucesso"),
        (ResultStatus.WARNING, "aviso"),
        (ResultStatus.ERROR, "falha"),
        (ResultStatus.INFO, "informação"),
        (ResultStatus.SKIPPED, "não executado"),
    )
    labels = [
        f"{_status_label(status, use_color)}={meaning}"
        for status, meaning in entries
    ]
    return f"Legenda: {' | '.join(labels)}"


def format_report(
    *,
    target: str,
    timeout: float,
    dns_result: CheckResult,
    tcp_results: Sequence[CheckResult] = (),
    http_result: CheckResult | None = None,
    use_color: bool = False,
) -> str:
    """Cria o relatório terminal completo para as verificações executadas."""

    results = [dns_result, *tcp_results]
    if http_result is not None:
        results.append(http_result)

    sections = [
        ["=== MonitorCheck ===", f"Alvo principal: {target}", f"Timeout: {timeout:g} s"],
        _format_dns(dns_result, use_color),
    ]
    if tcp_results:
        sections.append(_format_tcp(tcp_results, use_color))
    if http_result is not None:
        sections.append(_format_http(http_result, use_color))

    summary = summarize_results(results)
    sections.append(_format_summary(summary, use_color))
    sections.append([_format_legend(use_color)])
    return "\n\n".join("\n".join(section) for section in sections)

