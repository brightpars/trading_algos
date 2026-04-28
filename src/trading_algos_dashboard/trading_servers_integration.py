from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from typing import Callable

from trading_servers import CentralServer
from trading_servers import DataServer
from trading_servers import FakeDateTimeServer
from trading_servers.xmlrpc_server import Base_XML_RPC_Server

from trading_algos_dashboard.engines_control_runtime import EnginesControlRuntimeServer


@dataclass(frozen=True)
class TradingServerRuntimeRequest:
    name: str
    host: str
    port: int
    user_id: int


ServerBuilder = Callable[[TradingServerRuntimeRequest], Base_XML_RPC_Server]


class CounterRepository(Protocol):
    def get_counter_seed_value(self, counter_name: str) -> int: ...

    def get_next_counter_value(self, counter_name: str, seed_value: int) -> int: ...


def build_central_server(
    request: TradingServerRuntimeRequest,
    *,
    counter_repository: CounterRepository,
) -> Base_XML_RPC_Server:
    return CentralServer(
        user_id=request.user_id,
        ip=request.host,
        port=request.port,
        sever_name=request.name,
        log_requests_to_terminal=False,
        counter_repository=counter_repository,
    )


def build_data_server(request: TradingServerRuntimeRequest) -> Base_XML_RPC_Server:
    return DataServer(
        user_id=request.user_id,
        ip=request.host,
        port=request.port,
        sever_name=request.name,
        log_requests_to_terminal=False,
    )


def build_fake_datetime_server(
    request: TradingServerRuntimeRequest,
) -> Base_XML_RPC_Server:
    return FakeDateTimeServer(
        user_id=request.user_id,
        ip=request.host,
        port=request.port,
        sever_name=request.name,
        log_requests_to_terminal=False,
    )


def build_engines_control_server(
    request: TradingServerRuntimeRequest,
) -> Base_XML_RPC_Server:
    return EnginesControlRuntimeServer(
        user_id=request.user_id,
        ip=request.host,
        port=request.port,
        sever_name=request.name,
        log_requests_to_terminal=False,
    )
