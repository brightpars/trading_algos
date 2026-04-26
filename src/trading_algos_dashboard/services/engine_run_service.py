from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from xmlrpc.client import ServerProxy


@dataclass(frozen=True)
class EngineRunRequest:
    symbol: str
    start_dt: datetime
    end_dt: datetime
    speed_factor: int
    candles: list[dict[str, Any]]
    alertgens: list[dict[str, Any]]
    decmaker: dict[str, Any]
    report_dir: str


class EngineRunService:
    def __init__(
        self,
        *,
        server_control_service: Any,
        fake_datetime_endpoint_resolver: Any,
        engines_control_endpoint_resolver: Any,
    ) -> None:
        self.server_control_service = server_control_service
        self.fake_datetime_endpoint_resolver = fake_datetime_endpoint_resolver
        self.engines_control_endpoint_resolver = engines_control_endpoint_resolver

    def run_chain(self, request: EngineRunRequest) -> dict[str, Any]:
        self._ensure_required_services_running()
        self._initialize_fake_datetime(
            start_dt=request.start_dt,
            speed_factor=request.speed_factor,
        )
        endpoint = self._engines_control_endpoint()
        proxy = ServerProxy(endpoint, allow_none=True)
        payload = {
            "symbol": request.symbol,
            "start": request.start_dt.astimezone(timezone.utc).isoformat(),
            "end": request.end_dt.astimezone(timezone.utc).isoformat(),
            "speed_factor": int(request.speed_factor),
            "candles": request.candles,
            "alertgens": request.alertgens,
            "decmaker": request.decmaker,
            "report_base_path": request.report_dir,
        }
        result = proxy.run_engine_chain(payload)
        if not isinstance(result, dict):
            raise RuntimeError(
                "Engines control returned an invalid engine-chain payload"
            )
        return result

    def stop_chain(self) -> None:
        endpoint = self._engines_control_endpoint()
        proxy = ServerProxy(endpoint, allow_none=True)
        stop_chain = getattr(proxy, "stop_engine_chain", None)
        if callable(stop_chain):
            stop_chain()

    def _ensure_required_services_running(self) -> None:
        for server_name in ("central", "data", "fake_datetime", "engines_control"):
            state = self.server_control_service._server_runtime_state(server_name)
            if state == "up":
                continue
            result = self.server_control_service.perform_action(
                server_name=server_name,
                action="start",
            )
            if not result.succeeded:
                raise RuntimeError(
                    f"Required service failed to start: server={server_name}"
                )

    def _initialize_fake_datetime(
        self,
        *,
        start_dt: datetime,
        speed_factor: int,
    ) -> None:
        endpoint = self._fake_datetime_endpoint()
        proxy = ServerProxy(endpoint, allow_none=True)
        proxy.init(
            start_dt.strftime("%Y-%m-%d"),
            start_dt.strftime("%H:%M:%S"),
            int(speed_factor),
        )
        proxy.start_clock()

    def _fake_datetime_endpoint(self) -> str:
        host, port = self.fake_datetime_endpoint_resolver()
        return f"http://{host}:{int(port)}"

    def _engines_control_endpoint(self) -> str:
        host, port = self.engines_control_endpoint_resolver()
        return f"http://{host}:{int(port)}"
