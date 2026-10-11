"""Testes dos contratos compartilhados."""

import unittest

from monitorcheck.models import CheckResult, CheckType, ResultStatus


class CheckResultTests(unittest.TestCase):
    def test_creates_shared_result(self) -> None:
        result = CheckResult(
            check_type=CheckType.DNS,
            target="example.com",
            status=ResultStatus.SUCCESS,
            message="Endereço resolvido.",
            duration_ms=12.5,
            details={"addresses": ["192.0.2.1"]},
        )

        self.assertEqual(result.check_type, CheckType.DNS)
        self.assertEqual(result.status, ResultStatus.SUCCESS)
        self.assertEqual(result.duration_ms, 12.5)

    def test_rejects_negative_duration(self) -> None:
        with self.assertRaises(ValueError):
            CheckResult(
                check_type=CheckType.TCP,
                target="example.com:443",
                status=ResultStatus.ERROR,
                message="Falha.",
                duration_ms=-1,
            )

    def test_details_default_is_not_shared(self) -> None:
        first = CheckResult(CheckType.DNS, "a.test", ResultStatus.INFO, "A")
        second = CheckResult(CheckType.DNS, "b.test", ResultStatus.INFO, "B")

        self.assertIsNot(first.details, second.details)


if __name__ == "__main__":
    unittest.main()
