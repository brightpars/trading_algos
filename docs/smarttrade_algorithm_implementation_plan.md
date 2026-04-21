# SmartTrade Algorithm Configuration Implementation Plan

## Purpose

This document turns the requirements in `docs/smarttrade_algorithm_requirements.md` into an implementation-ready plan across:

1. `trading_algos` package
2. `trading_algos_dashboard` application
3. external `smarttrade` application

The goal is to introduce a first-class, publishable algorithm configuration model that supports composition, local drafting/testing in the dashboard, and runtime publication/discovery in SmartTrade without redeploying SmartTrade for configuration-only changes.

---

## 1. Current State Summary

### 1.1 `trading_algos`

Current strengths:
- registry/catalog-driven alert algorithm discovery already exists
- parameter normalization already exists per algorithm spec
- single-algorithm factory and execution flow already exists
- built-in aggregate algorithms demonstrate composition needs

Current limitations:
- execution is centered on flat `sensor_config` with `alg_key` + `alg_param`
- composition is hardcoded inside specific algorithm implementations instead of represented declaratively
- no shared configuration graph schema exists
- no compatibility/version/lifecycle model exists for publishable configurations

### 1.2 `trading_algos_dashboard`

Current strengths:
- algorithm catalog API exists
- experiment running/history already exists
- result storage and chart/report display already exists
- UI already supports algorithm inspection and comparison flows

Current limitations:
- experiment input is still raw `algorithms_json`
- no first-class configuration builder exists
- no local draft/revision model exists
- no publication workflow to SmartTrade exists
- experiments store flat selected algorithms rather than a reusable configuration snapshot

### 1.3 `smarttrade`

Current strengths:
- already uses `trading_algos` package for alert generation runtime
- has runtime dashboards and analysis flows

Current limitations:
- no SmartTrade-owned repository for published configurations
- no API contract for external publication
- runtime selection still assumes direct engine/sensor configuration
- no compatibility/lifecycle/audit model for published configurations

---

## 2. Target Architecture

### 2.1 Ownership boundaries

#### `trading_algos`
Owns:
- shared declarative configuration schema
- validation rules
- configuration execution engine
- composition semantics
- compatibility checks against installed algorithm package

#### `trading_algos_dashboard`
Owns:
- local drafts and revisions
- visual configuration builder
- run/compare/history experience
- local validation before publication
- publishing configurations to SmartTrade API

#### `smarttrade`
Owns:
- published configuration storage
- lifecycle state transitions
- activation/deactivation/deprecation
- runtime discovery APIs and UI
- runtime execution from stored configuration payloads
- audit trail and compatibility status visible to users

### 2.2 Key architectural rule

Published runtime configurations must be:
- declarative JSON payloads
- stored in SmartTrade-owned persistence
- executed using the installed `trading_algos` package
- rejected if incompatible with the installed package

Published runtime configurations must **not** contain arbitrary executable Python code.

---

## 3. Shared Domain Model

## 3.1 New package area in `trading_algos`

Add a new package namespace:

- `src/trading_algos/configuration/__init__.py`
- `src/trading_algos/configuration/models.py`
- `src/trading_algos/configuration/validation.py`
- `src/trading_algos/configuration/serialization.py`
- `src/trading_algos/configuration/executor.py`
- `src/trading_algos/configuration/compatibility.py`

## 3.2 Top-level configuration model

Recommended top-level fields:

- `config_key`: stable machine key / slug
- `version`: integer or semantic version string
- `name`
- `description`
- `tags`
- `notes`
- `status`
- `root_node_id`
- `nodes`
- `runtime_overrides`
- `algorithm_package_constraints`
- `compatibility_metadata`
- `created_by`
- `created_at`
- `updated_at`

## 3.3 Node model

Support these node types initially:

- `algorithm`
- `and`
- `or`
- `pipeline`

Recommended common node fields:

- `node_id`
- `node_type`
- `name`
- `description`

Algorithm node fields:

- `alg_key`
- `alg_param`
- `buy_enabled`
- `sell_enabled`
- `runtime_editable_param_keys`

