from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime
from typing import Any

from trading_algos.alertgen import (
    get_alert_algorithm_spec_by_key,
    list_alert_algorithm_specs,
)
from trading_algos_dashboard.repositories.algorithm_catalog_repository import (
    AlgorithmCatalogRepository,
)


AdminCatalogPage = dict[str, Any]


class AlgorithmCatalogService:
    REVIEW_STATE_OPTIONS = [
        {"value": "not_reviewed", "label": "Not reviewed"},
        {"value": "confirmed", "label": "Confirmed"},
        {"value": "suggested", "label": "Suggested"},
        {"value": "needs_review", "label": "Needs review"},
        {"value": "rejected", "label": "Rejected"},
        {"value": "deferred", "label": "Deferred"},
    ]

    def __init__(
        self,
        *,
        catalog_repository: AlgorithmCatalogRepository,
    ):
        self.catalog_repository = catalog_repository

    def list_algorithm_implementations(self) -> list[dict[str, Any]]:
        return [_spec_to_dict(spec) for spec in list_alert_algorithm_specs()]

    def list_catalog_entries(self) -> list[dict[str, Any]]:
        entries = self._list_merged_catalog_entries()
        return [self._build_catalog_summary(entry) for entry in entries]

    def list_catalog_entries_filtered(
        self,
        *,
        implementation_status: str | None = None,
        category: str | None = None,
        catalog_type: str | None = None,
        advanced_label: str | None = None,
        search_text: str | None = None,
    ) -> list[dict[str, Any]]:
        items = self.list_catalog_entries()
        return self._filter_catalog_items(
            items,
            implementation_status=implementation_status,
            review_state=None,
            only_broken=False,
            only_unresolved=False,
            category=category,
            catalog_type=catalog_type,
            advanced_label=advanced_label,
            search_text=search_text,
            linked=None,
        )

    def list_admin_catalog_entries(
        self,
        *,
        implementation_status: str | None = None,
        review_state: str | None = None,
        only_broken: bool = False,
        only_unresolved: bool = False,
        category: str | None = None,
        catalog_type: str | None = None,
        advanced_label: str | None = None,
        search_text: str | None = None,
        linked: bool | None = None,
        page: int = 1,
        page_size: int | None = 25,
    ) -> AdminCatalogPage:
        items = [
            self._build_catalog_detail(entry)
            for entry in self._list_merged_catalog_entries()
        ]
        items = self._filter_catalog_items(
            items,
            implementation_status=implementation_status,
            review_state=review_state,
            only_broken=only_broken,
            only_unresolved=only_unresolved,
            category=category,
            catalog_type=catalog_type,
            advanced_label=advanced_label,
            search_text=search_text,
            linked=linked,
        )

        total_count = len(items)
        requested_page = max(page, 1)
        effective_page_size = None if page_size is None else max(page_size, 1)
        if effective_page_size is None:
            return {
                "items": items,
                "total_count": total_count,
                "page": 1,
                "page_size": total_count,
                "total_pages": 1,
            }
        total_pages = max(
            (total_count + effective_page_size - 1) // effective_page_size, 1
        )
        effective_page = min(requested_page, total_pages)
        start_index = (effective_page - 1) * effective_page_size
        end_index = start_index + effective_page_size
        paged_items = items[start_index:end_index]
        return {
            "items": paged_items,
            "total_count": total_count,
            "page": effective_page,
            "page_size": effective_page_size,
            "total_pages": total_pages,
        }

    def list_algorithm_implementation_options(self) -> list[dict[str, str]]:
        options = [
            {
                "key": spec["key"],
                "name": spec["name"],
                "label": f"{spec['name']} ({spec['key']})",
            }
            for spec in self.list_algorithm_implementations()
        ]
        return sorted(options, key=lambda item: item["name"])

    def list_runnable_algorithm_implementations(self) -> list[dict[str, Any]]:
        return sorted(
            [
                spec
                for spec in self.list_algorithm_implementations()
                if str(spec.get("status", "")) in {"stable", "runnable"}
            ],
            key=lambda item: str(item.get("name", "")),
        )

    def get_runnable_algorithm_implementation(self, alg_key: str) -> dict[str, Any]:
        spec = self.get_algorithm_implementation(alg_key)
        if str(spec.get("status", "")) not in {"stable", "runnable"}:
            raise ValueError(f"Algorithm is not runnable: {alg_key}")
        return spec

    def list_review_state_options(self) -> list[dict[str, str]]:
        return [dict(item) for item in self.REVIEW_STATE_OPTIONS]

    def get_catalog_page_data(
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
    ) -> dict[str, Any]:
        unresolved_payload = self.list_admin_catalog_entries(
            implementation_status="not_implemented",
            category=category,
            catalog_type=catalog_type,
            advanced_label=advanced_label,
            linked=linked,
            search_text=search_text,
            page=unresolved_page,
            page_size=25,
        )
        broken_payload = self.list_admin_catalog_entries(
            only_broken=True,
            category=category,
            catalog_type=catalog_type,
            advanced_label=advanced_label,
            linked=linked,
            search_text=search_text,
            page=broken_page,
            page_size=25,
        )
        review_payload = self.list_admin_catalog_entries(
            review_state="not_reviewed",
            category=category,
            catalog_type=catalog_type,
            advanced_label=advanced_label,
            linked=linked,
            search_text=search_text,
            page=review_page,
            page_size=25,
        )
        queue_payload = self.list_admin_catalog_entries(
            implementation_status=implementation_status,
            review_state=review_state,
            only_broken=only_broken,
            only_unresolved=only_unresolved,
            category=category,
            catalog_type=catalog_type,
            advanced_label=advanced_label,
            linked=linked,
            search_text=search_text,
            page=queue_page,
            page_size=50,
        )
        latest_run = self.catalog_repository.db[
            "algorithm_catalog_import_runs"
        ].find_one({})
        import_runs = list(
            self.catalog_repository.db["algorithm_catalog_import_runs"]
            .find({})
            .sort("completed_at", -1)
        )
        summary = self.get_catalog_summary(
            category=category,
            catalog_type=catalog_type,
            advanced_label=advanced_label,
            linked=linked,
            search_text=search_text,
        )
        return {
            "summary": summary,
            "latest_run": latest_run,
            "import_runs": import_runs,
            "unresolved_payload": unresolved_payload,
            "broken_payload": broken_payload,
            "review_payload": review_payload,
            "queue_payload": queue_payload,
            "filters": {
                "implementation_status": implementation_status or "",
                "review_state": review_state or "",
                "only_broken": only_broken,
                "category": category or "",
                "catalog_type": catalog_type or "",
                "advanced_label": advanced_label or "",
                "linked": "" if linked is None else ("true" if linked else "false"),
                "only_unresolved": only_unresolved,
                "search_text": search_text or "",
                "unresolved_page": unresolved_payload["page"],
                "broken_page": broken_payload["page"],
                "review_page": review_payload["page"],
                "page": queue_payload["page"],
                "queue_page": queue_payload["page"],
            },
            "categories": self._distinct_entry_values("category"),
            "catalog_types": self._distinct_entry_values("catalog_type"),
            "advanced_labels": self._distinct_entry_values("advanced_label"),
            "implementation_statuses": [
                {"value": "implemented", "label": "Implemented"},
                {"value": "not_implemented", "label": "Not implemented"},
                {"value": "deferred", "label": "Deferred"},
                {"value": "broken_link", "label": "Broken link"},
                {
                    "value": "implementation_needs_review",
                    "label": "Needs review",
                },
            ],
            "review_states": [
                *self.list_review_state_options(),
            ],
        }

    def get_catalog_summary(
        self,
        *,
        category: str | None = None,
        catalog_type: str | None = None,
        advanced_label: str | None = None,
        linked: bool | None = None,
        search_text: str | None = None,
    ) -> dict[str, object]:
        unresolved_payload = self.list_admin_catalog_entries(
            implementation_status="not_implemented",
            category=category,
            catalog_type=catalog_type,
            advanced_label=advanced_label,
            linked=linked,
            search_text=search_text,
            page_size=None,
        )
        broken_payload = self.list_admin_catalog_entries(
            only_broken=True,
            category=category,
            catalog_type=catalog_type,
            advanced_label=advanced_label,
            linked=linked,
            search_text=search_text,
            page_size=None,
        )
        review_payload = self.list_admin_catalog_entries(
            review_state="not_reviewed",
            category=category,
            catalog_type=catalog_type,
            advanced_label=advanced_label,
            linked=linked,
            search_text=search_text,
            page_size=None,
        )
        implemented_payload = self.list_admin_catalog_entries(
            implementation_status="implemented",
            category=category,
            catalog_type=catalog_type,
            advanced_label=advanced_label,
            linked=linked,
            search_text=search_text,
            page_size=None,
        )
        latest_run = self.catalog_repository.db[
            "algorithm_catalog_import_runs"
        ].find_one({})
        return {
            "entry_count": self.catalog_repository.count_entries(),
            "link_count": self.catalog_repository.count_entries_with_implementation(),
            "latest_run": latest_run,
            "implemented_count": int(implemented_payload["total_count"]),
            "unresolved_count": int(unresolved_payload["total_count"]),
            "broken_link_count": int(broken_payload["total_count"]),
            "needs_review_count": int(review_payload["total_count"]),
        }

    def _distinct_entry_values(self, key: str) -> list[str]:
        return sorted(
            {
                str(entry.get(key, ""))
                for entry in self._list_merged_catalog_entries()
                if str(entry.get(key, ""))
            }
        )

    def get_catalog_entry(self, entry_id_or_slug: str) -> dict[str, Any]:
        entry = self.catalog_repository.get_entry_by_id(entry_id_or_slug)
        if entry is None:
            entry = self.catalog_repository.get_entry_by_slug(entry_id_or_slug)
        if entry is None:
            entry = self._find_catalog_entry_by_alg_impl_id(entry_id_or_slug)
        if entry is None:
            entry = self._build_runtime_only_entry_by_alg_impl_id(entry_id_or_slug)
        if entry is None:
            raise ValueError(f"Unknown algorithm catalog entry: {entry_id_or_slug}")
        return self._build_catalog_detail(entry)

    def update_catalog_entry(
        self,
        entry_id_or_slug: str,
        *,
        catalog_values: dict[str, Any],
        review_state: str | None,
        link_notes: str | None,
        implementation_id: str | None = None,
    ) -> dict[str, Any]:
        entry = self.catalog_repository.get_entry_by_id(entry_id_or_slug)
        if entry is None:
            entry = self.catalog_repository.get_entry_by_slug(entry_id_or_slug)
        if entry is None:
            raise ValueError(f"Unknown algorithm catalog entry: {entry_id_or_slug}")

        normalized_values = self._normalize_catalog_update_values(catalog_values)
        update_values: dict[str, Any] = {
            **normalized_values,
            "updated_at": _utc_now(),
        }

        if implementation_id is not None:
            normalized_implementation_id = str(implementation_id).strip()
            if normalized_implementation_id:
                alg_impl_spec = self.get_algorithm_implementation(
                    normalized_implementation_id
                )
                update_values.update(
                    {
                        "implementation_id": normalized_implementation_id,
                        "implementation_catalog_ref": str(
                            alg_impl_spec.get("catalog_ref", "")
                        ).strip(),
                        "implementation_source": "manual",
                        "implementation_confidence": 1.0,
                        "implementation_mapping_notes": (
                            "algorithm_catalog: manually assigned implementation"
                        ),
                        "implementation_mapping_reason": "manual implementation assignment",
                        "implementation_builder_name": str(
                            alg_impl_spec.get("builder_name", "")
                        ),
                        "implementation_builder_module": str(
                            alg_impl_spec.get("builder_module", "")
                        ),
                        "implementation_source_file": str(
                            alg_impl_spec.get("builder_source_file", "")
                        ),
                        "review_state": "not_reviewed",
                    }
                )
            else:
                update_values.update(
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
                        "review_state": "not_reviewed",
                    }
                )

        self.catalog_repository.update_entry_admin_fields(entry["id"], update_values)
        updated_entry = (
            self.catalog_repository.get_entry_by_id(str(entry["id"])) or entry
        )

        if review_state is not None or link_notes is not None:
            if not str(updated_entry.get("implementation_id", "")).strip():
                raise ValueError(
                    "Algorithm review state cannot be changed because no implementation is assigned."
                )
            effective_review_state = (
                str(review_state).strip() if review_state is not None else ""
            ) or str(updated_entry.get("review_state", "")).strip()
            if effective_review_state not in {
                option["value"] for option in self.REVIEW_STATE_OPTIONS
            }:
                raise ValueError(
                    f"Invalid review state: {effective_review_state or 'empty'}"
                )
            self.catalog_repository.update_entry_admin_fields(
                str(entry["id"]),
                {
                    "review_state": effective_review_state,
                    "updated_at": _utc_now(),
                },
            )

        return self.get_catalog_entry(str(entry["id"]))

    def create_catalog_entry(
        self,
        *,
        catalog_values: dict[str, Any],
        catalog_type: str = "algorithm",
        alg_impl_id: str | None = None,
    ) -> dict[str, Any]:
        normalized_catalog_type = str(catalog_type).strip() or "algorithm"
        normalized_values = self._normalize_catalog_update_values(catalog_values)
        entry_name = normalized_values["name"]
        slug = _slugify(entry_name)
        if not slug:
            raise ValueError("Algorithm slug cannot be empty.")
        if self.catalog_repository.get_entry_by_slug(slug) is not None:
            raise ValueError(f"Algorithm already exists: {entry_name}")

        timestamp = _utc_now()
        next_number = self.catalog_repository.next_catalog_number(
            normalized_catalog_type
        )
        entry = self.catalog_repository.upsert_entry(
            source_version="manual",
            catalog_type=normalized_catalog_type,
            catalog_number=next_number,
            document={
                **normalized_values,
                "slug": slug,
                "catalog_type": normalized_catalog_type,
                "catalog_number": next_number,
                "source_version": "manual",
                "source_filename": "manual_entry",
                "source_origin": "manual",
                "source_row_hash": "",
                "is_active": True,
                "created_at": timestamp,
                "updated_at": timestamp,
            },
        )

        normalized_alg_impl_id = str(alg_impl_id or "").strip()
        if normalized_alg_impl_id:
            alg_impl_spec = self.get_algorithm_implementation(normalized_alg_impl_id)
            self.catalog_repository.update_entry_admin_fields(
                str(entry["id"]),
                {
                    "implementation_id": normalized_alg_impl_id,
                    "implementation_catalog_ref": str(
                        alg_impl_spec.get("catalog_ref", "")
                    ).strip(),
                    "implementation_source": "manual",
                    "implementation_confidence": 1.0,
                    "implementation_mapping_notes": (
                        "algorithm_catalog: manually assigned implementation"
                    ),
                    "review_state": "not_reviewed",
                    "implementation_mapping_reason": "manual implementation assignment",
                    "implementation_builder_name": str(
                        alg_impl_spec.get("builder_name", "")
                    ),
                    "implementation_builder_module": str(
                        alg_impl_spec.get("builder_module", "")
                    ),
                    "implementation_source_file": str(
                        alg_impl_spec.get("builder_source_file", "")
                    ),
                    "updated_at": timestamp,
                },
            )

        return self.get_catalog_entry(str(entry["id"]))

    def _normalize_catalog_update_values(
        self, values: dict[str, Any]
    ) -> dict[str, Any]:
        editable_text_fields = {
            "name",
            "category",
            "subcategory",
            "advanced_label",
            "best_use_horizon",
            "core_idea",
            "typical_inputs",
            "signal_style",
            "extended_implementation_details",
            "initial_reference",
            "implementation_decision",
            "implementation_notes",
            "admin_annotations",
        }
        normalized: dict[str, Any] = {}
        for field_name in editable_text_fields:
            normalized[field_name] = str(values.get(field_name, "")).strip()
        if not normalized["name"]:
            raise ValueError("Algorithm name cannot be empty.")
        try:
            score = int(values.get("home_suitability_score", 0))
        except (TypeError, ValueError) as exc:
            raise ValueError("Home suitability score must be an integer.") from exc
        if score < 0 or score > 10:
            raise ValueError("Home suitability score must be between 0 and 10.")
        normalized["home_suitability_score"] = score
        return normalized

    def get_algorithm_implementation(self, alg_key: str) -> dict[str, Any]:
        return _spec_to_dict(get_alert_algorithm_spec_by_key(alg_key))

    def _find_catalog_entry_by_alg_impl_id(
        self, alg_impl_id: str
    ) -> dict[str, Any] | None:
        for entry in self.catalog_repository.list_active_entries():
            if str(entry.get("implementation_id", "")).strip() == alg_impl_id:
                return entry
        return None

    def _list_merged_catalog_entries(self) -> list[dict[str, Any]]:
        entries = [
            dict(entry) for entry in self.catalog_repository.list_active_entries()
        ]
        linked_algorithm_ids = {
            str(entry.get("implementation_id", "")).strip()
            for entry in entries
            if str(entry.get("implementation_id", "")).strip()
        }
        for spec in self.list_algorithm_implementations():
            spec_key = str(spec.get("key", "")).strip()
            if not spec_key or spec_key in linked_algorithm_ids:
                continue
            entries.append(self._build_runtime_only_entry(spec))
        return entries

    def _build_runtime_only_entry_by_alg_impl_id(
        self, alg_impl_id: str
    ) -> dict[str, Any] | None:
        normalized_id = str(alg_impl_id).strip()
        if not normalized_id:
            return None
        if self._find_catalog_entry_by_alg_impl_id(normalized_id) is not None:
            return None
        try:
            spec = self.get_algorithm_implementation(normalized_id)
        except ValueError:
            return None
        return self._build_runtime_only_entry(spec)

    def _build_runtime_only_entry(self, spec: dict[str, Any]) -> dict[str, Any]:
        alg_impl_id = str(spec.get("key", "")).strip()
        name = str(spec.get("name", alg_impl_id)).strip() or alg_impl_id
        return {
            "id": f"runtime-only::{alg_impl_id}",
            "slug": f"runtime-only-{_slugify(alg_impl_id)}",
            "catalog_type": "algorithm",
            "catalog_number": "—",
            "name": name,
            "category": str(spec.get("category", "")).strip(),
            "subcategory": str(spec.get("subcategory", "")).strip(),
            "advanced_label": "Runtime only",
            "best_use_horizon": "",
            "home_suitability_score": 0,
            "core_idea": str(spec.get("description", "")).strip(),
            "typical_inputs": ", ".join(
                str(item) for item in spec.get("input_domains", [])
            ),
            "signal_style": str(spec.get("runtime_kind", "")).strip(),
            "extended_implementation_details": str(spec.get("description", "")).strip(),
            "initial_reference": str(spec.get("catalog_ref", "")).strip(),
            "source_version": "runtime_only",
            "source_origin": "runtime_only",
            "source_filename": "not present in catalog",
            "source_path": "",
            "source_row_hash": "",
            "is_active": True,
            "implementation_id": alg_impl_id,
            "implementation_catalog_ref": str(spec.get("catalog_ref", "")).strip(),
            "implementation_source": "runtime_only",
            "implementation_confidence": 1.0,
            "implementation_mapping_notes": (
                "algorithm_catalog: runtime implementation has no catalog entry"
            ),
            "implementation_mapping_reason": "runtime-only implementation",
            "implementation_builder_name": str(spec.get("builder_name", "")).strip(),
            "implementation_builder_module": str(
                spec.get("builder_module", "")
            ).strip(),
            "implementation_source_file": str(
                spec.get("builder_source_file", "")
            ).strip(),
            "review_state": "",
            "implementation_decision": "",
            "implementation_notes": "",
            "admin_annotations": "",
            "created_at": "",
            "updated_at": "",
            "is_readonly": True,
        }

    def _build_catalog_summary(self, entry: dict[str, Any]) -> dict[str, Any]:
        alg_impl_id = str(entry.get("implementation_id", "")).strip()
        alg_impl_spec = _safe_get_alg_impl_spec(alg_impl_id)
        implementation_status = _compute_implementation_status(entry, alg_impl_spec)
        execution_status = _execution_status(implementation_status)
        source_origin = str(entry.get("source_origin", "")).strip()
        source_path = str(entry.get("source_path", "")).strip()
        source_filename = str(entry.get("source_filename", "")).strip()
        return {
            "id": entry["id"],
            "slug": entry["slug"],
            "catalog_type": entry["catalog_type"],
            "catalog_number": entry["catalog_number"],
            "name": entry["name"],
            "category": entry["category"],
            "advanced_label": entry["advanced_label"],
            "best_use_horizon": entry["best_use_horizon"],
            "home_suitability_score": entry["home_suitability_score"],
            "core_idea": entry["core_idea"],
            "implementation_status": implementation_status,
            "implementation_label": _implementation_label(implementation_status),
            "execution_status": execution_status,
            "execution_label": _execution_label(execution_status),
            "is_runnable": execution_status == "runnable",
            "alg_impl_id": alg_impl_id or None,
            "origin_label": _origin_label(source_origin),
            "source_origin": source_origin,
            "source_file_label": _source_file_label(
                source_origin, source_path, source_filename
            ),
            "source_file_value": source_path or source_filename,
            "runtime_source_file": str(
                entry.get("implementation_source_file", "")
            ).strip(),
            "is_readonly": bool(entry.get("is_readonly", False)),
            "alg_impl_status": None
            if alg_impl_spec is None
            else alg_impl_spec["status"],
        }

    def _build_catalog_detail(self, entry: dict[str, Any]) -> dict[str, Any]:
        summary = self._build_catalog_summary(entry)
        alg_impl_id = str(entry.get("implementation_id", "")).strip()
        alg_impl_spec = _safe_get_alg_impl_spec(alg_impl_id)
        alg_impl_link = None
        if alg_impl_id:
            alg_impl_link = {
                "alg_impl_id": alg_impl_id,
                "catalog_ref": entry.get("implementation_catalog_ref", ""),
                "match_type": entry.get("implementation_source", ""),
                "match_confidence": entry.get("implementation_confidence", 0.0),
                "notes": entry.get("implementation_mapping_notes", ""),
                "review_state": entry.get("review_state", ""),
                "confirmed_by": "",
                "confirmed_at": "",
                "match_reason": entry.get("implementation_mapping_reason", ""),
            }
        return {
            **summary,
            "subcategory": entry.get("subcategory", ""),
            "typical_inputs": entry.get("typical_inputs", ""),
            "signal_style": entry.get("signal_style", ""),
            "extended_implementation_details": entry.get(
                "extended_implementation_details", ""
            ),
            "initial_reference": entry.get("initial_reference", ""),
            "source_version": entry.get("source_version", ""),
            "source_origin": entry.get("source_origin", ""),
            "source_filename": entry.get("source_filename", ""),
            "source_path": entry.get("source_path", ""),
            "implementation_decision": entry.get("implementation_decision", ""),
            "implementation_notes": entry.get("implementation_notes", ""),
            "admin_annotations": entry.get("admin_annotations", ""),
            "last_import_timestamp": entry.get("updated_at", ""),
            "link_source_label": _link_source_label(
                str(entry.get("implementation_source", ""))
            ),
            "implementation_builder_name": entry.get("implementation_builder_name", ""),
            "implementation_builder_module": entry.get(
                "implementation_builder_module", ""
            ),
            "implementation_source_file": entry.get("implementation_source_file", ""),
            "review_state_label": _review_state_label(
                ""
                if alg_impl_link is None
                else str(alg_impl_link.get("review_state", ""))
            ),
            "alg_impl_link": alg_impl_link,
            "alg_impl_spec": alg_impl_spec,
        }

    def _filter_catalog_items(
        self,
        items: list[dict[str, Any]],
        *,
        implementation_status: str | None,
        review_state: str | None,
        only_broken: bool,
        only_unresolved: bool,
        category: str | None,
        catalog_type: str | None,
        advanced_label: str | None,
        search_text: str | None,
        linked: bool | None,
    ) -> list[dict[str, Any]]:
        filtered = items
        if implementation_status:
            filtered = [
                item
                for item in filtered
                if item["implementation_status"] == implementation_status
            ]
        if review_state:
            filtered = [
                item
                for item in filtered
                if (item.get("alg_impl_link") or {}).get("review_state") == review_state
            ]
        if only_broken:
            filtered = [
                item
                for item in filtered
                if item["implementation_status"] == "broken_link"
            ]
        if only_unresolved:
            filtered = [item for item in filtered if _is_unresolved_status(item)]
        if category:
            filtered = [item for item in filtered if item["category"] == category]
        if catalog_type:
            filtered = [
                item for item in filtered if item["catalog_type"] == catalog_type
            ]
        if advanced_label:
            filtered = [
                item
                for item in filtered
                if item.get("advanced_label") == advanced_label
            ]
        if linked is not None:
            filtered = [
                item
                for item in filtered
                if (item.get("alg_impl_id") is not None) == linked
            ]
        if search_text:
            normalized = search_text.strip().lower()
            filtered = [
                item
                for item in filtered
                if any(
                    normalized in candidate
                    for candidate in _searchable_catalog_strings(item)
                )
            ]
        return filtered


