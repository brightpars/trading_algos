from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from trading_algos.options import (
    compute_greek_exposure,
    hedge_rebalance_required,
    hedge_units_for_delta,
    option_chain_from_row,
    select_atm_straddle,
    select_dispersion_contracts,
    select_skew_contracts,
    select_term_structure_contracts,
    surface_metrics_from_snapshot,
)


@dataclass(frozen=True)
class OptionSurfaceDecisionMetrics:
    timestamp: str
    underlying_symbol: str
    selected_contracts: tuple[str, ...]
    contract_count: int
    average_implied_vol: float
    realized_vol: float
    iv_rv_gap: float
    net_delta: float
    delta_abs: float
    hedge_units: float
    hedge_rebalance_required: bool
    net_gamma: float
    gamma_abs: float
    net_vega: float
    vega_abs: float
    dispersion_gap: float
    put_call_skew: float
    term_structure_slope: float
    expected_move_gap: float


def build_option_surface_metrics(
    row: dict[str, Any], *, selection_mode: str, hedge_band: float = 0.0
) -> OptionSurfaceDecisionMetrics:
    snapshot = option_chain_from_row(row)
    if selection_mode == "dispersion":
        contracts = select_dispersion_contracts(snapshot)
    elif selection_mode == "skew":
        contracts = select_skew_contracts(snapshot)
    elif selection_mode == "term":
        contracts = select_term_structure_contracts(snapshot)
    else:
        contracts = select_atm_straddle(snapshot)
    greeks = compute_greek_exposure(contracts)
    surface = surface_metrics_from_snapshot(snapshot)
    return OptionSurfaceDecisionMetrics(
        timestamp=snapshot.timestamp,
        underlying_symbol=snapshot.underlying_symbol,
        selected_contracts=tuple(contract.symbol for contract in contracts),
        contract_count=greeks.contract_count,
        average_implied_vol=greeks.average_implied_vol,
        realized_vol=snapshot.realized_vol,
        iv_rv_gap=surface["iv_rv_gap"],
        net_delta=greeks.net_delta,
        delta_abs=greeks.delta_abs,
        hedge_units=hedge_units_for_delta(greeks.net_delta),
        hedge_rebalance_required=hedge_rebalance_required(
            net_delta=greeks.net_delta,
            band=hedge_band,
        ),
        net_gamma=greeks.net_gamma,
        gamma_abs=greeks.gamma_abs,
        net_vega=greeks.net_vega,
        vega_abs=greeks.vega_abs,
        dispersion_gap=surface["dispersion_gap"],
        put_call_skew=surface["put_call_skew"],
        term_structure_slope=surface["term_structure_slope"],
        expected_move_gap=surface["expected_move_gap"],
    )
