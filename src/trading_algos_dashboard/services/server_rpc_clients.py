from __future__ import annotations

from typing import Any
from typing import cast
from xmlrpc.client import ServerProxy


def _endpoint_url(host: str, port: int) -> str:
    return f"http://{host}:{int(port)}"


def _proxy_call(proxy: Any, method_name: str, *args: Any) -> Any:
    method = getattr(proxy, method_name)
    return cast(Any, method(*args))


def _dict_list(value: Any) -> list[dict[str, Any]]:
    return [dict(cast(dict[str, Any], item)) for item in cast(list[Any], value)]


def _dict_value(value: Any) -> dict[str, Any]:
    return dict(cast(dict[str, Any], value))


class CentralServerClient:
    def __init__(self, *, host: str, port: int) -> None:
        self._proxy = ServerProxy(_endpoint_url(host, port), allow_none=True)

    def ping(self) -> str:
        return str(_proxy_call(self._proxy, "ping"))

    def ping_with_timeout(self, timeout_seconds: float) -> str:
        return str(_proxy_call(self._proxy, "ping_with_timeout", timeout_seconds))

    def get_next_alertID(self) -> int:
        return int(cast(Any, _proxy_call(self._proxy, "get_next_alertID")))

    def get_next_assetID(self) -> int:
        return int(cast(Any, _proxy_call(self._proxy, "get_next_assetID")))

    def get_next_operationID(self) -> int:
        return int(cast(Any, _proxy_call(self._proxy, "get_next_operationID")))

    def get_next_executionID(self) -> int:
        return int(cast(Any, _proxy_call(self._proxy, "get_next_executionID")))


class DataServerClient:
    def __init__(self, *, host: str, port: int, timeout_seconds: float) -> None:
        self.timeout_seconds = timeout_seconds
        self._proxy = ServerProxy(_endpoint_url(host, port), allow_none=True)

    def ping(self) -> str:
        ping_with_timeout = getattr(self._proxy, "ping_with_timeout", None)
        if callable(ping_with_timeout):
            return str(ping_with_timeout(self.timeout_seconds))
        ping = getattr(self._proxy, "ping", None)
        if callable(ping):
            return str(ping())
        is_server_up = getattr(self._proxy, "is_server_up", None)
        if callable(is_server_up) and bool(is_server_up()):
            return "pong"
        return "down"

    @staticmethod
    def _serialize_remote_datetime(value: Any) -> Any:
        strftime = getattr(value, "strftime", None)
        if callable(strftime):
            return strftime("%Y-%m-%d %H:%M:%S")
        return value

    def get_price(self, symbol: str, ts: object) -> Any:
        return _proxy_call(
            self._proxy,
            "get_price",
            symbol,
            self._serialize_remote_datetime(ts),
        )

    def get_history_price(self, symbol: str, ts1: object, ts2: object) -> Any:
        return _proxy_call(
            self._proxy,
            "get_history_price",
            symbol,
            self._serialize_remote_datetime(ts1),
            self._serialize_remote_datetime(ts2),
        )

    def get_data(self, symbol: str, ts: object) -> Any:
        return _proxy_call(
            self._proxy,
            "get_data",
            symbol,
            self._serialize_remote_datetime(ts),
        )

    def get_candles(self, symbol: str, start: object, end: object) -> Any:
        return _proxy_call(
            self._proxy,
            "get_candles",
            symbol,
            self._serialize_remote_datetime(start),
            self._serialize_remote_datetime(end),
        )


