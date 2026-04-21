from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class DashboardConfig:
    secret_key: str
    mongo_uri: str
    mongo_db_name: str
    report_base_path: str
    smarttrade_path: str
    smarttrade_user_id: int
    smarttrade_api_base_url: str = "http://127.0.0.1:5000"
    smarttrade_api_token: str = ""
    smarttrade_api_timeout_secs: int = 10

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
            smarttrade_path=os.environ.get(
                "SMARTTRADE_PATH", "/home/mohammad/development/smarttrade"
            ),
            smarttrade_user_id=int(
                os.environ.get("TRADING_ALGOS_DASHBOARD_SMARTTRADE_USER_ID", "1")
            ),
            smarttrade_api_base_url=os.environ.get(
                "TRADING_ALGOS_DASHBOARD_SMARTTRADE_API_BASE_URL",
                "http://127.0.0.1:5000",
            ),
            smarttrade_api_token=os.environ.get(
                "TRADING_ALGOS_DASHBOARD_SMARTTRADE_API_TOKEN",
                "",
            ),
            smarttrade_api_timeout_secs=int(
                os.environ.get(
                    "TRADING_ALGOS_DASHBOARD_SMARTTRADE_API_TIMEOUT_SECS", "10"
                )
            ),
        )
