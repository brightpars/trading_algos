from __future__ import annotations

import importlib
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from xmlrpc.client import Fault

from trading_algos_dashboard.services.data_source_settings_service import (
    DEFAULT_DATA_SERVER_IP,
    DEFAULT_DATA_SERVER_PORT,
)


DEFAULT_CONNECTION_CHECK_TIMEOUT_SECONDS = 2.0


class DataSourceUnavailableError(RuntimeError):
    """Raised when the smarttrade data source cannot be accessed."""


class MarketDataUnavailableError(ValueError):
    """Raised when requested market data is not available for the given range."""


class SmarttradeDataSourceService:
    def __init__(
        self,
        *,
        smarttrade_path: str,
        user_id: int,
        endpoint_resolver: Any | None = None,
    ):
        self.smarttrade_path = smarttrade_path
        self.user_id = user_id
        self.endpoint_resolver = endpoint_resolver

    def _is_proxy_server_up(
        self,
        proxy: Any,
        *,
        timeout_seconds: float = DEFAULT_CONNECTION_CHECK_TIMEOUT_SECONDS,
    ) -> bool:
        ping_with_timeout = getattr(proxy, "ping_with_timeout", None)
        if callable(ping_with_timeout):
            return ping_with_timeout(timeout_seconds) == "pong"
        return bool(proxy.is_server_up())

    def _resolved_endpoint_override(self) -> tuple[str, int] | None:
        if self.endpoint_resolver is None:
            return None
        resolved = self.endpoint_resolver()
        if resolved is None:
            return None
        return str(resolved[0]), int(resolved[1])

    def _format_unavailable_message(self) -> str:
        endpoint = self._data_server_endpoint_label()
        return (
            "Smarttrade data service is unavailable. "
            "Please make sure the data server is running. "
            f"Tried to connect to {endpoint}."
        )

    def _prepare_imports(self) -> None:
        path = str(Path(self.smarttrade_path).resolve())
        if path not in sys.path:
            sys.path.insert(0, path)

    def _data_server_endpoint_label(self) -> str:
        override = self._resolved_endpoint_override()
        if override is not None:
            ip, port = override
            return f"{ip}:{port}"
        self._prepare_imports()
        try:
            config_service_module = importlib.import_module("config.service")
            get_config_service = getattr(config_service_module, "get_config_service")
            config_service = get_config_service()
            ip = config_service.get_effective_value("DATA_SERVER_IP")
            port = config_service.get_effective_value("DATA_SERVER_PORT")
            return f"{ip}:{port}"
        except Exception:
            return f"{DEFAULT_DATA_SERVER_IP}:{DEFAULT_DATA_SERVER_PORT}"

    def _create_proxy(self, *, ip: str, port: int) -> Any:
        self._prepare_imports()
        try:
            online_services_module = importlib.import_module(
                "utils_shared.online_services"
            )
            users_context_module = importlib.import_module(
                "utils_shared.context.users_context_manager"
            )
            proxy_operations_module = importlib.import_module(
                "utils_shared.objects_factory.proxy_operations"
            )
            data_proxy_class = getattr(online_services_module, "Data_Proxy")
            users_context_manager = getattr(
                users_context_module, "Users_Context_Manager"
            )
            get_or_create_proxy_obj = getattr(
                proxy_operations_module, "get_or_create_proxy_obj"
            )
        except ModuleNotFoundError as exc:
            raise DataSourceUnavailableError(
                "Smarttrade data service dependencies are unavailable. "
                "Run the dashboard in an environment where smarttrade is installed."
            ) from exc

        ctx = users_context_manager().get_ctx(self.user_id)
        return get_or_create_proxy_obj(
            ctx,
            data_proxy_class,
            f"DataProxyObj:{ip}:{port}",
            ip,
            port,
        )

    def _data_proxy(self) -> Any:
        try:
            override = self._resolved_endpoint_override()
            if override is None:
                self._prepare_imports()
                data_proxy_module = importlib.import_module(
                    "utils_shared.objects_factory.data_proxy"
                )
                get_or_create_data_proxy = getattr(
                    data_proxy_module, "get_or_create_data_proxy"
                )
                proxy = get_or_create_data_proxy(self.user_id)
            else:
                ip, port = override
                proxy = self._create_proxy(ip=ip, port=port)
            if not self._is_proxy_server_up(proxy):
                raise DataSourceUnavailableError(self._format_unavailable_message())
            return proxy
        except ModuleNotFoundError as exc:
            raise DataSourceUnavailableError(
                "Smarttrade data service dependencies are unavailable. "
                "Run the dashboard in an environment where smarttrade is installed."
            ) from exc
        except Exception as exc:
            raise DataSourceUnavailableError(
                self._format_unavailable_message()
            ) from exc

    def check_connection(self) -> dict[str, Any]:
        self._data_proxy()
        return {
            "status": "ok",
            "endpoint": self._data_server_endpoint_label(),
            "server_up": True,
        }

    def fetch_candles(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        if end < start:
            raise ValueError("End datetime must be after start datetime")

        proxy = self._data_proxy()
        result: list[dict[str, Any]] = []
        missing_timestamps: list[datetime] = []
        ts = start
        while ts <= end:
            try:
                row = proxy.get_data(symbol, ts)
            except Fault:
                missing_timestamps.append(ts)
                ts += timedelta(minutes=1)
                continue
            except Exception as exc:
                raise DataSourceUnavailableError(
                    self._format_unavailable_message()
                ) from exc
            mapping = dict(row)
            mapping.pop("_id", None)
            result.append(mapping)
            ts += timedelta(minutes=1)

        if not result:
            raise MarketDataUnavailableError(
                "No candle data is available for the requested symbol and time range. "
                "Please choose a range that contains market data."
            )

        return result


def parse_date_range(
    start_date: str,
    start_time: str,
    end_date: str,
    end_time: str,
) -> tuple[datetime, datetime]:
    start = datetime.fromisoformat(f"{start_date}T{start_time}")
    end = datetime.fromisoformat(f"{end_date}T{end_time}")
    if end < start:
        raise ValueError("End datetime must be after start datetime")
    return start, end
