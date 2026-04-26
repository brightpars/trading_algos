from __future__ import annotations

from dataclasses import dataclass

from trading_algos.options.chain import OptionChainSnapshot


@dataclass(frozen=True)
class SurfaceMetrics:
    index_implied_vol: float
    constituent_implied_vol: float
    dispersion_gap: float
    put_call_skew: float
    term_structure_slope: float
    expected_move_gap: float
    iv_rv_gap: float


def surface_metrics_from_snapshot(snapshot: OptionChainSnapshot) -> dict[str, float]:
    return {
        "index_implied_vol": snapshot.index_implied_vol,
        "constituent_implied_vol": snapshot.constituent_implied_vol,
        "dispersion_gap": snapshot.constituent_implied_vol - snapshot.index_implied_vol,
        "put_call_skew": snapshot.put_skew_implied_vol - snapshot.call_skew_implied_vol,
        "term_structure_slope": snapshot.long_term_implied_vol
        - snapshot.short_term_implied_vol,
        "expected_move_gap": snapshot.expected_move - snapshot.priced_move,
        "iv_rv_gap": snapshot.index_implied_vol - snapshot.realized_vol,
    }


def surface_metrics_object_from_snapshot(
    snapshot: OptionChainSnapshot,
) -> SurfaceMetrics:
    metrics = surface_metrics_from_snapshot(snapshot)
    return SurfaceMetrics(**metrics)
