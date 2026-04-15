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

## Before running Python commands
- Check whether `.venv` exists.
- If `.venv` does not exist, tell me clearly and suggest the exact command to create it.
- If a command fails because a package is missing, use `./.venv/bin/python -m pip ...`, not global pip.

## When running tests:
- Not always tests are correct, so if test is failing can be because of test itself or because of code that is being tested so see which one is really the root cause.

## Before reaching to conclusion that task is done
- once again check that requirements are fully implemented.
- run test fast tests and make sure they pass.

## when concluded that tast is done
- make sure no linting issues so run ruff to check and fix. 
- make sure no ruff format issue. check and if you find any fix it.
- run mypy and make sure it is happy.

## when all changes are done, 
Produce 1 short sentence for summarizing what is done in this task so that can be used as comment for git commit.

## Notes
- Do not rely on `source .venv/bin/activate` as the only mechanism.
- Explicit interpreter paths are preferred for reliability.

=