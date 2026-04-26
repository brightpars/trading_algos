from trading_algos_dashboard.repositories.backtrace_session_repository import (
    BacktraceSessionRepository,
)


class _Cursor:
    def __init__(self, docs):
        self.docs = docs

    def __iter__(self):
        return iter(self.docs)


class _Collection:
    def __init__(self):
        self.docs = []

    def insert_one(self, payload):
        self.docs.append(dict(payload))

    def find_one(self, query):
        for doc in self.docs:
            if all(doc.get(key) == value for key, value in query.items()):
                return dict(doc)
        return None

    def find(self, query):
        return _Cursor(
            [
                dict(doc)
                for doc in self.docs
                if all(doc.get(key) == value for key, value in query.items())
            ]
        )

    def update_one(self, query, update, upsert=False):
        for doc in self.docs:
            if all(doc.get(key) == value for key, value in query.items()):
                doc.update(update["$set"])
                return None
        if upsert:
            payload = dict(query)
            payload.update(update.get("$set", {}))
            self.docs.append(payload)
        return None


def test_backtrace_session_repository_round_trip() -> None:
    collection = _Collection()
    repository = BacktraceSessionRepository(
        {"dashboard_backtrace_sessions": collection}
    )

    repository.create_session(
        {
            "run_id": "run-1",
            "request_id": "req-1",
            "status": "running",
            "algorithm_key": "demo_algo",
            "symbol": "AAPL",
            "request": {"algorithm_key": "demo_algo"},
            "input_summary": {"candle_count": 2},
            "result_summary": {},
            "full_result": None,
            "error": None,
            "created_at": "2025-01-01T10:00:00+00:00",
            "started_at": "2025-01-01T10:00:00+00:00",
            "finished_at": None,
        }
    )
    repository.update_session(
        "run-1",
        {
            "status": "completed",
            "result_summary": {"total_rows": 2},
            "full_result": {"status": "completed"},
            "finished_at": "2025-01-01T10:00:01+00:00",
        },
    )

    payload = repository.get_run("run-1")

    assert payload is not None
    assert payload["status"] == "completed"
    assert payload["result_summary"] == {"total_rows": 2}
    assert payload["full_result"] == {"status": "completed"}


def test_backtrace_session_repository_lists_recent_runs_newest_first() -> None:
    collection = _Collection()
    repository = BacktraceSessionRepository(
        {"dashboard_backtrace_sessions": collection}
    )

    repository.create_session(
        {
            "run_id": "run-1",
            "status": "completed",
            "created_at": "2025-01-01T10:00:00+00:00",
        }
    )
    repository.create_session(
        {
            "run_id": "run-2",
            "status": "failed",
            "created_at": "2025-01-01T10:00:01+00:00",
        }
    )
    repository.create_session(
        {
            "run_id": "run-3",
            "status": "running",
            "created_at": "2025-01-01T10:00:02+00:00",
        }
    )

    recent_runs = repository.list_recent_runs(limit=2)

    assert [item["run_id"] for item in recent_runs] == ["run-3", "run-2"]
