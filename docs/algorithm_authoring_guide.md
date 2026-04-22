# Algorithm Authoring Guide

Use this guide when adding a new algorithm to the library.

## Authoring flow

1. Place the implementation under the correct family package in `src/trading_algos/alertgen/algorithms/`.
2. Register the algorithm in the matching family `catalog.py` module.
3. Define a rich spec with a required `catalog_ref`, family, subcategory, input domains, output modes, and composition roles.
4. Reuse shared validation helpers and keep `alg_param` machine-readable.
5. Ensure the algorithm can produce normalized output via `BaseAlertAlgorithm.normalized_output()`.
6. Add or extend tests that verify catalog exposure and parameter schema behavior.

## Family layout

- `trend/`
- `momentum/`
- `mean_reversion/`
- `stat_arb/`
- `volatility/`
- `patterns/`
- `microstructure/`
- `execution/`
- `composite/`

## Required metadata

Every algorithm spec should define at least:

- stable `key`
- human-readable `name`
- stable `catalog_ref` in the form `<catalog_type>:<catalog_number>` such as `algorithm:6`
- `family`
- `subcategory`
- `description`
- `default_param`
- `param_schema`
- `input_domains`
- `asset_scope`
- `output_modes`
- `composition_roles`

## Output contract

Algorithms should remain compatible with the current alert pipeline, but should also support normalized output for future composition and dashboard use:

- `buy` / `sell` / `neutral` signal label
- optional confidence
- optional score
- optional reason codes / event markers

## Testing expectations

At minimum, new algorithms should verify:

- registration succeeds
- catalog serialization exposes the spec correctly
- params validate with defaults
- execution handles short history sanely