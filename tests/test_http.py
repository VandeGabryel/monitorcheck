"""Testes HTTP/HTTPS unitários, sem acesso real à Internet."""

import errno
import io
import socket
import ssl
import unittest
import urllib.error
from unittest.mock import MagicMock, patch

from monitorcheck.checks.http import check_http
from monitorcheck.models import CheckType, ResultStatus


class HttpCheckTests(unittest.TestCase):
    @patch("monitorcheck.checks.http.perf_counter", side_effect=[10.0, 10.05])
    @patch("monitorcheck.checks.http.urllib.request.urlopen")
    def test_get_records_status_and_final_redirect_url(
        self, urlopen, _perf_counter
    ) -> None:
        response = MagicMock()
        response.getcode.return_value = 200
        response.geturl.return_value = "https://example.test/final"
        urlopen.return_value.__enter__.return_value = response

        result = check_http("https://example.test/start", 1.5)

        self.assertEqual(result.check_type, CheckType.HTTP)
        self.assertEqual(result.status, ResultStatus.SUCCESS)
        self.assertEqual(result.details["status_code"], 200)
        self.assertEqual(result.details["final_url"], "https://example.test/final")
        self.assertEqual(result.details["outcome"], "response")
        self.assertAlmostEqual(result.duration_ms, 50.0)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://example.test/start")
        self.assertEqual(request.get_method(), "GET")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 1.5)
        self.assertNotIn("context", urlopen.call_args.kwargs)
        response.read.assert_not_called()

    @patch("monitorcheck.checks.http.perf_counter", side_effect=[20.0, 20.01])
    @patch("monitorcheck.checks.http.urllib.request.urlopen")
    def test_http_error_records_code_and_url(self, urlopen, _perf_counter) -> None:
        urlopen.side_effect = urllib.error.HTTPError(
            "https://example.test/missing",
            404,
            "Not Found",
            None,
            io.BytesIO(),
        )

        result = check_http("https://example.test/missing", 2.0)

        self.assertEqual(result.status, ResultStatus.ERROR)
        self.assertEqual(result.details["outcome"], "http_error")
        self.assertEqual(result.details["status_code"], 404)
        self.assertEqual(result.details["final_url"], "https://example.test/missing")
        self.assertAlmostEqual(result.duration_ms, 10.0)

    @patch("monitorcheck.checks.http.perf_counter", side_effect=[30.0, 30.25])
    @patch("monitorcheck.checks.http.urllib.request.urlopen")
    def test_direct_timeout_is_controlled(self, urlopen, _perf_counter) -> None:
        urlopen.side_effect = socket.timeout("timed out")

        result = check_http("http://example.test", 0.25)

        self.assertEqual(result.status, ResultStatus.ERROR)
        self.assertEqual(result.details["outcome"], "timeout")
        self.assertAlmostEqual(result.duration_ms, 250.0)

    @patch("monitorcheck.checks.http.perf_counter", side_effect=[35.0, 35.1])
    @patch("monitorcheck.checks.http.urllib.request.urlopen")
    def test_wrapped_timeout_is_controlled(self, urlopen, _perf_counter) -> None:
        urlopen.side_effect = urllib.error.URLError(socket.timeout("timed out"))

        result = check_http("https://example.test", 0.1)

        self.assertEqual(result.status, ResultStatus.ERROR)
        self.assertEqual(result.details["outcome"], "timeout")
        self.assertAlmostEqual(result.duration_ms, 100.0)

    @patch("monitorcheck.checks.http.perf_counter", side_effect=[40.0, 40.02])
    @patch("monitorcheck.checks.http.urllib.request.urlopen")
    def test_wrapped_tls_error_is_distinguished(self, urlopen, _perf_counter) -> None:
        tls_error = ssl.SSLCertVerificationError(1, "certificate verify failed")
        urlopen.side_effect = urllib.error.URLError(tls_error)

        result = check_http("https://example.test", 1.0)

        self.assertEqual(result.status, ResultStatus.ERROR)
        self.assertEqual(result.details["outcome"], "tls_error")
        self.assertIn("Erro TLS", result.message)

    @patch("monitorcheck.checks.http.perf_counter", side_effect=[50.0, 50.005])
    @patch("monitorcheck.checks.http.urllib.request.urlopen")
    def test_network_error_is_controlled(self, urlopen, _perf_counter) -> None:
        reason = ConnectionRefusedError(errno.ECONNREFUSED, "Connection refused")
        urlopen.side_effect = urllib.error.URLError(reason)

        result = check_http("http://example.test", 1.0)

        self.assertEqual(result.status, ResultStatus.ERROR)
        self.assertEqual(result.details["outcome"], "network_error")
        self.assertIn("Erro de conexão/rede", result.message)
        self.assertAlmostEqual(result.duration_ms, 5.0)


if __name__ == "__main__":
    unittest.main()