Composite node fields:

- `children`

Pipeline node fields:

- `children`
- optional future stage policy metadata

## 3.4 Compatibility metadata model

Recommended fields:

- `expected_package_name`
- `expected_package_version`
- `minimum_supported_version`
- `maximum_supported_version`
- `algorithm_refs`
- `compatibility_state`: `compatible | warning | incompatible`
- `compatibility_messages`

---

## 4. Validation Rules

Implement shared validation in `trading_algos.configuration.validation`.

### 4.1 Structural validation

- root node exists
- all referenced child node IDs exist
- graph is acyclic
- all node IDs are unique
- node types are recognized
- AND/OR nodes have at least 2 children
- pipeline nodes have at least 2 ordered children
- algorithm nodes must not declare children

### 4.2 Algorithm validation

- `alg_key` must exist in package registry
- `alg_param` must validate via existing algorithm spec normalizers
- at least one of buy/sell is enabled

### 4.3 Publication validation

- publish name/key is unique or explicitly versioned
- compatibility metadata is present
- runtime-editable parameters are a safe subset of supported params
- payload is JSON-serializable and stable

### 4.4 Compatibility validation

- all referenced algorithms exist in installed package
- package version constraints match installed package version
- algorithm param schema still matches expected normalizers

---

## 5. Execution Model

## 5.1 Execution entry points

Retain legacy single-algorithm execution support, but introduce a shared graph executor.

Recommended functions:

- `run_alert_algorithm(...)` for current single-algorithm use cases
- `run_configuration_graph(...)` for declarative graph execution
- `evaluate_configuration_graph(...)` for metrics/report assembly

## 5.2 Initial composition semantics

### Algorithm node
- instantiate underlying algorithm from registry
- process candles
- produce standard decision stream

### AND node
- buy when all children emit buy on the same candle
- sell when all children emit sell on the same candle
- otherwise neutral

### OR node
- buy when any child emits buy on the same candle
- sell when any child emits sell on the same candle
- otherwise neutral

### Pipeline node
Recommended MVP handling:
- support schema and validation immediately
- implement runtime semantics only after exact stage behavior is agreed

Reason: pipeline semantics can mean filtering, gating, enrichment, or stateful stage chaining, so they should be explicit rather than guessed.

## 5.3 Migration direction for current aggregate algorithms

Existing hardcoded aggregate algorithms should not remain the long-term composition mechanism.

Target direction:
- preserve current behavior short term
- represent aggregate strategies as normal configuration graphs over time
- avoid adding more hardcoded aggregate wrappers

---

## 6. Dashboard Implementation Plan

## 6.1 New dashboard domain objects

Add repository/service support for:

- configuration drafts
- draft revisions
- publish history
- configuration-linked experiments
- baseline-pinned experiment results

Recommended repository files:

- `src/trading_algos_dashboard/repositories/configuration_draft_repository.py`
- `src/trading_algos_dashboard/repositories/configuration_revision_repository.py`
- `src/trading_algos_dashboard/repositories/publication_record_repository.py`

Recommended services:

- `configuration_builder_service.py`
- `configuration_validation_service.py`
- `configuration_run_service.py`
- `configuration_publish_service.py`
- `configuration_revision_service.py`

## 6.2 Evolve experiment storage model

Current experiment model stores flat `selected_algorithms`.

Replace or extend with:

- `input_kind`: `single_algorithm | configuration`
- `input_snapshot`: frozen JSON payload used for execution
- `input_reference`: optional draft/config identifier
- `package_version`
- `time_range`
- `symbol`
- `notes`
- `metrics`

This keeps runs reproducible even if the draft changes later.

## 6.3 New routes/pages

Recommended pages:

- `/configurations`
- `/configurations/new`
- `/configurations/<draft_id>`
- `/configurations/<draft_id>/history`
- `/configurations/<draft_id>/publish`
- `/configurations/<draft_id>/run`

## 6.4 Builder UX phases

### MVP
- choose algorithm from catalog
- create multiple algorithm instances
- edit parameters using generated forms
- nest nodes into AND / OR groups
- edit name, description, tags, notes
- show generated JSON payload
- save draft locally

