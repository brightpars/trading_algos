from __future__ import annotations

from typing import Any

from trading_algos_dashboard.repositories.experiment_runtime_settings_repository import (
    ExperimentRuntimeSettingsRepository,
)


class ExperimentRuntimeSettingsService:
    def __init__(
        self,
        *,
        repository: ExperimentRuntimeSettingsRepository,
        default_max_concurrent_experiments: int,
    ) -> None:
        self.repository = repository
        self.default_max_concurrent_experiments = default_max_concurrent_experiments

    def get_effective_settings(self) -> dict[str, Any]:
        stored = self.repository.get_settings() or {}
        value = stored.get(
            "max_concurrent_experiments", self.default_max_concurrent_experiments
        )
        return {
            "max_concurrent_experiments": int(value),
            "is_default": "max_concurrent_experiments" not in stored,
            "updated_at": stored.get("updated_at"),
        }

    def save_settings(self, *, max_concurrent_experiments: int) -> dict[str, Any]:
        if max_concurrent_experiments < 1:
            raise ValueError("Max concurrent experiments must be at least 1")
        saved = self.repository.save_settings(
            max_concurrent_experiments=max_concurrent_experiments
        )
        return {
            "max_concurrent_experiments": int(saved["max_concurrent_experiments"]),
            "is_default": False,
            "updated_at": saved.get("updated_at"),
        }
