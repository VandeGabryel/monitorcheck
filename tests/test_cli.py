"""Testes do parsing e das validações da CLI."""

import argparse
import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

from monitorcheck.cli import (
    main,
    parse_args,
    parse_host,
    parse_ports,
    parse_timeout,
    parse_url,
)
from monitorcheck.models import CheckResult, CheckType, ResultStatus


class CliParsingTests(unittest.TestCase):
    def test_parses_complete_configuration(self) -> None:
        config = parse_args(
            [
                "example.com",
                "--ports",
                "80, 443,80",
                "--url",
                "https://example.com/health",
                "--timeout",
                "1.5",
                "--no-color",
            ]
        )

        self.assertEqual(config.host, "example.com")
        self.assertEqual(config.ports, (80, 443))
        self.assertEqual(config.url, "https://example.com/health")
        self.assertEqual(config.timeout, 1.5)
        self.assertFalse(config.use_color)

    def test_uses_safe_defaults(self) -> None:
        config = parse_args(["127.0.0.1"])

        self.assertEqual(config.ports, ())
        self.assertIsNone(config.url)
        self.assertEqual(config.timeout, 3.0)
        self.assertTrue(config.use_color)


class CliDnsIntegrationTests(unittest.TestCase):
    @patch("monitorcheck.cli.resolve_host")
    def test_main_presents_dns_result_and_returns_success(self, resolver) -> None:
        resolver.return_value = CheckResult(
            check_type=CheckType.DNS,
            target="example.com",
            status=ResultStatus.SUCCESS,
            message="1 endereço encontrado.",
            duration_ms=2.5,
            details={"addresses": ("192.0.2.1",)},
        )
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(["example.com"])

        self.assertEqual(exit_code, 0)
        self.assertIn("=== MonitorCheck ===", output.getvalue())
        self.assertIn("Status: [SUCCESS]", output.getvalue())
        self.assertIn("192.0.2.1", output.getvalue())
        self.assertIn("Resultado geral: [SUCCESS]", output.getvalue())
        resolver.assert_called_once_with("example.com")

    @patch("monitorcheck.cli.resolve_host")
    def test_main_returns_failure_for_dns_error(self, resolver) -> None:
        resolver.return_value = CheckResult(
            check_type=CheckType.DNS,
            target="missing.invalid",
            status=ResultStatus.ERROR,
            message="Não foi possível resolver o host.",
            duration_ms=1.0,
        )

        with redirect_stdout(io.StringIO()):
            exit_code = main(["missing.invalid"])

        self.assertEqual(exit_code, 1)


class CliTcpIntegrationTests(unittest.TestCase):
    @patch("monitorcheck.cli.check_tcp_ports")
    @patch("monitorcheck.cli.resolve_host")
    def test_main_checks_explicit_ports_with_configured_timeout(
        self, resolver, tcp_checker
    ) -> None:
        resolver.return_value = CheckResult(
            CheckType.DNS,
            "localhost",
            ResultStatus.SUCCESS,
            "1 endereço encontrado.",
            1.0,
            {"addresses": ("127.0.0.1",)},
        )
        tcp_checker.return_value = (
            CheckResult(
                CheckType.TCP,
                "localhost:8000",
                ResultStatus.SUCCESS,
                "Conexão estabelecida.",
                2.0,
                {"port": 8000, "outcome": "open"},
            ),
            CheckResult(
                CheckType.TCP,
                "localhost:8001",
                ResultStatus.ERROR,
                "Conexão recusada.",
                3.0,
                {"port": 8001, "outcome": "refused"},
            ),
        )
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(
                ["localhost", "--ports", "8000,8001", "--timeout", "0.5"]
            )

        self.assertEqual(exit_code, 1)
        self.assertIn("Porta 8000 [SUCCESS]", output.getvalue())
        self.assertIn("Porta 8001 [ERROR]", output.getvalue())
        self.assertIn("Falhas: 1", output.getvalue())
        tcp_checker.assert_called_once_with("localhost", (8000, 8001), 0.5)


class CliHttpIntegrationTests(unittest.TestCase):
    @patch("monitorcheck.cli.check_http")
    @patch("monitorcheck.cli.resolve_host")
    def test_main_checks_explicit_url_with_configured_timeout(
        self, resolver, http_checker
    ) -> None:
        resolver.return_value = CheckResult(
            CheckType.DNS,
            "localhost",
            ResultStatus.SUCCESS,
            "1 endereço encontrado.",
            1.0,
            {"addresses": ("127.0.0.1",)},
        )
        http_checker.return_value = CheckResult(
            CheckType.HTTP,
            "http://localhost:8000/start",
            ResultStatus.WARNING,
            "Resposta HTTP recebida sem código de status.",
            4.0,
            {
                "requested_url": "http://localhost:8000/start",
                "final_url": "http://localhost:8000/final",
                "status_code": None,
                "outcome": "response",
            },
        )
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(
                [
                    "localhost",
                    "--url",
                    "http://localhost:8000/start",
                    "--timeout",
                    "0.75",
                ]
            )

        self.assertEqual(exit_code, 0)
        self.assertIn("HTTP/HTTPS", output.getvalue())
        self.assertIn("Status: [WARNING]", output.getvalue())
        self.assertIn("Resultado geral: [WARNING]", output.getvalue())
        self.assertIn("URL final: http://localhost:8000/final", output.getvalue())
        http_checker.assert_called_once_with("http://localhost:8000/start", 0.75)

    @patch("monitorcheck.cli.supports_color", return_value=True)
    @patch("monitorcheck.cli.resolve_host")
    def test_no_color_never_emits_ansi(self, resolver, _supports_color) -> None:
        resolver.return_value = CheckResult(
            CheckType.DNS,
            "localhost",
            ResultStatus.SUCCESS,
            "Resolvido.",
            1.0,
            {"addresses": ("127.0.0.1",)},
        )
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = main(["localhost", "--no-color"])

        self.assertEqual(exit_code, 0)
        self.assertNotIn("\033[", output.getvalue())


class InputValidationTests(unittest.TestCase):
    def test_accepts_hostname_ipv4_and_ipv6(self) -> None:
        for host in ("example.com", "127.0.0.1", "::1", "localhost"):
            with self.subTest(host=host):
                self.assertEqual(parse_host(host), host)

    def test_rejects_host_with_url_components(self) -> None:
        for host in ("https://example.com", "example.com:443", "example.com/path"):
            with self.subTest(host=host):
                with self.assertRaises(argparse.ArgumentTypeError):
                    parse_host(host)

    def test_validates_and_deduplicates_ports(self) -> None:
        self.assertEqual(parse_ports("80,443,80"), (80, 443))
        for ports in ("", "0", "65536", "80,,443", "http"):
            with self.subTest(ports=ports):
                with self.assertRaises(argparse.ArgumentTypeError):
                    parse_ports(ports)

    def test_accepts_only_http_urls_with_a_host(self) -> None:
        self.assertEqual(parse_url("https://example.com/a"), "https://example.com/a")
        for url in ("example.com", "ftp://example.com", "https:///path", "https://a b"):
            with self.subTest(url=url):
                with self.assertRaises(argparse.ArgumentTypeError):
                    parse_url(url)

    def test_timeout_must_be_positive_and_finite(self) -> None:
        self.assertEqual(parse_timeout("0.5"), 0.5)
        for timeout in ("0", "-1", "nan", "inf", "soon"):
            with self.subTest(timeout=timeout):
                with self.assertRaises(argparse.ArgumentTypeError):
                    parse_timeout(timeout)


if __name__ == "__main__":
    unittest.main()
