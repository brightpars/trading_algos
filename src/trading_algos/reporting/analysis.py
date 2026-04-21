from __future__ import annotations

from trading_algos.evaluation.models import EvaluationResult
from trading_algos.reporting.charts import metric
from trading_algos.reporting.models import AnalysisBlock


def _as_int(value: object) -> int:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return 0


def build_analysis_blocks(
    *,
    signal_summary: dict[str, object],
    evaluation_results: list[EvaluationResult],
) -> list[AnalysisBlock]:
    total_rows = _as_int(signal_summary.get("total_rows", 0) or 0)
    signal_count = _as_int(signal_summary.get("buy_count", 0) or 0) + _as_int(
        signal_summary.get("sell_count", 0) or 0
    )
    activity_ratio = (signal_count / total_rows) if total_rows else 0.0
    cumulative_return = metric(
        evaluation_results, "trading_backtest", "cumulative_return"
    )
    max_drawdown = metric(evaluation_results, "trading_backtest", "max_drawdown")
    buy_precision = metric(evaluation_results, "signal_quality", "buy_precision")
    sell_precision = metric(evaluation_results, "signal_quality", "sell_precision")
    trade_count = metric(evaluation_results, "trading_backtest", "trade_count")
    robustness = metric(evaluation_results, "robustness", "rolling_window_count")
    warnings = [warning for result in evaluation_results for warning in result.warnings]
    return [
        AnalysisBlock(
            block_id="overall_behavior",
            title="Overall behavior summary",
            body=(
                f"Strategy activity_ratio={activity_ratio:.3f} signal_count={signal_count} total_rows={total_rows}; "
                "activity is classified from normalized alert outputs."
            ),
        ),
        AnalysisBlock(
            block_id="performance_summary",
            title="Performance summary",
            body=(
                f"Performance cumulative_return={cumulative_return} max_drawdown={max_drawdown}; "
                "results use the shared baseline backtest assumption set."
            ),
        ),
        AnalysisBlock(
            block_id="signal_quality_summary",
            title="Signal quality summary",
            body=(
                f"Signal quality buy_precision={buy_precision} sell_precision={sell_precision} trade_count={trade_count}; "
                "use these values to assess overtrading or undertrading behavior."
            ),
        ),
        AnalysisBlock(
            block_id="risk_summary",
            title="Risk summary",
            body=(
                f"Risk view max_drawdown={max_drawdown} rolling_window_count={robustness}; "
                "concentration and regime-specific risk remain heuristic in this phase."
            ),
        ),
        AnalysisBlock(
            block_id="limitations",
            title="Limitations / caveats",
            body=(
                "; ".join(warnings)
                if warnings
                else "This report currently supports signal-quality, baseline backtest, robustness summary, and extension hooks for specialized families."
            ),
            severity="warning",
        ),
    ]