def _safe_get_alg_impl_spec(alg_impl_id: str) -> dict[str, Any] | None:
    if not alg_impl_id:
        return None
    try:
        return _spec_to_dict(get_alert_algorithm_spec_by_key(alg_impl_id))
    except ValueError:
        return None


def _compute_implementation_status(
    entry: dict[str, Any], alg_impl_spec: dict[str, Any] | None
) -> str:
    if not str(entry.get("implementation_id", "")).strip():
        return "not_implemented"
    if str(entry.get("source_origin", "")) == "runtime_only":
        return "implementation_needs_review"
    if str(entry.get("review_state", "")) == "deferred":
        return "deferred"
    if str(entry.get("review_state", "")) == "rejected":
        return "not_implemented"
    if alg_impl_spec is None:
        return "broken_link"
    if str(entry.get("review_state", "")) in {
        "not_reviewed",
        "needs_review",
        "suggested",
    }:
        return "implementation_needs_review"
    return "implemented"


def _implementation_label(status: str) -> str:
    return {
        "implemented": "Approved",
        "not_implemented": "Not implemented",
        "deferred": "Deferred",
        "broken_link": "Broken link",
        "implementation_needs_review": "Runnable · needs review",
    }.get(status, "Unknown")


def _execution_status(implementation_status: str) -> str:
    return {
        "implemented": "runnable",
        "implementation_needs_review": "runnable",
        "broken_link": "broken_link",
    }.get(implementation_status, "not_runnable")


