"""Contratos compartilhados pelas verificações do MonitorCheck."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class CheckType(str, Enum):
    """Tipos de verificação suportados pelo núcleo da aplicação."""

    DNS = "dns"
    TCP = "tcp"
    HTTP = "http"


class ResultStatus(str, Enum):
    """Estados comuns usados por todas as verificações."""

    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    INFO = "info"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class CheckResult:
    """Resultado independente da interface que irá apresentá-lo.

    ``duration_ms`` pode ser ``None`` quando uma verificação não chegou a ser
    executada, por exemplo em um resultado com estado ``SKIPPED``.
    """

    check_type: CheckType
    target: str
    status: ResultStatus
    message: str
    duration_ms: float | None = None
    details: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.target.strip():
            raise ValueError("O alvo do resultado não pode estar vazio.")
        if not self.message.strip():
            raise ValueError("A mensagem do resultado não pode estar vazia.")
        if self.duration_ms is not None and self.duration_ms < 0:
            raise ValueError("A duração do resultado não pode ser negativa.")

