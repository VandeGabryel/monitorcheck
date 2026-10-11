"""Smoke tests da camada GUI que não exigem um display gráfico."""

import unittest
from tkinter import ttk

from monitorcheck.gui import MonitorCheckApp, create_application, main
from monitorcheck.gui.app import (
    DEFAULT_TIMEOUT_SECONDS,
    INITIAL_RESULT_TEXT,
    NOT_REQUESTED_TEXT,
    format_gui_results,
    parse_gui_inputs,
)
from monitorcheck.models import CheckResult, CheckType, ResultStatus
from monitorcheck.runner import RunResults
from monitorcheck.validation import DEFAULT_TIMEOUT, ValidationError


class GuiModuleTests(unittest.TestCase):
    def test_gui_api_can_be_imported_without_creating_a_window(self) -> None:
        self.assertTrue(issubclass(MonitorCheckApp, ttk.Frame))
        self.assertTrue(callable(create_application))
        self.assertTrue(callable(main))

    def test_initial_constants_match_the_cli_and_empty_state(self) -> None:
        self.assertEqual(DEFAULT_TIMEOUT_SECONDS, DEFAULT_TIMEOUT)
        self.assertEqual(INITIAL_RESULT_TEXT, "Nenhuma verificação foi executada.")

    def test_parses_gui_inputs_with_optional_fields(self) -> None:
        inputs = parse_gui_inputs("localhost", "", "", "3")

        self.assertEqual(inputs.host, "localhost")
        self.assertEqual(inputs.ports, ())
        self.assertIsNone(inputs.url)
        self.assertEqual(inputs.timeout, 3.0)

    def test_rejects_invalid_gui_input_without_tk_window(self) -> None:
        with self.assertRaises(ValidationError):
            parse_gui_inputs("localhost", "0", "", "3")

    def test_formats_results_and_marks_optional_checks_as_not_requested(self) -> None:
        execution = RunResults(
            dns_result=CheckResult(
                CheckType.DNS,
                "localhost",
                ResultStatus.SUCCESS,
                "Resolvido.",
                1.25,
                {"addresses": ("127.0.0.1",)},
            )
        )

        sections = format_gui_results(execution)

        self.assertIn("[SUCCESS]", sections["dns"])
        self.assertIn("127.0.0.1", sections["dns"])
        self.assertEqual(sections["tcp"], NOT_REQUESTED_TEXT)
        self.assertEqual(sections["http"], NOT_REQUESTED_TEXT)
        self.assertIn("Total de verificações: 1", sections["summary"])
        self.assertIn("Resultado geral: [SUCCESS]", sections["summary"])


if __name__ == "__main__":
    unittest.main()
