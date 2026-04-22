# DB-Backed Algorithm Catalog Build Plan

## Goal

Build a first-class algorithm catalog in the dashboard that:

- stores the enriched algorithm library in MongoDB
- shows all cataloged algorithms, not only currently implemented ones
- clearly indicates whether each algorithm is implemented in the current codebase
- supports a compact browseable list plus on-demand rich details
- uses the markdown file `docs/algorithm_library_requirements_enriched_v2.md` as an import source, not as the runtime page source

## Product outcome

After implementation, the dashboard should provide:

1. a catalog page for all algorithms and composite methodologies
2. filters and search for fast discovery
3. a clear implementation status badge per row
4. AJAX-loaded rich details for heavy fields like implementation notes
5. an admin-driven import/sync workflow from the enriched markdown document into MongoDB

---

## 1. Current state summary

### What exists now

- `/algorithms` already exists in the dashboard
- the current catalog service only exposes registered runtime alert algorithms
- the current page only shows lightweight runtime metadata
- the API endpoint `/api/algorithms` already returns implemented algorithm specs from the runtime registry

### What is missing

- there is no DB-backed algorithm library domain model
- there is no representation of algorithms that are planned but not implemented
- there is no import pipeline from the enriched requirements document
- there is no mapping layer between catalog rows and runtime algorithm keys
- there is no rich details interaction model for heavy fields

---

## 2. Target architecture

The solution should have three separate concerns:

1. **Catalog content**  
   Stored in MongoDB and imported from the enriched markdown document.

2. **Runtime implementation metadata**  
   Derived live from the installed `trading_algos` registry.

3. **Catalog-to-runtime linkage**  
   Stored explicitly so catalog items can be matched accurately to runtime algorithms.

This avoids mixing documentation content, implementation facts, and UI concerns into one model.

---

## 3. Domain model

### 3.1 Collection: `algorithm_catalog_entries`

One document per row from the imported catalog.

Recommended fields:

- `id`
- `catalog_type`
  - `algorithm`
  - `composite_methodology`
- `catalog_number`
- `name`
- `slug`
- `category`
- `subcategory`
- `advanced_label`
- `best_use_horizon`
- `home_suitability_score`
- `core_idea`
- `typical_inputs`
- `signal_style`
- `extended_implementation_details`
- `initial_reference`
- `source_version`
- `source_path`
- `source_row_hash`
- `is_active`
- `created_at`
- `updated_at`

### 3.2 Collection: `algorithm_catalog_links`

Stores the mapping between a catalog entry and a runtime implementation key.

Recommended fields:

- `id`
- `catalog_entry_id`
- `runtime_key`
- `match_type`
  - `manual`
  - `exact_name`
  - `normalized_name`
  - `suggested`
  - `unlinked`
- `match_confidence`
- `notes`
- `created_at`
- `updated_at`

### 3.3 Collection: `algorithm_catalog_import_runs`

Tracks imports for auditability and operational visibility.

Recommended fields:

- `id`
- `source_version`
- `source_path`
- `status`
- `started_at`
- `completed_at`
- `rows_seen`
- `rows_created`
- `rows_updated`
- `rows_unchanged`
- `rows_deactivated`
- `warnings`

---

## 4. Source-of-truth rules

### Catalog content source of truth

MongoDB becomes the runtime source of truth for catalog content.

### Runtime implementation source of truth

The `trading_algos` runtime registry remains the source of truth for:

- algorithm existence
- runtime key
- runtime status
- parameter schema
- warmup period
- input domains
- asset scope
- output modes
- runtime kind
- composition roles

### Import source

`docs/algorithm_library_requirements_enriched_v2.md` is the import input, not the runtime page source.

---

## 5. Implementation status model

Implementation status should be computed dynamically at read time.

### Status rules

- `implemented`  
  A link exists and the linked runtime key exists in the current registry.

- `not_implemented`  
  No link exists for the catalog entry.

- `broken_link`  
  A link exists but the runtime key is no longer present in the registry.

- `implementation_needs_review`  
  A suggested or low-confidence link exists but has not been confirmed.

### Displayed UI badge

