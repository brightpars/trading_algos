from __future__ import annotations

from typing import Any

from trading_algos_dashboard.repositories.market_data_cache_settings_repository import (
    MarketDataCacheSettingsRepository,
)

DEFAULT_MEMORY_ENABLED = True
DEFAULT_MEMORY_MAX_ENTRIES = 100
DEFAULT_SHARED_ENABLED = True
DEFAULT_SHARED_MAX_ENTRIES = 1000
DEFAULT_SHARED_TTL_HOURS = 168


class MarketDataCacheSettingsService:
    def __init__(
        self,
        *,
        repository: MarketDataCacheSettingsRepository,
    ) -> None:
        self.repository = repository

    def get_effective_settings(self) -> dict[str, Any]:
        stored = self.repository.get_settings() or {}
        return {
            "memory_enabled": bool(
                stored.get("memory_enabled", DEFAULT_MEMORY_ENABLED)
            ),
            "memory_max_entries": int(
                stored.get("memory_max_entries", DEFAULT_MEMORY_MAX_ENTRIES)
            ),
            "shared_enabled": bool(
                stored.get("shared_enabled", DEFAULT_SHARED_ENABLED)
            ),
            "shared_max_entries": int(
                stored.get("shared_max_entries", DEFAULT_SHARED_MAX_ENTRIES)
            ),
            "shared_ttl_hours": int(
                stored.get("shared_ttl_hours", DEFAULT_SHARED_TTL_HOURS)
            ),
            "is_default": not bool(stored),
            "updated_at": stored.get("updated_at"),
        }

    def save_settings(
        self,
        *,
        memory_enabled: bool,
        memory_max_entries: int,
        shared_enabled: bool,
        shared_max_entries: int,
        shared_ttl_hours: int,
    ) -> dict[str, Any]:
        if memory_max_entries < 1:
            raise ValueError("Memory cache max entries must be at least 1")
        if shared_max_entries < 1:
            raise ValueError("DB cache max entries must be at least 1")
        if shared_ttl_hours < 1:
            raise ValueError("DB cache TTL hours must be at least 1")
        saved = self.repository.save_settings(
            memory_enabled=memory_enabled,
            memory_max_entries=memory_max_entries,
            shared_enabled=shared_enabled,
            shared_max_entries=shared_max_entries,
            shared_ttl_hours=shared_ttl_hours,
        )
        return {
            "memory_enabled": bool(saved["memory_enabled"]),
            "memory_max_entries": int(saved["memory_max_entries"]),
            "shared_enabled": bool(saved["shared_enabled"]),
            "shared_max_entries": int(saved["shared_max_entries"]),
            "shared_ttl_hours": int(saved["shared_ttl_hours"]),
            "is_default": False,
            "updated_at": saved.get("updated_at"),
        }
