from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class OptionContract:
    symbol: str
    option_type: str
    strike: float
    expiry_days: int
    implied_vol: float
    delta: float
    gamma: float
    vega: float
    moneyness: float


@dataclass(frozen=True)
class OptionChainSnapshot:
    timestamp: str
    underlying_symbol: str
    underlying_price: float
    contracts: tuple[OptionContract, ...]
    realized_vol: float
    expected_move: float
    priced_move: float
    index_implied_vol: float
    constituent_implied_vol: float
    short_term_implied_vol: float
    long_term_implied_vol: float
    put_skew_implied_vol: float
    call_skew_implied_vol: float


def query_contracts(
    snapshot: OptionChainSnapshot,
    *,
    option_type: str | None = None,
    expiry_days: int | None = None,
    max_abs_moneyness: float | None = None,
) -> tuple[OptionContract, ...]:
    contracts = snapshot.contracts
    if option_type is not None:
        contracts = tuple(
            contract for contract in contracts if contract.option_type == option_type
        )
    if expiry_days is not None:
        contracts = tuple(
            contract for contract in contracts if contract.expiry_days == expiry_days
        )
    if max_abs_moneyness is not None:
        contracts = tuple(
            contract
            for contract in contracts
            if abs(contract.moneyness) <= max_abs_moneyness
        )
    return tuple(
        sorted(
            contracts,
            key=lambda contract: (
                contract.expiry_days,
                abs(contract.moneyness),
                contract.strike,
                contract.symbol,
            ),
        )
    )


def nearest_expiry(
    snapshot: OptionChainSnapshot, *, option_type: str | None = None
) -> int | None:
    contracts = query_contracts(snapshot, option_type=option_type)
    if not contracts:
        return None
    return min(contract.expiry_days for contract in contracts)


def _safe_moneyness(*, strike: float, underlying_price: float) -> float:
    if underlying_price == 0.0:
        return 0.0
    return (strike / underlying_price) - 1.0


def _contract(
    *,
    underlying_symbol: str,
    option_type: str,
    strike: float,
    expiry_days: int,
    implied_vol: float,
    delta: float,
    gamma: float,
    vega: float,
    underlying_price: float,
    suffix: str,
) -> OptionContract:
    return OptionContract(
        symbol=f"{underlying_symbol}_{suffix}",
        option_type=option_type,
        strike=strike,
        expiry_days=expiry_days,
        implied_vol=implied_vol,
        delta=delta,
        gamma=gamma,
        vega=vega,
        moneyness=_safe_moneyness(strike=strike, underlying_price=underlying_price),
    )


