# Repository Guidelines

## Project Structure and Module Organization
- `rqalpha/` is the main package; core engine code is under `rqalpha/core/`, and built-in mods under `rqalpha/mod/`.
- `rqalpha/examples/`, `strategy_test/`, and `test_strategy/` provide sample strategies/configs.
- `tests/` is split into `tests/unittest/` and `tests/integration_tests/`; docs live in `docs/`.

## Architecture Overview (for Agent Onboarding)
- The engine is event-driven: `rqalpha/core/executor.py` consumes events and publishes them through `rqalpha/core/events.py`.
- Strategy lifecycle hooks live in `rqalpha/core/strategy.py` (`init`, `before_trading`, `handle_bar`, `handle_tick`, `open_auction`, `after_trading`) with pre/post phases for mod hooks.
- `rqalpha/environment.py` is the runtime registry for core services (data proxy/source, broker, portfolio, mods).
- Extension contracts are defined in `rqalpha/interface.py`; new data/execution integrations should implement these.

## Build, Test, and Development Commands
- `pip install -e .` installs the package and `rqalpha` CLI.
- `rqalpha run -f path/to/strategy.py -s YYYY-MM-DD -e YYYY-MM-DD` runs a backtest.
- `make -C docs html` builds documentation locally.

## Coding Style and Naming Conventions
- Follow PEP 8: 4-space indentation, `snake_case` functions/variables, `CapWords` classes, `UPPER_SNAKE_CASE` constants.
- Keep APIs, errors, and type hints consistent with existing `rqalpha/` modules.

## Testing Guidelines
- Use `pytest`; run `pytest tests` for the full suite.
- Unit tests target individual modules under `tests/unittest/`.
- Integration tests under `tests/integration_tests/` run full backtests via `rqalpha.run_func`.
- Pattern to follow (see `tests/integration_tests/test_backtest_results/`): define strategy callbacks in-test, build a `config` dict, and use `run_and_assert_result` to compare outputs against `outs/*.txt`.
- If not explicitly told otherwise, prefer strategy-style integration tests that exercise the full framework with real data. Agents may read bundle data or call `rqdatac` to pick concrete instruments and dates.

## Commit and Pull Request Guidelines
- Recent commits use imperative, sentence-case summaries (e.g., "Refactor ...", "Fix ...", "Update ..."). Keep messages short and scoped.
- PRs should describe the change, link related issues if any, and include test results or rationale when tests are not run.

## Agent-Specific Pointers
- Entry points: `rqalpha/__main__.py`, `rqalpha/cmds/run.py`, and `rqalpha/main.py`.
- For strategy behavior: `rqalpha/core/strategy.py` and `rqalpha/core/events.py`.
- For data/instruments: `rqalpha/data/` and `rqalpha/interface.py`; for orders/portfolio: `rqalpha/portfolio/` and `rqalpha/mod/rqalpha_mod_sys_accounts/`.

## Documentation and Data Notes
- Update `docs/` when public behavior changes.
- Data access and strategy behavior are tightly coupled to RQAlpha/RQData; avoid changing data contracts without migration notes.
