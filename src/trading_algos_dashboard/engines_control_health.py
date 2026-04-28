from __future__ import annotations

import os
import socket
from typing import Callable
from typing import Iterable
from xmlrpc.client import ServerProxy


ConnectionTarget = tuple[str, str, int]


def default_connection_targets() -> list[ConnectionTarget]:
    return [
        (
            "central",
            os.environ.get("TRADING_ALGOS_DASHBOARD_CENTRAL_HOST", "127.0.0.1").strip()
            or "127.0.0.1",
            int(os.environ.get("TRADING_ALGOS_DASHBOARD_CENTRAL_PORT", "6000")),
        ),
        (
            "fake_datetime",
            os.environ.get(
                "TRADING_ALGOS_DASHBOARD_FAKE_DATETIME_HOST", "127.0.0.1"
            ).strip()
            or "127.0.0.1",
            int(os.environ.get("TRADING_ALGOS_DASHBOARD_FAKE_DATETIME_PORT", "7100")),
        ),
        (
            "data",
            os.environ.get("TRADING_ALGOS_DASHBOARD_DATA_HOST", "127.0.0.1").strip()
            or "127.0.0.1",
            int(os.environ.get("TRADING_ALGOS_DASHBOARD_DATA_PORT", "6010")),
        ),
        (
            "broker",
            os.environ.get("TRADING_ALGOS_DASHBOARD_BROKER_HOST", "127.0.0.1").strip()
            or "127.0.0.1",
            int(os.environ.get("TRADING_ALGOS_DASHBOARD_BROKER_PORT", "7101")),
        ),
    ]


def xmlrpc_ping(host: str, port: int) -> bool:
    try:
        proxy = ServerProxy(f"http://{host}:{port}", allow_none=True)
        return proxy.ping() == "pong"
    except Exception:
        return False


def tcp_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.25):
            return True
    except OSError:
        return False


def service_state(host: str, port: int) -> str:
    if xmlrpc_ping(host, port):
        return "up"
    if tcp_port_open(host, port):
        return "up"
    return "down"


def build_connection_statuses(
    targets: Iterable[ConnectionTarget],
    *,
    state_resolver: Callable[[str, int], str] = service_state,
) -> list[dict[str, str]]:
    return [
        {f"{name}({host}:{port})": state_resolver(host, port)}
        for name, host, port in targets
    ]
