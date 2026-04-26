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

