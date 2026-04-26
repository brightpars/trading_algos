from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from trading_algos.configuration.serialization import configuration_from_dict
from trading_algos.configuration.validation import validate_configuration_payload

from trading_algos_dashboard.repositories.configuration_draft_repository import (
    ConfigurationDraftRepository,
)
from trading_algos_dashboard.repositories.configuration_revision_repository import (
    ConfigurationRevisionRepository,
)


class ConfigurationBuilderService:
    def __init__(
        self,
        *,
        draft_repository: ConfigurationDraftRepository,
        revision_repository: ConfigurationRevisionRepository,
    ):
        self.draft_repository = draft_repository
        self.revision_repository = revision_repository

    def create_draft(self, payload: dict[str, Any]) -> str:
        normalized = validate_configuration_payload(configuration_from_dict(payload))
        now = datetime.now(timezone.utc)
        draft_id = f"cfgdraft_{uuid4().hex[:12]}"
        self.draft_repository.create_draft(
            {
                "draft_id": draft_id,
                "config_key": normalized.config_key,
                "name": normalized.name,
                "status": "draft",
                "payload": normalized.to_dict(),
                "created_at": now,
                "updated_at": now,
            }
        )
        self.revision_repository.create_revision(
            {
                "draft_id": draft_id,
                "revision_no": 1,
                "payload": normalized.to_dict(),
                "created_at": now,
            }
        )
        return draft_id

    def update_draft(self, draft_id: str, payload: dict[str, Any]) -> None:
        normalized = validate_configuration_payload(configuration_from_dict(payload))
        revisions = self.revision_repository.list_revisions(draft_id)
        revision_no = int(revisions[0]["revision_no"]) + 1 if revisions else 1
        now = datetime.now(timezone.utc)
        self.draft_repository.update_draft(
            draft_id,
            {
                "config_key": normalized.config_key,
                "name": normalized.name,
                "payload": normalized.to_dict(),
                "updated_at": now,
            },
        )
        self.revision_repository.create_revision(
            {
                "draft_id": draft_id,
                "revision_no": revision_no,
                "payload": normalized.to_dict(),
                "created_at": now,
            }
        )

    def list_drafts(self) -> list[dict[str, Any]]:
        return self.draft_repository.list_drafts()

    def get_draft_detail(self, draft_id: str) -> dict[str, Any] | None:
        draft = self.draft_repository.get_draft(draft_id)
        if draft is None:
            return None
        return {
            "draft": draft,
            "revisions": self.revision_repository.list_revisions(draft_id),
        }

    def delete_draft(self, draft_id: str) -> bool:
        draft = self.draft_repository.get_draft(draft_id)
        if draft is None:
            return False
        self.revision_repository.delete_revisions(draft_id)
        self.draft_repository.delete_draft(draft_id)
        return True
