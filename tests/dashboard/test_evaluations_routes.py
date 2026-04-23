from datetime import datetime, timezone

from trading_algos_dashboard.app import create_app
from trading_algos_dashboard.config import DashboardConfig

from tests.dashboard.test_experiments_routes import _Client


def test_evaluations_index_renders(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )

    response = app.test_client().get("/evaluations")

    assert response.status_code == 200
    assert b"Evaluations" in response.data
    assert b"Find comparable runs" in response.data


def test_evaluations_cohort_renders_matching_completed_runs(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )
    start = datetime(2024, 2, 1, 9, 30, tzinfo=timezone.utc)
    end = datetime(2024, 2, 3, 16, 0, tzinfo=timezone.utc)
    app.extensions["experiment_repository"].create_experiment(
        {
            "experiment_id": "exp_eval",
            "created_at": start,
            "finished_at": end,
            "status": "completed",
            "symbol": "AAPL",
            "time_range": {"start": start, "end": end},
            "dataset_source": {"endpoint": "127.0.0.1:7003"},
            "candle_count": 10,
            "duration_seconds": 3.0,
        }
    )
    app.extensions["result_repository"].insert_result(
        {
            "experiment_id": "exp_eval",
            "alg_name": "Algo Eval",
            "signal_summary": {"buy_count": 1, "sell_count": 1, "total_rows": 3},
            "report": {
                "algorithm_summary": {"algorithm_name": "Algo Eval", "family": "trend"},
                "evaluation_summary": {"headline_metrics": {"cumulative_return": 0.25}},
            },
        }
    )

    response = app.test_client().get(
        "/evaluations/cohort?symbol=AAPL&start_date=2024-02-01&start_time=09:30&end_date=2024-02-03&end_time=16:00"
    )

    assert response.status_code == 200
    assert b"Evaluation cohort" in response.data
    assert b"Algo Eval" in response.data
    assert b"0.25" in response.data


def test_evaluations_cohort_returns_400_for_invalid_range(monkeypatch):
    monkeypatch.setattr(
        "trading_algos_dashboard.app.MongoClient", lambda *_a, **_k: _Client()
    )
    app = create_app(
        DashboardConfig("x", "mongodb://example", "db", "reports", "/tmp/smarttrade", 1)
    )

    response = app.test_client().get(
        "/evaluations/cohort?symbol=AAPL&start_date=2024-02-03&start_time=16:00&end_date=2024-02-01&end_time=09:30"
    )

    assert response.status_code == 400
