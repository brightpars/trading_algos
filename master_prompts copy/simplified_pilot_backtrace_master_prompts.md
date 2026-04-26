# Simplified Pilot Backtrace Master Prompts

## PROMPT: create backtrace contracts and runtime service
You are working in the repository `/home/mohammad/development/trading_algos`.

Goal:
Create the core application-layer service and typed contracts for a simplified “pilot-like” backtrace run that will later be exposed through `engines_control`. In this round, do **not** wire XML-RPC yet, do **not** add persistence, and do **not** add dashboard routes/UI.

Context:
- This repo already has a dashboard and a stub `engines_control` runtime in `src/trading_algos_dashboard/service_runtime.py`.
- We want a simplified pilot concept: run algorithms locally and inspect outputs, without broker integration.
- There is already algorithm execution capability elsewhere in the dashboard codebase, but in this round you should only create the service skeleton and stable request/result contracts.
- Follow repo rules: use small changes, clean architecture, no backward-compat shims, no dead wrappers, explicit types.

What to build:
1. Add a new typed model module for simplified backtrace request/result contracts.
2. Add a new runtime service module for engines-control-driven backtrace execution.
3. The runtime service must validate and normalize incoming requests.
4. The runtime service should expose a method like `run_backtrace(request: dict[str, Any]) -> dict[str, Any]`.
5. In this round, execution can be placeholder/stubbed, but the returned result shape must be stable and future-proof.

Required request contract:
- `algorithm_key`: required string
- `algorithm_params`: optional dict, default `{}`
- `symbol`: required string
- `candles`: required list of dicts
- `buy`: optional bool, default `True`
- `sell`: optional bool, default `True`
- `request_id`: optional string
- `report_base_path`: optional string
- `metadata`: optional dict

Expected candle fields:
- `ts`
- `Open`
- `High`
- `Low`
- `Close`
- optional `Volume`

Required result shape:
- `status`: `completed` or `failed`
- `run_id`: string
- `request_id`: string or null
- `algorithm_key`: string
- `symbol`: string
- `input_summary`: dict
- `result_payload`: dict
- `error`: string or null
- `started_at`: string timestamp
- `finished_at`: string timestamp

Behavior requirements:
- Validate required fields explicitly.
- Normalize defaults explicitly.
- Fail clearly on malformed requests.
- Keep transport-friendly plain dict outputs.
- Do not introduce XML-RPC concerns into this service.

Suggested files:
- `src/trading_algos_dashboard/services/backtrace_models.py`
- `src/trading_algos_dashboard/services/engines_control_runtime_service.py`
- `tests/dashboard/test_engines_control_runtime_service.py`

Testing requirements:
- Add tests for valid request normalization.
- Add tests for missing required fields.
- Add tests for invalid candle payload shape.
- Add tests ensuring result payload shape is stable.

Important constraints:
- No broker integration.
- No data fetching from external/data services.
- No persistence.
- No API routes/UI.
- No async execution.

Before finishing:
- Run the smallest relevant tests.
- Run ruff check.
- Run ruff format check.
- Run mypy.
- Use the project venv explicitly: `./.venv/bin/python ...`

Deliverable:
A cleanly typed runtime service and backtrace contract foundation ready to be wired into `engines_control` in the next round.

## PROMPT: wire backtrace into engines_control xml-rpc server
You are working in `/home/mohammad/development/trading_algos`.

Goal:
Wire the simplified backtrace runtime service into the existing `engines_control` server so it exposes a real XML-RPC method for backtrace execution.

Assumptions:
- Round 1 has already created:
  - typed backtrace request/result contracts
  - `EnginesControlRuntimeService`
- The existing file `src/trading_algos_dashboard/service_runtime.py` currently contains `DashboardEnginesControlServer` with stub methods.

What to build:
1. Add a real XML-RPC method `run_backtrace(request)` to `DashboardEnginesControlServer`.
2. Register that method in `register_all_functions()`.
3. Delegate all business logic to `EnginesControlRuntimeService`.
4. Keep XML-RPC layer thin and transport-only.
5. Preserve existing service startup behavior.

Implementation requirements:
- `run_backtrace(request)` must call `reject_if_shutting_down()`.
- It must pass the request to the runtime service.
- It must return a plain dict result that is XML-RPC-safe.
- Keep error handling explicit and clean.
- Do not move business logic into the XML-RPC class.

Suggested files to update:
- `src/trading_algos_dashboard/service_runtime.py`
- tests around service runtime behavior, likely under `tests/dashboard/`

Testing requirements:
- Add tests that the method is registered.
- Add tests that `run_backtrace()` delegates to the runtime service.
- Add tests that the returned payload is dict-based and stable.
- Add tests for failure behavior on invalid input.

Constraints:
- No real algorithm execution yet unless already provided by Round 1.
- No persistence.
- No dashboard HTTP API.
- No UI work.
- No broker integration.

Architecture rule:
This round is about transport wiring only. Keep it clean, minimal, and self-contained.

