from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, init=False)
class DashboardConfig:
    secret_key: str
    mongo_uri: str
    mongo_db_name: str
    report_base_path: str
    experiment_max_concurrent_runs: int = 1

    def __init__(
        self,
        secret_key: str,
        mongo_uri: str,
        mongo_db_name: str,
        report_base_path: str,
        *_legacy_args: object,
        experiment_max_concurrent_runs: int = 1,
        **_legacy_kwargs: object,
    ) -> None:
        object.__setattr__(self, "secret_key", secret_key)
        object.__setattr__(self, "mongo_uri", mongo_uri)
        object.__setattr__(self, "mongo_db_name", mongo_db_name)
        object.__setattr__(self, "report_base_path", report_base_path)
        object.__setattr__(
            self,
            "experiment_max_concurrent_runs",
            int(experiment_max_concurrent_runs),
        )

    @classmethod
    def from_env(cls) -> "DashboardConfig":
        return cls(
            secret_key=os.environ.get("TRADING_ALGOS_DASHBOARD_SECRET", "dev-secret"),
            mongo_uri=os.environ.get(
                "TRADING_ALGOS_DASHBOARD_MONGO_URI", "mongodb://127.0.0.1:27017"
            ),
            mongo_db_name=os.environ.get(
                "TRADING_ALGOS_DASHBOARD_MONGO_DB", "trading_algos_dashboard"
            ),
            report_base_path=os.environ.get(
                "TRADING_ALGOS_DASHBOARD_REPORT_PATH", "dashboard_reports"
            ),
            experiment_max_concurrent_runs=int(
                os.environ.get(
                    "TRADING_ALGOS_DASHBOARD_EXPERIMENT_MAX_CONCURRENT_RUNS",
                    "1",
                )
            ),
        )
