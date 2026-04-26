from __future__ import annotations

from typing import Any

from trading_algos.contracts.multi_leg_output import MultiLegOutput


def build_multi_leg_report_payload(output: MultiLegOutput) -> dict[str, Any]:
    latest = output.rebalances[-1] if output.rebalances else None
    return {
        "algorithm_key": output.algorithm_key,
        "metadata": dict(output.metadata),
        "rebalance_count": len(output.rebalances),
        "latest_spread_value": latest.spread_value if latest is not None else None,
        "latest_hedge_ratio": latest.hedge_ratio if latest is not None else None,
        "latest_gross_exposure": latest.gross_exposure if latest is not None else None,
        "latest_net_exposure": latest.net_exposure if latest is not None else None,
        "latest_legs": [leg.to_dict() for leg in latest.legs]
        if latest is not None
        else [],
        "latest_diagnostics": dict(latest.diagnostics) if latest is not None else {},
    }
