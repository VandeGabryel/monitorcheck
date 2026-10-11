"""Resolução DNS independente da interface de apresentação."""

from __future__ import annotations

import socket
from time import perf_counter

from monitorcheck.models import CheckResult, CheckType, ResultStatus


def _elapsed_ms(started_at: float) -> float:
    """Retorna o tempo decorrido em milissegundos."""

    return (perf_counter() - started_at) * 1_000


def _unique_addresses(
    address_info: list[tuple[int, int, int, str, tuple[object, ...]]],
) -> tuple[str, ...]:
    """Extrai IPv4/IPv6 únicos em uma ordem determinística."""

    addresses: set[tuple[int, str]] = set()
    for family, _socket_type, _protocol, _canonical_name, socket_address in address_info:
        if family in {socket.AF_INET, socket.AF_INET6} and socket_address:
            addresses.add((family, str(socket_address[0])))

    family_order = {socket.AF_INET: 0, socket.AF_INET6: 1}
    ordered = sorted(
        addresses,
        key=lambda item: (family_order[item[0]], item[1]),
    )
    return tuple(address for _family, address in ordered)


def resolve_host(host: str) -> CheckResult:
    """Resolve um host em endereços IPv4 e IPv6.

    Falhas esperadas do resolvedor são convertidas em ``CheckResult`` para que
    nenhuma exceção de rede precise chegar à camada de apresentação.
    """

    started_at = perf_counter()
    try:
        address_info = socket.getaddrinfo(
            host,
            None,
            family=socket.AF_UNSPEC,
            type=socket.SOCK_STREAM,
        )
        addresses = _unique_addresses(address_info)
    except (socket.gaierror, OSError, UnicodeError) as error:
        return CheckResult(
            check_type=CheckType.DNS,
            target=host,
            status=ResultStatus.ERROR,
            message=f"Não foi possível resolver o host: {error}",
            duration_ms=_elapsed_ms(started_at),
            details={"error": str(error)},
        )

    duration_ms = _elapsed_ms(started_at)
    if not addresses:
        return CheckResult(
            check_type=CheckType.DNS,
            target=host,
            status=ResultStatus.ERROR,
            message="O resolvedor não retornou endereços IPv4 ou IPv6.",
            duration_ms=duration_ms,
            details={"addresses": ()},
        )

    count = len(addresses)
    return CheckResult(
        check_type=CheckType.DNS,
        target=host,
        status=ResultStatus.SUCCESS,
        message=f"{count} endereço(s) encontrado(s).",
        duration_ms=duration_ms,
        details={"addresses": addresses},
    )