def _execution_label(execution_status: str) -> str:
    return {
        "runnable": "Runnable",
        "not_runnable": "Not runnable",
        "broken_link": "Broken link",
    }.get(execution_status, "Unknown")


def _link_source_label(match_type: str | None) -> str:
    return {
        "manual": "Manual",
        "normalized_name": "Normalized name",
        "exact_name": "Exact name",
        "curated_alias": "Curated alias",
        "suggested": "Suggested",
        "runtime_declared": "Implementation declared",
        "runtime_only": "Runtime only",
    }.get(match_type or "", "Unlinked")


def _origin_label(source_origin: str) -> str:
    return {
        "manual": "Manual",
        "imported": "Imported",
        "runtime_only": "Runtime only",
    }.get(source_origin, "Unknown")


def _source_file_label(
    source_origin: str, source_path: str, source_filename: str
) -> str:
    if source_origin == "imported":
        return "Catalog file"
    if source_origin == "manual":
        return "Catalog file"
    if source_origin == "runtime_only":
        return "Catalog file"
    if source_path or source_filename:
        return "Catalog file"
    return "Source file"


def _review_state_label(review_state: str) -> str:
    return {
        "not_reviewed": "Not reviewed",
        "confirmed": "Confirmed",
        "suggested": "Suggested",
        "needs_review": "Needs review",
        "rejected": "Rejected",
        "deferred": "Deferred",
    }.get(review_state, "Not reviewed")


