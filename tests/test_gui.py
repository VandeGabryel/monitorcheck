"""Smoke tests da camada GUI que não exigem um display gráfico."""

import unittest
from dataclasses import fields
from tkinter import ttk

from monitorcheck.gui import MonitorCheckApp, create_application, main
from monitorcheck.gui.app import (
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_THEME,
    INITIAL_RESULT_TEXT,
    NOT_REQUESTED_TEXT,
    THEME_LABELS,
    format_gui_results,
    format_tcp_rows,
    get_theme_palette,
    parse_gui_inputs,
    status_presentation,
    summarize_gui_results,
    theme_name_from_label,
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
        self.assertEqual(DEFAULT_THEME, "dark")

    def test_light_and_dark_themes_have_distinct_complete_palettes(self) -> None:
        light = get_theme_palette("light")
        dark = get_theme_palette("dark")

        self.assertNotEqual(light.background, dark.background)
        self.assertNotEqual(light.foreground, dark.foreground)
        for palette in (light, dark):
            for palette_field in fields(palette):
                self.assertRegex(
                    getattr(palette, palette_field.name),
                    r"^#[0-9A-F]{6}$",
                )

    def test_theme_labels_round_trip_to_internal_names(self) -> None:
        for theme_name, label in THEME_LABELS.items():
            with self.subTest(theme_name=theme_name):
                self.assertEqual(theme_name_from_label(label), theme_name)

        with self.assertRaises(ValueError):
            get_theme_palette("sepia")
        with self.assertRaises(ValueError):
            theme_name_from_label("Sépia")

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

    def test_every_status_has_text_and_visual_style(self) -> None:
        for status in ResultStatus:
            with self.subTest(status=status):
                label, style = status_presentation(status)

                self.assertIn(f"[{status.name}]", label)
                self.assertTrue(label.removeprefix(f"[{status.name}]").strip())
                self.assertTrue(style.startswith("MonitorCheck."))

    def test_formats_each_tcp_port_as_an_independent_row(self) -> None:
        results = (
            CheckResult(
                CheckType.TCP,
                "localhost:8000",
                ResultStatus.SUCCESS,
                "Conexão estabelecida.",
                2.5,
                {"port": 8000},
            ),
            CheckResult(
                CheckType.TCP,
                "localhost:8001",
                ResultStatus.ERROR,
                "Conexão recusada.",
                3.75,
                {"port": 8001},
            ),
        )

        rows = format_tcp_rows(results)

        self.assertEqual(len(rows), 2)
        self.assertEqual(
            rows[0],
            (
                "8000",
                "[SUCCESS] Sucesso",
                "Conexão estabelecida.",
                "2.50 ms",
                "success",
            ),
        )
        self.assertEqual(
            rows[1],
            (
                "8001",
                "[ERROR] Falha",
                "Conexão recusada.",
                "3.75 ms",
                "error",
            ),
        )

    def test_summary_prioritizes_errors_and_counts_only_executed_checks(self) -> None:
        execution = RunResults(
            dns_result=CheckResult(
                CheckType.DNS,
                "localhost",
                ResultStatus.SUCCESS,
                "Resolvido.",
                1.0,
            ),
            tcp_results=(
                CheckResult(
                    CheckType.TCP,
                    "localhost:8001",
                    ResultStatus.ERROR,
                    "Conexão recusada.",
                    2.0,
                ),
            ),
        )

        summary = summarize_gui_results(execution)

        self.assertEqual(summary.total, 2)
        self.assertEqual(summary.successes, 1)
        self.assertEqual(summary.failures, 1)
        self.assertEqual(summary.warnings, 0)
        self.assertIs(summary.overall_status, ResultStatus.ERROR)


if __name__ == "__main__":
    unittest.main()
