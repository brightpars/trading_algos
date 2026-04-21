# New Requirements for SmartTrade and Algorithm Designer

> **Purpose:** This document summarizes the new functional and architectural requirements discussed for two separate applications:
>
> 1. **SmartTrade** - the runtime application used by end users to select algorithms/configurations and run trading/backtesting workflows.
> 2. **Algorithm Designer Dashboard** - the developer-focused application used to create, test, visualize, compare, and publish algorithm configurations.
>
> **Main goal:** Keep algorithm implementation development separate from SmartTrade, while allowing user-defined algorithm configurations to be published dynamically and consumed by SmartTrade without requiring a full Git push + SmartTrade redeployment for every configuration-level change.

## 1. High-Level Product Intent

- The algorithm implementation code itself remains independent from SmartTrade and continues to live in a Python package / Git-based development workflow.
- SmartTrade should not need knowledge of how algorithms are internally developed.
- The Algorithm Designer Dashboard should remain primarily focused on algorithm evaluation, visualization, comparison, and configuration design.
- A new concept of **publishable algorithm configuration** must be introduced.
- These published configurations must become visible and selectable in SmartTrade dynamically.
- Configuration publication should not require redeploying SmartTrade, as long as the underlying algorithm code already exists in the installed package version available to SmartTrade.

## 2. Core Domain Concepts

| Concept | Description |
|---|---|
| Algorithm | A Python-implemented trading logic unit that reads market data and emits signals such as buy / sell / neutral. |
| Algorithm Parameters | Tunable inputs specific to an algorithm instance, for example thresholds, window sizes, coefficients, or strategy flags. |
| Algorithm Configuration | A named, reusable definition that selects one or more existing algorithms, assigns parameters to them, and optionally combines them using logical/compositional rules such as AND / OR / chaining / cascade. |
| Published Configuration | A configuration that has been validated and persisted into SmartTrade-owned storage so it becomes available to runtime users. |
| Run Result / Evaluation Result | The stored output of executing an algorithm or configuration on historical data, including metrics, visualizations, and metadata. |

## 3. Architectural Direction

**Recommended direction:** Keep the source of truth for published runtime configurations inside **SmartTrade's domain**, most likely in SmartTrade's database and behind SmartTrade-owned APIs.

- The Algorithm Designer Dashboard may have its own local database for experiment history, previous runs, and developer-side metadata.
- However, the final published configuration repository should be owned by SmartTrade.
- The Algorithm Designer Dashboard should publish configurations to SmartTrade through a dedicated API.
- SmartTrade should expose APIs to list, validate, create, update, activate/deactivate, and retrieve configuration details.
- This approach keeps SmartTrade as the runtime authority while preserving separation of concerns.

## 4. Detailed Requirements - Algorithm Designer Dashboard

### 4.1 Usability and Developer Workflow

- The dashboard shall provide a developer-friendly interface to browse existing algorithms available in the installed Python package.
- The dashboard shall let the developer inspect each algorithm's metadata, expected parameters, defaults, and signal behavior.
- The dashboard shall support selecting an algorithm and running it on historical data without manually editing raw JSON files.
- The dashboard should still support JSON import/export for advanced users, debugging, and reproducibility.
- The dashboard shall allow the user to save draft configurations locally before publication.

### 4.2 Configuration Builder

- The dashboard shall introduce a first-class visual concept called **Configuration Builder**.
- The builder shall allow the developer to create a reusable named configuration from one or more algorithms.
- The developer shall be able to:
  - Choose one algorithm or multiple algorithms.
  - Assign parameters to each algorithm instance.
  - Create multiple instances of the same algorithm with different parameter sets.
  - Arrange algorithms into a logical/composite structure.
- The configuration shall support at least the following logical relationships:
  - **AND**: emit a buy/sell decision only when all required child conditions agree.
  - **OR**: emit a buy/sell decision when at least one child condition matches.
  - **Cascade / Pipeline**: run one algorithm or decision stage after another.
  - **Parallel composition**: evaluate multiple algorithms on the same data and combine outcomes.
