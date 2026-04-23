# Python environment rule

For this repository, always use the project virtual environment.

## Interpreter
- Linux/macOS: `./.venv/bin/python`
- Windows: `.\.venv\Scripts\python.exe`

## Required behavior
- Never use system `python`, `python3`, or `pip` directly.
- Never assume the shell has already activated `.venv`.
- Prefer explicit commands using the venv interpreter.

## Command patterns
- Run scripts: `./.venv/bin/python path/to/script.py`
- Run modules: `./.venv/bin/python -m <module>`
- Install packages: `./.venv/bin/python -m pip install -r requirements.txt`
- Run tests: `./.venv/bin/python -m pytest`
- Run mypy: `./.venv/bin/python -m mypy .`
- Run flask: `./.venv/bin/python -m flask run`
- Run ruff check: `./.venv/bin/python -m ruff check .`
- Run ruff fix: `./.venv/bin/python -m ruff check . --fix`
- Run ruff format check: `./.venv/bin/python -m ruff format . --check`
- Run ruff format: `./.venv/bin/python -m ruff format .`

## Before running Python commands
- Check whether `.venv` exists.
- If `.venv` does not exist, tell me clearly and suggest the exact command to create it.
- If a command fails because a package is missing, use `./.venv/bin/python -m pip ...`, not global pip.

## Patch size and number of file changes
1. Make changes in small file-by-file edits.
2. Do not attempt one large multi-file patch.
3. If multiple files need to change, edit them one at a time.

## Implementation and architecture rules
When touching a file, implementing something new, or fixing a bug/issue, always try to:
1. Do **not** preserve legacy architecture, legacy compatibility layers, transitional adapters, fallback paths, or wrapper APIs whose only purpose is backward compatibility.
2. Assume there are no old clients, no old data migrations needed, and no backward compatibility requirements.
3. Remove bad old design instead of hiding it behind adapters.
4. Favor clean boundaries, explicit ownership, and deletion of obsolete code over minimizing diff size.
5. Keep intended behavior correct, but simplify architecture aggressively where appropriate.
6. Ensure all new code is cohesive, explicit, testable, typed consistently, and aligned with the target architecture.
7. Do not leave dead code, unused indirection, duplicate pathways, temporary compatibility helpers, or parallel old/new flows behind.

## Logging and exception-handling rules
1. Use one consistent log message format across the project: `<area>: <event>; key=value key=value`
2. `debug` = detailed internal visibility, branch decisions, intermediate values, retry/polling details, verbose diagnostics; may be noisy and slower.
3. `info` = useful runtime information and notable events, less verbose than debug.
4. `important` = high-level lifecycle/state information intentionally visible on screen; use sparingly and consciously.
5. `warning` = bad/unusual situation or exception, but recovery/fallback succeeded and no major business loss occurred.
6. `error` = harmful or unhandled failure, broken assumption, or business-significant loss/failure.
7. If an exception is expected and acceptable, do **not** log it as warning/error; use debug/info or no log.
8. Do **not** log the same exception at multiple layers unless each layer adds meaningful new context.
9. Use `exc_info=True` only when stack traces are genuinely useful.
10. Remove vague log messages; every log must clearly describe the event and include useful context.
11. Avoid noisy logs in hot loops unless they are debug and intentionally diagnostic.
12. Validation failures and expected user mistakes are not system errors unless they reveal broken assumptions or security concerns.

## When running tests
- Tests are not always correct.
- If a test fails, determine whether the root cause is:
  - the test itself, or
  - the code being tested.
- Do not assume the product code is wrong just because a test fails.

## Before concluding that the task is done
- Check again that the requirements are fully implemented.
- Run the fast test suite and make sure it passes.

## Before finalizing
- Run ruff check and fix any issues found.
- Run ruff format check and fix any formatting issues found.
- Run mypy and make sure it passes.

## When all changes are done
- Produce 1 short sentence summarizing what was done in this task so it can be used as a git commit comment.

## Notes
- Do not rely on `source .venv/bin/activate` as the only mechanism.
- Explicit interpreter paths are preferred for reliability.