class FakeDateTimeServerClient:
    def __init__(self, *, host: str, port: int) -> None:
        self._proxy = ServerProxy(_endpoint_url(host, port), allow_none=True)

    def ping(self) -> str:
        return str(_proxy_call(self._proxy, "ping"))

    def ping_with_timeout(self, timeout_seconds: float) -> str:
        return str(_proxy_call(self._proxy, "ping_with_timeout", timeout_seconds))

    def init(self, date: str, time: str, speed: int) -> int:
        return int(cast(Any, _proxy_call(self._proxy, "init", date, time, int(speed))))

    def start_clock(self) -> int:
        return int(cast(Any, _proxy_call(self._proxy, "start_clock")))

    def stop(self) -> str:
        return str(_proxy_call(self._proxy, "stop"))

    def restart(self) -> int:
        return int(cast(Any, _proxy_call(self._proxy, "restart")))

    def get_ts(self, delta_seconds: int) -> str:
        return str(_proxy_call(self._proxy, "get_ts", int(delta_seconds)))

    def get_speed_factor(self) -> int:
        return int(cast(Any, _proxy_call(self._proxy, "get_speed_factor")))


class EnginesControlServerClient:
    def __init__(self, *, host: str, port: int) -> None:
        self._proxy = ServerProxy(_endpoint_url(host, port), allow_none=True)

    def ping(self) -> str:
        return str(_proxy_call(self._proxy, "ping"))

    def ping_with_timeout(self, timeout_seconds: float) -> str:
        return str(_proxy_call(self._proxy, "ping_with_timeout", timeout_seconds))

    def run_alertgen_and_sensors(self, payload: dict[str, Any]) -> int | str:
        result = _proxy_call(self._proxy, "run_alertgen_and_sensors", payload)
        return int(result) if result == 0 else str(result)

    def get_all_alertgen_info(self) -> list[dict[str, Any]]:
        return _dict_list(_proxy_call(self._proxy, "get_all_alertgen_info"))

    def stop_all_alertgen_instances(self) -> list[dict[str, Any]]:
        return _dict_list(_proxy_call(self._proxy, "stop_all_alertgen_instances"))

    def start_decision_maker(self, payload: dict[str, Any]) -> int | str:
        result = _proxy_call(self._proxy, "start_decision_maker", payload)
        return int(result) if result == 0 else str(result)

    def get_decision_maker_info(self) -> dict[str, Any]:
        return _dict_value(_proxy_call(self._proxy, "get_decision_maker_info"))

    def stop_decision_maker_instance(self) -> dict[str, Any]:
        return _dict_value(_proxy_call(self._proxy, "stop_decision_maker_instance"))

    def is_decision_maker_stop_complete(self) -> bool:
        return bool(_proxy_call(self._proxy, "is_decision_maker_stop_complete"))

    def get_decision_maker_stop_report(self) -> dict[str, Any] | None:
        result = _proxy_call(self._proxy, "get_decision_maker_stop_report")
        return None if result is None else _dict_value(result)

    def get_all_engines_reports(self) -> dict[str, Any]:
        return _dict_value(_proxy_call(self._proxy, "get_all_engines_reports"))

    def check_connections(self) -> list[dict[str, str]]:
        return [
            dict(cast(dict[str, str], item))
            for item in cast(list[Any], _proxy_call(self._proxy, "check_connections"))
        ]

    def run_all_engines(self) -> int:
        return int(cast(Any, _proxy_call(self._proxy, "run_all_engines")))

    def pause_all_engines(self) -> int:
        return int(cast(Any, _proxy_call(self._proxy, "pause_all_engines")))

    def is_alertgen_stop_complete(self) -> bool:
        return bool(_proxy_call(self._proxy, "is_alertgen_stop_complete"))

    def get_alertgen_stop_reports(self) -> list[dict[str, Any]] | None:
        result = _proxy_call(self._proxy, "get_alertgen_stop_reports")
        if result is None:
            return None
        return _dict_list(result)

    def run_engine_chain(self, payload: dict[str, Any]) -> dict[str, Any]:
        return _dict_value(_proxy_call(self._proxy, "run_engine_chain", payload))

    def stop_engine_chain(self) -> int:
        return int(cast(Any, _proxy_call(self._proxy, "stop_engine_chain")))
