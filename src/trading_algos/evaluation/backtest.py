from __future__ import annotations

from statistics import median

from trading_algos.alertgen.contracts.outputs import AlertAlgorithmOutput
from trading_algos.evaluation.models import EvaluationResult


def _safe_float(value: object) -> float:
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, int | float):
        return float(value)
    return 0.0


def evaluate_baseline_backtest(output: AlertAlgorithmOutput) -> EvaluationResult:
    close_series = [
        _safe_float(value) for value in output.derived_series.get("close", [])
    ]
    if len(close_series) < 2:
        return EvaluationResult(
            evaluator_id="baseline_backtest_v1",
            evaluator_version="1.0",
            metric_group="trading_backtest",
            applies=False,
            metrics={},
            warnings=("Not enough close prices for baseline backtest evaluation.",),
        )

    per_bar_returns: list[float] = []
    trade_returns: list[float] = []
    equity_curve: list[float] = [1.0]
    in_position = False
    entry_price = 0.0
    exposure_bars = 0
    turnover_events = 0

    for index, point in enumerate(output.points[:-1]):
        next_price = close_series[index + 1]
        current_price = close_series[index]
        if current_price <= 0:
            per_bar_returns.append(0.0)
            equity_curve.append(equity_curve[-1])
            continue

        if point.signal_label == "buy" and not in_position:
            in_position = True
            entry_price = next_price
            turnover_events += 1
        elif point.signal_label == "sell" and in_position:
            trade_return = (next_price / entry_price) - 1.0 if entry_price > 0 else 0.0
            trade_returns.append(trade_return)
            in_position = False
            entry_price = 0.0
            turnover_events += 1

        bar_return = 0.0
        if in_position:
            bar_return = (next_price / current_price) - 1.0
            exposure_bars += 1
        per_bar_returns.append(bar_return)
        equity_curve.append(equity_curve[-1] * (1.0 + bar_return))

    if in_position and entry_price > 0:
        final_return = (close_series[-1] / entry_price) - 1.0
        trade_returns.append(final_return)

    running_peak = equity_curve[0]
    drawdowns: list[float] = []
    for value in equity_curve:
        running_peak = max(running_peak, value)
        if running_peak <= 0:
            drawdowns.append(0.0)
        else:
            drawdowns.append((value / running_peak) - 1.0)

    win_count = sum(1 for value in trade_returns if value > 0)
    loss_count = sum(1 for value in trade_returns if value < 0)
    gross_profit = sum(value for value in trade_returns if value > 0)
    gross_loss = abs(sum(value for value in trade_returns if value < 0))
    total_bars = max(len(close_series) - 1, 1)
    cumulative_return = equity_curve[-1] - 1.0
    max_drawdown = min(drawdowns) if drawdowns else 0.0
    metrics = {
        "assumptions": {
            "entry_rule": "enter next bar close after buy signal",
            "exit_rule": "exit next bar close after sell signal or final bar",
            "slippage": 0.0,
            "fees": 0.0,
        },
        "trade_count": len(trade_returns),
        "win_rate": (win_count / len(trade_returns)) if trade_returns else 0.0,
        "loss_rate": (loss_count / len(trade_returns)) if trade_returns else 0.0,
        "average_return_per_trade": (
            sum(trade_returns) / len(trade_returns) if trade_returns else 0.0
        ),
        "median_return_per_trade": median(trade_returns) if trade_returns else 0.0,
        "cumulative_return": cumulative_return,
        "max_drawdown": max_drawdown,
        "average_holding_duration_bars": (
            exposure_bars / len(trade_returns) if trade_returns else 0.0
        ),
        "exposure_ratio": exposure_bars / total_bars,
        "turnover_estimate": turnover_events / total_bars,
        "profit_factor": (gross_profit / gross_loss) if gross_loss > 0 else None,
        "recovery_factor": (
            cumulative_return / abs(max_drawdown)
            if max_drawdown not in (0, None)
            else None
        ),
        "equity_curve": equity_curve,
        "drawdown_curve": drawdowns,
        "trade_returns": trade_returns,
    }
    return EvaluationResult(
        evaluator_id="baseline_backtest_v1",
        evaluator_version="1.0",
        metric_group="trading_backtest",
        applies=True,
        metrics=metrics,
        warnings=(),
        applicability_status="applicable",
        notes=("Uses baseline next-bar-close entry and exit assumptions.",),
    )
