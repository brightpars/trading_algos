from __future__ import annotations

from typing import Any

from trading_algos_dashboard.repositories.data_source_settings_repository import (
    DataSourceSettingsRepository,
)

DEFAULT_DATA_SERVER_IP = "127.0.0.2"
DEFAULT_DATA_SERVER_PORT = 6010


class DataSourceSettingsService:
    def __init__(self, *, repository: DataSourceSettingsRepository):
        self.repository = repository

    def get_effective_settings(self) -> dict[str, Any]:
        stored = self.repository.get_settings() or {}
        ip = stored.get("ip", DEFAULT_DATA_SERVER_IP)
        port = stored.get("port", DEFAULT_DATA_SERVER_PORT)
        return {
            "ip": str(ip),
            "port": int(port),
            "is_default": "ip" not in stored and "port" not in stored,
            "updated_at": stored.get("updated_at"),
        }

    def save_settings(self, *, ip: str, port: int) -> dict[str, Any]:
        normalized_ip = ip.strip()
        if not normalized_ip:
            raise ValueError("Data server IP is required")
        if port < 1 or port > 65535:
            raise ValueError("Data server port must be between 1 and 65535")
        saved = self.repository.save_settings(ip=normalized_ip, port=port)
        return {
            "ip": saved["ip"],
            "port": int(saved["port"]),
            "is_default": False,
            "updated_at": saved.get("updated_at"),
        }
