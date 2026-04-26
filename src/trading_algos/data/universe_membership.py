from __future__ import annotations

from trading_algos.data.panel_dataset import MultiAssetPanel


def universe_membership_for_rebalance(
    panel: MultiAssetPanel, *, rebalance_timestamp: str
) -> tuple[str, ...]:
    return panel.universe_on(rebalance_timestamp)