### Later enhancement
- richer drag/drop graph editor
- pipeline stage designer
- revision diff visualization
- guided compatibility warnings per environment

## 6.5 Visualization requirements

Support two complementary views:

### Structure view
- tree/graph of nodes
- explicit AND / OR / PIPELINE labels
- node summaries with key params

### Signal/result view
- child algorithm signal markers
- final composite signal markers
- separate source vs final decision overlays

## 6.6 Publication workflow in dashboard

Dashboard publish flow should:

1. validate locally
2. call SmartTrade compatibility endpoint
3. publish new or create new version
4. optionally activate/deactivate
5. store returned SmartTrade config ID/version/status locally

Config needed in dashboard app config:

- SmartTrade base URL
- auth credentials / token
- timeout
- target environment label

---

## 7. SmartTrade Implementation Plan

## 7.1 Published configuration repository

Add SmartTrade-owned persistence for published configurations.

Recommended stored fields:

- `config_id`
- `config_key`
- `version`
- `name`
- `description`
- `tags`
- `payload`
- `status`
- `compatibility_metadata`
- `algorithm_refs`
- `created_by`
- `created_at`
- `updated_at`
- `published_from`

Recommended audit collection/table:

- `published_configuration_audit_events`

Audit event fields:

- `config_id`
- `version`
- `event_type`
- `actor`
- `timestamp`
- `details`

## 7.2 SmartTrade services

Recommended services/modules:

- configuration repository service
- configuration validation service
- configuration compatibility service
- configuration lifecycle service
- configuration execution service

## 7.3 SmartTrade API contract

Recommended endpoints:

- `POST /api/algorithm-configurations/validate`
- `POST /api/algorithm-configurations`
- `PUT /api/algorithm-configurations/<config_id>`
- `POST /api/algorithm-configurations/<config_id>/versions`
- `GET /api/algorithm-configurations`
- `GET /api/algorithm-configurations/<config_id>`
- `POST /api/algorithm-configurations/<config_id>/activate`
- `POST /api/algorithm-configurations/<config_id>/deactivate`
- `POST /api/algorithm-configurations/<config_id>/deprecate`

Expected behaviors:
- list endpoints default to active/published runtime-visible configs
- compatibility result is returned explicitly
- failures are clear and non-silent
- endpoints are authenticated and authorized

## 7.4 Runtime discovery in SmartTrade UI

When runtime users open the relevant page:

- load raw package algorithms separately from published configs
- show published configs dynamically from SmartTrade storage
- no redeploy required for config-only changes
- allow inspecting summary, version, tags, and compatibility state

## 7.5 Runtime execution in SmartTrade

SmartTrade runtime should:

1. fetch stored config payload
2. validate against installed `trading_algos` package
3. apply only allowed runtime overrides
4. execute via shared config executor from the package
5. reject incompatible/missing algorithms with clear errors

---

## 8. Backlog by Phase

## Phase 1 — Shared configuration schema and validator

### `trading_algos`
- add configuration package namespace
- add typed models
- add serializer/deserializer
- add graph validation
- add compatibility evaluator
- add unit tests

### Deliverable
- stable shared config schema ready for dashboard and SmartTrade adoption

## Phase 2 — Graph execution engine

### `trading_algos`
- implement algorithm node execution
- implement AND and OR composition
- expose shared execution API
- reuse existing reporting/evaluation utilities where possible
- add tests for deterministic composition behavior

### Deliverable
- draft configurations can be run from declarative payloads

## Phase 3 — Dashboard drafts and revisions

### `trading_algos_dashboard`
- add draft repository and service
- add revision history repository and service
- add draft create/edit/detail pages
- support JSON import/export
- update experiments to store frozen config snapshots

### Deliverable
- developers can save reusable local configurations before publication

## Phase 4 — Dashboard builder MVP and local execution

### `trading_algos_dashboard`
- build visual form-based configuration builder
- show structure view
- allow run against historical data
- store richer metrics and result metadata
- support algorithm vs config comparisons

