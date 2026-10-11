"""Testes da orquestração compartilhada, sem acesso real à rede."""

import unittest
from unittest.mock import patch

from monitorcheck.models import CheckResult, CheckType, ResultStatus
from monitorcheck.runner import run_checks


def result(check_type: CheckType, target: str) -> CheckResult:
    return CheckResult(check_type, target, ResultStatus.SUCCESS, "Sucesso.", 1.0)


class RunnerTests(unittest.TestCase):
    @patch("monitorcheck.runner.check_http")
    @patch("monitorcheck.runner.check_tcp_ports")
    @patch("monitorcheck.runner.resolve_host")
    def test_runs_all_requested_checks(self, resolver, tcp_checker, http_checker) -> None:
        dns_result = result(CheckType.DNS, "localhost")
        tcp_results = (result(CheckType.TCP, "localhost:8000"),)
        http_result = result(CheckType.HTTP, "http://localhost:8000")
        resolver.return_value = dns_result
        tcp_checker.return_value = tcp_results
        http_checker.return_value = http_result

        execution = run_checks(
            "localhost",
            (8000,),
            "http://localhost:8000",
            0.5,
        )

        resolver.assert_called_once_with("localhost")
        tcp_checker.assert_called_once_with("localhost", (8000,), 0.5)
        http_checker.assert_called_once_with("http://localhost:8000", 0.5)
        self.assertIs(execution.dns_result, dns_result)
        self.assertEqual(execution.tcp_results, tcp_results)
        self.assertIs(execution.http_result, http_result)
        self.assertEqual(execution.all_results, (dns_result, *tcp_results, http_result))

    @patch("monitorcheck.runner.check_http")
    @patch("monitorcheck.runner.check_tcp_ports")
    @patch("monitorcheck.runner.resolve_host")
    def test_skips_optional_checks_when_not_requested(
        self, resolver, tcp_checker, http_checker
    ) -> None:
        dns_result = result(CheckType.DNS, "localhost")
        resolver.return_value = dns_result

        execution = run_checks("localhost", (), None, 3.0)

        tcp_checker.assert_not_called()
        http_checker.assert_not_called()
        self.assertEqual(execution.tcp_results, ())
        self.assertIsNone(execution.http_result)
        self.assertEqual(execution.all_results, (dns_result,))


if __name__ == "__main__":
    unittest.main()
