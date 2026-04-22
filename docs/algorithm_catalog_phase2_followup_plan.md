t t# Algorithm Catalog Phase 2 Follow-Up Plan

## Goal

Extend the DB-backed algorithm catalog with the operational and curation tooling needed to maintain catalog quality over time.

Phase 1 delivered:

- DB-backed catalog persistence
- markdown import pipeline
- computed implementation status
- upgraded catalog UI
- AJAX detail loading
- basic admin import support

Phase 2 focuses on the missing admin and review workflows.

---

## 1. Phase 2 objectives

Phase 2 should make the catalog:

1. reviewable
2. manually correctable
3. operationally observable
4. safer to maintain as the document and runtime registry evolve

---

## 2. Main workstreams

### 2.1 Manual link management UI

Add a dedicated admin catalog management page where an operator can inspect and change the mapping between imported catalog rows and runtime algorithm keys.

#### Required features

- show current catalog entry metadata
- show current implementation status
- show current runtime link if one exists
- allow manual link assignment
- allow replacing an existing link
- allow unlinking a catalog item
- allow marking an item as intentionally unimplemented or deferred

#### Why this matters

The importer currently creates links from a curated alias map and normalized-name matching. That is useful, but long-term correctness requires explicit operator control.

---

### 2.2 Import review dashboard

Add a dedicated review surface for import runs.

#### Required features

- latest import summary
- import history list
- counts for:
  - rows seen
  - rows created
  - rows updated
  - rows unchanged
  - rows deactivated
  - links written
- warning section

#### Nice to have

- show what changed compared with the previous import
- group changes into new, changed, removed/deactivated

---

### 2.3 Unresolved-link review workflow

Add a queue-style admin view for entries that need attention.

#### Review states to support

- not implemented
- broken link
- needs review
- auto-linked
- manually linked

#### Each row should show

- catalog number
- catalog type
- name
- category
- implementation status
- current link metadata
- suggested runtime matches if available
- actions

---

### 2.4 Broken-link diagnostics

Add a focused view for cases where a stored link points to a runtime key that no longer exists.

#### Show

- catalog entry
- stored runtime key
- match type
- latest import timestamp
- available replacement suggestions

#### Actions

- relink
- unlink
- mark for review

---

### 2.5 Better matching assistance

Keep manual confirmation as the source of truth, but improve suggestion quality.

#### Matching inputs

- normalized exact-name match
- alias map
- token overlap on names
- category-aware suggestions
- curated exception map

#### Output

- top candidate list per unresolved entry
- confidence score
- match reason text

#### Important rule

Suggested matches must not silently become authoritative implementation links unless explicitly confirmed.

---

### 2.6 Catalog detail transparency improvements

Expose more curation metadata in catalog detail views.

#### Add fields

- link source: manual / normalized / suggested
- confidence
- link notes
- last import timestamp
- source version
- review state

This makes implemented/not-implemented status explainable to both admins and normal users.

---

### 2.7 Server-side query improvements

Move beyond mostly client-side filtering for administration use cases.

#### Add query support for

- implementation status
- category
- catalog type
- advanced label
- linked/unlinked
- text search
- only broken links
- only unresolved items

This will make the admin pages more scalable and easier to work with.

---

## 3. Domain model additions

The existing collections can remain, but Phase 2 should enrich the link model.

### 3.1 `algorithm_catalog_links`

Add or standardize these fields if not already present:

- `review_state`
  - `confirmed`
  - `suggested`
  - `needs_review`
  - `rejected`
- `confirmed_by`
- `confirmed_at`
- `rejected_at`
- `rejection_reason`
- `match_reason`

### 3.2 Optional catalog-level override fields

Potential future additions on the catalog entry itself:

- `implementation_decision`
  - `implemented`
  - `planned`
  - `intentionally_unimplemented`
- `implementation_notes`

This is useful if some items should remain cataloged but intentionally not linked.

---

## 4. Service changes