### Deliverable
- first-class configuration creation and local testing without raw JSON editing

## Phase 5 — SmartTrade repository and external API

### `smarttrade`
- add published configuration storage
- add compatibility and lifecycle services
- add external publication APIs
- add audit trail persistence
- document API contract

### Deliverable
- SmartTrade becomes source of truth for runtime-published configurations

## Phase 6 — Dashboard publication integration

### `trading_algos_dashboard`
- add SmartTrade API client
- add publish actions and status views
- record publish results locally
- support publish new / update / new version / activate / deactivate request

### Deliverable
- developer can publish a validated configuration directly from dashboard

## Phase 7 — SmartTrade runtime discovery and execution

### `smarttrade`
- add runtime picker for published configs
- display runtime config summaries
- execute stored declarative payloads
- allow safe runtime overrides where permitted

### Deliverable
- end users can select and run published configurations without SmartTrade redeploy

## Phase 8 — Governance, compatibility UX, and polish

### Both apps
- compatibility status badges
- lifecycle state UX
- revision/publish history UX
- baseline pinning
- warnings for incompatible deployments
- future extension points for NOT, weighted vote, majority vote, precedence rules

### Deliverable
- production-ready governance and user experience

---

## 9. Testing Strategy

## 9.1 `trading_algos` tests

Add tests for:
- valid/invalid configuration schema
- node reference validation
- cycle detection
- algorithm existence validation
- parameter validation via registry
- AND execution semantics
- OR execution semantics
- compatibility classification

## 9.2 `trading_algos_dashboard` tests

Add tests for:
- draft create/load/update
- revision history creation
- config run creation
- publish workflow success/failure paths
- builder form validation
- comparison pages for config results

## 9.3 `smarttrade` tests

Add tests for:
- publication API auth/authz
- create/update/new-version API behavior
- lifecycle transitions
- compatibility validation endpoint
- runtime discovery list behavior
- runtime execution success from stored payload
- runtime execution rejection for missing algorithms

## 9.4 End-to-end scenario tests

At minimum verify:

1. dashboard creates draft
2. draft validates locally
3. draft publishes to SmartTrade
4. SmartTrade stores config and exposes it immediately
5. runtime user sees config without redeploy
6. runtime user executes config successfully
7. incompatible deployment returns explicit warning/error

---

## 10. Delivery Sequence Recommendation

Recommended order:

1. shared configuration schema
2. validation and compatibility model
3. graph executor for algorithm/AND/OR
4. dashboard draft persistence
5. dashboard builder MVP
6. dashboard config execution/history integration
7. SmartTrade published-config repository and API
8. dashboard publish integration
9. SmartTrade runtime discovery/execution
10. lifecycle, audit, compatibility polish

This order minimizes risk because it establishes the shared contract before UI-heavy or integration-heavy work begins.

---

## 11. Open Decisions to Confirm Before Full Build

These items should be clarified before implementing deeper phases:

1. exact versioning format: integer vs semantic version
2. exact pipeline semantics for execution
3. which metrics are dashboard-native vs SmartTrade-native
4. which parameters are allowed to be runtime-editable
5. authentication mechanism between dashboard and SmartTrade
6. SmartTrade persistence technology and migration approach
7. whether old built-in aggregate algorithms should be migrated immediately or later

Until clarified, the safest path is:
- implement full support for `algorithm`, `and`, and `or`
- support `pipeline` at schema level first
- keep runtime overrides explicit and whitelist-based

---

## 12. Definition of Done

The implementation should be considered complete when:

- developers can create reusable composite configurations visually in dashboard
- configurations can be saved locally with revision history
- configurations can be executed and compared against historical data
- configurations can be published to SmartTrade by API
- SmartTrade stores them in SmartTrade-owned persistence
- SmartTrade users can discover them dynamically without redeploy
- SmartTrade users can execute them safely against the installed algorithm package
- compatibility mismatch is visible and never fails silently

---

## 13. Suggested Commit Comment

Add an implementation plan for shared algorithm configuration publishing, dashboard builder work, and SmartTrade runtime integration.