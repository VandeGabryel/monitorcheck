"""Testes do relatório consolidado de terminal."""

import unittest

from monitorcheck.models import CheckResult, CheckType, ResultStatus
from monitorcheck.presenters.terminal import format_report, summarize_results


def _dns_result() -> CheckResult:
    return CheckResult(
        CheckType.DNS,
        "example.test",
        ResultStatus.SUCCESS,
        "2 endereço(s) encontrado(s).",
        1.25,
        {"addresses": ("192.0.2.1", "2001:db8::1")},
    )


def _tcp_results() -> tuple[CheckResult, ...]:
    return (
        CheckResult(
            CheckType.TCP,
            "example.test:80",
            ResultStatus.SUCCESS,
            "Conexão estabelecida.",
            2.5,
            {"port": 80, "outcome": "open"},
        ),
        CheckResult(
            CheckType.TCP,
            "example.test:81",
            ResultStatus.ERROR,
            "Conexão recusada.",
            3.75,
            {"port": 81, "outcome": "refused"},
        ),
    )


def _http_result(status: ResultStatus = ResultStatus.WARNING) -> CheckResult:
    return CheckResult(
        CheckType.HTTP,
        "https://example.test/start",
        status,
        "Resposta HTTP recebida sem código de status.",
        4.5,
        {
            "requested_url": "https://example.test/start",
            "final_url": "https://example.test/final",
            "status_code": None,
            "outcome": "response",
        },
    )


class ReportSummaryTests(unittest.TestCase):
    def test_counts_results_and_prioritizes_failure(self) -> None:
        results = [_dns_result(), *_tcp_results(), _http_result()]

        summary = summarize_results(results)

        self.assertEqual(summary.total, 4)
        self.assertEqual(summary.successes, 2)
        self.assertEqual(summary.warnings, 1)
        self.assertEqual(summary.failures, 1)
        self.assertEqual(summary.overall_status, ResultStatus.ERROR)


class TerminalReportTests(unittest.TestCase):
    def test_report_contains_sections_details_and_summary_without_color(self) -> None:
        report = format_report(
            target="example.test",
            timeout=2.0,
            dns_result=_dns_result(),
            tcp_results=_tcp_results(),
            http_result=_http_result(),
            use_color=False,
        )

        self.assertIn("=== MonitorCheck ===", report)
        self.assertIn("Alvo principal: example.test", report)
        self.assertIn("Timeout: 2 s", report)
        self.assertIn("Endereços: 192.0.2.1, 2001:db8::1", report)
        self.assertIn("Porta 80 [SUCCESS]", report)
        self.assertIn("Porta 81 [ERROR]", report)
        self.assertIn("URL final: https://example.test/final", report)
        self.assertIn("Total de verificações: 4", report)
        self.assertIn("Sucessos: 2", report)
        self.assertIn("Avisos: 1", report)
        self.assertIn("Falhas: 1", report)
        self.assertIn("Resultado geral: [ERROR]", report)
        self.assertIn("Legenda:", report)
        self.assertNotIn("\033[", report)

    def test_color_adds_ansi_without_replacing_status_text(self) -> None:
        report = format_report(
            target="example.test",
            timeout=3.0,
            dns_result=_dns_result(),
            use_color=True,
        )

        self.assertIn("\033[32m[SUCCESS]\033[0m", report)
        self.assertIn("SUCCESS", report)
        self.assertIn("Legenda:", report)

    def test_omits_sections_that_were_not_requested(self) -> None:
        report = format_report(
            target="example.test",
            timeout=3.0,
            dns_result=_dns_result(),
        )

        self.assertIn("\nDNS\n", report)
        self.assertNotIn("\nTCP\n", report)
        self.assertNotIn("\nHTTP/HTTPS\n", report)
        self.assertIn("Total de verificações: 1", report)


if __name__ == "__main__":
    unittest.main()
