from datetime import datetime, timezone

from trading_algos_dashboard.services.evaluation_service import EvaluationService


class _ExperimentRepository:
    def __init__(self, experiments):
        self.experiments = experiments

    def list_completed_experiments_for_scope(
        self, *, symbol, start, end, status="completed"
    ):
        def _normalize(value):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc)
            return value.astimezone(timezone.utc)

        normalized_start = _normalize(start)
        normalized_end = _normalize(end)
        return [
            experiment
            for experiment in self.experiments
            if experiment.get("symbol") == symbol
            and experiment.get("status") == status
            and _normalize(experiment.get("time_range", {}).get("start"))
            == normalized_start
            and _normalize(experiment.get("time_range", {}).get("end"))
            == normalized_end
        ]

    def list_completed_experiment_cohorts(self):
        grouped: dict[tuple[str, datetime, datetime], dict] = {}
        for experiment in self.experiments:
            if experiment.get("status") != "completed":
                continue
            symbol = str(experiment.get("symbol", "")).strip().upper()
            time_range = experiment.get("time_range", {})
            start = time_range.get("start")
            end = time_range.get("end")
            if (
                not symbol
                or not isinstance(start, datetime)
                or not isinstance(end, datetime)
            ):
                continue
            key = (symbol, start, end)
            grouped.setdefault(
                key,
                {
                    "symbol": symbol,
                    "start": start,
                    "end": end,
                    "completed_run_count": 0,
                    "latest_finished_at": None,
                    "candle_counts": [],
                    "dataset_endpoints": [],
                    "experiment_ids": [],
                },
            )
            cohort = grouped[key]
            cohort["completed_run_count"] += 1
            cohort["experiment_ids"].append(experiment["experiment_id"])
        return list(grouped.values())


class _ResultRepository:
    def __init__(self, results):
        self.results = results

    def list_results_for_experiments(self, experiment_ids):
        return [
            result
            for result in self.results
            if result.get("experiment_id") in set(experiment_ids)
        ]


def test_evaluation_service_returns_ranked_rows_and_warnings():
    start = datetime(2024, 2, 1, 9, 30, tzinfo=timezone.utc)
    end = datetime(2024, 2, 3, 16, 0, tzinfo=timezone.utc)
    experiments = [
        {
            "experiment_id": "exp_1",
            "symbol": "AAPL",
            "status": "completed",
            "time_range": {"start": start, "end": end},
            "dataset_source": {"endpoint": "127.0.0.1:7003"},
            "candle_count": 10,
            "duration_seconds": 11.0,
        },
        {
            "experiment_id": "exp_2",
            "symbol": "AAPL",
            "status": "completed",
            "time_range": {"start": start, "end": end},
            "dataset_source": {"endpoint": "127.0.0.1:8000"},
            "candle_count": 12,
            "duration_seconds": 9.0,
        },
    ]
    results = [
        {
            "experiment_id": "exp_1",
            "alg_name": "Algo 1",
            "signal_summary": {"buy_count": 1, "sell_count": 2, "total_rows": 4},
            "report": {
                "algorithm_summary": {"algorithm_name": "Algo 1", "family": "trend"},
                "evaluation_summary": {"headline_metrics": {"cumulative_return": 0.4}},
            },
        },
        {
            "experiment_id": "exp_2",
            "alg_name": "Algo 2",
            "signal_summary": {"buy_count": 2, "sell_count": 1, "total_rows": 5},
            "report": {
                "algorithm_summary": {"algorithm_name": "Algo 2", "family": "trend"},
                "summary_cards": [{"label": "Win rate", "value": "0.6"}],
            },
        },
    ]
    service = EvaluationService(
        experiment_repository=_ExperimentRepository(experiments),
        result_repository=_ResultRepository(results),
    )

    payload = service.find_comparable_runs(
        symbol="AAPL",
        start_date="2024-02-01",
        start_time="09:30",
        end_date="2024-02-03",
        end_time="16:00",
    )

    assert payload["cohort"]["completed_run_count"] == 2
    assert [row["algorithm_name"] for row in payload["rows"]] == ["Algo 1", "Algo 2"]
    assert payload["rows"][0]["metrics"]["cumulative_return"] == 0.4
    assert payload["rows"][1]["metrics"]["win_rate"] == 0.6
    assert payload["rows"][0]["trade_count"] == 3
    assert len(payload["warnings"]) == 2


def test_evaluation_service_returns_empty_rows_for_no_matches():
    service = EvaluationService(
        experiment_repository=_ExperimentRepository([]),
        result_repository=_ResultRepository([]),
    )

    payload = service.find_comparable_runs(
        symbol="AAPL",
        start_date="2024-02-01",
        start_time="09:30",
        end_date="2024-02-03",
        end_time="16:00",
    )

    assert payload["rows"] == []
    assert payload["warnings"] == []


def test_evaluation_service_lists_comparable_run_cohorts():
    start = datetime(2024, 2, 1, 9, 30, tzinfo=timezone.utc)
    end = datetime(2024, 2, 3, 16, 0, tzinfo=timezone.utc)
    experiments = [
        {
            "experiment_id": "exp_1",
            "symbol": "AAPL",
            "status": "completed",
            "time_range": {"start": start, "end": end},
            "finished_at": end,
        },
        {
            "experiment_id": "exp_2",
            "symbol": "AAPL",
            "status": "completed",
            "time_range": {"start": start, "end": end},
            "finished_at": end,
        },
    ]
    results = [
        {"experiment_id": "exp_1", "alg_name": "Algo 1"},
        {"experiment_id": "exp_1", "alg_name": "Algo 1b"},
        {"experiment_id": "exp_2", "alg_name": "Algo 2"},
    ]
    service = EvaluationService(
        experiment_repository=_ExperimentRepository(experiments),
        result_repository=_ResultRepository(results),
    )

    payload = service.list_comparable_run_cohorts()

    assert len(payload) == 1
    assert payload[0]["symbol"] == "AAPL"
    assert payload[0]["completed_run_count"] == 2
    assert payload[0]["result_count"] == 3
    assert payload[0]["filters"]["start_date"] == "2024-02-01"
