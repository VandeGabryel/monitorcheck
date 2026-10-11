"""Testes unitários das verificações TCP sem serviços externos."""

import errno
import socket
import unittest
from unittest.mock import MagicMock, patch

from monitorcheck.checks.tcp import check_tcp_port, check_tcp_ports
from monitorcheck.models import CheckType, ResultStatus


class TcpPortCheckTests(unittest.TestCase):
    @patch("monitorcheck.checks.tcp.perf_counter", side_effect=[10.0, 10.012])
    @patch("monitorcheck.checks.tcp.socket.create_connection")
    def test_open_port_returns_success(self, create_connection, _perf_counter) -> None:
        connection = MagicMock()
        create_connection.return_value = connection

        result = check_tcp_port("example.test", 443, 1.5)

        self.assertEqual(result.check_type, CheckType.TCP)
        self.assertEqual(result.status, ResultStatus.SUCCESS)
        self.assertEqual(result.details["outcome"], "open")
        self.assertEqual(result.details["port"], 443)
        self.assertAlmostEqual(result.duration_ms, 12.0)
        create_connection.assert_called_once_with(("example.test", 443), timeout=1.5)
        connection.__exit__.assert_called_once()

    @patch("monitorcheck.checks.tcp.perf_counter", side_effect=[20.0, 20.003])
    @patch("monitorcheck.checks.tcp.socket.create_connection")
    def test_refused_connection_returns_controlled_error(
        self, create_connection, _perf_counter
    ) -> None:
        create_connection.side_effect = ConnectionRefusedError(
            errno.ECONNREFUSED, "Connection refused"
        )

        result = check_tcp_port("example.test", 22, 2.0)

        self.assertEqual(result.status, ResultStatus.ERROR)
        self.assertEqual(result.details["outcome"], "refused")
        self.assertEqual(result.message, "Conexão recusada.")
        self.assertAlmostEqual(result.duration_ms, 3.0)

    @patch("monitorcheck.checks.tcp.perf_counter", side_effect=[30.0, 30.25])
    @patch("monitorcheck.checks.tcp.socket.create_connection")
    def test_timeout_returns_controlled_error(
        self, create_connection, _perf_counter
    ) -> None:
        create_connection.side_effect = socket.timeout("timed out")

        result = check_tcp_port("example.test", 80, 0.25)

        self.assertEqual(result.status, ResultStatus.ERROR)
        self.assertEqual(result.details["outcome"], "timeout")
        self.assertEqual(result.message, "Tempo limite excedido.")
        self.assertAlmostEqual(result.duration_ms, 250.0)

    @patch("monitorcheck.checks.tcp.perf_counter", side_effect=[40.0, 40.005])
    @patch("monitorcheck.checks.tcp.socket.create_connection")
    def test_other_socket_error_is_distinguished(
        self, create_connection, _perf_counter
    ) -> None:
        create_connection.side_effect = OSError(errno.ENETUNREACH, "Network unreachable")

        result = check_tcp_port("example.test", 8080, 1.0)

        self.assertEqual(result.status, ResultStatus.ERROR)
        self.assertEqual(result.details["outcome"], "socket_error")
        self.assertIn("Erro de socket", result.message)
        self.assertAlmostEqual(result.duration_ms, 5.0)

    @patch("monitorcheck.checks.tcp.perf_counter", side_effect=[0.0, 0.1, 1.0, 1.2])
    @patch("monitorcheck.checks.tcp.socket.create_connection")
    def test_failure_does_not_prevent_next_port(
        self, create_connection, _perf_counter
    ) -> None:
        create_connection.side_effect = [
            ConnectionRefusedError(errno.ECONNREFUSED, "Connection refused"),
            MagicMock(),
        ]

        results = check_tcp_ports("example.test", (81, 82), 0.5)

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].details["outcome"], "refused")
        self.assertEqual(results[1].details["outcome"], "open")
        self.assertEqual(
            create_connection.call_args_list[0].args,
            (("example.test", 81),),
        )
        self.assertEqual(
            create_connection.call_args_list[1].args,
            (("example.test", 82),),
        )


if __name__ == "__main__":
    unittest.main()
