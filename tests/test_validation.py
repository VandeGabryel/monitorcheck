"""Testes das validações compartilhadas pelas interfaces."""

import unittest

from monitorcheck.validation import (
    ValidationError,
    validate_host,
    validate_ports,
    validate_timeout,
    validate_url,
)


class SharedValidationTests(unittest.TestCase):
    def test_accepts_and_normalizes_valid_inputs(self) -> None:
        self.assertEqual(validate_host(" example.com "), "example.com")
        self.assertEqual(validate_ports("80, 443,80"), (80, 443))
        self.assertEqual(validate_url(" https://example.com/a "), "https://example.com/a")
        self.assertEqual(validate_timeout("1.5"), 1.5)

    def test_rejects_invalid_inputs_with_neutral_error(self) -> None:
        invalid_calls = (
            (validate_host, ""),
            (validate_ports, "0"),
            (validate_url, "ftp://example.com"),
            (validate_timeout, "0"),
        )
        for validator, value in invalid_calls:
            with self.subTest(validator=validator.__name__, value=value):
                with self.assertRaises(ValidationError):
                    validator(value)


if __name__ == "__main__":
    unittest.main()
