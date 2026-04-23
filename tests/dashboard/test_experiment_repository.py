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

    @staticmethod
    def _matches_query(doc, query):
        for key, value in query.items():
            if key == "$or":
                if not any(_Collection._matches_query(doc, item) for item in value):
                    return False
                continue
            if isinstance(value, dict):
                if "$lte" in value:
                    doc_value = doc.get(key)
                    if doc_value is None or doc_value > value["$lte"]:
                        return False
                    continue
            if doc.get(key) != value:
                return False
        return True

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

    def count_documents(self, query):
        return sum(
            1 for doc in self.docs if all(doc.get(k) == v for k, v in query.items())
        )

    def find_one_and_update(
        self, query, update, sort=None, return_document=None, upsert=False
    ):
        matches = [doc for doc in self.docs if self._matches_query(doc, query)]
        if sort:
            for key, direction in reversed(sort):
                matches.sort(key=lambda item: item.get(key), reverse=direction == -1)
        if not matches:
            if not upsert:
                return None
            doc = {}
            for key, value in query.items():
                if key.startswith("$") or isinstance(value, dict):
                    continue
                doc[key] = value
            if "$set" in update and isinstance(update["$set"], dict):
                doc.update(update["$set"])
            self.docs.append(doc)
            return dict(doc)
        doc = matches[0]
        doc.update(update["$set"])
        return dict(doc)

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


def test_experiment_repository_counts_and_lists_running_experiments():
    collection = _Collection()
    repo = ExperimentRepository({"dashboard_experiments": collection})
    repo.create_experiment({"experiment_id": "exp_1", "status": "running"})
    repo.create_experiment({"experiment_id": "exp_2", "status": "running"})
    repo.create_experiment({"experiment_id": "exp_3", "status": "queued"})

    assert repo.count_running_experiments() == 2
    assert [item["experiment_id"] for item in repo.list_running_experiments()] == [
        "exp_1",
        "exp_2",
    ]


def test_experiment_repository_claims_next_queued_experiment_in_fifo_order():
    collection = _Collection()
    repo = ExperimentRepository({"dashboard_experiments": collection})
    repo.create_experiment(
        {
            "experiment_id": "exp_b",
            "status": "queued",
            "created_at": datetime(2024, 2, 1, 12, 1, tzinfo=timezone.utc),
            "queue_enqueued_at": datetime(2024, 2, 1, 12, 1, tzinfo=timezone.utc),
        }
    )
    repo.create_experiment(
        {
            "experiment_id": "exp_a",
            "status": "queued",
            "created_at": datetime(2024, 2, 1, 12, 0, tzinfo=timezone.utc),
            "queue_enqueued_at": datetime(2024, 2, 1, 12, 0, tzinfo=timezone.utc),
        }
    )

    claimed = repo.claim_next_queued_experiment(
        started_at=datetime(2024, 2, 1, 13, 0, tzinfo=timezone.utc)
    )

    assert claimed is not None
    assert claimed["experiment_id"] == "exp_a"
    assert claimed["status"] == "running"


def test_experiment_repository_lists_completed_experiments_for_exact_scope():
    collection = _Collection()
    repo = ExperimentRepository({"dashboard_experiments": collection})
    start = datetime(2024, 2, 1, 9, 30, tzinfo=timezone.utc)
    end = datetime(2024, 2, 3, 16, 0, tzinfo=timezone.utc)
    repo.create_experiment(
        {
            "experiment_id": "exp_match",
            "status": "completed",
            "symbol": "AAPL",
            "time_range": {"start": start, "end": end},
            "created_at": start,
        }
    )
    repo.create_experiment(
        {
            "experiment_id": "exp_wrong_status",
            "status": "running",
            "symbol": "AAPL",
            "time_range": {"start": start, "end": end},
            "created_at": start,
        }
    )
    repo.create_experiment(
        {
            "experiment_id": "exp_wrong_range",
            "status": "completed",
            "symbol": "AAPL",
            "time_range": {
                "start": start,
                "end": datetime(2024, 2, 4, 16, 0, tzinfo=timezone.utc),
            },
            "created_at": start,
        }
    )

    matches = repo.list_completed_experiments_for_scope(
        symbol="AAPL",
        start=start,
        end=end,
    )

    assert [item["experiment_id"] for item in matches] == ["exp_match"]
