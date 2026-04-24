from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence


def _clamp_unit_interval(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _clamp_signed_unit(value: float) -> float:
    return max(-1.0, min(1.0, float(value)))


def _coerce_float(value: Any, *, label: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"rl_environment: invalid_float; label={label}") from exc


def _normalize_weight_map(
    weights: Mapping[str, float], *, gross_limit: float
) -> dict[str, float]:
    cleaned = {
        str(symbol): float(weight)
        for symbol, weight in weights.items()
        if float(weight) != 0.0
    }
    gross = sum(abs(weight) for weight in cleaned.values())
    if gross <= 0.0:
        return {}
    scale = min(1.0, float(gross_limit) / gross)
    return {symbol: weight * scale for symbol, weight in cleaned.items()}


@dataclass(frozen=True)
class RLEnvironmentRow:
    timestamp: str
    state: dict[str, float]
    action_scores: dict[str, float]
    reward: float
    candidate_weights: dict[str, float]
    policy_confidence: float
    metadata: dict[str, Any]


@dataclass(frozen=True)
class RLParsedEnvironment:
    rows: tuple[RLEnvironmentRow, ...]
    action_keys: tuple[str, ...]
    state_keys: tuple[str, ...]


@dataclass(frozen=True)
class RLActionDecision:
    action_key: str
    weights: dict[str, float]
    score: float
    confidence: float
    diagnostics: dict[str, Any]


def parse_rl_environment_rows(
    raw_rows: Sequence[Mapping[str, Any]],
) -> RLParsedEnvironment:
    rows: list[RLEnvironmentRow] = []
    action_keys: set[str] = set()
    state_keys: set[str] = set()
    for index, raw_row in enumerate(raw_rows):
        timestamp = str(raw_row.get("timestamp", raw_row.get("ts", ""))).strip()
        if not timestamp:
            raise ValueError(f"rl_environment: missing_timestamp; row_index={index}")
        raw_state = raw_row.get("state", {})
        if not isinstance(raw_state, Mapping):
            raise ValueError(f"rl_environment: invalid_state; row_index={index}")
        state = {
            str(key): _coerce_float(value, label=f"state[{key}]")
            for key, value in raw_state.items()
        }
        raw_actions = raw_row.get("action_scores", raw_row.get("policy_actions", {}))
        if not isinstance(raw_actions, Mapping) or not raw_actions:
            raise ValueError(
                f"rl_environment: invalid_action_scores; row_index={index}"
            )
        action_scores = {
            str(key): _clamp_signed_unit(
                _coerce_float(value, label=f"action_scores[{key}]")
            )
            for key, value in raw_actions.items()
        }
        raw_candidate_weights = raw_row.get("candidate_weights", {})
        if not isinstance(raw_candidate_weights, Mapping):
            raise ValueError(
                f"rl_environment: invalid_candidate_weights; row_index={index}"
            )
        candidate_weights: dict[str, float] = {}
        for action_key, raw_weight_map in raw_candidate_weights.items():
            if not isinstance(raw_weight_map, Mapping):
                raise ValueError(
                    "rl_environment: invalid_candidate_weight_map; "
                    f"row_index={index} action_key={action_key}"
                )
            normalized = _normalize_weight_map(
                {
                    str(symbol): _coerce_float(
                        value,
                        label=f"candidate_weights[{action_key}][{symbol}]",
                    )
                    for symbol, value in raw_weight_map.items()
                },
                gross_limit=1.0,
            )
            for symbol, weight in normalized.items():
                candidate_weights[f"{action_key}:{symbol}"] = weight
        reward = _coerce_float(raw_row.get("reward", 0.0), label="reward")
        policy_confidence = _clamp_unit_interval(
            _coerce_float(
                raw_row.get("policy_confidence", raw_row.get("confidence", 0.0)),
                label="policy_confidence",
            )
        )
        metadata = (
            dict(raw_row.get("metadata", {}))
            if isinstance(raw_row.get("metadata"), Mapping)
            else {}
        )
        rows.append(
            RLEnvironmentRow(
                timestamp=timestamp,
                state=state,
                action_scores=action_scores,
                reward=reward,
                candidate_weights=candidate_weights,
                policy_confidence=policy_confidence,
                metadata=metadata,
            )
        )
        action_keys.update(action_scores)
        state_keys.update(state)
    return RLParsedEnvironment(
        rows=tuple(rows),
        action_keys=tuple(sorted(action_keys)),
        state_keys=tuple(sorted(state_keys)),
    )


def choose_action(
    row: RLEnvironmentRow,
    *,
    allowed_actions: Sequence[str] | None = None,
    action_overrides: Mapping[str, float] | None = None,
) -> tuple[str, float]:
    candidate_scores = dict(row.action_scores)
    if action_overrides:
        candidate_scores.update(
            {
                str(key): _clamp_signed_unit(
                    _coerce_float(value, label=f"action_override[{key}]")
                )
                for key, value in action_overrides.items()
            }
        )
    if allowed_actions is not None:
        filtered = {
            key: candidate_scores[key]
            for key in allowed_actions
            if key in candidate_scores
        }
        if filtered:
            candidate_scores = filtered
    action_key, score = max(
        candidate_scores.items(),
        key=lambda item: (item[1], item[0]),
    )
    return action_key, float(score)
