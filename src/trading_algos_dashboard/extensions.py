from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass
class MongoExtension:
    client: Any = None
    db: Any = None


mongo = MongoExtension()


def load_form_state(raw_cookie: str | None) -> dict[str, str]:
    if not raw_cookie:
        return {}
    try:
        payload = json.loads(raw_cookie)
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    return {
        str(key): value
        for key, value in payload.items()
        if isinstance(key, str) and isinstance(value, str)
    }


def persist_form_state(
    response: Any,
    *,
    cookie_name: str,
    form_data: dict[str, str],
) -> None:
    response.set_cookie(
        cookie_name, json.dumps(form_data), httponly=False, samesite="Lax"
    )


def clear_form_state(response: Any, *, cookie_name: str) -> None:
    response.delete_cookie(cookie_name)