### 4.1 `AlgorithmCatalogService`

Extend it to support:

- filtered admin queries
- candidate suggestion generation
- unresolved-entry summaries
- broken-link summaries
- richer detail payloads with review metadata

### 4.2 `AlgorithmCatalogImportService`

Extend it to:

- preserve confirmed manual links on re-import
- write suggested candidates separately from confirmed links
- optionally record previous-vs-current diffs

### 4.3 `AdministrationService`

Extend it to:

- expose import history and latest import summary
- expose unresolved-link queues
- expose broken-link queues
- process link create/update/delete operations

---

## 5. Blueprint and API changes

### 5.1 Administration routes

Add routes such as:

- `GET /administration/algorithm-catalog`
- `POST /administration/algorithm-catalog/<entry_id>/link`
- `POST /administration/algorithm-catalog/<entry_id>/unlink`
- `POST /administration/algorithm-catalog/<entry_id>/review-state`
- `GET /administration/algorithm-catalog/imports`

### 5.2 Admin/API endpoints

Add JSON endpoints if needed for a richer UI:

- `GET /api/algorithms/catalog/admin`
- `GET /api/algorithms/catalog/<entry_id>/candidates`
- `POST /api/algorithms/catalog/<entry_id>/link`
- `DELETE /api/algorithms/catalog/<entry_id>/link`

---

## 6. UI plan

### 6.1 Admin catalog management page

Create a dedicated page under Administration with tabs or sections for:

1. Overview
2. Unresolved entries
3. Broken links
4. Import history

### 6.2 Unresolved review table

Columns:

- catalog #
- name
- category
- current status
- current link
- top suggestion
- actions

### 6.3 Link action panel

Per entry, allow:

- select a runtime key from dropdown
- confirm link
- unlink
- mark as deferred
- save notes

### 6.4 Import history section

Show:

- run time
- status
- source version
- changed counts
- link counts

---

## 7. Suggested file changes

### Create

- `docs/algorithm_catalog_phase2_followup_plan.md`
- `src/trading_algos_dashboard/templates/administration/algorithm_catalog.html`
- `src/trading_algos_dashboard/static/js/administration_algorithm_catalog.js`
- `tests/dashboard/test_algorithm_catalog_admin_routes.py`

### Update

- `src/trading_algos_dashboard/blueprints/administration.py`
- `src/trading_algos_dashboard/blueprints/api.py`
- `src/trading_algos_dashboard/services/administration_service.py`
- `src/trading_algos_dashboard/services/algorithm_catalog_service.py`
- `src/trading_algos_dashboard/services/algorithm_catalog_import_service.py`
- `src/trading_algos_dashboard/repositories/algorithm_catalog_link_repository.py`
- `src/trading_algos_dashboard/templates/administration/index.html`
- `src/trading_algos_dashboard/templates/base.html`
- `src/trading_algos_dashboard/static/css/app.css`
- relevant test files in `tests/dashboard/`

---

## 8. Recommended implementation order

### Phase 2A: Admin overview and queues

- add admin catalog page
- add unresolved and broken-link summaries
- add import history view

### Phase 2B: Manual link actions

- add create/update/delete link actions
- preserve manual confirmations on re-import

### Phase 2C: Candidate suggestions

- add runtime candidate generation
- surface suggestions in the admin UI

### Phase 2D: Import diff visibility

- show changed/new/deactivated rows between imports

### Phase 2E: Verification

- add route/service tests
- run Ruff, format, mypy, and dashboard/admin tests

---

## 9. Definition of done

Phase 2 is complete when:

- an admin can review unresolved entries
- an admin can manually assign and remove runtime links
- broken links are visible and repairable
- import runs are inspectable
- implementation status is explainable through visible link metadata
- manual curation survives re-imports correctly

---

## 10. Suggested commit summary

Add a Phase 2 plan for algorithm catalog curation, manual linking, broken-link review, and import history tooling.