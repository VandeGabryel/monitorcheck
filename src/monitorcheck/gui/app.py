"""Interface gráfica local do MonitorCheck."""

from __future__ import annotations

import queue
import threading
import tkinter as tk
from dataclasses import dataclass
from tkinter import font as tkfont
from tkinter import messagebox, ttk

from monitorcheck.models import CheckResult, ResultStatus
from monitorcheck.runner import RunResults, run_checks
from monitorcheck.validation import (
    DEFAULT_TIMEOUT,
    ValidationError,
    validate_host,
    validate_ports,
    validate_timeout,
    validate_url,
)

WINDOW_TITLE = "MonitorCheck"
DEFAULT_TIMEOUT_SECONDS = DEFAULT_TIMEOUT
INITIAL_RESULT_TEXT = "Nenhuma verificação foi executada."
RUNNING_RESULT_TEXT = "Verificando conectividade..."
NOT_REQUESTED_TEXT = "Não solicitado."
DEFAULT_THEME = "dark"


@dataclass(frozen=True, slots=True)
class ThemePalette:
    """Cores usadas para configurar os estilos de um tema da GUI."""

    background: str
    surface: str
    card: str
    border: str
    secondary_border: str
    input_border: str
    foreground: str
    muted_foreground: str
    accent: str
    success: str
    warning: str
    error: str
    info: str
    skipped: str
    success_row: str
    warning_row: str
    error_row: str
    info_row: str
    skipped_row: str


@dataclass(frozen=True, slots=True)
class VisualMetrics:
    """Espessuras compartilhadas pelos componentes visuais da GUI."""

    section_border_width: int = 1
    table_border_width: int = 1
    heading_border_width: int = 0
    internal_border_width: int = 0


VISUAL_METRICS = VisualMetrics()


THEME_PALETTES = {
    "light": ThemePalette(
        background="#F4F6F8",
        surface="#FFFFFF",
        card="#FFFFFF",
        border="#CBD5E1",
        secondary_border="#CBD5E1",
        input_border="#CBD5E1",
        foreground="#172033",
        muted_foreground="#52606D",
        accent="#0284C7",
        success="#176B3A",
        warning="#8A5700",
        error="#A22727",
        info="#1E5F8A",
        skipped="#66727D",
        success_row="#E8F5ED",
        warning_row="#FFF4D6",
        error_row="#FDEAEA",
        info_row="#EAF3F8",
        skipped_row="#EEF1F3",
    ),
    "dark": ThemePalette(
        background="#0F172A",
        surface="#111827",
        card="#1E293B",
        border="#334155",
        secondary_border="#475569",
        input_border="#3B4A60",
        foreground="#E5E7EB",
        muted_foreground="#94A3B8",
        accent="#38BDF8",
        success="#22C55E",
        warning="#F59E0B",
        error="#EF4444",
        info="#3B82F6",
        skipped="#94A3B8",
        success_row="#143524",
        warning_row="#3B2B0B",
        error_row="#3B1D24",
        info_row="#142F4C",
        skipped_row="#273344",
    ),
}
THEME_LABELS = {"dark": "Escuro", "light": "Claro"}

_STATUS_DESCRIPTIONS = {
    ResultStatus.SUCCESS: "Sucesso",
    ResultStatus.WARNING: "Aviso",
    ResultStatus.ERROR: "Falha",
    ResultStatus.INFO: "Informação",
    ResultStatus.SKIPPED: "Não solicitado",
}
_STATUS_STYLES = {
    ResultStatus.SUCCESS: "MonitorCheck.Success.TLabel",
    ResultStatus.WARNING: "MonitorCheck.Warning.TLabel",
    ResultStatus.ERROR: "MonitorCheck.Error.TLabel",
    ResultStatus.INFO: "MonitorCheck.Info.TLabel",
    ResultStatus.SKIPPED: "MonitorCheck.Skipped.TLabel",
}


def get_theme_palette(theme_name: str) -> ThemePalette:
    """Retorna uma paleta conhecida ou rejeita um identificador inválido."""

    try:
        return THEME_PALETTES[theme_name]
    except KeyError as error:
        raise ValueError(f"tema desconhecido: {theme_name!r}") from error


def theme_name_from_label(label: str) -> str:
    """Converte o rótulo apresentado no seletor para o identificador interno."""

    for theme_name, theme_label in THEME_LABELS.items():
        if label == theme_label:
            return theme_name
    raise ValueError(f"rótulo de tema desconhecido: {label!r}")


@dataclass(frozen=True, slots=True)
class GuiInputs:
    """Entradas da GUI após validação compartilhada."""

    host: str
    ports: tuple[int, ...]
    url: str | None
    timeout: float


