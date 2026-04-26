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