Before finishing:
- Run the smallest relevant tests.
- Run `./.venv/bin/python -m ruff check .`
- Run `./.venv/bin/python -m ruff format . --check`
- Run `./.venv/bin/python -m mypy .`

Deliverable:
A working `engines_control` XML-RPC endpoint exposing `run_backtrace(request)` and delegating to the runtime service.

## PROMPT: execute one alert algorithm through backtrace flow
You are working in `/home/mohammad/development/trading_algos`.

Goal:
Make the `engines_control` backtrace flow actually execute one alert algorithm using existing local runner logic, with inline candle payloads only.

Assumptions:
- Round 1 created request/result contracts and `EnginesControlRuntimeService`.
- Round 2 exposed `run_backtrace(request)` on `DashboardEnginesControlServer`.
- There is existing algorithm execution support in the dashboard codebase, including `run_alert_algorithm` and related evaluation/report generation.

What to build:
1. Update `EnginesControlRuntimeService` so `run_backtrace(request)` executes a real algorithm run.
2. Reuse the existing algorithm runner rather than inventing a new pipeline.
3. Support a single algorithm per request.
4. Support inline candles only.
5. Return normalized output including report/evaluation/chart information.

Expected input:
- `algorithm_key`
- `algorithm_params`
- `symbol`
- `candles`
- optional `buy` / `sell`

Expected output fields:
- `status`
- `run_id`
- `request_id`
- `algorithm_key`
- `symbol`
- `input_summary`
- `signal_summary`
- `evaluation_summary`
- `report`
- `chart_payload`
- `execution_steps`
- `error`
- `started_at`
- `finished_at`

Implementation notes:
- Reuse `run_alert_algorithm` if that is the correct current entrypoint.
- If a tiny extraction/helper is needed for reuse, do it cleanly.
- Do not create a parallel algorithm execution stack.
- Short-history behavior should remain consistent with current runner behavior.

Suggested files to update:
- `src/trading_algos_dashboard/services/engines_control_runtime_service.py`
- possibly `src/trading_algos_dashboard/services/algorithm_runner_service.py`
- tests in `tests/dashboard/`

Testing requirements:
- Success case with inline candles.
- Invalid algorithm key failure case.
- Short-input-history case.
- Result shape assertions for report/evaluation/chart payloads.

Constraints:
- No broker integration.
- No persistence yet.
- No HTTP API yet.
- No UI yet.
- No data-source fetching.
- No batching.

Before finishing:
- Run targeted tests.
- Run ruff check.
- Run ruff format check.
- Run mypy.
- Use `./.venv/bin/python` explicitly.

Deliverable:
A real synchronous simplified backtrace execution path through `engines_control`, for one alert algorithm with inline candles.

## PROMPT: add persistence for backtrace runs
You are working in `/home/mohammad/development/trading_algos`.

Goal:
Add persistence for simplified backtrace runs so each run request and its result can be inspected later from the dashboard.

Assumptions:
- Previous rounds already support synchronous `engines_control.run_backtrace(request)` execution.
- The app already uses Mongo-backed repositories in other dashboard areas.

What to build:
1. Add a repository for persisted backtrace sessions/results.
2. Persist each run’s lifecycle and outputs.
3. Integrate persistence into the backtrace runtime service.
4. Keep execution synchronous.

Suggested persisted document fields:
- `run_id`
- `request_id`
- `status`
- `algorithm_key`
- `symbol`
- `request`
- `input_summary`
- `result_summary`
- `full_result`
- `error`
- `created_at`
- `started_at`
- `finished_at`

Behavior requirements:
- Save an initial record when the run starts.
- Update it on success with completed outputs.
- Update it on failure with failed status and error.
- Provide repository methods to get one run and list recent runs.

Suggested files:
- `src/trading_algos_dashboard/repositories/backtrace_session_repository.py`
- `src/trading_algos_dashboard/services/engines_control_runtime_service.py`
- `src/trading_algos_dashboard/app.py`
- tests under `tests/dashboard/`

Testing requirements:
- Repository save/load behavior.
- Runtime service persists success result.
- Runtime service persists failure result.
- List/detail retrieval behavior.

Constraints:
- No UI yet.
- No dashboard HTTP API yet.
- No async queueing.
- No broker integration.

Architecture guidance:
- Keep persistence concerns in repository layer.
- Keep runtime service orchestrating repository calls.
- Do not bury Mongo logic in XML-RPC or route handlers.

Before finishing:
- Run targeted tests.
- Run ruff check.
- Run ruff format check.
- Run mypy.

Deliverable:
Persisted backtrace session records for every engines_control run, with retrievable detail and history.

## PROMPT: expose backtrace through dashboard http api
You are working in `/home/mohammad/development/trading_algos`.

Goal:
Expose the simplified backtrace feature through dashboard HTTP API endpoints for submit, list, and detail.

Assumptions:
- Previous rounds already provide:
  - `engines_control.run_backtrace(request)`
  - persisted backtrace session/results