def _is_unresolved_status(item: dict[str, Any]) -> bool:
    return item.get("implementation_status") in {
        "not_implemented",
        "broken_link",
        "implementation_needs_review",
    }


def _searchable_catalog_strings(item: dict[str, Any]) -> list[str]:
    alg_impl_link = item.get("alg_impl_link")
    alg_impl_spec = item.get("alg_impl_spec")

    searchable_values: list[object] = [
        item.get("id"),
        item.get("slug"),
        item.get("catalog_type"),
        item.get("catalog_number"),
        item.get("name"),
        item.get("category"),
        item.get("subcategory"),
        item.get("advanced_label"),
        item.get("best_use_horizon"),
        item.get("home_suitability_score"),
        item.get("core_idea"),
        item.get("typical_inputs"),
        item.get("signal_style"),
        item.get("extended_implementation_details"),
        item.get("initial_reference"),
        item.get("source_version"),
        item.get("implementation_decision"),
        item.get("implementation_notes"),
        item.get("admin_annotations"),
        item.get("implementation_status"),
        item.get("implementation_label"),
        item.get("alg_impl_id"),
        item.get("alg_impl_status"),
        item.get("link_source_label"),
        item.get("review_state_label"),
        item.get("last_import_timestamp"),
    ]

    if isinstance(alg_impl_link, dict):
        searchable_values.extend(
            [
                alg_impl_link.get("alg_impl_id"),
                alg_impl_link.get("catalog_ref"),
                alg_impl_link.get("match_type"),
                alg_impl_link.get("match_confidence"),
                alg_impl_link.get("notes"),
                alg_impl_link.get("review_state"),
                alg_impl_link.get("confirmed_by"),
                alg_impl_link.get("confirmed_at"),
                alg_impl_link.get("match_reason"),
            ]
        )

    if isinstance(alg_impl_spec, dict):
        searchable_values.extend(
            [
                alg_impl_spec.get("key"),
                alg_impl_spec.get("name"),
                alg_impl_spec.get("description"),
                alg_impl_spec.get("category"),
                alg_impl_spec.get("family"),
                alg_impl_spec.get("subcategory"),
                alg_impl_spec.get("default_param"),
                alg_impl_spec.get("warmup_period"),
                alg_impl_spec.get("supports_buy"),
                alg_impl_spec.get("supports_sell"),
                alg_impl_spec.get("version"),
                alg_impl_spec.get("status"),
                alg_impl_spec.get("asset_scope"),
                alg_impl_spec.get("runtime_kind"),
                alg_impl_spec.get("catalog_ref"),
                alg_impl_spec.get("tags"),
                alg_impl_spec.get("input_domains"),
                alg_impl_spec.get("output_modes"),
                alg_impl_spec.get("composition_roles"),
            ]
        )

    return [
        _normalize_searchable_value(value)
        for value in searchable_values
        if value is not None
    ]


