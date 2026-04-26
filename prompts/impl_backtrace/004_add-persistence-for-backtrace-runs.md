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

