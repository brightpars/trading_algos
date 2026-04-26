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

