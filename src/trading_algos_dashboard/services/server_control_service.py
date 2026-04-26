from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from trading_algos_dashboard.repositories.server_control_settings_repository import (
    ServerControlSettingsRepository,
)

SMARTTRADE_SERVER_DEFINITIONS: tuple[dict[str, Any], ...] = (
    {
        "name": "central",
        "label": "Central",
        "ip_key": "CENTRAL_SERVER_IP",
        "port_key": "CENTRAL_SERVER_PORT",
        "default_ip": "127.0.0.1",
        "default_port": 6000,
        "controllable": True,
        "uses_user_scope": False,
    },
    {
        "name": "data",
        "label": "Data",
        "ip_key": "DATA_SERVER_IP",
        "port_key": "DATA_SERVER_PORT",
        "default_ip": "127.0.0.1",
        "default_port": 6010,
        "controllable": True,
        "uses_user_scope": False,
    },
    {
        "name": "fake_datetime",
        "label": "Fake datetime",
        "ip_key": "FAKE_DATE_TIME_SERVER_IP",
        "port_key": "FAKE_DATE_TIME_SERVER_PORT",
        "default_ip": "127.0.0.1",
        "default_port": 7100,
        "controllable": True,
        "uses_user_scope": True,
    },
    {
        "name": "broker",
        "label": "Broker",
        "ip_key": "BROKER_SERVER_IP",
        "port_key": "BROKER_SERVER_PORT",
        "default_ip": "127.0.0.1",
        "default_port": 7101,
        "controllable": False,
        "uses_user_scope": True,
    },
    {
        "name": "engines_control",
        "label": "Engines control",
        "ip_key": "ENGINES_CONTROL_SERVER_IP",
        "port_key": "ENGINES_CONTROL_SERVER_PORT",
        "default_ip": "127.0.0.1",
        "default_port": 7102,
        "controllable": True,
        "uses_user_scope": True,
    },
)


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
        smarttrade_path: str,
        user_id: int,
        repository: ServerControlSettingsRepository,
    ) -> None:
        self.smarttrade_path = smarttrade_path
        self.user_id = user_id
        self.repository = repository

    def _prepare_imports(self) -> None:
        path = str(Path(self.smarttrade_path).resolve())
        if path not in sys.path:
            sys.path.insert(0, path)

    def _load_config_service(self) -> Any:
        self._prepare_imports()
        config_module = importlib.import_module("config.service")
        return getattr(config_module, "get_config_service")()

    def _load_server_lifecycle(self) -> Any:
        self._prepare_imports()
        return importlib.import_module("infrastructure.runtime.server_lifecycle")

    def _load_config_storage(self) -> Any:
        self._prepare_imports()
        return importlib.import_module("config.storage")

    def _load_toggle_server_boundary(self) -> Any:
        self._prepare_imports()
        return importlib.import_module("application.system.toggle_server")

    def _load_server_toggle_service_class(self) -> type[Any]:
        lifecycle_module = self._load_server_lifecycle()
        return lifecycle_module.ServerToggleService

    def _load_proxy(self, module_name: str, factory_name: str) -> Any:
        self._prepare_imports()
        module = importlib.import_module(module_name)
        factory = getattr(module, factory_name)
        return factory(self.user_id)

    def _definition_by_name(self, server_name: str) -> dict[str, Any]:
        for definition in SMARTTRADE_SERVER_DEFINITIONS:
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
            for definition in SMARTTRADE_SERVER_DEFINITIONS
        }

    def _persisted_port_config_values(self, ports: dict[str, int]) -> dict[str, int]:
        config_service = self._load_config_service()
        port_step = int(config_service.get_global("PORT_PER_USER"))
        return {
            "CENTRAL_SERVER_PORT": int(ports["central"]),
            "DATA_SERVER_PORT": int(ports["data"]),
            "USER_FAKE_DATE_TIME_SERVER_PORT": int(ports["fake_datetime"])
            - self.user_id * port_step,
            "USER_BROKER_SERVER_PORT": int(ports["broker"]) - self.user_id * port_step,
            "USER_ENGINES_CONTROL_SERVER_PORT": int(ports["engines_control"])
            - self.user_id * port_step,
        }

    def _persist_port_settings(self, ports: dict[str, int]) -> None:
        storage = self._load_config_storage()
        state = storage.get_state_copy()
        global_state = state.setdefault("global", {})
        updated_at = datetime.now(timezone.utc).isoformat()
        for key, value in self._persisted_port_config_values(ports).items():
            global_state[key] = {
                "value": int(value),
                "updated_at": updated_at,
                "updated_by": "trading_algos_dashboard",
            }
        storage.save_state(state)

    def get_port_settings(self) -> dict[str, Any]:
        defaults = self._default_port_map()
        stored_ports = self._stored_ports()
        ports = {**defaults, **stored_ports}
        return {
            "ports": ports,
            "is_default": not stored_ports,
            "updated_at": (self.repository.get_settings() or {}).get("updated_at"),
        }

    def apply_port_settings(self) -> dict[str, int]:
        config_service = self._load_config_service()
        ports = self.get_port_settings()["ports"]
        self._persist_port_settings(ports)
        persisted_values = self._persisted_port_config_values(ports)
        for definition in SMARTTRADE_SERVER_DEFINITIONS:
            if definition["uses_user_scope"]:
                config_service.set_runtime_override(
                    definition["port_key"],
                    int(ports[definition["name"]]),
                    user_id=self.user_id,
                )
                continue
            config_service.set_runtime_override(
                definition["port_key"],
                int(persisted_values[definition["port_key"]]),
            )
        for key, value in persisted_values.items():
            if key.startswith("USER_"):
                config_service.set_runtime_override(key, int(value))
        return ports

    def save_ports(self, submitted_ports: dict[str, Any]) -> dict[str, Any]:
        normalized_ports: dict[str, int] = {}
        for definition in SMARTTRADE_SERVER_DEFINITIONS:
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
        self._persist_port_settings(normalized_ports)
        self.apply_port_settings()
        return {
            "ports": {key: int(value) for key, value in dict(saved["ports"]).items()},
            "is_default": False,
            "updated_at": saved.get("updated_at"),
        }

    def _server_runtime_state(self, server_name: str) -> str:
        lifecycle = self._load_server_lifecycle()
        return str(
            lifecycle.get_server_runtime_state(
                servername=server_name,
                user_id=self.user_id,
            )
        )

    def _toggle_service(self) -> Any:
        toggle_service = getattr(self, "_cached_toggle_service", None)
        if toggle_service is None:
            toggle_service = self._load_server_toggle_service_class()()
            self._cached_toggle_service = toggle_service
        return toggle_service

    def _perform_smarttrade_toggle(self, server_name: str) -> dict[str, Any]:
        toggle_boundary = self._load_toggle_server_boundary()
        result = toggle_boundary.toggle_server(
            active_user=_ServerRuntimeUserAdapter(
                smarttrade_path=self.smarttrade_path,
                user_id=self.user_id,
            ),
            servername=server_name,
            toggle_service=self._toggle_service(),
        )
        return dict(result.to_dict())

    def _build_status_details(self, server_name: str, state: str) -> str:
        if state != "up":
            return ""
        if server_name == "data":
            proxy = self._load_proxy(
                "utils_shared.objects_factory.data_proxy",
                "get_or_create_data_proxy",
            )
            ping_with_timeout = getattr(proxy, "ping_with_timeout", None)
            if callable(ping_with_timeout):
                try:
                    return str(ping_with_timeout(2.0))
                except Exception:
                    return "running"
        return "running"

    def list_servers(self) -> list[dict[str, Any]]:
        self.apply_port_settings()
        config_service = self._load_config_service()
        port_settings = self.get_port_settings()["ports"]
        servers: list[dict[str, Any]] = []
        for definition in SMARTTRADE_SERVER_DEFINITIONS:
            if definition["uses_user_scope"]:
                ip = str(
                    config_service.get_effective_value(
                        definition["ip_key"], user_id=self.user_id
                    )
                )
            else:
                ip = str(config_service.get_effective_value(definition["ip_key"]))
            state = self._server_runtime_state(definition["name"])
            servers.append(
                {
                    "name": definition["name"],
                    "label": definition["label"],
                    "ip": ip,
                    "port": int(port_settings[definition["name"]]),
                    "state": state,
                    "details": self._build_status_details(definition["name"], state),
                    "controllable": bool(definition["controllable"]),
                }
            )
        return servers

    def perform_action(self, *, server_name: str, action: str) -> ServerActionResult:
        definition = self._definition_by_name(server_name)
        if not definition["controllable"]:
            raise ValueError(f"Server {definition['label']} cannot be controlled here")
        if action not in {"start", "stop"}:
            raise ValueError("Action must be start or stop")
        self.apply_port_settings()
        current_state = self._server_runtime_state(server_name)
        desired_state = "up" if action == "start" else "down"
        if current_state != desired_state:
            toggle_result = self._perform_smarttrade_toggle(server_name)
            state = str(
                toggle_result.get("state", self._server_runtime_state(server_name))
            )
            return ServerActionResult(
                server_name=server_name,
                action=action,
                state=state,
                expected_state=desired_state,
                succeeded=state == desired_state,
            )
        return ServerActionResult(
            server_name=server_name,
            action=action,
            state=self._server_runtime_state(server_name),
            expected_state=desired_state,
            succeeded=True,
        )


