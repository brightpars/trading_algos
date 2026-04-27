from __future__ import annotations

import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from trading_algos_dashboard.repositories.server_control_settings_repository import (
    ServerControlSettingsRepository,
)

SERVICE_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "name": "central",
        "label": "Central",
        "default_ip": "127.0.0.1",
        "default_port": 6000,
        "controllable": True,
        "start_command_env": "TRADING_ALGOS_DASHBOARD_CENTRAL_START_CMD",
        "workdir_env": "TRADING_ALGOS_DASHBOARD_CENTRAL_WORKDIR",
        "host_env": "TRADING_ALGOS_DASHBOARD_CENTRAL_HOST",
        "default_start_command": "./.venv/bin/python -m trading_algos_dashboard.service_runtime central",
    },
    {
        "name": "data",
        "label": "Data",
        "default_ip": "127.0.0.1",
        "default_port": 6010,
        "controllable": True,
        "start_command_env": "TRADING_ALGOS_DASHBOARD_DATA_START_CMD",
        "workdir_env": "TRADING_ALGOS_DASHBOARD_DATA_WORKDIR",
        "host_env": "TRADING_ALGOS_DASHBOARD_DATA_HOST",
        "default_start_command": "./.venv/bin/python -m trading_algos_dashboard.service_runtime data",
    },
    {
        "name": "fake_datetime",
        "label": "Fake datetime",
        "default_ip": "127.0.0.1",
        "default_port": 7100,
        "controllable": True,
        "start_command_env": "TRADING_ALGOS_DASHBOARD_FAKE_DATETIME_START_CMD",
        "workdir_env": "TRADING_ALGOS_DASHBOARD_FAKE_DATETIME_WORKDIR",
        "host_env": "TRADING_ALGOS_DASHBOARD_FAKE_DATETIME_HOST",
        "default_start_command": "./.venv/bin/python -m trading_algos_dashboard.service_runtime fake_datetime",
    },
    {
        "name": "broker",
        "label": "Broker",
        "default_ip": "127.0.0.1",
        "default_port": 7101,
        "controllable": False,
        "start_command_env": "TRADING_ALGOS_DASHBOARD_BROKER_START_CMD",
        "workdir_env": "TRADING_ALGOS_DASHBOARD_BROKER_WORKDIR",
        "host_env": "TRADING_ALGOS_DASHBOARD_BROKER_HOST",
        "default_start_command": "",
    },
    {
        "name": "engines_control",
        "label": "Engines control",
        "default_ip": "127.0.0.1",
        "default_port": 7102,
        "controllable": True,
        "start_command_env": "TRADING_ALGOS_DASHBOARD_ENGINES_CONTROL_START_CMD",
        "workdir_env": "TRADING_ALGOS_DASHBOARD_ENGINES_CONTROL_WORKDIR",
        "host_env": "TRADING_ALGOS_DASHBOARD_ENGINES_CONTROL_HOST",
        "default_start_command": "./.venv/bin/python -m trading_algos_dashboard.service_runtime engines_control",
    },
)

_REPO_ROOT = Path(__file__).resolve().parents[3]

_START_TIMEOUT_SECONDS = 5.0
_STOP_TIMEOUT_SECONDS = 5.0
_POLL_INTERVAL_SECONDS = 0.1


@dataclass(frozen=True)
class ServerActionResult:
    server_name: str
    action: str
    state: str
    expected_state: str
    succeeded: bool


