from __future__ import annotations

from dataclasses import dataclass

from trading_algos.options.chain import OptionContract


@dataclass(frozen=True)
class GreekExposure:
    net_delta: float
    net_gamma: float
    net_vega: float
    average_implied_vol: float
    delta_abs: float
    gamma_abs: float
    vega_abs: float
    contract_count: int


@dataclass(frozen=True)
class HedgePlan:
    target_delta: float
    current_delta: float
    hedge_units: float
    rebalance_required: bool
    band: float


def compute_greek_exposure(contracts: tuple[OptionContract, ...]) -> GreekExposure:
    if not contracts:
        return GreekExposure(
            net_delta=0.0,
            net_gamma=0.0,
            net_vega=0.0,
            average_implied_vol=0.0,
            delta_abs=0.0,
            gamma_abs=0.0,
            vega_abs=0.0,
            contract_count=0,
        )
    net_delta = sum(contract.delta for contract in contracts)
    net_gamma = sum(contract.gamma for contract in contracts)
    net_vega = sum(contract.vega for contract in contracts)
    average_implied_vol = sum(contract.implied_vol for contract in contracts) / len(
        contracts
    )
    delta_abs = sum(abs(contract.delta) for contract in contracts)
    gamma_abs = sum(abs(contract.gamma) for contract in contracts)
    vega_abs = sum(abs(contract.vega) for contract in contracts)
    return GreekExposure(
        net_delta=net_delta,
        net_gamma=net_gamma,
        net_vega=net_vega,
        average_implied_vol=average_implied_vol,
        delta_abs=delta_abs,
        gamma_abs=gamma_abs,
        vega_abs=vega_abs,
        contract_count=len(contracts),
    )


def hedge_units_for_delta(net_delta: float) -> float:
    return -net_delta


def hedge_rebalance_required(*, net_delta: float, band: float) -> bool:
    return abs(net_delta) > max(0.0, band)


def build_delta_hedge_plan(
    *,
    net_delta: float,
    band: float,
    target_delta: float = 0.0,
) -> HedgePlan:
    hedge_units = target_delta - net_delta
    return HedgePlan(
        target_delta=target_delta,
        current_delta=net_delta,
        hedge_units=hedge_units,
        rebalance_required=abs(net_delta - target_delta) > max(0.0, band),
        band=max(0.0, band),
    )
