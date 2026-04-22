from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

from trading_algos_dashboard.repositories.algorithm_catalog_import_run_repository import (
    AlgorithmCatalogImportRunRepository,
)
from trading_algos_dashboard.repositories.algorithm_catalog_repository import (
    AlgorithmCatalogRepository,
)


class AlgorithmCatalogImportService:
    def __init__(
        self,
        *,
        catalog_repository: AlgorithmCatalogRepository,
        import_run_repository: AlgorithmCatalogImportRunRepository,
        default_source_version: str = "uploaded_algorithm_catalog",
    ):
        self.catalog_repository = catalog_repository
        self.import_run_repository = import_run_repository
        self.default_source_version = default_source_version

    def import_catalog(
        self,
        *,
        content: str,
        source_filename: str,
        source_content_type: str | None = None,
        source_version: str | None = None,
    ) -> dict[str, Any]:
        effective_source_version = source_version or _derive_source_version(
            source_filename, self.default_source_version
        )
        started_at = _utc_now()
        rows = self._parse_source(
            content,
            source_filename=source_filename,
            source_version=effective_source_version,
        )
        if not rows:
            raise ValueError(
                "algorithm_catalog_import: import rejected; reason=no_supported_rows_found"
            )
        active_keys: set[tuple[str, int]] = set()
        created = 0
        updated = 0
        unchanged = 0
        created_entry_ids: list[str] = []
        updated_entry_ids: list[str] = []
        unchanged_entry_ids: list[str] = []
        existing_by_key = {
            (
                str(item.get("catalog_type", "")),
                int(item.get("catalog_number", 0)),
            ): item
            for item in self.catalog_repository.list_active_entries()
            if item.get("source_version") == effective_source_version
        }
        for row in rows:
            row_key = (str(row["catalog_type"]), int(row["catalog_number"]))
            active_keys.add(row_key)
            existing = existing_by_key.get(row_key)
            stored = self.catalog_repository.upsert_entry(
                source_version=effective_source_version,
                catalog_type=str(row["catalog_type"]),
                catalog_number=int(row["catalog_number"]),
                document=row,
            )
            if existing is None:
                created += 1
                created_entry_ids.append(str(stored["id"]))
            elif _content_hash(existing) == _content_hash(stored):
                unchanged += 1
                unchanged_entry_ids.append(str(stored["id"]))
            else:
                updated += 1
                updated_entry_ids.append(str(stored["id"]))
        deactivated_entry_ids = self._collect_deactivated_entry_ids(
            active_keys, source_version=effective_source_version
        )
        deactivated = self.catalog_repository.mark_missing_entries_inactive(
            source_version=effective_source_version,
            active_keys=active_keys,
            updated_at=started_at,
        )
        completed_at = _utc_now()
        run = self.import_run_repository.create_run(
            {
                "source_version": effective_source_version,
                "source_filename": source_filename,
                "source_content_type": source_content_type
                or "application/octet-stream",
                "source_format": _detect_source_format(source_filename),
                "status": "completed",
                "started_at": started_at,
                "completed_at": completed_at,
                "rows_seen": len(rows),
                "rows_created": created,
                "rows_updated": updated,
                "rows_unchanged": unchanged,
                "rows_deactivated": deactivated,
                "warnings": [],
                "links_written": 0,
                "created_entry_ids": created_entry_ids,
                "updated_entry_ids": updated_entry_ids,
                "unchanged_entry_ids": unchanged_entry_ids,
                "deactivated_entry_ids": deactivated_entry_ids,
                "unresolved_entry_ids": [],
                "preserved_manual_link_entry_ids": [],
                "changed_link_entry_ids": [],
            }
        )
        return run

    def _parse_source(
        self, content: str, *, source_filename: str, source_version: str
    ) -> list[dict[str, Any]]:
        tables = re.findall(r"<table>(.*?)</table>", content, flags=re.DOTALL)
        entries: list[dict[str, Any]] = []
        for index, table in enumerate(tables[:2]):
            for cells in _extract_rows(table):
                number_text = _strip_html(cells[0])
                if not number_text.isdigit():
                    continue
                name = _strip_html(cells[2])
                catalog_type = "algorithm" if index == 0 else "composite_methodology"
                entries.append(
                    {
                        "catalog_type": catalog_type,
                        "catalog_number": int(number_text),
                        "name": name,
                        "slug": _slugify(name),
                        "category": _strip_html(cells[1]),
                        "subcategory": "",
                        "advanced_label": _strip_html(cells[3]),
                        "best_use_horizon": _strip_html(cells[4]),
                        "home_suitability_score": _parse_score(cells[5]),
                        "core_idea": _strip_html(cells[6]),
                        "typical_inputs": _strip_html(cells[7]),
                        "signal_style": _strip_html(cells[8]),
                        "extended_implementation_details": _strip_html(cells[9]),
                        "initial_reference": _strip_html(cells[10]),
                        "source_version": source_version,
                        "source_filename": source_filename,
                        "source_origin": "imported",
                        "source_row_hash": hashlib.sha256(
                            "|".join(_strip_html(cell) for cell in cells).encode(
                                "utf-8"
                            )
                        ).hexdigest(),
                        "is_active": True,
                        "created_at": _utc_now(),
                        "updated_at": _utc_now(),
                    }
                )
        return entries

    def _collect_deactivated_entry_ids(
        self, active_keys: set[tuple[str, int]], *, source_version: str
    ) -> list[str]:
        deactivated_entry_ids: list[str] = []
        for document in self.catalog_repository.list_entries_for_source_version(
            source_version
        ):
            entry_key = (
                str(document.get("catalog_type", "")),
                int(document.get("catalog_number", 0)),
            )
            if entry_key in active_keys:
                continue
            if document.get("is_active", True):
                deactivated_entry_ids.append(str(document.get("id", "")))
        return deactivated_entry_ids


def _extract_rows(table_html: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for row_html in re.findall(r"<tr>(.*?)</tr>", table_html, flags=re.DOTALL):
        cells = re.findall(r"<td>(.*?)</td>", row_html, flags=re.DOTALL)
        if len(cells) == 11:
            rows.append(cells)
    return rows


def _strip_html(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", value)
    text = text.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", text).strip()


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return normalized.strip("-")


def _parse_score(value: str) -> int:
    digits = re.sub(r"\D+", "", _strip_html(value))
    return int(digits or "0")


def _derive_source_version(source_filename: str, fallback: str) -> str:
    normalized = _slugify(source_filename.rsplit(".", 1)[0])
    return normalized or fallback


def _detect_source_format(source_filename: str) -> str:
    if "." not in source_filename:
        return "unknown"
    return source_filename.rsplit(".", 1)[1].lower()


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _content_hash(document: dict[str, Any]) -> str:
    relevant = {
        key: value
        for key, value in document.items()
        if key not in {"id", "created_at", "updated_at"}
    }
    return hashlib.sha256(repr(sorted(relevant.items())).encode("utf-8")).hexdigest()