- The dashboard already has existing blueprint/API patterns you should follow.

What to build:
1. Add an API endpoint to submit a backtrace run.
2. Add an API endpoint to list backtrace runs.
3. Add an API endpoint to fetch one backtrace run by id.
4. The dashboard should remain the user-facing orchestration layer.

Preferred endpoint shape:
- `POST /api/backtraces`
- `GET /api/backtraces`
- `GET /api/backtraces/<run_id>`

POST payload should support:
- `algorithm_key`
- `algorithm_params`
- `symbol`
- `candles`
- optional metadata

Implementation guidance:
- Route handlers should be thin.
- Use a dedicated service/client helper if needed to call `engines_control` cleanly.
- Reuse repository layer for list/detail reads.
- Keep responses JSON and stable.

Suggested files:
- `src/trading_algos_dashboard/blueprints/api.py`
- optional new service helper such as `src/trading_algos_dashboard/services/backtrace_client_service.py`
- `src/trading_algos_dashboard/app.py`
- tests under `tests/dashboard/`

Testing requirements:
- Submit success case.
- Submit validation failure case.
- List runs case.
- Detail run case.
- If service calling is abstracted, mock cleanly and test route behavior.

Constraints:
- No UI yet.
- No data-source-backed input yet.
- No batching.
- No broker integration.

Before finishing:
- Run targeted tests.
- Run ruff check.
- Run ruff format check.
- Run mypy.

Deliverable:
Dashboard API endpoints for creating and inspecting simplified backtrace runs.

## PROMPT: build dashboard ui for simplified backtrace
You are working in `/home/mohammad/development/trading_algos`.

Goal:
Build a simple dashboard UI to manually submit a simplified backtrace run and inspect its result.

Assumptions:
- Previous rounds already implemented:
  - HTTP API for submit/list/detail
  - engines_control-backed backtrace execution
  - persistence of results

What to build:
1. Add a dashboard page for backtrace submission.
2. Add a dashboard page or detail section for viewing a backtrace result.
3. Optionally add a run list page if it improves usability.
4. Keep the UI simple and functional.

UI input fields:
- algorithm key
- symbol
- params JSON
- candles JSON textarea
- optional metadata JSON

Result view should show:
- status
- algorithm key
- symbol
- input summary
- signal/evaluation summary
- execution steps
- diagnostics / error if any
- report/chart summary
- optional raw JSON section

Suggested files:
- blueprint update or new blueprint under `src/trading_algos_dashboard/blueprints/`
- templates under `src/trading_algos_dashboard/templates/backtraces/`
- optional JS under `src/trading_algos_dashboard/static/js/`
- tests under `tests/dashboard/`

Behavior guidance:
- Keep route handlers thin.
- Use API/service layer rather than embedding runtime logic in templates/routes.
- Do not mention broker/execution server concepts in UI.

Testing requirements:
- GET page render tests.
- POST/submit flow tests.
- Result detail page tests.
- Validation/error rendering tests.

Constraints:
- No data-source-backed input yet.
- No batching.
- No async queueing.
- No broker integration.

Before finishing:
- Run targeted tests.
- Run ruff check.
- Run ruff format check.
- Run mypy.

Deliverable:
A usable dashboard UI for manual simplified backtrace runs and result inspection.

## PROMPT: support data-source-backed candle input
You are working in `/home/mohammad/development/trading_algos`.

Goal:
Extend the simplified backtrace flow so requests can use a data-source reference and time range instead of requiring inline candles.

Assumptions:
- Inline-candle backtrace flow already works.
- The dashboard already has data source service patterns that can likely be reused.

What to build:
1. Extend request contract to support either:
   - inline candles, or
   - a data source reference with symbol/time-range parameters
2. Resolve candles before algorithm execution.
3. Keep single-algorithm synchronous execution.

Constraints:
- Preserve existing inline candle path.
- Validate that exactly one input mode is used.
- No broker integration.
- No batching in this round.

Testing:
- Inline mode still works.
- Data-source mode works.
- Invalid mixed/missing modes fail clearly.

Deliverable:
Backtrace requests can use either inline candles or data-source-backed candle retrieval.

## PROMPT: support batch backtrace execution
You are working in `/home/mohammad/development/trading_algos`.

Goal:
Extend the simplified backtrace feature to support executing multiple algorithm runs in one request.

Assumptions:
- Single-run backtrace execution already works.
- Persistence and API/UI already exist.

What to build:
1. Add batch request/result contracts.
2. Reuse the single-run runtime service internally rather than duplicating logic.
3. Support multiple algorithms and/or multiple symbols/requests in one submission.
4. Return per-item success/failure results.

Constraints:
- Keep failures isolated per item.
- Preserve single-run API if already present.
- No broker integration.
- No async queueing unless absolutely necessary.

Testing:
- Multi-item success case.
- Mixed success/failure case.
- Stable aggregated result shape.

Deliverable:
A batch-capable simplified backtrace feature built on top of the single-run path.