class ServerControlService:
    def __init__(
        self,
        *,
        user_id: int = 1,
        repository: ServerControlSettingsRepository,
    ) -> None:
        self.user_id = user_id
        self.repository = repository

    def _definition_by_name(self, server_name: str) -> dict[str, Any]:
        for definition in SERVICE_DEFINITIONS:
            if definition["name"] == server_name:
                return dict(definition)
        raise ValueError(f"Unknown server: {server_name}")

    def _stored_ports(self) -> dict[str, int]:
        stored = self.repository.get_settings() or {}
        raw_ports = stored.get("ports") or {}
        return {str(key): int(value) for key, value in dict(raw_ports).items()}

    def _default_port_map(self) -> dict[str, int]:
        return {
            definition["name"]: int(definition["default_port"])
            for definition in SERVICE_DEFINITIONS
        }

    def _port_map(self) -> dict[str, int]:
        return {**self._default_port_map(), **self._stored_ports()}

    def _configured_host(self, definition: dict[str, Any]) -> str:
        env_value = os.environ.get(str(definition["host_env"]), "").strip()
        if env_value:
            return env_value
        return str(definition["default_ip"])

    def _default_start_command_for_definition(
        self, definition: dict[str, Any]
    ) -> str | None:
        default_command = str(definition.get("default_start_command", "")).strip()
        return default_command or None

    def _default_workdir_for_definition(self, definition: dict[str, Any]) -> str:
        return str(_REPO_ROOT)

    def _service_environment(
        self, definition: dict[str, Any], *, port: int
    ) -> dict[str, str]:
        host = self._configured_host(definition)
        return {
            "SERVICE_NAME": str(definition["name"]),
            "SERVICE_LABEL": str(definition["label"]),
            "SERVICE_HOST": host,
            "SERVICE_PORT": str(port),
            "SERVICE_USER_ID": str(self.user_id),
        }

    def _start_command_details(
        self, definition: dict[str, Any]
    ) -> tuple[str | None, str]:
        env_value = os.environ.get(str(definition["start_command_env"]), "").strip()
        if env_value:
            return env_value, "env override"
        default_command = self._default_start_command_for_definition(definition)
        if default_command:
            return default_command, "dashboard default"
        return None, "No dashboard start command is configured for this service."

    def _service_startability(self, definition: dict[str, Any]) -> tuple[bool, str]:
        command, source_or_reason = self._start_command_details(definition)
        if command is None:
            return False, source_or_reason
        return True, source_or_reason

    def get_port_settings(self) -> dict[str, Any]:
        settings = self.repository.get_settings() or {}
        stored_ports = self._stored_ports()
        return {
            "ports": self._port_map(),
            "is_default": not stored_ports,
            "updated_at": settings.get("updated_at"),
        }

    def get_service_endpoint(self, server_name: str) -> tuple[str, int]:
        definition = self._definition_by_name(server_name)
        return self._configured_host(definition), int(self._port_map()[server_name])

    def save_ports(self, submitted_ports: dict[str, Any]) -> dict[str, Any]:
        normalized_ports: dict[str, int] = {}
        for definition in SERVICE_DEFINITIONS:
            raw_value = submitted_ports.get(definition["name"])
            if raw_value is None:
                raise ValueError(f"Port is required for {definition['label']}")
            port = int(raw_value)
            if port < 1 or port > 65535:
                raise ValueError(
                    f"Port for {definition['label']} must be between 1 and 65535"
                )
            normalized_ports[definition["name"]] = port
        saved = self.repository.save_settings(ports=normalized_ports)
        return {
            "ports": {key: int(value) for key, value in dict(saved["ports"]).items()},
            "is_default": False,
            "updated_at": saved.get("updated_at"),
        }

    def _listener_pids(self, port: int) -> list[int]:
        result = subprocess.run(
            ["lsof", "-t", "-nP", f"-iTCP:{port}", "-sTCP:LISTEN"],
            capture_output=True,
            text=True,
            check=False,
        )
        values = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        return sorted({int(value) for value in values})

    def _is_port_listening(self, port: int) -> bool:
        return bool(self._listener_pids(port))

    def _wait_for_port_state(
        self, *, port: int, listening: bool, timeout: float
    ) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if self._is_port_listening(port) == listening:
                return True
            time.sleep(_POLL_INTERVAL_SECONDS)
        return self._is_port_listening(port) == listening

    def _server_runtime_state(self, server_name: str) -> str:
        port = int(self._port_map()[server_name])
        return "up" if self._is_port_listening(port) else "down"

    def _build_status_details(self, server_name: str, state: str) -> str:
        if state != "up":
            return ""
        port = int(self._port_map()[server_name])
        pids = self._listener_pids(port)
        if not pids:
            return "running"
        return f"listening; pids={','.join(str(pid) for pid in pids)}"

    def list_servers(self) -> list[dict[str, Any]]:
        ports = self._port_map()
        servers: list[dict[str, Any]] = []
        for definition in SERVICE_DEFINITIONS:
            state = self._server_runtime_state(str(definition["name"]))
            startable, start_reason = self._service_startability(definition)
            servers.append(
                {
                    "name": definition["name"],
                    "label": definition["label"],
                    "ip": self._configured_host(definition),
                    "port": int(ports[str(definition["name"])]),
                    "state": state,
                    "details": self._build_status_details(
                        str(definition["name"]), state
                    ),
                    "controllable": bool(definition["controllable"]),
                    "startable": startable,
                    "start_reason": start_reason,
                }
            )
        return servers

    def _start_command(self, definition: dict[str, Any]) -> str:
        command, source_or_reason = self._start_command_details(definition)
        if command is None:
            raise RuntimeError(
                f"Start unavailable for {definition['label']}: {source_or_reason}"
            )
        return command

    def _spawn_service(self, definition: dict[str, Any], *, port: int) -> None:
        environment = os.environ.copy()
        environment.update(self._service_environment(definition, port=port))
        workdir = os.environ.get(str(definition["workdir_env"]), "").strip() or str(
            _REPO_ROOT
        )
        environment["PYTHONPATH"] = (
            f"{_REPO_ROOT / 'src'}:{environment['PYTHONPATH']}"
            if environment.get("PYTHONPATH")
            else str(_REPO_ROOT / "src")
        )
        subprocess.Popen(
            ["/bin/bash", "-lc", self._start_command(definition)],
            cwd=workdir,
            env=environment,
            start_new_session=True,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _stop_service(self, *, port: int) -> None:
        for pid in self._listener_pids(port):
            try:
                os.kill(pid, 15)
            except OSError:
                continue
        if self._wait_for_port_state(port=port, listening=False, timeout=1.0):
            return
        for pid in self._listener_pids(port):
            try:
                os.kill(pid, 9)
            except OSError:
                continue

    def perform_action(self, *, server_name: str, action: str) -> ServerActionResult:
        definition = self._definition_by_name(server_name)
        if not bool(definition["controllable"]):
            raise ValueError(f"Server {definition['label']} cannot be controlled here")
        if action not in {"start", "stop"}:
            raise ValueError("Action must be start or stop")

        port = int(self._port_map()[server_name])
        desired_state = "up" if action == "start" else "down"
        current_state = self._server_runtime_state(server_name)
        if current_state == desired_state:
            return ServerActionResult(
                server_name=server_name,
                action=action,
                state=current_state,
                expected_state=desired_state,
                succeeded=True,
            )

        if action == "start":
            self._spawn_service(definition, port=port)
            succeeded = self._wait_for_port_state(
                port=port,
                listening=True,
                timeout=_START_TIMEOUT_SECONDS,
            )
        else:
            self._stop_service(port=port)
            succeeded = self._wait_for_port_state(
                port=port,
                listening=False,
                timeout=_STOP_TIMEOUT_SECONDS,
            )

        return ServerActionResult(
            server_name=server_name,
            action=action,
            state=self._server_runtime_state(server_name),
            expected_state=desired_state,
            succeeded=succeeded,
        )
