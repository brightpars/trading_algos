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

    def update_one(self, query, update):
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in query.items()):
                doc.update(update["$set"])


def test_experiment_repository_round_trip():
    collection = _Collection()
    repo = ExperimentRepository({"dashboard_experiments": collection})
    repo.create_experiment({"experiment_id": "exp1", "status": "running"})
    repo.update_experiment_status("exp1", "completed")
    payload = repo.get_experiment("exp1")
    assert payload is not None
    assert payload["status"] == "completed"
