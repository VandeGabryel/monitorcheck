"""Estrutura visual inicial da interface gráfica local."""

from __future__ import annotations

import tkinter as tk
from tkinter import font as tkfont
from tkinter import ttk

WINDOW_TITLE = "MonitorCheck"
DEFAULT_TIMEOUT_SECONDS = 3.0
INITIAL_RESULT_TEXT = "Nenhuma verificação foi executada."


class MonitorCheckApp(ttk.Frame):
    """Frame principal da GUI, ainda sem integração com as verificações."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=16)

        self.host_var = tk.StringVar(master=master)
        self.ports_var = tk.StringVar(master=master)
        self.url_var = tk.StringVar(master=master)
        self.timeout_var = tk.StringVar(
            master=master,
            value=f"{DEFAULT_TIMEOUT_SECONDS:g}",
        )
        self.result_vars = {
            "dns": tk.StringVar(master=master, value=INITIAL_RESULT_TEXT),
            "tcp": tk.StringVar(master=master, value=INITIAL_RESULT_TEXT),
            "http": tk.StringVar(master=master, value=INITIAL_RESULT_TEXT),
            "summary": tk.StringVar(master=master, value=INITIAL_RESULT_TEXT),
        }

        self._configure_styles()
        self._build_layout()

    def _configure_styles(self) -> None:
        default_font = tkfont.nametofont("TkDefaultFont")
        self._title_font = default_font.copy()
        self._title_font.configure(size=18, weight="bold")

        self._subtitle_font = default_font.copy()
        self._subtitle_font.configure(size=10)

        style = ttk.Style(self)
        style.configure("MonitorCheck.Title.TLabel", font=self._title_font)
        style.configure("MonitorCheck.Subtitle.TLabel", font=self._subtitle_font)

    def _build_layout(self) -> None:
        self.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._build_header()
        self._build_inputs()
        self._build_result_sections()

    def _build_header(self) -> None:
        header = ttk.Frame(self)
        header.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="MonitorCheck",
            style="MonitorCheck.Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Verificações locais de conectividade de hosts e serviços",
            style="MonitorCheck.Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

    def _build_inputs(self) -> None:
        form = ttk.LabelFrame(self, text="Configuração", padding=12)
        form.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Host:").grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=4
        )
        self.host_entry = ttk.Entry(form, textvariable=self.host_var)
        self.host_entry.grid(row=0, column=1, columnspan=2, sticky="ew", pady=4)

        ttk.Label(form, text="Portas TCP:").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=4
        )
        self.ports_entry = ttk.Entry(form, textvariable=self.ports_var)
        self.ports_entry.grid(row=1, column=1, columnspan=2, sticky="ew", pady=4)

        ttk.Label(form, text="URL HTTP/HTTPS:").grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=4
        )
        self.url_entry = ttk.Entry(form, textvariable=self.url_var)
        self.url_entry.grid(row=2, column=1, columnspan=2, sticky="ew", pady=4)

        ttk.Label(form, text="Timeout:").grid(
            row=3, column=0, sticky="w", padx=(0, 8), pady=4
        )
        self.timeout_entry = ttk.Entry(
            form,
            textvariable=self.timeout_var,
            width=12,
        )
        self.timeout_entry.grid(row=3, column=1, sticky="w", pady=4)
        ttk.Label(form, text="segundos").grid(
            row=3, column=2, sticky="w", padx=(8, 0), pady=4
        )

        actions = ttk.Frame(form)
        actions.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        actions.columnconfigure(1, weight=1)

        self.run_button = ttk.Button(
            actions,
            text="Executar verificação",
            state="disabled",
        )
        self.run_button.grid(row=0, column=0, sticky="w")
        ttk.Label(
            actions,
            text="Integração com as verificações será adicionada no próximo gate.",
        ).grid(row=0, column=1, sticky="w", padx=(12, 0))

    def _build_result_sections(self) -> None:
        results = ttk.Frame(self)
        results.grid(row=2, column=0, sticky="nsew")
        results.columnconfigure(0, weight=1, uniform="result-column")
        results.columnconfigure(1, weight=1, uniform="result-column")
        results.rowconfigure(0, weight=1, uniform="result-row")
        results.rowconfigure(1, weight=1, uniform="result-row")

        sections = (
            ("DNS", "dns", 0, 0),
            ("TCP", "tcp", 0, 1),
            ("HTTP/HTTPS", "http", 1, 0),
            ("Resumo", "summary", 1, 1),
        )
        for title, key, row, column in sections:
            section = ttk.LabelFrame(results, text=title, padding=12)
            section.grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=(0, 6) if column == 0 else (6, 0),
                pady=(0, 6) if row == 0 else (6, 0),
            )
            section.columnconfigure(0, weight=1)
            section.rowconfigure(0, weight=1)
            ttk.Label(
                section,
                textvariable=self.result_vars[key],
                anchor="nw",
                justify="left",
                wraplength=340,
            ).grid(row=0, column=0, sticky="nsew")


def create_application() -> tk.Tk:
    """Cria a janela principal sem iniciar o loop de eventos."""

    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.geometry("900x680")
    root.minsize(720, 560)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    MonitorCheckApp(root)
    return root


def main() -> None:
    """Inicia a interface gráfica local."""

    application = create_application()
    application.mainloop()