- The model should be extensible later for NOT, weighted voting, majority voting, precedence rules, and custom combiners.
- The builder shall allow naming each configuration clearly and adding description fields, tags, notes, and intended use cases.
- The builder shall generate a machine-readable configuration payload suitable for publication to SmartTrade.

### 4.3 Visualization of Composite Configurations

- The dashboard shall visualize not only individual algorithm outputs but also composite configuration structure.
- The user should be able to see a graph, tree, or pipeline representation of how algorithms are combined.
- The dashboard shall clearly indicate where AND / OR / sequential nodes exist in the configuration.
- The user should be able to inspect the signal produced by:
  - each individual child algorithm, and
  - the final combined configuration output.
- The dashboard shall visualize buy / sell / neutral points over market data as it already does, but also distinguish source signals versus final decision signals.

### 4.4 Evaluation and Performance Analysis

- The dashboard shall support running a configuration or algorithm against historical data for a specified date/time range.
- The dashboard shall store previous run results and make them searchable in a run catalog.
- Each stored run should contain:
  - algorithm/configuration name,
  - exact parameter values,
  - algorithm package version,
  - time range used,
  - market/instrument used,
  - execution timestamp,
  - performance metrics,
  - optional notes from developer.
- The dashboard should display performance metrics beyond the visual signal markers, such as:
  - profit/loss,
  - return percentage,
  - win rate,
  - drawdown,
  - number of trades,
  - signal count,
  - buy/sell distribution,
  - stability across time windows.
- The dashboard should support running the same algorithm/configuration over multiple periods or datasets for comparison.
- The dashboard should support side-by-side comparison of:
  - two or more algorithms,
  - two or more parameter sets,
  - an individual algorithm versus a composite configuration.

### 4.5 Comparison and Experiment Tracking

- The dashboard shall provide a comparison mode where developers can compare run results visually and numerically.
- The dashboard shall make it easy to answer questions like:
  - Which parameter set performed better?
  - Did combining A AND B improve precision or reduce false positives?
  - How stable is this config across different periods?
- The dashboard should allow pinning important runs as baselines.
- The dashboard should allow promoting a successful draft configuration to a publishable version.
- The dashboard should maintain a local revision history of configuration edits.

### 4.6 Validation Before Publication

- Before publication, the dashboard shall validate that:
  - all referenced algorithms exist in the known algorithm package,
  - all required parameters are supplied,
  - parameter types are valid,
  - the configuration structure is logically valid,
  - the config has a unique or explicitly versioned publish name,
  - the target SmartTrade environment is compatible.
- The dashboard should warn the developer if the configuration depends on algorithm code that is not yet available in the SmartTrade deployment environment.

### 4.7 Publication Workflow

- The dashboard shall support an explicit **Publish Configuration** action.
- Publication shall send the configuration payload to SmartTrade via API.
- The publish flow should support:
  - creating a new published config,
  - updating an existing published config,
  - creating a new version of an existing config,
  - saving as draft only,
  - optional activation/deactivation request.
- After publication, the dashboard should display the publication result, returned config ID/version, and current publish status.

### 4.8 Non-Functional Expectations for the Dashboard

- The UI should be significantly easier than editing configuration manually through raw JSON.
- Advanced operations should remain inspectable and exportable as JSON for transparency.
- The system should be modular enough to add future composition types and future metrics.
- The run history and comparison features should remain performant as stored experiments grow.

## 5. Detailed Requirements - SmartTrade

### 5.1 Configuration Repository Ownership

- SmartTrade shall become the owner of the runtime-published configuration repository.
- SmartTrade shall persist published configurations in its own database.
- The repository shall store:
  - configuration name,
  - version,
  - description,
  - payload/definition,
  - status (draft/published/active/inactive/deprecated),
  - created by,
  - created at,
  - updated at,
  - compatibility metadata,
  - algorithm references used inside the config.

### 5.2 SmartTrade API for External Publication

- SmartTrade shall expose API endpoints for the Algorithm Designer Dashboard to publish and manage configurations.
- These APIs should support:
  - publish new config,
  - update config,
  - create new version,
  - list configs,
  - retrieve config details,
  - activate/deactivate config,
  - validate compatibility,
  - optional soft delete/deprecation.
