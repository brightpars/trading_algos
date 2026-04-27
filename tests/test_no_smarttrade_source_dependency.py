from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_SNIPPETS = (
    ' / "smarttrade"',
    '"smarttrade"',
    "'smarttrade'",
    "from config.service import",
    "from utils_shared",
    "import utils_shared",
    "trading_servers.engines_control_runtime",
)

SCANNED_FILES = (
    REPO_ROOT / "src" / "trading_algos_dashboard" / "service_runtime.py",
    REPO_ROOT
    / "src"
    / "trading_algos_dashboard"
    / "services"
    / "server_control_service.py",
)


def test_dashboard_runtime_contains_no_sibling_smarttrade_source_dependency() -> None:
    for path in SCANNED_FILES:
        content = path.read_text(encoding="utf-8")
        for forbidden in FORBIDDEN_SNIPPETS:
            assert forbidden not in content, (
                f"Forbidden dependency marker {forbidden!r} found in {path}"
            )
