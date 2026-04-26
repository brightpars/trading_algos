from __future__ import annotations

import logging
from collections.abc import Callable
from collections.abc import Iterable
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from time import perf_counter
from time import sleep
from typing import Any
from typing import Protocol
from typing import cast
from uuid import uuid4
from xmlrpc.client import DateTime as XmlRpcDateTime
from xmlrpc.client import Fault
from xmlrpc.client import ServerProxy

from trading_algos_dashboard.services.data_source_settings_service import (
    DEFAULT_DATA_SERVER_IP,
    DEFAULT_DATA_SERVER_PORT,
)
from trading_algos_dashboard.services.market_data_cache import (
    InMemoryMarketDataCache,
    LayeredMarketDataCache,
)


DEFAULT_CONNECTION_CHECK_TIMEOUT_SECONDS = 2.0
DEFAULT_CACHE_FILL_LEASE_SECONDS = 10
DEFAULT_CACHE_FILL_WAIT_SECONDS = 0.5
DEFAULT_CACHE_FILL_POLL_INTERVAL_SECONDS = 0.05

logger = logging.getLogger(__name__)


class DataSourceUnavailableError(RuntimeError):
    """Raised when the market data source cannot be accessed."""


class MarketDataUnavailableError(ValueError):
    """Raised when requested market data is not available for the given range."""


@dataclass(frozen=True)
class MarketDataFetchResult:
    candles: list[dict[str, Any]]
    cache_hit: bool
    source_kind: str
    symbol: str
    start: datetime
    end: datetime
    candle_count: int


class MarketDataProxy(Protocol):
    def ping(self) -> str: ...

    def get_data(self, symbol: str, ts: object) -> Any: ...

    def get_candles(self, symbol: str, start: object, end: object) -> Any: ...