The UI may simplify these into:

- Implemented
- Not implemented
- Needs review

---

## 6. Import pipeline design

Build a dedicated import service that parses the markdown document and upserts DB records.

### Import responsibilities

1. read the markdown file
2. extract the main algorithm table
3. extract the composite methodologies table
4. normalize each row into a typed internal record
5. upsert `algorithm_catalog_entries`
6. preserve stable identity using source version plus catalog number and slug
7. create import run records
8. optionally generate suggested runtime links

### Upsert behavior

For imported rows:

- match existing records by `source_version + catalog_number`
- fallback by `slug` if needed
- update content fields from source
- keep manual linkage records stable unless explicitly overwritten by admin action

### Removal behavior

If a previously imported row no longer appears in the source:

- mark `is_active = false`
- do not hard-delete by default

---

## 7. Matching and linkage strategy

Do not rely purely on name matching.

### Matching priority

1. manual link override
2. exact normalized-name match
3. curated mapping table for known exceptions
4. optional low-confidence suggestion
5. unresolved remains unlinked

### Why explicit linkage is necessary

The enriched document names and runtime keys do not always align exactly. A separate link model prevents incorrect implementation claims.

---

## 8. Repository and service design

### 8.1 New repositories

Create:

- `src/trading_algos_dashboard/repositories/algorithm_catalog_repository.py`
- `src/trading_algos_dashboard/repositories/algorithm_catalog_link_repository.py`
- `src/trading_algos_dashboard/repositories/algorithm_catalog_import_run_repository.py`

Responsibilities:

- Mongo CRUD and query logic
- filtering, sorting, pagination support
- stable collection access patterns

### 8.2 New services

Create:

- `src/trading_algos_dashboard/services/algorithm_catalog_import_service.py`
- expand `src/trading_algos_dashboard/services/algorithm_catalog_service.py`

#### `algorithm_catalog_import_service`

Responsibilities:

- parse markdown tables
- normalize source rows
- upsert entries
- write import run summary
- create or refresh link suggestions

#### `algorithm_catalog_service`

Responsibilities:

- read catalog entries from DB
- merge entries with link records and runtime registry metadata
- compute implementation status
- return summary list models and detail models for UI and API

---

## 9. API design

### Read endpoints

- `GET /algorithms`  
  Server-rendered catalog page.

- `GET /api/algorithms/catalog`  
  Returns catalog summaries, filterable by query params.

- `GET /api/algorithms/catalog/<entry_id>`  
  Returns rich detail payload for one catalog item.

### Admin endpoints

- `POST /administration/algorithm-catalog/import`
- `GET /administration/algorithm-catalog/imports`
- `POST /administration/algorithm-catalog/<entry_id>/link`
- `DELETE /administration/algorithm-catalog/<entry_id>/link`

If admin UI is deferred, the import action can initially exist only as a service or CLI-triggered action, but the architecture should allow later exposure in the dashboard.

---

## 10. UI design

### 10.1 Catalog list page

Upgrade `/algorithms` into a real browseable catalog.

Each row or card should show compact summary information:

- catalog number
- algorithm name
- category
- best use / horizon
- home suitability score
- advanced label
- implementation badge
- runtime key if implemented
- short core idea preview
- details action

### 10.2 Filters and search

Support at least:

- text search
- category filter
- implementation status filter
- advanced label filter
- home suitability filter
- catalog type filter

### 10.3 Detail interaction model

Heavy fields should be shown on demand.

Recommended pattern:

- user clicks a row or “Details” button
- frontend fetches detail JSON from `/api/algorithms/catalog/<entry_id>`
- details render in a Bootstrap offcanvas or modal

### 10.4 Detail content

The detail panel should show:

#### Catalog section

- name
- category
- advanced label
- best use / horizon
- home suitability
- core idea
- typical inputs
- signal style
- extended implementation details
- initial reference

#### Implementation section

- implementation status
- runtime key
- runtime name
- runtime status
- input domains
- asset scope
- output modes
- runtime kind
- composition roles
- param schema
- default params
- warmup period

### 10.5 Hover guidance