def _normalize_searchable_value(value: object) -> str:
    if isinstance(value, str):
        return value.lower()
    if isinstance(value, Iterable) and not isinstance(value, bytes):
        return " ".join(_normalize_searchable_value(item) for item in value)
    return str(value).lower()


def _slugify(value: str) -> str:
    normalized = "".join(
        char.lower() if char.isalnum() else "-" for char in value.strip()
    )
    while "--" in normalized:
        normalized = normalized.replace("--", "-")
    return normalized.strip("-")


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _spec_to_dict(spec: Any) -> dict[str, Any]:
    return {
        "key": spec.key,
        "name": spec.name,
        "description": spec.description,
        "param_schema": list(spec.param_schema),
        "category": spec.category,
        "family": spec.family,
        "subcategory": spec.subcategory,
        "tags": list(spec.tags),
        "default_param": spec.default_param,
        "warmup_period": spec.warmup_period,
        "supports_buy": spec.supports_buy,
        "supports_sell": spec.supports_sell,
        "version": spec.version,
        "status": spec.status,
        "input_domains": list(spec.input_domains),
        "asset_scope": spec.asset_scope,
        "output_modes": list(spec.output_modes),
        "runtime_kind": spec.runtime_kind,
        "composition_roles": list(spec.composition_roles),
        "catalog_ref": spec.catalog_ref,
        "builder_name": spec.builder_name,
        "builder_module": spec.builder_module,
        "builder_source_file": spec.builder_source_file,
    }