class XmlRpcMarketDataProxy:
    def __init__(self, *, ip: str, port: int, timeout_seconds: float) -> None:
        self.endpoint = f"http://{ip}:{port}"
        self.timeout_seconds = timeout_seconds
        self._proxy = ServerProxy(self.endpoint, allow_none=True)

    @staticmethod
    def _serialize_remote_datetime(value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S")

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

    def get_data(self, symbol: str, ts: object) -> Any:
        payload = ts
        if isinstance(ts, datetime):
            payload = self._serialize_remote_datetime(ts)
        return self._proxy.get_data(symbol, cast(Any, payload))

    def get_candles(self, symbol: str, start: object, end: object) -> Any:
        start_payload = start
        end_payload = end
        if isinstance(start, datetime):
            start_payload = self._serialize_remote_datetime(start)
        if isinstance(end, datetime):
            end_payload = self._serialize_remote_datetime(end)
        return self._proxy.get_candles(
            symbol,
            cast(Any, start_payload),
            cast(Any, end_payload),
        )


class MarketDataSourceService:
    def __init__(
        self,
        *,
        smarttrade_path: str | None = None,
        user_id: int | None = None,
        endpoint_resolver: Callable[[], tuple[str, int] | None] | None = None,
        market_data_cache: LayeredMarketDataCache | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        proxy_factory: Callable[..., MarketDataProxy] | None = None,
    ):
        self.endpoint_resolver = endpoint_resolver
        self.market_data_cache = market_data_cache or LayeredMarketDataCache(
            memory_cache=InMemoryMarketDataCache(enabled=True)
        )
        self.sleep_fn = sleep_fn or sleep
        self.proxy_factory = proxy_factory or (
            lambda *, ip, port, timeout_seconds: XmlRpcMarketDataProxy(
                ip=ip,
                port=port,
                timeout_seconds=timeout_seconds,
            )
        )

    def _resolved_endpoint(self) -> tuple[str, int]:
        if self.endpoint_resolver is None:
            return DEFAULT_DATA_SERVER_IP, DEFAULT_DATA_SERVER_PORT
        resolved = self.endpoint_resolver()
        if resolved is None:
            return DEFAULT_DATA_SERVER_IP, DEFAULT_DATA_SERVER_PORT
        return str(resolved[0]), int(resolved[1])

    def _data_server_endpoint_label(self) -> str:
        ip, port = self._resolved_endpoint()
        return f"{ip}:{port}"

    def _format_unavailable_message(self) -> str:
        return (
            "Market data service is unavailable. "
            "Please make sure the data server is running. "
            f"Tried to connect to {self._data_server_endpoint_label()}."
        )

    def _is_proxy_server_up(
        self,
        proxy: Any,
        *,
        timeout_seconds: float = DEFAULT_CONNECTION_CHECK_TIMEOUT_SECONDS,
    ) -> bool:
        ping_with_timeout = getattr(proxy, "ping_with_timeout", None)
        if callable(ping_with_timeout):
            return ping_with_timeout(timeout_seconds) == "pong"
        ping = getattr(proxy, "ping", None)
        if callable(ping):
            return ping() == "pong"
        is_server_up = getattr(proxy, "is_server_up", None)
        if callable(is_server_up):
            return bool(is_server_up())
        return False

    def get_market_data_server_details(self) -> dict[str, Any]:
        ip, port = self._resolved_endpoint()
        return {
            "kind": "xmlrpc_dataserver",
            "ip": ip,
            "port": port,
            "endpoint": f"{ip}:{port}",
            "cache": {
                "enabled": self.market_data_cache.enabled,
                **self.market_data_cache.stats(),
            },
        }

    def _data_proxy(self) -> MarketDataProxy:
        ip, port = self._resolved_endpoint()
        try:
            proxy = self.proxy_factory(
                ip=ip,
                port=port,
                timeout_seconds=DEFAULT_CONNECTION_CHECK_TIMEOUT_SECONDS,
            )
            if not self._is_proxy_server_up(proxy):
                raise DataSourceUnavailableError(self._format_unavailable_message())
            return proxy
        except DataSourceUnavailableError:
            raise
        except Exception as exc:
            raise DataSourceUnavailableError(
                self._format_unavailable_message()
            ) from exc

    @staticmethod
    def _clone_candles(candles: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
        return [dict(row) for row in candles]

    @staticmethod
    def _serialize_dataserver_datetime(value: datetime) -> str:
        return value.strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def _normalize_xmlrpc_value(value: Any) -> Any:
        if isinstance(value, XmlRpcDateTime):
            parsed = datetime.strptime(value.value, "%Y%m%dT%H:%M:%S")
            return parsed.replace(tzinfo=timezone.utc)
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)
        if isinstance(value, Mapping):
            return {
                str(key): MarketDataSourceService._normalize_xmlrpc_value(item)
                for key, item in value.items()
            }
        if isinstance(value, tuple):
            return tuple(
                MarketDataSourceService._normalize_xmlrpc_value(item) for item in value
            )
        if isinstance(value, list):
            return [
                MarketDataSourceService._normalize_xmlrpc_value(item) for item in value
            ]
        return value

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
        normalized = MarketDataSourceService._normalize_xmlrpc_value(mapping)
        if not isinstance(normalized, dict):
            raise TypeError("Normalized candle row must be a mapping")
        return normalized

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
            raw_rows = get_candles(
                symbol,
                self._serialize_dataserver_datetime(start),
                self._serialize_dataserver_datetime(end),
            )
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
                row = proxy.get_data(
                    symbol,
                    self._serialize_dataserver_datetime(ts),
                )
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
    ) -> MarketDataFetchResult:
        if end < start:
            raise ValueError("End datetime must be after start datetime")

        normalized_symbol = symbol.strip().upper()

        logger.info(
            "data_source: candle_fetch_mode_selected; mode=dataserver_bulk_rpc_with_proxy_fallback symbol=%s start=%s end=%s",
            normalized_symbol,
            start.isoformat(sep=" "),
            end.isoformat(sep=" "),
        )

        cached = self.market_data_cache.get(
            symbol=normalized_symbol,
            start=start,
            end=end,
        )
        if cached is not None:
            candles = self._clone_candles(cached.candles)
            return MarketDataFetchResult(
                candles=candles,
                cache_hit=True,
                source_kind=cached.source_kind,
                symbol=normalized_symbol,
                start=start,
                end=end,
                candle_count=len(candles),
            )

        owner_id = f"cache_fill_{uuid4().hex}"
        shared_cache = self.market_data_cache.shared_cache
        has_fill_claim = False
        if shared_cache is not None:
            has_fill_claim = shared_cache.try_claim_fill(
                symbol=normalized_symbol,
                start=start,
                end=end,
                owner_id=owner_id,
                lease_until=datetime.now(timezone.utc)
                + timedelta(seconds=DEFAULT_CACHE_FILL_LEASE_SECONDS),
            )
            if not has_fill_claim:
                waited = self._wait_for_shared_cache_fill(
                    symbol=normalized_symbol,
                    start=start,
                    end=end,
                )
                if waited is not None:
                    candles = self._clone_candles(waited.candles)
                    return MarketDataFetchResult(
                        candles=candles,
                        cache_hit=True,
                        source_kind=waited.source_kind,
                        symbol=normalized_symbol,
                        start=start,
                        end=end,
                        candle_count=len(candles),
                    )

        try:
            result = self._fetch_candles_via_proxy(
                symbol=normalized_symbol,
                start=start,
                end=end,
            )
        finally:
            if has_fill_claim and shared_cache is not None:
                shared_cache.release_fill_claim(
                    symbol=normalized_symbol,
                    start=start,
                    end=end,
                    owner_id=owner_id,
                )

        if not result:
            raise MarketDataUnavailableError(
                "No candle data is available for the requested symbol and time range. "
                "Please choose a range that contains market data."
            )

        self.market_data_cache.put(
            symbol=normalized_symbol,
            start=start,
            end=end,
            candles=result,
        )

        candles = self._clone_candles(result)
        return MarketDataFetchResult(
            candles=candles,
            cache_hit=False,
            source_kind="dataserver",
            symbol=normalized_symbol,
            start=start,
            end=end,
            candle_count=len(candles),
        )

    def _wait_for_shared_cache_fill(
        self,
        *,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> Any | None:
        deadline = perf_counter() + DEFAULT_CACHE_FILL_WAIT_SECONDS
        while perf_counter() < deadline:
            cached = self.market_data_cache.get(symbol=symbol, start=start, end=end)
            if cached is not None and cached.source_kind == "shared_cache":
                return cached
            self.sleep_fn(DEFAULT_CACHE_FILL_POLL_INTERVAL_SECONDS)
        return None


class LegacyMarketDataSourceService(MarketDataSourceService):
    def __init__(
        self,
        *,
        smarttrade_path: str | None = None,
        user_id: int | None = None,
        endpoint_resolver: Callable[[], tuple[str, int] | None] | None = None,
        market_data_cache: LayeredMarketDataCache | None = None,
        sleep_fn: Callable[[float], None] | None = None,
        proxy_factory: Callable[..., MarketDataProxy] | None = None,
    ):
        super().__init__(
            smarttrade_path=smarttrade_path,
            user_id=user_id,
            endpoint_resolver=endpoint_resolver,
            market_data_cache=market_data_cache,
            sleep_fn=sleep_fn,
            proxy_factory=proxy_factory,
        )


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