@dataclass(frozen=True, slots=True)
class GuiSummary:
    """Contagens exibidas no painel de resumo da GUI."""

    total: int
    successes: int
    warnings: int
    failures: int
    overall_status: ResultStatus


def parse_gui_inputs(
    host: str,
    ports: str,
    url: str,
    timeout: str,
) -> GuiInputs:
    """Valida os campos da GUI sem acessar widgets ou a rede."""

    return GuiInputs(
        host=validate_host(host),
        ports=validate_ports(ports) if ports.strip() else (),
        url=validate_url(url) if url.strip() else None,
        timeout=validate_timeout(timeout),
    )


def status_presentation(status: ResultStatus) -> tuple[str, str]:
    """Retorna rótulo textual e estilo visual para um estado."""

    return (
        f"[{status.name}] {_STATUS_DESCRIPTIONS[status]}",
        _STATUS_STYLES[status],
    )


def summarize_gui_results(execution: RunResults) -> GuiSummary:
    """Calcula o resumo visual considerando somente checks executados."""

    results = execution.all_results
    successes = sum(item.status is ResultStatus.SUCCESS for item in results)
    warnings = sum(item.status is ResultStatus.WARNING for item in results)
    failures = sum(item.status is ResultStatus.ERROR for item in results)
    if failures:
        overall = ResultStatus.ERROR
    elif warnings:
        overall = ResultStatus.WARNING
    elif successes:
        overall = ResultStatus.SUCCESS
    elif any(item.status is ResultStatus.INFO for item in results):
        overall = ResultStatus.INFO
    else:
        overall = ResultStatus.SKIPPED

    return GuiSummary(
        total=len(results),
        successes=successes,
        warnings=warnings,
        failures=failures,
        overall_status=overall,
    )


def _duration_text(result: CheckResult) -> str:
    if result.duration_ms is None:
        return "não disponível"
    return f"{result.duration_ms:.2f} ms"


def format_tcp_rows(
    results: tuple[CheckResult, ...],
) -> tuple[tuple[str, str, str, str, str], ...]:
    """Converte resultados TCP em linhas independentes para a tabela."""

    return tuple(
        (
            str(result.details.get("port", "?")),
            status_presentation(result.status)[0],
            result.message,
            _duration_text(result),
            result.status.value,
        )
        for result in results
    )


def _format_dns(result: CheckResult) -> str:
    lines = [
        f"Status: {status_presentation(result.status)[0]}",
        f"Alvo: {result.target}",
        f"Mensagem: {result.message}",
        f"Duração: {_duration_text(result)}",
    ]
    addresses = result.details.get("addresses", ())
    if addresses:
        lines.append(f"Endereços: {', '.join(map(str, addresses))}")
    return "\n".join(lines)


def _format_tcp(results: tuple[CheckResult, ...]) -> str:
    if not results:
        return NOT_REQUESTED_TEXT
    return "\n".join(
        f"Porta {port}: {status} — {message} ({duration})"
        for port, status, message, duration, _tag in format_tcp_rows(results)
    )


def _format_http(result: CheckResult | None) -> str:
    if result is None:
        return NOT_REQUESTED_TEXT

    lines = [
        f"Status: {status_presentation(result.status)[0]}",
        f"Mensagem: {result.message}",
        f"Duração: {_duration_text(result)}",
        f"URL solicitada: {result.details.get('requested_url', result.target)}",
    ]
    final_url = result.details.get("final_url")
    status_code = result.details.get("status_code")
    if final_url:
        lines.append(f"URL final: {final_url}")
    if status_code is not None:
        lines.append(f"Código HTTP: {status_code}")
    return "\n".join(lines)


def format_gui_results(execution: RunResults) -> dict[str, str]:
    """Formata resultados para consumo textual ou testes sem display."""

    summary = summarize_gui_results(execution)
    return {
        "dns": _format_dns(execution.dns_result),
        "tcp": _format_tcp(execution.tcp_results),
        "http": _format_http(execution.http_result),
        "summary": "\n".join(
            (
                f"Total de verificações: {summary.total}",
                f"Sucessos: {summary.successes}",
                f"Avisos: {summary.warnings}",
                f"Falhas: {summary.failures}",
                f"Resultado geral: [{summary.overall_status.name}]",
            )
        ),
    }


