"""Testes do parsing e das validações da CLI."""

import argparse
import unittest

from monitorcheck.cli import parse_args, parse_host, parse_ports, parse_timeout, parse_url


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
