from datetime import datetime, timezone

from trading_algos_dashboard.repositories.experiment_repository import (
    ExperimentRepository,
)


class _Cursor:
    def __init__(self, docs):
        self.docs = docs

    def sort(self, *_args, **_kwargs):
        return self.docs


class _Collection:
    def __init__(self):
        self.docs = []

    def insert_one(self, payload):
        self.docs.append(dict(payload))

    def find_one(self, query):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                return dict(doc)
        return None

    def find(self, query):
        return _Cursor(
            [
                dict(doc)
                for doc in self.docs
                if all(doc.get(k) == v for k, v in query.items())
            ]
        )

    def update_one(self, query, update, upsert=False):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(update["$set"])
                return None

        if upsert:
            payload = dict(query)
            if "$set" in update:
                payload.update(update["$set"])
            self.docs.append(payload)
        return None

    def delete_one(self, query):
        for index, doc in enumerate(self.docs):
            if all(doc.get(k) == v for k, v in query.items()):
                del self.docs[index]
                return type("_DeleteResult", (), {"deleted_count": 1})()
        return type("_DeleteResult", (), {"deleted_count": 0})()

    def delete_many(self, query):
        original_count = len(self.docs)
        self.docs = [
            doc
            for doc in self.docs
            if not all(doc.get(k) == v for k, v in query.items())
        ]
        return type(
            "_DeleteResult", (), {"deleted_count": original_count - len(self.docs)}
        )()


def test_experiment_repository_round_trip():
    collection = _Collection()
    repo = ExperimentRepository({"dashboard_experiments": collection})
    repo.create_experiment({"experiment_id": "exp1", "status": "running"})
    repo.update_experiment_status("exp1", "completed")
    payload = repo.get_experiment("exp1")
    assert payload is not None
    assert payload["status"] == "completed"


def test_experiment_repository_lists_queued_experiments_in_fifo_order():
    collection = _Collection()
    repo = ExperimentRepository({"dashboard_experiments": collection})
    repo.create_experiment(
        {
            "experiment_id": "exp_late",
            "status": "queued",
            "created_at": datetime(2024, 2, 1, 12, 5, tzinfo=timezone.utc),
            "queue_enqueued_at": datetime(2024, 2, 1, 12, 5, tzinfo=timezone.utc),
        }
    )
    repo.create_experiment(
        {
            "experiment_id": "exp_first",
            "status": "queued",
            "created_at": datetime(2024, 2, 1, 12, 0, tzinfo=timezone.utc),
            "queue_enqueued_at": datetime(2024, 2, 1, 12, 0, tzinfo=timezone.utc),
        }
    )

    queued = repo.list_queued_experiments()
    next_queued = repo.get_next_queued_experiment()

    assert [item["experiment_id"] for item in queued] == ["exp_first", "exp_late"]
    assert next_queued is not None
    assert next_queued["experiment_id"] == "exp_first"
    assert repo.count_queued_before("exp_late") == 1


def test_experiment_repository_get_running_experiment_returns_running_item():
    collection = _Collection()
    repo = ExperimentRepository({"dashboard_experiments": collection})
    repo.create_experiment(
        {
            "experiment_id": "exp_running",
            "status": "running",
            "created_at": datetime(2024, 2, 1, 12, 0, tzinfo=timezone.utc),
        }
    )
    repo.create_experiment(
        {
            "experiment_id": "exp_queued",
            "status": "queued",
            "created_at": datetime(2024, 2, 1, 12, 1, tzinfo=timezone.utc),
            "queue_enqueued_at": datetime(2024, 2, 1, 12, 1, tzinfo=timezone.utc),
        }
    )

    running = repo.get_running_experiment()

    assert running is not None
    assert running["experiment_id"] == "exp_running"