class _ServerRuntimeUserAdapter:
    def __init__(self, *, smarttrade_path: str, user_id: int) -> None:
        self.smarttrade_path = smarttrade_path
        self.user_id = user_id

    def _prepare_imports(self) -> None:
        path = str(Path(self.smarttrade_path).resolve())
        if path not in sys.path:
            sys.path.insert(0, path)

    def _load_proxy(self, module_name: str, factory_name: str) -> Any:
        self._prepare_imports()
        module = importlib.import_module(module_name)
        factory = getattr(module, factory_name)
        return factory(self.user_id)

    def is_decision_maker_process_up(self) -> bool:
        proxy = self._load_proxy(
            "utils_shared.objects_factory.engines_control_proxy",
            "get_or_create_engines_control_proxy",
        )
        method = getattr(proxy, "is_decision_maker_running", None)
        if not callable(method):
            return False
        try:
            return bool(method())
        except Exception:
            return False

    def are_alertgens_processes_up(self) -> bool:
        proxy = self._load_proxy(
            "utils_shared.objects_factory.engines_control_proxy",
            "get_or_create_engines_control_proxy",
        )
        method = getattr(proxy, "get_all_alertgen_info", None)
        if not callable(method):
            return False
        try:
            result = method()
        except Exception:
            return False
        return bool(result)
