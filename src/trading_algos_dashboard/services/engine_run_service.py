from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from trading_algos_dashboard.services.server_rpc_clients import (
    EnginesControlServerClient,
    FakeDateTimeServerClient,
)


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
        fake_datetime_client = self._fake_datetime_client()
        self._initialize_fake_datetime(
            client=fake_datetime_client,
            start_dt=request.start_dt,
            speed_factor=request.speed_factor,
        )
        client = self._engines_control_client()
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
        result = client.run_engine_chain(payload)
        if not isinstance(result, dict):
            raise RuntimeError(
                "Engines control returned an invalid engine-chain payload"
            )
        return result

    def stop_chain(self) -> None:
        self._engines_control_client().stop_engine_chain()

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
        client: FakeDateTimeServerClient,
        start_dt: datetime,
        speed_factor: int,
    ) -> None:
        client.init(
            start_dt.strftime("%Y-%m-%d"),
            start_dt.strftime("%H:%M:%S"),
            int(speed_factor),
        )
        client.start_clock()

    def _fake_datetime_client(self) -> FakeDateTimeServerClient:
        host, port = self.fake_datetime_endpoint_resolver()
        return FakeDateTimeServerClient(host=host, port=int(port))

    def _engines_control_client(self) -> EnginesControlServerClient:
        host, port = self.engines_control_endpoint_resolver()
        return EnginesControlServerClient(host=host, port=int(port))

    def _fake_datetime_endpoint(self) -> str:
        host, port = self.fake_datetime_endpoint_resolver()
        return f"http://{host}:{int(port)}"

    def _engines_control_endpoint(self) -> str:
        host, port = self.engines_control_endpoint_resolver()
        return f"http://{host}:{int(port)}"
