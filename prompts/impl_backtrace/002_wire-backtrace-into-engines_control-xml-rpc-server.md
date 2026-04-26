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

