"""Testes unitários da resolução DNS sem acesso real à Internet."""

import socket
import unittest
from unittest.mock import patch

from monitorcheck.checks.dns import resolve_host
from monitorcheck.models import CheckType, ResultStatus


class DnsResolutionTests(unittest.TestCase):
    @patch("monitorcheck.checks.dns.perf_counter", side_effect=[10.0, 10.025])
    @patch("monitorcheck.checks.dns.socket.getaddrinfo")
    def test_returns_unique_ipv4_and_ipv6_in_consistent_order(
        self, getaddrinfo, _perf_counter
    ) -> None:
        getaddrinfo.return_value = [
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2001:db8::2", 0, 0, 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.2", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.1", 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.0.2.2", 0)),
            (socket.AF_INET6, socket.SOCK_STREAM, 6, "", ("2001:db8::1", 0, 0, 0)),
        ]

        result = resolve_host("example.com")

        self.assertEqual(result.check_type, CheckType.DNS)
        self.assertEqual(result.status, ResultStatus.SUCCESS)
        self.assertEqual(
            result.details["addresses"],
            ("192.0.2.1", "192.0.2.2", "2001:db8::1", "2001:db8::2"),
        )
        self.assertAlmostEqual(result.duration_ms, 25.0)
        getaddrinfo.assert_called_once_with(
            "example.com",
            None,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )

    @patch("monitorcheck.checks.dns.perf_counter", side_effect=[20.0, 20.004])
    @patch("monitorcheck.checks.dns.socket.getaddrinfo")
    def test_converts_unknown_host_to_controlled_error(
        self, getaddrinfo, _perf_counter
    ) -> None:
        getaddrinfo.side_effect = socket.gaierror(-2, "Name or service not known")

        result = resolve_host("missing.invalid")

        self.assertEqual(result.status, ResultStatus.ERROR)
        self.assertIn("Não foi possível resolver", result.message)
        self.assertAlmostEqual(result.duration_ms, 4.0)
        self.assertIn("error", result.details)

    @patch("monitorcheck.checks.dns.perf_counter", side_effect=[30.0, 30.001])
    @patch("monitorcheck.checks.dns.socket.getaddrinfo", return_value=[])
    def test_empty_resolver_response_is_an_error(
        self, _getaddrinfo, _perf_counter
    ) -> None:
        result = resolve_host("empty.test")

        self.assertEqual(result.status, ResultStatus.ERROR)
        self.assertEqual(result.details["addresses"], ())
        self.assertAlmostEqual(result.duration_ms, 1.0)


if __name__ == "__main__":
    unittest.main()
