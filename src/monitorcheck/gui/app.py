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
RUNNING_RESULT_TEXT = "Verificação em andamento..."
NOT_REQUESTED_TEXT = "Não solicitado."


@dataclass(frozen=True, slots=True)
class GuiInputs:
    """Entradas da GUI após validação compartilhada."""

    host: str
    ports: tuple[int, ...]
    url: str | None
    timeout: float


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


def _duration_text(result: CheckResult) -> str:
    if result.duration_ms is None:
        return "não disponível"
    return f"{result.duration_ms:.2f} ms"


def _format_dns(result: CheckResult) -> str:
    lines = [
        f"Status: [{result.status.name}]",
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

    entries = []
    for result in results:
        port = result.details.get("port", "?")
        entries.append(
            "\n".join(
                (
                    f"Porta {port}: [{result.status.name}]",
                    f"Alvo: {result.target}",
                    f"Mensagem: {result.message}",
                    f"Duração: {_duration_text(result)}",
                )
            )
        )
    return "\n\n".join(entries)


def _format_http(result: CheckResult | None) -> str:
    if result is None:
        return NOT_REQUESTED_TEXT

    lines = [
        f"Status: [{result.status.name}]",
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
    """Formata resultados estruturados para as quatro áreas textuais da GUI."""

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

    summary = "\n".join(
        (
            f"Total de verificações: {len(results)}",
            f"Sucessos: {successes}",
            f"Avisos: {warnings}",
            f"Falhas: {failures}",
            f"Resultado geral: [{overall.name}]",
        )
    )
    return {
        "dns": _format_dns(execution.dns_result),
        "tcp": _format_tcp(execution.tcp_results),
        "http": _format_http(execution.http_result),
        "summary": summary,
    }


class MonitorCheckApp(ttk.Frame):
    """Frame principal da GUI integrada ao núcleo por um worker."""

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
        self.status_var = tk.StringVar(master=master, value="Pronto para executar.")
        self._result_queue: queue.Queue[tuple[str, object]] = queue.Queue()
        self._worker_thread: threading.Thread | None = None
        self._running = False

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
            command=self._start_verification,
        )
        self.run_button.grid(row=0, column=0, sticky="w")
        ttk.Label(
            actions,
            textvariable=self.status_var,
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
            self.status_var.set("Entrada inválida.")
            messagebox.showerror(
                "Entrada inválida",
                str(error),
                parent=self.winfo_toplevel(),
            )
            return

        self._set_running(True)
        for result_var in self.result_vars.values():
            result_var.set(RUNNING_RESULT_TEXT)

        self._worker_thread = threading.Thread(
            target=self._run_worker,
            args=(inputs,),
            name="monitorcheck-gui-worker",
            daemon=True,
        )
        self._worker_thread.start()
        self.after(100, self._poll_worker)

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
            for key, text in format_gui_results(payload).items():
                self.result_vars[key].set(text)
            self._set_running(False)
            self.status_var.set("Verificação concluída.")
            return

        self._finish_with_error(str(payload) or "Erro inesperado durante a verificação.")

    def _finish_with_error(self, message: str) -> None:
        """Apresenta uma falha inesperada sem propagar traceback à GUI."""

        self._set_running(False)
        self.status_var.set("Não foi possível concluir a verificação.")
        for result_var in self.result_vars.values():
            result_var.set("Verificação não concluída.")
        messagebox.showerror(
            "Erro na verificação",
            message,
            parent=self.winfo_toplevel(),
        )

    def _set_running(self, running: bool) -> None:
        self._running = running
        if running:
            self.run_button.state(["disabled"])
            self.status_var.set(RUNNING_RESULT_TEXT)
        else:
            self.run_button.state(["!disabled"])


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
