from __future__ import annotations

from typing import Any


def normalize_interactive_payloads(
    payloads: list[tuple[Any, str]],
) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for payload, description in payloads:
        normalized.append({"payload": payload, "description": description})
    return normalized
