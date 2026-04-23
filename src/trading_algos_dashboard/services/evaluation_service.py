from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from trading_algos_dashboard.services.data_source_service import parse_date_range


class EvaluationService:
    def __init__(self, *, experiment_repository: Any, result_repository: Any):
        self.experiment_repository = experiment_repository
        self.result_repository = result_repository

    def find_comparable_runs(
        self,
        *,
        symbol: str,
        start_date: str,
        start_time: str,
        end_date: str,
        end_time: str,
        primary_metric: str = "cumulative_return",
    ) -> dict[str, Any]:
        start, end = parse_date_range(start_date, start_time, end_date, end_time)
        experiments = self.experiment_repository.list_completed_experiments_for_scope(
            symbol=symbol,
            start=start,
            end=end,
        )
        experiment_ids = [str(item.get("experiment_id", "")) for item in experiments]
        results = self.result_repository.list_results_for_experiments(experiment_ids)

        results_by_experiment: dict[str, list[dict[str, Any]]] = {}
        for result in results:
            experiment_id = str(result.get("experiment_id", ""))
            results_by_experiment.setdefault(experiment_id, []).append(result)

        rows: list[dict[str, Any]] = []
        for experiment in experiments:
            experiment_id = str(experiment.get("experiment_id", ""))
            for result in results_by_experiment.get(experiment_id, []):
                rows.append(
                    self._extract_comparison_row(experiment=experiment, result=result)
                )

        ranked_rows = self._rank_rows(rows=rows, primary_metric=primary_metric)
        warnings = self._build_warnings(experiments=experiments, rows=ranked_rows)

        return {
            "cohort": {
                "cohort_key": self.build_cohort_key(
                    symbol=symbol,
                    start=start,
                    end=end,
                ),
                "symbol": symbol,
                "start": start,
                "end": end,
                "completed_run_count": len(experiments),
                "result_count": len(ranked_rows),
                "candle_counts": sorted(
                    {
                        int(item["candle_count"])
                        for item in experiments
                        if isinstance(item.get("candle_count"), int)
                    }
                ),
                "dataset_endpoints": sorted(
                    {
                        str((item.get("dataset_source") or {}).get("endpoint", ""))
                        for item in experiments
                        if isinstance(item.get("dataset_source"), Mapping)
                        and (item.get("dataset_source") or {}).get("endpoint")
                    }
                ),
            },
            "filters": {
                "symbol": symbol,
                "start_date": start_date,
                "start_time": start_time,
                "end_date": end_date,
                "end_time": end_time,
                "primary_metric": primary_metric,
            },
            "warnings": warnings,
            "rows": ranked_rows,
        }

    @staticmethod
    def build_cohort_key(*, symbol: str, start: datetime, end: datetime) -> str:
        return (
            f"{symbol}__{start.astimezone(timezone.utc).isoformat()}__"
            f"{end.astimezone(timezone.utc).isoformat()}"
        )

    def _extract_comparison_row(
        self, *, experiment: dict[str, Any], result: dict[str, Any]
    ) -> dict[str, Any]:
        report = result.get("report")
        metrics = self._extract_metrics(report=report, result=result)
        algorithm_summary = (
            report.get("algorithm_summary") if isinstance(report, dict) else {}
        )
        if not isinstance(algorithm_summary, dict):
            algorithm_summary = {}
        return {
            "experiment_id": str(experiment.get("experiment_id", "")),
            "algorithm_key": str(
                result.get("alg_key")
                or algorithm_summary.get("algorithm_key")
                or result.get("config_key")
                or ""
            ),
            "algorithm_name": str(
                algorithm_summary.get("algorithm_name")
                or result.get("alg_name")
                or result.get("config_name")
                or "Unknown"
            ),
            "family": str(algorithm_summary.get("family") or ""),
            "parameters": result.get("alg_param")
            or algorithm_summary.get("parameter_values")
            or {},
            "status": str(experiment.get("status", "")),
            "created_at": experiment.get("created_at"),
            "finished_at": experiment.get("finished_at"),
            "duration_seconds": experiment.get("duration_seconds"),
            "signal_count": metrics.get("signal_count"),
            "trade_count": metrics.get("trade_count"),
            "metrics": metrics,
            "detail_url": f"/experiments/{experiment.get('experiment_id', '')}",
            "metric_notes": [] if isinstance(report, dict) else ["Report unavailable"],
        }

    def _extract_metrics(
        self, *, report: object, result: dict[str, Any]
    ) -> dict[str, float | int | None]:
        metrics: dict[str, float | int | None] = {
            "cumulative_return": None,
            "max_drawdown": None,
            "win_rate": None,
            "signal_count": None,
            "trade_count": None,
            "sharpe_ratio": None,
        }
        if isinstance(report, dict):
            evaluation_summary = report.get("evaluation_summary")
            if isinstance(evaluation_summary, dict):
                headline_metrics = evaluation_summary.get("headline_metrics")
                if isinstance(headline_metrics, dict):
                    for key in metrics:
                        if key in headline_metrics:
                            metrics[key] = self._coerce_metric_value(
                                headline_metrics.get(key)
                            )
            summary_cards = report.get("summary_cards")
            if isinstance(summary_cards, list):
                for card in summary_cards:
                    if not isinstance(card, dict):
                        continue
                    metric_key = str(
                        card.get("metric_key")
                        or self._label_to_metric_key(card.get("label"))
                    )
                    if metric_key in metrics and metrics[metric_key] is None:
                        metrics[metric_key] = self._coerce_metric_value(
                            card.get("value")
                        )

        signal_summary = result.get("signal_summary")
        if isinstance(signal_summary, dict):
            total_rows = signal_summary.get("total_rows")
            buy_count = signal_summary.get("buy_count")
            sell_count = signal_summary.get("sell_count")
            if metrics["signal_count"] is None and isinstance(total_rows, int):
                metrics["signal_count"] = total_rows
            if (
                metrics["trade_count"] is None
                and isinstance(buy_count, int)
                and isinstance(sell_count, int)
            ):
                metrics["trade_count"] = buy_count + sell_count
        return metrics

    @staticmethod
    def _coerce_metric_value(value: object) -> float | int | None:
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float)):
            return value
        if isinstance(value, str):
            normalized = value.strip().replace("%", "")
            if not normalized:
                return None
            try:
                return float(normalized)
            except ValueError:
                return None
        return None

    @staticmethod
    def _label_to_metric_key(label: object) -> str:
        if not isinstance(label, str):
            return ""
        return label.strip().lower().replace(" ", "_")

    @staticmethod
    def _rank_rows(
        *, rows: list[dict[str, Any]], primary_metric: str
    ) -> list[dict[str, Any]]:
        def _sort_key(row: dict[str, Any]) -> tuple[int, float, str]:
            raw_value = (row.get("metrics") or {}).get(primary_metric)
            if isinstance(raw_value, (int, float)):
                return 0, -float(raw_value), str(row.get("algorithm_name", ""))
            return 1, 0.0, str(row.get("algorithm_name", ""))

        ranked = sorted(rows, key=_sort_key)
        for index, row in enumerate(ranked, start=1):
            row["rank"] = index
        return ranked

    @staticmethod
    def _build_warnings(
        *, experiments: list[dict[str, Any]], rows: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        warnings: list[dict[str, str]] = []
        dataset_endpoints = {
            str((item.get("dataset_source") or {}).get("endpoint", ""))
            for item in experiments
            if isinstance(item.get("dataset_source"), Mapping)
            and (item.get("dataset_source") or {}).get("endpoint")
        }
        if len(dataset_endpoints) > 1:
            warnings.append(
                {
                    "level": "warning",
                    "message": "Dataset metadata differs across completed runs.",
                }
            )
        candle_counts = {
            int(item["candle_count"])
            for item in experiments
            if isinstance(item.get("candle_count"), int)
        }
        if len(candle_counts) > 1:
            warnings.append(
                {
                    "level": "warning",
                    "message": "Candle counts differ across completed runs.",
                }
            )
        if any(row.get("metric_notes") for row in rows):
            warnings.append(
                {
                    "level": "warning",
                    "message": "Some runs are missing normalized report metrics.",
                }
            )
        return warnings
