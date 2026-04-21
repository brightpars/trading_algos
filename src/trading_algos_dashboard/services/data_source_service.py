from __future__ import annotations

import importlib
import logging
import sys
from collections.abc import Iterable
from collections.abc import Mapping
from datetime import datetime, timedelta
from pathlib import Path
from time import perf_counter
from typing import Any
from typing import cast
from xmlrpc.client import Fault

from trading_algos_dashboard.services.data_source_settings_service import (
    DEFAULT_DATA_SERVER_IP,
    DEFAULT_DATA_SERVER_PORT,
)


DEFAULT_CONNECTION_CHECK_TIMEOUT_SECONDS = 2.0

logger = logging.getLogger(__name__)


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
        endpoint = self._resolved_endpoint()
        return f"{endpoint[0]}:{endpoint[1]}"

    def _resolved_endpoint(self) -> tuple[str, int]:
        override = self._resolved_endpoint_override()
        if override is not None:
            return override
        self._prepare_imports()
        try:
            config_service_module = importlib.import_module("config.service")
            get_config_service = getattr(config_service_module, "get_config_service")
            config_service = get_config_service()
            ip = str(config_service.get_effective_value("DATA_SERVER_IP"))
            port = int(config_service.get_effective_value("DATA_SERVER_PORT"))
            return ip, port
        except Exception:
            return DEFAULT_DATA_SERVER_IP, DEFAULT_DATA_SERVER_PORT

    def get_market_data_server_details(self) -> dict[str, Any]:
        ip, port = self._resolved_endpoint()
        return {
            "kind": "smarttrade_dataserver",
            "ip": ip,
            "port": port,
            "endpoint": f"{ip}:{port}",
        }

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

    @staticmethod
    def _normalize_candle_row(row: Any) -> dict[str, Any]:
        if isinstance(row, dict):
            mapping: dict[str, Any] = dict(cast(Mapping[str, Any], row))
        else:
            to_mongo = getattr(row, "to_mongo", None)
            if callable(to_mongo):
                mongo_document = to_mongo()
                to_dict = getattr(mongo_document, "to_dict", None)
                if not callable(to_dict):
                    raise TypeError("Unsupported candle row mongo document type")
                mapping = dict(cast(Mapping[str, Any], to_dict()))
            else:
                raise TypeError("Unsupported candle row type")
        mapping.pop("_id", None)
        return mapping

    def _fetch_candles_via_proxy(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> list[dict[str, Any]]:
        started_at_perf = perf_counter()
        proxy = self._data_proxy()
        get_candles = getattr(proxy, "get_candles", None)
        if callable(get_candles):
            raw_rows = get_candles(symbol, start, end)
            if not isinstance(raw_rows, Iterable):
                raise TypeError(
                    "dataserver get_candles returned a non-iterable payload"
                )
            bulk_result = [self._normalize_candle_row(row) for row in raw_rows]
            logger.info(
                "data_source: proxy_bulk_candle_fetch_completed; symbol=%s start=%s end=%s candle_count=%s duration_seconds=%.6f",
                symbol,
                start.isoformat(sep=" "),
                end.isoformat(sep=" "),
                len(bulk_result),
                perf_counter() - started_at_perf,
            )
            return bulk_result

        result: list[dict[str, Any]] = []
        missing_count = 0
        request_count = 0
        ts = start
        while ts <= end:
            request_count += 1
            try:
                row = proxy.get_data(symbol, ts)
            except Fault:
                missing_count += 1
                ts += timedelta(minutes=1)
                continue
            except Exception as exc:
                raise DataSourceUnavailableError(
                    self._format_unavailable_message()
                ) from exc
            result.append(self._normalize_candle_row(row))
            ts += timedelta(minutes=1)
        logger.info(
            "data_source: proxy_fetch_completed; symbol=%s start=%s end=%s candle_count=%s missing_count=%s request_count=%s duration_seconds=%.6f",
            symbol,
            start.isoformat(sep=" "),
            end.isoformat(sep=" "),
            len(result),
            missing_count,
            request_count,
            perf_counter() - started_at_perf,
        )
        return result

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

        logger.info(
            "data_source: candle_fetch_mode_selected; mode=dataserver_bulk_rpc_with_proxy_fallback symbol=%s start=%s end=%s",
            symbol,
            start.isoformat(sep=" "),
            end.isoformat(sep=" "),
        )
        result = self._fetch_candles_via_proxy(symbol=symbol, start=start, end=end)

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
