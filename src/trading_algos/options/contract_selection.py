from __future__ import annotations

from trading_algos.options.chain import (
    OptionChainSnapshot,
    OptionContract,
    nearest_expiry,
    query_contracts,
)


def _sorted_contracts(
    snapshot: OptionChainSnapshot,
    *,
    option_type: str | None = None,
) -> tuple[OptionContract, ...]:
    return tuple(
        sorted(
            query_contracts(snapshot, option_type=option_type),
            key=lambda contract: (
                abs(contract.moneyness),
                contract.expiry_days,
                contract.strike,
                contract.symbol,
            ),
        )
    )


def _contract_by_suffix(
    snapshot: OptionChainSnapshot,
    *,
    suffix: str,
) -> OptionContract | None:
    for contract in snapshot.contracts:
        if contract.symbol.endswith(suffix):
            return contract
    return None


def select_atm_straddle(snapshot: OptionChainSnapshot) -> tuple[OptionContract, ...]:
    call = _contract_by_suffix(snapshot, suffix="CALL_ATM")
    put = _contract_by_suffix(snapshot, suffix="PUT_ATM")
    selected = tuple(contract for contract in (call, put) if contract is not None)
    if selected:
        return selected
    return _sorted_contracts(snapshot)[:2]


def select_dispersion_contracts(
    snapshot: OptionChainSnapshot,
) -> tuple[OptionContract, ...]:
    index_proxy = _contract_by_suffix(snapshot, suffix="INDEX_PROXY")
    constituent_proxy = _contract_by_suffix(snapshot, suffix="CONSTITUENT_PROXY")
    selected = tuple(
        contract
        for contract in (index_proxy, constituent_proxy)
        if contract is not None
    )
    if selected:
        return selected
    return select_atm_straddle(snapshot)


def select_skew_contracts(snapshot: OptionChainSnapshot) -> tuple[OptionContract, ...]:
    put_25d = _contract_by_suffix(snapshot, suffix="PUT_25D")
    call_25d = _contract_by_suffix(snapshot, suffix="CALL_25D")
    selected = tuple(
        contract for contract in (put_25d, call_25d) if contract is not None
    )
    if selected:
        return selected
    puts = _sorted_contracts(snapshot, option_type="put")[:1]
    calls = _sorted_contracts(snapshot, option_type="call")[:1]
    return puts + calls


def select_term_structure_contracts(
    snapshot: OptionChainSnapshot,
) -> tuple[OptionContract, ...]:
    short_contract = _contract_by_suffix(snapshot, suffix="CALL_SHORT")
    long_contract = _contract_by_suffix(snapshot, suffix="CALL_LONG")
    selected = tuple(
        contract for contract in (short_contract, long_contract) if contract is not None
    )
    if selected:
        return selected
    nearest_call_expiry = nearest_expiry(snapshot, option_type="call")
    calls = tuple(
        sorted(
            query_contracts(snapshot, option_type="call"),
            key=lambda contract: (
                contract.expiry_days != nearest_call_expiry,
                contract.expiry_days,
                abs(contract.moneyness),
            ),
        )
    )
    if len(calls) >= 2:
        return (calls[0], calls[-1])
    return select_atm_straddle(snapshot)
