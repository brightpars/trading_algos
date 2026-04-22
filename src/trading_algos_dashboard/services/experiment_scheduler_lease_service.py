from __future__ import annotations

from datetime import datetime, timedelta, timezone

from trading_algos_dashboard.repositories.experiment_scheduler_lease_repository import (
    ExperimentSchedulerLeaseRepository,
)


class ExperimentSchedulerLeaseService:
    def __init__(
        self,
        *,
        repository: ExperimentSchedulerLeaseRepository,
        lease_seconds: int = 5,
    ) -> None:
        self.repository = repository
        self.lease_seconds = lease_seconds

    def try_acquire_lease(self, *, owner_id: str) -> bool:
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self.lease_seconds)
        return self.repository.try_acquire_lease(
            owner_id=owner_id,
            expires_at=expires_at,
        )

    def release_lease(self, *, owner_id: str) -> None:
        self.repository.release_lease(owner_id=owner_id)
