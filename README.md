Trading Algos

This repository contains reusable trading-oriented algorithm libraries, with `alertgen` focused on generating buy/sell/neutral alerts from market candles.

## Repository boundary

`trading_algos` should own reusable algorithm logic, algorithm registration, parameter normalization, and algorithm instantiation.

Runtime engine envelopes and application wiring such as:

- alertgen/decmaker engine payload defaults,
- smarttrade-specific execution configuration,
- smarttrade-backed dashboard/runtime integration,

belong in the consuming application layer, not in this library package.

There is still a `src/trading_algos_dashboard` package in this repository today, but it is intentionally treated as smarttrade-coupled application code and is a candidate to move into the smarttrade project.

## Alertgen direction

`alertgen` is structured around `BaseAlertAlgorithm`, which acts as the base contract for concrete alert algorithms. The goal is to grow this into a large library of trading algorithms that can be mixed, validated, evaluated, and composed consistently.

### Recent framework improvements

- `BaseAlertAlgorithm` is now an abstract base class with a clearer extension contract.
- Algorithm creation now flows through a registry/catalog instead of a hardcoded factory chain.
- Algorithm specs now expose richer library metadata such as family, asset scope, input domains, output modes, runtime kind, and composition roles.
- Built-in algorithms expose structured metadata via registered specs.
- Default config and validation now resolve supported algorithms from the shared registry.
- Typed alert domain models now exist for candles, decisions, metadata, and report payloads.
- Evaluation and report serialization logic are separated from the base algorithm class.
- Compatibility aliases were added while improving naming and composition metadata incrementally.
- Built-in alert algorithms now use descriptive strategy names instead of numbered `alg###` class/module names.

### Adding a new alert algorithm

1. Implement a new subclass of `BaseAlertAlgorithm`.
2. Define its prediction logic in `trend_prediction_logic()`.
3. Place it under the correct family package in `src/trading_algos/alertgen/algorithms/`.
4. Register it in the matching family `catalog.py` with:
   - stable key/name
   - family/subcategory
   - parameter normalizer
   - default parameter
   - description/tags
   - input domains / asset scope / output modes / composition roles
5. Use `list_alert_algorithm_specs()` to inspect available algorithms programmatically.

See `docs/algorithm_authoring_guide.md` for the expected authoring flow.

### Config migration note

`alertgen` now supports a string-based algorithm identifier via `alg_key`.

- Use `"alg_key": "close_high_channel_breakout"`.
- Use dict-shaped `alg_param`, for example `{"window": 20}`.

Numeric `alg_code` identifiers have been removed from the config contract and registry lookup flow.
Scalar/list `alg_param` formats are also removed from the config contract; built-in algorithms now use named dict parameters.

The library-level config contract is intentionally limited to per-algorithm execution inputs such as `alg_key`, `alg_param`, `symbol`, `buy`, and `sell`. Higher-level engine payload wrappers should be defined by the consuming application.

This keeps extension work localized and avoids editing a growing `if/elif` factory by hand.

## Configuration graphs

`trading_algos.configuration` provides a declarative graph model for reusable algorithm configurations.

Supported node types:
- `algorithm`
- `and`
- `or`
- `pipeline`

Current limitation:
- `pipeline` is supported in the schema and validation layer, but runtime execution is intentionally not implemented yet.

Primary entry points:
- `configuration_from_dict()`
- `configuration_to_dict()`
- `validate_configuration_payload()`
- `evaluate_configuration_compatibility()`
- `run_configuration_graph()`
- `evaluate_configuration_graph()`

Minimal example:

```python
from trading_algos.configuration import run_configuration_graph

configuration = {
    "config_key": "close-high-basic",
    "version": "1.0.0",
    "name": "Close High Basic",
    "root_node_id": "alg-1",
    "nodes": [
        {
            "node_id": "alg-1",
            "node_type": "algorithm",
            "alg_key": "close_high_channel_breakout",
            "alg_param": {"window": 20},
            "buy_enabled": True,
            "sell_enabled": True,
        }
    ],
}

result = run_configuration_graph(
    configuration=configuration,
    symbol="AAPL",
    report_base_path="/tmp/trading_algos_reports",
    candles=[
        {"ts": "2026-01-01 10:00:00", "Open": 10, "High": 11, "Low": 9, "Close": 10.5},
        {"ts": "2026-01-01 10:01:00", "Open": 10.5, "High": 11.5, "Low": 10, "Close": 11},
    ],
)
```

Composite AND example:

```python
configuration = {
    "config_key": "breakout-confirmed",
    "version": "1.0.0",
    "name": "Breakout Confirmed",
    "root_node_id": "group-1",
    "nodes": [
        {
            "node_id": "alg-1",
            "node_type": "algorithm",
            "alg_key": "close_high_channel_breakout",
            "alg_param": {"window": 20},
            "buy_enabled": True,
            "sell_enabled": True,
        },
        {
            "node_id": "alg-2",
            "node_type": "algorithm",
            "alg_key": "low_anchored_boundary_breakout",
            "alg_param": {"period": 5},
            "buy_enabled": True,
            "sell_enabled": True,
        },
        {
            "node_id": "group-1",
            "node_type": "and",
            "children": ["alg-1", "alg-2"],
        },
    ],
}
```

Compatibility metadata can optionally declare package expectations such as `expected_package_version`, `minimum_supported_version`, `maximum_supported_version`, and referenced algorithms.

### Testing expectations for algorithms

The test suite now covers a reusable baseline contract for registered alert algorithms:

- registry exposure and factory creation
- typed metadata and decision access
- flat-candle and short-history handling
- evaluation metric population
- aggregate/composition metadata and behavior
- validation and reporting helper behavior

When adding new algorithms, extend these shared expectations before relying only on algorithm-specific tests.