class MonitorCheckApp(ttk.Frame):
    """Frame principal da GUI integrada ao núcleo por um worker."""

    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master, padding=(24, 20), style="MonitorCheck.App.TFrame")

        self.host_var = tk.StringVar(master=master)
        self.ports_var = tk.StringVar(master=master)
        self.url_var = tk.StringVar(master=master)
        self.timeout_var = tk.StringVar(
            master=master,
            value=f"{DEFAULT_TIMEOUT_SECONDS:g}",
        )
        self.status_var = tk.StringVar(master=master, value="Pronto para executar.")
        self.theme_var = tk.StringVar(
            master=master,
            value=THEME_LABELS[DEFAULT_THEME],
        )
        self.dns_vars = self._new_detail_vars(master)
        self.http_vars = self._new_detail_vars(master)
        self.summary_vars = {
            "total": tk.StringVar(master=master, value="—"),
            "successes": tk.StringVar(master=master, value="—"),
            "warnings": tk.StringVar(master=master, value="—"),
            "failures": tk.StringVar(master=master, value="—"),
            "overall": tk.StringVar(master=master, value="[INFO] Aguardando"),
        }
        self._result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._worker_thread: threading.Thread | None = None
        self._running = False
        self._input_widgets: list[ttk.Entry] = []

        self._configure_styles()
        self._build_layout()
        self._apply_theme(DEFAULT_THEME)
        self._clear_results()

    @staticmethod
    def _new_detail_vars(master: tk.Misc) -> dict[str, tk.StringVar]:
        return {
            "status": tk.StringVar(master=master),
            "target": tk.StringVar(master=master),
            "message": tk.StringVar(master=master),
            "duration": tk.StringVar(master=master),
            "extra": tk.StringVar(master=master),
        }

    def _configure_styles(self) -> None:
        default_font = tkfont.nametofont("TkDefaultFont")
        self._title_font = default_font.copy()
        self._title_font.configure(size=20, weight="bold")
        self._subtitle_font = default_font.copy()
        self._subtitle_font.configure(size=10)
        self._section_font = default_font.copy()
        self._section_font.configure(size=10, weight="bold")
        self._badge_font = default_font.copy()
        self._badge_font.configure(weight="bold")
        self._overall_font = default_font.copy()
        self._overall_font.configure(size=13, weight="bold")

        self._style = ttk.Style(self)
        if "clam" in self._style.theme_names():
            self._style.theme_use("clam")
        self._apply_theme(DEFAULT_THEME)

    def _apply_theme(self, theme_name: str) -> None:
        """Aplica uma paleta aos widgets existentes sem recriá-los."""

        palette = get_theme_palette(theme_name)
        self.theme_var.set(THEME_LABELS[theme_name])
        selected_foreground = "#0F172A" if theme_name == "dark" else "#FFFFFF"
        style = self._style

        self.winfo_toplevel().configure(background=palette.background)
        self.winfo_toplevel().option_add(
            "*TCombobox*Listbox.background",
            palette.surface,
        )
        self.winfo_toplevel().option_add(
            "*TCombobox*Listbox.foreground",
            palette.foreground,
        )
        self.winfo_toplevel().option_add(
            "*TCombobox*Listbox.selectBackground",
            palette.accent,
        )
        self.winfo_toplevel().option_add(
            "*TCombobox*Listbox.selectForeground",
            selected_foreground,
        )

        style.configure(
            ".",
            background=palette.background,
            foreground=palette.foreground,
        )
        style.configure("TFrame", background=palette.card)
        style.configure("TLabel", background=palette.card, foreground=palette.foreground)
        style.configure(
            "TLabelframe",
            background=palette.card,
            bordercolor=palette.border,
            lightcolor=palette.border,
            darkcolor=palette.border,
            borderwidth=VISUAL_METRICS.section_border_width,
            relief="solid",
        )
        style.configure(
            "TLabelframe.Label",
            background=palette.card,
            foreground=palette.foreground,
        )
        style.configure(
            "TEntry",
            fieldbackground=palette.surface,
            foreground=palette.foreground,
            insertcolor=palette.foreground,
            bordercolor=palette.input_border,
            lightcolor=palette.input_border,
            darkcolor=palette.input_border,
            focuscolor=palette.accent,
        )
        style.map(
            "TEntry",
            fieldbackground=[("disabled", palette.card)],
            foreground=[("disabled", palette.muted_foreground)],
            bordercolor=[("focus", palette.accent)],
            lightcolor=[("focus", palette.accent)],
            darkcolor=[("focus", palette.accent)],
        )
        style.configure(
            "TButton",
            background=palette.surface,
            foreground=palette.foreground,
            bordercolor=palette.secondary_border,
            lightcolor=palette.secondary_border,
            darkcolor=palette.secondary_border,
            focuscolor=palette.accent,
        )
        style.map(
            "TButton",
            background=[
                ("active", palette.card),
                ("pressed", palette.accent),
                ("disabled", palette.card),
            ],
            foreground=[
                ("pressed", selected_foreground),
                ("disabled", palette.muted_foreground),
            ],
            bordercolor=[("focus", palette.accent)],
            lightcolor=[("focus", palette.accent)],
            darkcolor=[("focus", palette.accent)],
        )

        style.configure("MonitorCheck.App.TFrame", background=palette.background)
        style.configure("MonitorCheck.Header.TFrame", background=palette.surface)
        style.configure(
            "MonitorCheck.Title.TLabel",
            background=palette.surface,
            foreground=palette.accent,
            font=self._title_font,
        )
        style.configure(
            "MonitorCheck.Subtitle.TLabel",
            background=palette.surface,
            foreground=palette.muted_foreground,
            font=self._subtitle_font,
        )
        style.configure(
            "MonitorCheck.Section.TLabelframe",
            background=palette.card,
            bordercolor=palette.border,
            lightcolor=palette.border,
            darkcolor=palette.border,
            borderwidth=VISUAL_METRICS.section_border_width,
            relief="solid",
        )
        style.configure(
            "MonitorCheck.Section.TLabelframe.Label",
            background=palette.card,
            foreground=palette.foreground,
            font=self._section_font,
        )
        style.configure(
            "MonitorCheck.FieldName.TLabel",
            background=palette.card,
            foreground=palette.muted_foreground,
        )

        status_colors = {
            ResultStatus.SUCCESS: palette.success,
            ResultStatus.WARNING: palette.warning,
            ResultStatus.ERROR: palette.error,
            ResultStatus.INFO: palette.info,
            ResultStatus.SKIPPED: palette.skipped,
        }
        for status, color in status_colors.items():
            style_name = _STATUS_STYLES[status]
            style.configure(
                style_name,
                background=palette.card,
                foreground=color,
                font=self._badge_font,
            )
            style.configure(
                style_name.replace(".TLabel", ".Overall.TLabel"),
                background=palette.card,
                foreground=color,
                font=self._overall_font,
            )

        style.configure(
            "MonitorCheck.Theme.TCombobox",
            fieldbackground=palette.card,
            background=palette.card,
            foreground=palette.foreground,
            arrowcolor=palette.accent,
            bordercolor=palette.input_border,
            lightcolor=palette.input_border,
            darkcolor=palette.input_border,
            focuscolor=palette.accent,
        )
        style.map(
            "MonitorCheck.Theme.TCombobox",
            fieldbackground=[("readonly", palette.card)],
            foreground=[("readonly", palette.foreground)],
            selectbackground=[("readonly", palette.card)],
            selectforeground=[("readonly", palette.foreground)],
            bordercolor=[("focus", palette.accent)],
            lightcolor=[("focus", palette.accent)],
            darkcolor=[("focus", palette.accent)],
        )
        style.configure(
            "MonitorCheck.Treeview",
            background=palette.surface,
            fieldbackground=palette.surface,
            foreground=palette.foreground,
            bordercolor=palette.border,
            lightcolor=palette.border,
            darkcolor=palette.border,
            focuscolor=palette.accent,
            borderwidth=VISUAL_METRICS.table_border_width,
            relief="flat",
            rowheight=28,
        )
        style.map(
            "MonitorCheck.Treeview",
            background=[("selected", palette.accent)],
            foreground=[("selected", selected_foreground)],
            bordercolor=[("focus", palette.accent)],
        )
        style.configure(
            "MonitorCheck.Treeview.Heading",
            background=palette.card,
            foreground=palette.foreground,
            bordercolor=palette.secondary_border,
            lightcolor=palette.secondary_border,
            darkcolor=palette.secondary_border,
            borderwidth=VISUAL_METRICS.heading_border_width,
            relief="flat",
            font=self._section_font,
        )
        style.map(
            "MonitorCheck.Treeview.Heading",
            background=[("active", palette.surface)],
        )
        style.configure(
            "Vertical.TScrollbar",
            background=palette.card,
            troughcolor=palette.background,
            bordercolor=palette.secondary_border,
            lightcolor=palette.secondary_border,
            darkcolor=palette.secondary_border,
            arrowcolor=palette.foreground,
            borderwidth=VISUAL_METRICS.internal_border_width,
            relief="flat",
        )
        self._configure_tree_tags(palette)

    def _configure_tree_tags(self, palette: ThemePalette) -> None:
        if not hasattr(self, "tcp_tree"):
            return
        row_colors = {
            ResultStatus.SUCCESS: palette.success_row,
            ResultStatus.WARNING: palette.warning_row,
            ResultStatus.ERROR: palette.error_row,
            ResultStatus.INFO: palette.info_row,
            ResultStatus.SKIPPED: palette.skipped_row,
        }
        for status, background in row_colors.items():
            self.tcp_tree.tag_configure(
                status.value,
                background=background,
                foreground=palette.foreground,
            )

    def _build_layout(self) -> None:
        self.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)
        self._build_header()
        self._build_inputs()
        self._build_actions()
        self._build_results()
        self._build_summary()

    def _build_header(self) -> None:
        header = ttk.Frame(self, padding=(20, 14), style="MonitorCheck.Header.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)
        ttk.Label(
            header,
            text="MonitorCheck",
            style="MonitorCheck.Title.TLabel",
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Diagnóstico local de conectividade — DNS, TCP e HTTP/HTTPS",
            style="MonitorCheck.Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        theme_controls = ttk.Frame(
            header,
            style="MonitorCheck.Header.TFrame",
        )
        theme_controls.grid(row=0, column=1, rowspan=2, sticky="e")
        ttk.Label(
            theme_controls,
            text="Tema",
            style="MonitorCheck.Subtitle.TLabel",
        ).grid(row=0, column=0, sticky="w", pady=(0, 3))
        self.theme_selector = ttk.Combobox(
            theme_controls,
            textvariable=self.theme_var,
            values=(THEME_LABELS["dark"], THEME_LABELS["light"]),
            state="readonly",
            width=9,
            style="MonitorCheck.Theme.TCombobox",
        )
        self.theme_selector.grid(row=1, column=0, sticky="e")
        self.theme_selector.bind(
            "<<ComboboxSelected>>",
            self._on_theme_selected,
        )

    def _build_inputs(self) -> None:
        form = ttk.LabelFrame(
            self,
            text="Configuração",
            padding=(16, 12),
            style="MonitorCheck.Section.TLabelframe",
        )
        form.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        form.columnconfigure(1, weight=2)
        form.columnconfigure(3, weight=1)

        ttk.Label(form, text="Host").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.host_entry = ttk.Entry(form, textvariable=self.host_var)
        self.host_entry.grid(row=0, column=1, sticky="ew", padx=(0, 18))
        ttk.Label(form, text="Portas TCP").grid(
            row=0, column=2, sticky="w", padx=(0, 8)
        )
        self.ports_entry = ttk.Entry(form, textvariable=self.ports_var)
        self.ports_entry.grid(row=0, column=3, sticky="ew")

        ttk.Label(form, text="URL HTTP/HTTPS").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=(10, 0)
        )
        self.url_entry = ttk.Entry(form, textvariable=self.url_var)
        self.url_entry.grid(
            row=1,
            column=1,
            columnspan=2,
            sticky="ew",
            padx=(0, 18),
            pady=(10, 0),
        )

        timeout_frame = ttk.Frame(form)
        timeout_frame.grid(row=1, column=3, sticky="ew", pady=(10, 0))
        timeout_frame.columnconfigure(1, weight=1)
        ttk.Label(timeout_frame, text="Timeout").grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        self.timeout_entry = ttk.Entry(
            timeout_frame,
            textvariable=self.timeout_var,
            width=8,
        )
        self.timeout_entry.grid(row=0, column=1, sticky="ew")
        ttk.Label(timeout_frame, text="s").grid(row=0, column=2, padx=(5, 0))
        self._input_widgets = [
            self.host_entry,
            self.ports_entry,
            self.url_entry,
            self.timeout_entry,
        ]

    def _build_actions(self) -> None:
        actions = ttk.Frame(self, style="MonitorCheck.App.TFrame")
        actions.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        actions.columnconfigure(2, weight=1)
        self.run_button = ttk.Button(
            actions,
            text="Executar verificação",
            command=self._start_verification,
        )
        self.run_button.grid(row=0, column=0, sticky="w")
        self.clear_button = ttk.Button(
            actions,
            text="Limpar resultados",
            command=self._clear_results,
        )
        self.clear_button.grid(row=0, column=1, sticky="w", padx=(8, 0))
        self.activity_label = ttk.Label(
            actions,
            textvariable=self.status_var,
            style="MonitorCheck.Info.TLabel",
        )
        self.activity_label.grid(row=0, column=2, sticky="e", padx=(16, 0))

    def _build_results(self) -> None:
        results = ttk.Frame(self, style="MonitorCheck.App.TFrame")
        results.grid(row=3, column=0, sticky="nsew", pady=(0, 10))
        results.columnconfigure(0, weight=1, uniform="result-column")
        results.columnconfigure(1, weight=1, uniform="result-column")
        results.rowconfigure(0, weight=1)
        results.rowconfigure(1, weight=1)

        dns_panel = ttk.LabelFrame(
            results,
            text="DNS",
            padding=14,
            style="MonitorCheck.Section.TLabelframe",
        )
        dns_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=(0, 5))
        self.dns_status_label = self._build_detail_panel(dns_panel, self.dns_vars)
        http_panel = ttk.LabelFrame(
            results,
            text="HTTP/HTTPS",
            padding=14,
            style="MonitorCheck.Section.TLabelframe",
        )
        http_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=(0, 5))
        self.http_status_label = self._build_detail_panel(http_panel, self.http_vars)

        tcp_panel = ttk.LabelFrame(
            results,
            text="Portas TCP",
            padding=(12, 10),
            style="MonitorCheck.Section.TLabelframe",
        )
        tcp_panel.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(5, 0))
        tcp_panel.columnconfigure(0, weight=1)
        tcp_panel.rowconfigure(0, weight=1)
        columns = ("port", "status", "message", "duration")
        self.tcp_tree = ttk.Treeview(
            tcp_panel,
            columns=columns,
            show="headings",
            height=5,
            style="MonitorCheck.Treeview",
        )
        for column, title in zip(columns, ("Porta", "Estado", "Mensagem", "Duração")):
            self.tcp_tree.heading(column, text=title)
        self.tcp_tree.column(
            "port", width=90, minwidth=70, stretch=False, anchor="center"
        )
        self.tcp_tree.column("status", width=180, minwidth=145, stretch=False)
        self.tcp_tree.column("message", width=480, minwidth=220, stretch=True)
        self.tcp_tree.column(
            "duration", width=120, minwidth=90, stretch=False, anchor="e"
        )
        self.tcp_tree.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            tcp_panel,
            orient="vertical",
            command=self.tcp_tree.yview,
        )
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(5, 0))
        self.tcp_tree.configure(yscrollcommand=scrollbar.set)

    def _build_detail_panel(
        self,
        panel: ttk.LabelFrame,
        variables: dict[str, tk.StringVar],
    ) -> ttk.Label:
        panel.columnconfigure(1, weight=1)
        status_label = ttk.Label(panel, textvariable=variables["status"])
        status_label.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 9))
        detail_rows = (
            ("Alvo", "target"),
            ("Mensagem", "message"),
            ("Duração", "duration"),
            ("Detalhes", "extra"),
        )
        for row, (title, key) in enumerate(detail_rows, start=1):
            ttk.Label(
                panel,
                text=f"{title}:",
                style="MonitorCheck.FieldName.TLabel",
            ).grid(row=row, column=0, sticky="nw", padx=(0, 10), pady=2)
            value_label = ttk.Label(
                panel,
                textvariable=variables[key],
                justify="left",
                anchor="nw",
            )
            value_label.grid(row=row, column=1, sticky="ew", pady=2)
            self._bind_responsive_wrap(panel, value_label)
        return status_label

    @staticmethod
    def _bind_responsive_wrap(container: ttk.Widget, label: ttk.Label) -> None:
        def update_wrap(event: tk.Event) -> None:
            label.configure(wraplength=max(event.width - 110, 180))

        container.bind("<Configure>", update_wrap, add="+")

    def _build_summary(self) -> None:
        summary = ttk.LabelFrame(
            self,
            text="Resumo",
            padding=(16, 12),
            style="MonitorCheck.Section.TLabelframe",
        )
        summary.grid(row=4, column=0, sticky="ew")
        for column in range(5):
            summary.columnconfigure(column, weight=1)
        metrics = (
            ("Verificações", "total"),
            ("Sucessos", "successes"),
            ("Avisos", "warnings"),
            ("Falhas", "failures"),
        )
        for column, (title, key) in enumerate(metrics):
            ttk.Label(
                summary,
                text=title,
                style="MonitorCheck.FieldName.TLabel",
            ).grid(row=0, column=column, sticky="w")
            ttk.Label(summary, textvariable=self.summary_vars[key]).grid(
                row=1, column=column, sticky="w", pady=(2, 0)
            )
        ttk.Label(
            summary,
            text="Resultado geral",
            style="MonitorCheck.FieldName.TLabel",
        ).grid(row=0, column=4, sticky="e")
        self.overall_status_label = ttk.Label(
            summary,
            textvariable=self.summary_vars["overall"],
            style="MonitorCheck.Info.Overall.TLabel",
        )
        self.overall_status_label.grid(row=1, column=4, sticky="e", pady=(2, 0))
        ttk.Label(
            summary,
            text=(
                "Legenda: [SUCCESS] sucesso  •  [WARNING] aviso  •  "
                "[ERROR] falha  •  [INFO] informação  •  "
                "[SKIPPED] não solicitado"
            ),
            style="MonitorCheck.FieldName.TLabel",
        ).grid(row=2, column=0, columnspan=5, sticky="w", pady=(10, 0))

    def _start_verification(self) -> None:
        """Valida os campos e inicia uma única execução em background."""

        if self._running:
            return
        try:
            inputs = parse_gui_inputs(
                self.host_var.get(),
                self.ports_var.get(),
                self.url_var.get(),
                self.timeout_var.get(),
            )
        except ValidationError as error:
            self._set_activity("Entrada inválida.", ResultStatus.ERROR)
            messagebox.showerror(
                "Entrada inválida",
                str(error),
                parent=self.winfo_toplevel(),
            )
            return

        self._set_running(True)
        self._show_running_state()
        self._worker_thread = threading.Thread(
            target=self._run_worker,
            args=(inputs,),
            name="monitorcheck-gui-worker",
            daemon=True,
        )
        self._worker_thread.start()
        self.after(100, self._poll_worker)

    def _on_theme_selected(self, _event: tk.Event | None = None) -> None:
        """Aplica imediatamente a opção escolhida no cabeçalho."""

        self._apply_theme(theme_name_from_label(self.theme_var.get()))

    def _run_worker(self, inputs: GuiInputs) -> None:
        """Executa a rede fora da thread do Tkinter e publica o desfecho."""

        try:
            execution = run_checks(
                inputs.host,
                inputs.ports,
                inputs.url,
                inputs.timeout,
            )
        except Exception as error:  # proteção da fronteira da interface
            self._result_queue.put(("error", str(error)))
        else:
            self._result_queue.put(("success", execution))

    def _poll_worker(self) -> None:
        """Consome na thread principal o resultado produzido pelo worker."""

        try:
            outcome, payload = self._result_queue.get_nowait()
        except queue.Empty:
            if self._worker_thread is not None and self._worker_thread.is_alive():
                self.after(100, self._poll_worker)
                return
            self._finish_with_error("A verificação terminou sem retornar resultado.")
            return
        if outcome == "success" and isinstance(payload, RunResults):
            try:
                self._show_execution(payload)
            except Exception as error:  # restaura a GUI mesmo em erro de apresentação
                self._finish_with_error(str(error))
                return
            self._set_running(False)
            self._set_activity("Verificação concluída.", ResultStatus.SUCCESS)
            return
        self._finish_with_error(str(payload) or "Erro inesperado durante a verificação.")

    def _show_execution(self, execution: RunResults) -> None:
        self._show_dns(execution.dns_result)
        self._show_tcp(execution.tcp_results)
        self._show_http(execution.http_result)
        self._show_summary(summarize_gui_results(execution))

    def _show_dns(self, result: CheckResult) -> None:
        self._set_status(
            self.dns_status_label,
            self.dns_vars["status"],
            result.status,
        )
        addresses = result.details.get("addresses", ())
        self.dns_vars["target"].set(result.target)
        self.dns_vars["message"].set(result.message)
        self.dns_vars["duration"].set(_duration_text(result))
        self.dns_vars["extra"].set(
            "\n".join(map(str, addresses))
            if addresses
            else "Nenhum endereço disponível."
        )

    def _show_tcp(self, results: tuple[CheckResult, ...]) -> None:
        self._clear_tcp_rows()
        if not results:
            self._insert_tcp_placeholder(
                "[SKIPPED] Não solicitado",
                NOT_REQUESTED_TEXT,
                ResultStatus.SKIPPED,
            )
            return
        for port, status, message, duration, tag in format_tcp_rows(results):
            self.tcp_tree.insert(
                "",
                "end",
                values=(port, status, message, duration),
                tags=(tag,),
            )

    def _show_http(self, result: CheckResult | None) -> None:
        if result is None:
            self._set_status(
                self.http_status_label,
                self.http_vars["status"],
                ResultStatus.SKIPPED,
            )
            self.http_vars["target"].set("—")
            self.http_vars["message"].set(NOT_REQUESTED_TEXT)
            self.http_vars["duration"].set("—")
            self.http_vars["extra"].set("—")
            return
        self._set_status(
            self.http_status_label,
            self.http_vars["status"],
            result.status,
        )
        final_url = result.details.get("final_url")
        status_code = result.details.get("status_code")
        details = []
        if status_code is not None:
            details.append(f"Código HTTP: {status_code}")
        if final_url:
            details.append(f"URL final: {final_url}")
        self.http_vars["target"].set(
            str(result.details.get("requested_url", result.target))
        )
        self.http_vars["message"].set(result.message)
        self.http_vars["duration"].set(_duration_text(result))
        self.http_vars["extra"].set("\n".join(details) if details else "—")

    def _show_summary(self, summary: GuiSummary) -> None:
        self.summary_vars["total"].set(str(summary.total))
        self.summary_vars["successes"].set(str(summary.successes))
        self.summary_vars["warnings"].set(str(summary.warnings))
        self.summary_vars["failures"].set(str(summary.failures))
        label, style = status_presentation(summary.overall_status)
        self.summary_vars["overall"].set(label)
        self.overall_status_label.configure(
            style=style.replace(".TLabel", ".Overall.TLabel")
        )

    def _show_running_state(self) -> None:
        self._set_activity(RUNNING_RESULT_TEXT, ResultStatus.INFO)
        panels = (
            (self.dns_status_label, self.dns_vars),
            (self.http_status_label, self.http_vars),
        )
        for label, variables in panels:
            self._set_status(label, variables["status"], ResultStatus.INFO, "Verificando")
            variables["target"].set("—")
            variables["message"].set(RUNNING_RESULT_TEXT)
            variables["duration"].set("—")
            variables["extra"].set("—")
        self._clear_tcp_rows()
        self._insert_tcp_placeholder(
            "[INFO] Verificando",
            RUNNING_RESULT_TEXT,
            ResultStatus.INFO,
        )
        for key in ("total", "successes", "warnings", "failures"):
            self.summary_vars[key].set("—")
        self.summary_vars["overall"].set("[INFO] Verificando")
        self.overall_status_label.configure(style="MonitorCheck.Info.Overall.TLabel")

    def _clear_results(self) -> None:
        if self._running:
            return
        panels = (
            (getattr(self, "dns_status_label", None), self.dns_vars),
            (getattr(self, "http_status_label", None), self.http_vars),
        )
        for label, variables in panels:
            if label is not None:
                self._set_status(label, variables["status"], ResultStatus.INFO, "Aguardando")
            variables["target"].set("—")
            variables["message"].set(INITIAL_RESULT_TEXT)
            variables["duration"].set("—")
            variables["extra"].set("—")
        if hasattr(self, "tcp_tree"):
            self._clear_tcp_rows()
            self._insert_tcp_placeholder(
                "[INFO] Aguardando",
                INITIAL_RESULT_TEXT,
                ResultStatus.INFO,
            )
        for key in ("total", "successes", "warnings", "failures"):
            self.summary_vars[key].set("—")
        self.summary_vars["overall"].set("[INFO] Aguardando")
        if hasattr(self, "overall_status_label"):
            self.overall_status_label.configure(style="MonitorCheck.Info.Overall.TLabel")
        self._set_activity("Pronto para executar.", ResultStatus.INFO)

    def _finish_with_error(self, message: str) -> None:
        """Apresenta uma falha inesperada sem propagar traceback à GUI."""

        self._set_running(False)
        self._set_activity(
            "Não foi possível concluir a verificação.",
            ResultStatus.ERROR,
        )
        panels = (
            (self.dns_status_label, self.dns_vars),
            (self.http_status_label, self.http_vars),
        )
        for label, variables in panels:
            self._set_status(label, variables["status"], ResultStatus.ERROR)
            variables["target"].set("—")
            variables["message"].set("Verificação não concluída.")
            variables["duration"].set("—")
            variables["extra"].set("—")
        self._clear_tcp_rows()
        self._insert_tcp_placeholder(
            "[ERROR] Falha",
            "Verificação não concluída.",
            ResultStatus.ERROR,
        )
        self.summary_vars["overall"].set("[ERROR] Falha inesperada")
        self.overall_status_label.configure(
            style="MonitorCheck.Error.Overall.TLabel"
        )
        messagebox.showerror(
            "Erro na verificação",
            message,
            parent=self.winfo_toplevel(),
        )

    def _set_running(self, running: bool) -> None:
        self._running = running
        widget_state = "disabled" if running else "!disabled"
        self.run_button.state([widget_state])
        self.clear_button.state([widget_state])
        for entry in self._input_widgets:
            entry.state([widget_state])

    def _set_activity(self, text: str, status: ResultStatus) -> None:
        self.status_var.set(text)
        self.activity_label.configure(style=_STATUS_STYLES[status])

    @staticmethod
    def _set_status(
        label: ttk.Label,
        variable: tk.StringVar,
        status: ResultStatus,
        description: str | None = None,
    ) -> None:
        text, style = status_presentation(status)
        if description is not None:
            text = f"[{status.name}] {description}"
        variable.set(text)
        label.configure(style=style)

    def _clear_tcp_rows(self) -> None:
        children = self.tcp_tree.get_children()
        if children:
            self.tcp_tree.delete(*children)

    def _insert_tcp_placeholder(
        self,
        status: str,
        message: str,
        tag: ResultStatus,
    ) -> None:
        self.tcp_tree.insert(
            "",
            "end",
            values=("—", status, message, "—"),
            tags=(tag.value,),
        )


def create_application() -> tk.Tk:
    """Cria a janela principal sem iniciar o loop de eventos."""

    root = tk.Tk()
    root.title(WINDOW_TITLE)
    root.geometry("1040x780")
    root.minsize(840, 660)
    root.configure(background=get_theme_palette(DEFAULT_THEME).background)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    MonitorCheckApp(root)
    return root


def main() -> None:
    """Inicia a interface gráfica local."""

    application = create_application()
    application.mainloop()
