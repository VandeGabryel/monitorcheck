"""Smoke tests da camada GUI que não exigem um display gráfico."""

import unittest
from tkinter import ttk

from monitorcheck.cli import DEFAULT_TIMEOUT
from monitorcheck.gui import MonitorCheckApp, create_application, main
from monitorcheck.gui.app import DEFAULT_TIMEOUT_SECONDS, INITIAL_RESULT_TEXT


class GuiModuleTests(unittest.TestCase):
    def test_gui_api_can_be_imported_without_creating_a_window(self) -> None:
        self.assertTrue(issubclass(MonitorCheckApp, ttk.Frame))
        self.assertTrue(callable(create_application))
        self.assertTrue(callable(main))

    def test_initial_constants_match_the_cli_and_empty_state(self) -> None:
        self.assertEqual(DEFAULT_TIMEOUT_SECONDS, DEFAULT_TIMEOUT)
        self.assertEqual(INITIAL_RESULT_TEXT, "Nenhuma verificação foi executada.")


if __name__ == "__main__":
    unittest.main()