def _float_value(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = row.get(key, default)
    return float(value) if isinstance(value, int | float | str) else default


def _int_value(row: dict[str, Any], key: str, default: int = 0) -> int:
    value = row.get(key, default)
    return int(value) if isinstance(value, int | float | str) else default


def option_chain_from_row(row: dict[str, Any]) -> OptionChainSnapshot:
    underlying_symbol = str(row.get("symbol", "UNDERLYING"))
    underlying_price = _float_value(
        row, "underlying_price", _float_value(row, "Close", 0.0)
    )
    atm_strike = _float_value(row, "atm_strike", underlying_price)
    expiry_days = _int_value(row, "expiry_days", 30)
    short_expiry_days = _int_value(row, "short_expiry_days", max(7, expiry_days // 2))
    long_expiry_days = _int_value(
        row, "long_expiry_days", max(expiry_days + 30, short_expiry_days + 7)
    )

    call_iv = _float_value(row, "atm_call_iv", _float_value(row, "implied_vol", 0.0))
    put_iv = _float_value(row, "atm_put_iv", _float_value(row, "implied_vol", 0.0))
    index_iv = _float_value(row, "index_iv", _float_value(row, "implied_vol"))
    constituent_iv = _float_value(
        row,
        "constituent_iv_avg",
        _float_value(row, "implied_vol"),
    )
    short_term_iv = _float_value(row, "short_term_iv", _float_value(row, "implied_vol"))
    long_term_iv = _float_value(row, "long_term_iv", _float_value(row, "implied_vol"))
    put_skew_iv = _float_value(row, "put_25d_iv", put_iv)
    call_skew_iv = _float_value(row, "call_25d_iv", call_iv)
    call_delta = _float_value(row, "call_delta", 0.5)
    put_delta = _float_value(row, "put_delta", -0.5)
    call_gamma = _float_value(row, "call_gamma", _float_value(row, "gamma", 0.0) / 2.0)
    put_gamma = _float_value(row, "put_gamma", _float_value(row, "gamma", 0.0) / 2.0)
    call_vega = _float_value(row, "call_vega", _float_value(row, "vega", 0.0) / 2.0)
    put_vega = _float_value(row, "put_vega", _float_value(row, "vega", 0.0) / 2.0)
    put_25d_delta = _float_value(row, "put_25d_delta", -0.25)
    call_25d_delta = _float_value(row, "call_25d_delta", 0.25)
    put_25d_gamma = _float_value(row, "put_25d_gamma", put_gamma)
    call_25d_gamma = _float_value(row, "call_25d_gamma", call_gamma)
    put_25d_vega = _float_value(row, "put_25d_vega", put_vega)
    call_25d_vega = _float_value(row, "call_25d_vega", call_vega)
    put_25d_strike = _float_value(row, "put_25d_strike", atm_strike * 0.95)
    call_25d_strike = _float_value(row, "call_25d_strike", atm_strike * 1.05)

    contracts = (
        _contract(
            underlying_symbol=underlying_symbol,
            option_type="call",
            strike=atm_strike,
            expiry_days=expiry_days,
            implied_vol=call_iv,
            delta=call_delta,
            gamma=call_gamma,
            vega=call_vega,
            underlying_price=underlying_price,
            suffix="CALL_ATM",
        ),
        _contract(
            underlying_symbol=underlying_symbol,
            option_type="put",
            strike=atm_strike,
            expiry_days=expiry_days,
            implied_vol=put_iv,
            delta=put_delta,
            gamma=put_gamma,
            vega=put_vega,
            underlying_price=underlying_price,
            suffix="PUT_ATM",
        ),
        _contract(
            underlying_symbol=underlying_symbol,
            option_type="put",
            strike=put_25d_strike,
            expiry_days=expiry_days,
            implied_vol=put_skew_iv,
            delta=put_25d_delta,
            gamma=put_25d_gamma,
            vega=put_25d_vega,
            underlying_price=underlying_price,
            suffix="PUT_25D",
        ),
        _contract(
            underlying_symbol=underlying_symbol,
            option_type="call",
            strike=call_25d_strike,
            expiry_days=expiry_days,
            implied_vol=call_skew_iv,
            delta=call_25d_delta,
            gamma=call_25d_gamma,
            vega=call_25d_vega,
            underlying_price=underlying_price,
            suffix="CALL_25D",
        ),
        _contract(
            underlying_symbol=underlying_symbol,
            option_type="call",
            strike=atm_strike,
            expiry_days=short_expiry_days,
            implied_vol=short_term_iv,
            delta=call_delta,
            gamma=call_gamma,
            vega=call_vega,
            underlying_price=underlying_price,
            suffix="CALL_SHORT",
        ),
        _contract(
            underlying_symbol=underlying_symbol,
            option_type="call",
            strike=atm_strike,
            expiry_days=long_expiry_days,
            implied_vol=long_term_iv,
            delta=call_delta,
            gamma=call_gamma,
            vega=call_vega,
            underlying_price=underlying_price,
            suffix="CALL_LONG",
        ),
        _contract(
            underlying_symbol=underlying_symbol,
            option_type="call",
            strike=atm_strike,
            expiry_days=expiry_days,
            implied_vol=index_iv,
            delta=call_delta,
            gamma=call_gamma,
            vega=call_vega,
            underlying_price=underlying_price,
            suffix="INDEX_PROXY",
        ),
        _contract(
            underlying_symbol=underlying_symbol,
            option_type="call",
            strike=atm_strike,
            expiry_days=expiry_days,
            implied_vol=constituent_iv,
            delta=call_delta,
            gamma=call_gamma,
            vega=call_vega,
            underlying_price=underlying_price,
            suffix="CONSTITUENT_PROXY",
        ),
    )

    return OptionChainSnapshot(
        timestamp=str(row.get("ts", "")),
        underlying_symbol=underlying_symbol,
        underlying_price=underlying_price,
        contracts=contracts,
        realized_vol=_float_value(row, "realized_vol"),
        expected_move=_float_value(row, "expected_move"),
        priced_move=_float_value(row, "priced_move"),
        index_implied_vol=index_iv,
        constituent_implied_vol=constituent_iv,
        short_term_implied_vol=short_term_iv,
        long_term_implied_vol=long_term_iv,
        put_skew_implied_vol=put_skew_iv,
        call_skew_implied_vol=call_skew_iv,
    )
