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