Use hover only for lightweight hints like badge explanations or score legends. Do not use hover as the main surface for long implementation details.

---

## 11. Administration workflow

Add a lightweight algorithm catalog admin area under Administration.

### Initial admin needs

- import catalog from markdown
- review latest import results
- inspect unlinked entries
- manually assign or correct runtime link mappings
- inspect broken links

### Recommended rollout

Admin UI can be phased in after the import and browse experience works end to end.

---

## 12. Proposed file changes

### Create

- `docs/algorithm_catalog_db_backed_build_plan.md`
- `src/trading_algos_dashboard/repositories/algorithm_catalog_repository.py`
- `src/trading_algos_dashboard/repositories/algorithm_catalog_link_repository.py`
- `src/trading_algos_dashboard/repositories/algorithm_catalog_import_run_repository.py`
- `src/trading_algos_dashboard/services/algorithm_catalog_import_service.py`
- `src/trading_algos_dashboard/static/js/algorithm_catalog.js`

### Update

- `src/trading_algos_dashboard/services/algorithm_catalog_service.py`
- `src/trading_algos_dashboard/blueprints/algorithms.py`
- `src/trading_algos_dashboard/blueprints/api.py`
- `src/trading_algos_dashboard/blueprints/administration.py`
- `src/trading_algos_dashboard/templates/algorithms/list.html`
- `src/trading_algos_dashboard/templates/algorithms/detail.html`
- `src/trading_algos_dashboard/templates/administration/index.html`
- `src/trading_algos_dashboard/templates/base.html`
- `src/trading_algos_dashboard/static/css/app.css`
- `src/trading_algos_dashboard/app.py`
- relevant tests under `tests/dashboard/`

---

## 13. Implementation phases

### Phase 1: Domain and persistence

- define catalog entry, link, and import-run document shapes
- add Mongo repositories
- wire repositories into app factory/extensions

### Phase 2: Import pipeline

- implement markdown table parsing
- normalize source rows
- upsert DB records
- record import summaries

### Phase 3: Merge and read model

- merge DB entries with link data and runtime registry metadata
- compute implementation status
- expose summary and detail payloads from the catalog service

### Phase 4: Catalog UI

- redesign `/algorithms` list page
- add search and filters
- add status badges and summary layout

### Phase 5: AJAX details

- add JSON detail endpoint
- add frontend JS to fetch detail payloads
- render offcanvas or modal details

### Phase 6: Admin operations

- add import trigger in administration
- add simple review tooling for imports and links

### Phase 7: Verification

- add parser/import tests
- add repository/service tests
- add route tests
- add UI response tests for detail endpoint behavior

---

## 14. Testing plan

### Import tests

- parses the main table correctly
- parses the composite table correctly
- preserves catalog numbers and source fields
- deactivates removed rows correctly

### Merge tests

- implemented entry merges runtime metadata correctly
- unlinked entry shows not implemented
- broken runtime link shows broken status

### Route and API tests

- `/algorithms` renders full catalog list
- `/api/algorithms/catalog` returns filtered summaries
- `/api/algorithms/catalog/<entry_id>` returns rich detail payload
- admin import route reports import result correctly

### UI behavior tests

- implemented badge appears correctly
- not-implemented badge appears correctly
- detail endpoint payload supports long-form fields

---

## 15. Definition of done

The feature is complete when:

- the enriched catalog is stored in MongoDB
- the catalog page shows all imported entries, including not-yet-implemented ones
- each item clearly shows implementation status
- the user can browse summary data quickly
- the user can open rich on-demand details without page clutter
- the system can re-import updated source documents cleanly
- the architecture supports future manual link curation and catalog editing

---

## 16. Recommended first implementation scope

For the first working version, prioritize:

1. DB collections and repositories
2. markdown importer
3. merged catalog service
4. upgraded `/algorithms` page
5. AJAX-loaded detail endpoint and panel

Defer if necessary:

- full admin review UI
- advanced import diff previews
- inline catalog editing
- fuzzy-match review tools

---

## 17. Suggested commit summary

Add a DB-backed algorithm catalog build plan covering import, persistence, linkage, and dashboard UX.