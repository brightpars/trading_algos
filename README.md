Trading Algos

This repository contains reusable trading-oriented algorithm libraries, with `alertgen` focused on generating buy/sell/neutral alerts from market candles.

## Dashboard MVP

This repository now also contains a lightweight Flask dashboard package at `src/trading_algos_dashboard` for:

- browsing registered alert algorithms,
- launching experiment runs against smarttrade-backed market data,
- comparing algorithm outputs,
- reviewing saved reports and experiment history persisted in MongoDB.

### Run the dashboard

1. Ensure MongoDB is available.
2. Ensure the smarttrade repository is available at `/home/mohammad/development/smarttrade` or set `SMARTTRADE_PATH`.
3. Install dashboard dependencies into the project venv.
4. Run with:

```bash
./.venv/bin/python -m flask --app trading_algos_dashboard.app:create_app run
```

Or use the helper launcher:

```bash
bash /home/mohammad/development/trading_algos/scripts/run_dashboard.sh
```

The helper script sets `PYTHONPATH` to the repo `src/` directory automatically so the dashboard package can be imported without installing the project first.
By default, it starts the dashboard on port `2000`.

Useful environment variables:

- `TRADING_ALGOS_DASHBOARD_MONGO_URI`
- `TRADING_ALGOS_DASHBOARD_MONGO_DB`
- `TRADING_ALGOS_DASHBOARD_REPORT_PATH`
- `SMARTTRADE_PATH`
- `TRADING_ALGOS_DASHBOARD_SMARTTRADE_USER_ID`

## Alertgen direction

`alertgen` is structured around `BaseAlertAlgorithm`, which acts as the base contract for concrete alert algorithms. The goal is to grow this into a large library of trading algorithms that can be mixed, validated, evaluated, and composed consistently.

### Recent framework improvements

- `BaseAlertAlgorithm` is now an abstract base class with a clearer extension contract.
- Algorithm creation now flows through a registry/catalog instead of a hardcoded factory chain.
- Built-in algorithms expose structured metadata via registered specs.
- Default config and validation now resolve supported algorithms from the shared registry.
- Typed alert domain models now exist for candles, decisions, metadata, and report payloads.
- Evaluation and report serialization logic are separated from the base algorithm class.
- Compatibility aliases were added while improving naming and composition metadata incrementally.
- Built-in alert algorithms now use descriptive strategy names instead of numbered `alg###` class/module names.

### Adding a new alert algorithm

1. Implement a new subclass of `BaseAlertAlgorithm`.
2. Define its prediction logic in `trend_prediction_logic()`.
3. Register it in `src/trading_algos/alertgen/core/catalog.py` with:
   - stable key/name
   - parameter normalizer
   - default parameter
   - description/tags
4. Use `list_alert_algorithm_specs()` to inspect available algorithms programmatically.

### Config migration note

`alertgen` now supports a string-based algorithm identifier via `alg_key`.

- Use `"alg_key": "close_high_channel_breakout"`.
- Use dict-shaped `alg_param`, for example `{"window": 20}`.

Numeric `alg_code` identifiers have been removed from the config contract and registry lookup flow.
Scalar/list `alg_param` formats are also removed from the config contract; built-in algorithms now use named dict parameters.

This keeps extension work localized and avoids editing a growing `if/elif` factory by hand.

### Testing expectations for algorithms

The test suite now covers a reusable baseline contract for registered alert algorithms:

- registry exposure and factory creation
- typed metadata and decision access
- flat-candle and short-history handling
- evaluation metric population
- aggregate/composition metadata and behavior
- validation and reporting helper behavior

When adding new algorithms, extend these shared expectations before relying only on algorithm-specific tests.