- These APIs should be protected by authentication and authorization.

### 5.3 Runtime Discovery of Configurations

- When a SmartTrade user opens the relevant runtime dashboard, SmartTrade shall dynamically load the current list of available published configurations.
- The list shall not require a SmartTrade redeploy if only configuration data has changed.
- The runtime UI shall clearly distinguish between:
  - raw algorithms directly available in the package, and
  - published composite/user-defined configurations.
- The user shall be able to pick a published configuration by name.
- The user should be able to inspect a summary of what that configuration contains.

### 5.4 Runtime Use of Published Configurations

- SmartTrade shall be able to execute a published configuration exactly as defined by the payload stored in its repository.
- SmartTrade shall resolve all referenced algorithms from its installed algorithm package.
- If a published configuration references algorithms unavailable in the current environment, SmartTrade shall reject execution with a clear error message.
- SmartTrade should allow the runtime user to:
  - use the published configuration as-is, or
  - start from that configuration as a preset/template and override selected runtime-adjustable parameters.
- It should be configurable which parameters are locked versus runtime-editable.

### 5.5 Versioning and Compatibility

- SmartTrade shall version published configurations.
- SmartTrade shall store which algorithm package version(s) a configuration expects.
- SmartTrade should be able to mark a configuration as:
  - compatible,
  - warning, or
  - incompatible
  with the currently installed algorithm package.
- SmartTrade should avoid silent failures caused by configuration/code mismatch.

### 5.6 Governance and Lifecycle

- SmartTrade shall support status transitions such as draft, published, active, inactive, and deprecated.
- Only active/published configurations should be shown by default to runtime end users.
- Deprecated or incompatible configurations should either be hidden or visibly marked.
- SmartTrade should keep an audit trail of who published or modified each configuration.

### 5.7 Non-Functional Expectations for SmartTrade

- Configuration retrieval should be fast enough for interactive dashboard usage.
- The schema must be extensible for future combinational logic and metadata.
- The publication API should be stable and documented because it becomes a contract between the two applications.

## 6. Suggested API / Data Contract Direction

This is not a strict implementation, but a recommended direction so the coder has a clearer target.

- A published configuration payload should include:
  - config name and version,
  - human-readable description,
  - list of nodes,
  - node types (algorithm / AND / OR / pipeline stage),
  - algorithm references,
  - parameter sets per algorithm instance,
  - composition graph or tree,
  - optional runtime-overridable parameters,
  - compatibility metadata.
- The schema should be explicit enough so SmartTrade can reconstruct and execute the config reliably.
- Prefer a declarative config schema rather than executable code inside the configuration itself.

## 7. Out of Scope / Separation of Concerns

- Creating brand-new algorithm source code from scratch is still a Git/package development concern, not a runtime SmartTrade concern.
- Publishing a configuration must not be treated as publishing arbitrary Python code.
- Only configurations built from already-supported algorithm implementations should be publishable dynamically.
- The Algorithm Designer Dashboard may remain independent from SmartTrade except for the publishing/discovery API integration.

## 8. Implementation Priorities

1. **Phase 1:** Introduce configuration domain model and schema.
2. **Phase 2:** Build visual configuration builder in the Algorithm Designer Dashboard.
3. **Phase 3:** Add local save, run, compare, and history features for configurations.
4. **Phase 4:** Add SmartTrade database tables and publication APIs.
5. **Phase 5:** Add SmartTrade runtime config discovery and execution.
6. **Phase 6:** Add versioning, compatibility checks, lifecycle management, and stronger UX polish.

## 9. Acceptance Criteria Summary

- A developer can create a named composite configuration from existing algorithms without editing raw JSON manually.
- A developer can compare the new configuration against other algorithms/configurations using stored historical runs and metrics.
- A developer can publish that configuration to SmartTrade through an API.
- SmartTrade stores the published configuration in its own database.
- A SmartTrade user can later see the published configuration in the runtime dashboard without redeploying SmartTrade.
- A SmartTrade user can select and execute the published configuration.
- Configuration publication does not require changing SmartTrade code as long as the referenced algorithm implementation already exists in the installed package.
