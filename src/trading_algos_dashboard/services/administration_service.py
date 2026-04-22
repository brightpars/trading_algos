from __future__ import annotations

from datetime import UTC, datetime

from trading_algos.alertgen import list_alert_algorithm_specs
from trading_algos_dashboard.services.algorithm_catalog_service import (
    AlgorithmCatalogService,
)

from trading_algos_dashboard.repositories.experiment_repository import (
    ExperimentRepository,
)
from trading_algos_dashboard.repositories.algorithm_catalog_import_run_repository import (
    AlgorithmCatalogImportRunRepository,
)
from trading_algos_dashboard.repositories.algorithm_catalog_repository import (
    AlgorithmCatalogRepository,
)
from trading_algos_dashboard.repositories.result_repository import ResultRepository


class AdministrationService:
    ALGORITHM_CATALOG_DELETE_CONFIRMATION = "DELETE ALL ALGORITHM CATALOG ENTRIES"

    def __init__(
        self,
        *,
        experiment_repository: ExperimentRepository,
        result_repository: ResultRepository,
        algorithm_catalog_repository: AlgorithmCatalogRepository,
        algorithm_catalog_import_run_repository: AlgorithmCatalogImportRunRepository,
        algorithm_catalog_service: AlgorithmCatalogService,
    ):
        self.experiment_repository = experiment_repository
        self.result_repository = result_repository
        self.algorithm_catalog_repository = algorithm_catalog_repository
        self.algorithm_catalog_import_run_repository = (
            algorithm_catalog_import_run_repository
        )
        self.algorithm_catalog_service = algorithm_catalog_service

    def get_database_content_summary(self) -> list[dict[str, object]]:
        return [
            {
                "key": "experiments",
                "label": "Experiments",
                "description": "Delete all stored experiment runs and their related results.",
                "record_count": self.experiment_repository.count_experiments(),
                "action_endpoint": "administration.clear_experiments",
                "action_label": "Delete experiments",
            },
            {
                "key": "results",
                "label": "Results",
                "description": "Delete all stored report/result documents without deleting experiments.",
                "record_count": self.result_repository.count_results(),
                "action_endpoint": "administration.clear_results",
                "action_label": "Delete results",
            },
            {
                "key": "algorithm_catalog_entries",
                "label": "Algorithm catalog entries",
                "description": "Imported algorithm catalog rows stored from the enriched requirements document.",
                "record_count": self.algorithm_catalog_repository.count_entries(),
                "action_endpoint": None,
                "action_label": "Managed via import",
            },
            {
                "key": "algorithm_catalog_links",
                "label": "Algorithm implementations",
                "description": "Catalog entries that currently have an implementation assignment.",
                "record_count": self.algorithm_catalog_repository.count_entries_with_implementation(),
                "action_endpoint": "administration.sync_algorithm_catalog_links",
                "action_label": "Sync implementation linkages",
            },
        ]

    def get_algorithm_catalog_summary(
        self,
        *,
        category: str | None = None,
        catalog_type: str | None = None,
        advanced_label: str | None = None,
        linked: bool | None = None,
        search_text: str | None = None,
    ) -> dict[str, object]:
        return self.algorithm_catalog_service.get_catalog_summary(
            category=category,
            catalog_type=catalog_type,
            advanced_label=advanced_label,
            linked=linked,
            search_text=search_text,
        )

    def get_algorithm_catalog_admin_page_data(
        self,
        *,
        implementation_status: str | None = None,
        review_state: str | None = None,
        only_broken: bool = False,
        category: str | None = None,
        catalog_type: str | None = None,
        advanced_label: str | None = None,
        linked: bool | None = None,
        only_unresolved: bool = False,
        search_text: str | None = None,
        unresolved_page: int = 1,
        broken_page: int = 1,
        review_page: int = 1,
        queue_page: int = 1,
    ) -> dict[str, object]:
        return self.algorithm_catalog_service.get_catalog_page_data(
            implementation_status=implementation_status,
            review_state=review_state,
            only_broken=only_broken,
            category=category,
            catalog_type=catalog_type,
            advanced_label=advanced_label,
            linked=linked,
            only_unresolved=only_unresolved,
            search_text=search_text,
            unresolved_page=unresolved_page,
            broken_page=broken_page,
            review_page=review_page,
            queue_page=queue_page,
        )

    def rebuild_algorithm_catalog_links(self) -> dict[str, object]:
        updated_at = datetime.now(UTC).isoformat()
        active_entries = self.algorithm_catalog_repository.list_active_entries()
        entries_by_ref = {
            f"{entry.get('catalog_type', '')}:{int(entry.get('catalog_number', 0))}": entry
            for entry in active_entries
        }
        linked_count = 0
        missing_catalog_refs: list[str] = []
        for entry in active_entries:
            if str(entry.get("implementation_source", "")) != "runtime_declared":
                continue
            existing_review_state = str(entry.get("review_state", "")).strip()
            preserved_review_state = existing_review_state or "not_reviewed"
            self.algorithm_catalog_repository.update_entry_admin_fields(
                str(entry["id"]),
                {
                    "implementation_id": "",
                    "implementation_catalog_ref": "",
                    "implementation_source": "",
                    "implementation_confidence": 0.0,
                    "implementation_mapping_notes": "",
                    "implementation_mapping_reason": "",
                    "implementation_builder_name": "",
                    "implementation_builder_module": "",
                    "implementation_source_file": "",
                    "review_state": preserved_review_state,
                    "updated_at": updated_at,
                },
            )
        for spec in list_alert_algorithm_specs():
            catalog_ref = str(spec.catalog_ref).strip()
            if not catalog_ref:
                missing_catalog_refs.append(spec.key)
                continue
            matched_entry = entries_by_ref.get(catalog_ref)
            if matched_entry is None:
                missing_catalog_refs.append(spec.key)
                continue
            if str(matched_entry.get("implementation_source", "")) == "manual":
                linked_count += 1
                continue
            existing_review_state = str(matched_entry.get("review_state", "")).strip()
            preserved_review_state = existing_review_state or "not_reviewed"
            self.algorithm_catalog_repository.update_entry_admin_fields(
                str(matched_entry["id"]),
                {
                    "implementation_id": spec.key,
                    "implementation_catalog_ref": catalog_ref,
                    "implementation_source": "runtime_declared",
                    "implementation_confidence": 1.0,
                    "implementation_mapping_notes": "algorithm_catalog: linked from implementation-declared catalog_ref",
                    "review_state": preserved_review_state,
                    "implementation_mapping_reason": "implementation-declared catalog_ref",
                    "implementation_builder_name": str(
                        getattr(spec.builder, "__name__", "")
                    ),
                    "implementation_builder_module": str(
                        getattr(spec.builder, "__module__", "")
                    ),
                    "implementation_source_file": str(
                        getattr(spec, "builder_source_file", "")
                    ),
                    "updated_at": updated_at,
                },
            )
            linked_count += 1
        return {
            "linked_count": linked_count,
            "missing_catalog_ref_count": len(missing_catalog_refs),
            "missing_catalog_ref_alg_impl_ids": missing_catalog_refs,
        }

    def get_import_run_detail(self, run_id: str) -> dict[str, object]:
        run = self.algorithm_catalog_import_run_repository.get_run_by_id(run_id)
        if run is None:
            raise ValueError(f"Unknown import run: {run_id}")
        all_runs = self.algorithm_catalog_import_run_repository.list_runs()
        previous_run = None
        for index, candidate in enumerate(all_runs):
            if candidate.get("id") == run_id and index + 1 < len(all_runs):
                previous_run = all_runs[index + 1]
                break
        return {
            "run": run,
            "previous_run": previous_run,
            "created_entries": self._entries_from_ids(run.get("created_entry_ids", [])),
            "updated_entries": self._entries_from_ids(run.get("updated_entry_ids", [])),
            "deactivated_entries": self._entries_from_ids(
                run.get("deactivated_entry_ids", [])
            ),
            "unresolved_entries": self._entries_from_ids(
                run.get("unresolved_entry_ids", [])
            ),
            "preserved_manual_link_entries": self._entries_from_ids(
                run.get("preserved_manual_link_entry_ids", [])
            ),
            "changed_link_entries": self._entries_from_ids(
                run.get("changed_link_entry_ids", [])
            ),
        }

    def _entries_from_ids(self, entry_ids: list[str]) -> list[dict[str, object]]:
        entries: list[dict[str, object]] = []
        for entry_id in entry_ids:
            entry = self.algorithm_catalog_repository.get_entry_by_id(entry_id)
            if entry is not None:
                entries.append(entry)
        return entries

    def clear_experiments(self) -> dict[str, int]:
        deleted_results = self.result_repository.delete_all_results()
        deleted_experiments = self.experiment_repository.delete_all_experiments()
        return {
            "deleted_experiments": deleted_experiments,
            "deleted_results": deleted_results,
        }

    def clear_results(self) -> int:
        return self.result_repository.delete_all_results()

    def delete_algorithm_catalog_content(
        self, *, confirmation_text: str
    ) -> dict[str, int]:
        normalized_confirmation = confirmation_text.strip()
        if normalized_confirmation != self.ALGORITHM_CATALOG_DELETE_CONFIRMATION:
            raise ValueError("invalid confirmation text")
        deleted_entries = self.algorithm_catalog_repository.delete_all_entries()
        return {
            "deleted_entries": deleted_entries,
            "deleted_links": 0,
        }
