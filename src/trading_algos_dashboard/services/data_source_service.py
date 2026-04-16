from __future__ import annotations

import importlib
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
from xmlrpc.client import Fault


class DataSourceUnavailableError(RuntimeError):
    """Raised when the smarttrade data source cannot be accessed."""


class MarketDataUnavailableError(ValueError):
    """Raised when requested market data is not available for the given range."""


class SmarttradeDataSourceService:
    def __init__(self, *, smarttrade_path: str, user_id: int):
        self.smarttrade_path = smarttrade_path
        self.user_id = user_id

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
        self._prepare_imports()
        try:
            config_service_module = importlib.import_module("config.service")
            get_config_service = getattr(config_service_module, "get_config_service")
            config_service = get_config_service()
            ip = config_service.get_effective_value("DATA_SERVER_IP")
            port = config_service.get_effective_value("DATA_SERVER_PORT")
            return f"{ip}:{port}"
        except Exception:
            return "the configured Smarttrade data server endpoint"

    def _data_proxy(self) -> Any:
        self._prepare_imports()
        try:
            data_proxy_module = importlib.import_module(
                "utils_shared.objects_factory.data_proxy"
            )
            get_or_create_data_proxy = getattr(
                data_proxy_module, "get_or_create_data_proxy"
            )
        except ModuleNotFoundError as exc:
            raise DataSourceUnavailableError(
                "Smarttrade data service dependencies are unavailable. "
                "Run the dashboard in an environment where smarttrade is installed."
            ) from exc

        try:
            proxy = get_or_create_data_proxy(self.user_id)
            if not proxy.is_server_up():
                raise DataSourceUnavailableError(self._format_unavailable_message())
            return proxy
        except Exception as exc:
            raise DataSourceUnavailableError(
                self._format_unavailable_message()
            ) from exc

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
