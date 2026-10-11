"""Orquestração das verificações, independente das interfaces."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from monitorcheck.checks.dns import resolve_host
from monitorcheck.checks.http import check_http
from monitorcheck.checks.tcp import check_tcp_ports
from monitorcheck.models import CheckResult


@dataclass(frozen=True, slots=True)
class RunResults:
    """Resultados estruturados de uma execução do MonitorCheck."""

    dns_result: CheckResult
    tcp_results: tuple[CheckResult, ...] = ()
    http_result: CheckResult | None = None

    @property
    def all_results(self) -> tuple[CheckResult, ...]:
        """Retorna somente as verificações efetivamente executadas."""

        results = (self.dns_result, *self.tcp_results)
        if self.http_result is not None:
            return (*results, self.http_result)
        return results


def run_checks(
    host: str,
    ports: Sequence[int],
    url: str | None,
    timeout: float,
) -> RunResults:
    """Executa DNS e, quando solicitadas, as verificações TCP e HTTP."""

    dns_result = resolve_host(host)
    tcp_results = check_tcp_ports(host, ports, timeout) if ports else ()
    http_result = check_http(url, timeout) if url is not None else None
    return RunResults(
        dns_result=dns_result,
        tcp_results=tcp_results,
        http_result=http_result,
    )
