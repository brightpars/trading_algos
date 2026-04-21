# Dashboard Configuration Builder UI Plan

## Goal

Replace raw JSON editing on `/configurations/new` with a guided visual builder that lets users create `algorithm`, `and`, and `or` configurations without manually writing payloads.

## Current problem

The current page only provides:

- a heading
- one `Configuration JSON` textarea
- one save button

That means normal users must understand the full configuration schema before they can create a draft.

## MVP product direction

The dashboard should become a form-based builder where:

1. the user edits metadata using normal form fields
2. the user adds algorithms and groups visually
3. the browser keeps an in-memory builder state
4. the browser serializes the final JSON payload into a hidden form field on submit
5. raw JSON remains available only in an advanced, collapsible section

## Files to change

### Create

- `src/trading_algos_dashboard/static/js/configuration_builder.js`

### Update

- `src/trading_algos_dashboard/templates/base.html`
- `src/trading_algos_dashboard/templates/configurations/new.html`
- `src/trading_algos_dashboard/templates/configurations/detail.html`
- `src/trading_algos_dashboard/static/css/app.css`
- `src/trading_algos_dashboard/blueprints/configurations.py`
- `tests/dashboard/test_configurations_routes.py`

## MVP page structure

### Left column

1. page title and short guidance
2. starter templates
3. metadata form
4. visual structure builder
5. save action row

### Right column

1. validation summary
2. human-readable structure preview
3. advanced JSON preview

## Metadata form fields

- name
- config key
- version
- description
- tags
- notes

## Supported starter templates

- blank
- single algorithm
- and strategy
- or strategy
- breakout example

## Client-side state shape

```js
const state = {
  metadata: {
    config_key: "",
    version: "1.0.0",
    name: "",
    description: "",
    tagsText: "",
    notes: "",
    status: "draft",
  },
  rootNodeId: null,
  nodesById: {},
  catalog: [],
  ui: {
    validationMessages: [],
    manualConfigKeyDirty: false,
  },
};
```

## Node shapes

### Algorithm node

```js
{
  node_id: "node-1",
  node_type: "algorithm",
  name: "Close/High Channel Breakout",
  description: "",
  alg_key: "close_high_channel_breakout",
  alg_param: { window: 20 },
  buy_enabled: true,
  sell_enabled: true,
  runtime_editable_param_keys: [],
}
```

### Group node

```js
{
  node_id: "node-2",
  node_type: "and",
  name: "AND group",
  description: "",
  children: ["node-3", "node-4"],
}
```

## Serialization target

The builder must serialize to the existing backend payload shape so the server contract remains unchanged.

## Validation rules in the UI

- name required
- config key required
- version required
- root node required
- algorithm node must have `alg_key`
- algorithm node cannot disable both buy and sell
- group nodes must have at least 2 children
- integer parameters must be positive

## Detail page improvements

The configuration detail page should show:

- metadata summary
- human-readable structure tree
- revision history
- publish history
- raw JSON only in an advanced section

## Implementation phases

### Phase 1

- add docs
- redesign `new.html` into a builder shell
- add builder CSS and JS asset loading

### Phase 2

- implement builder state model
- fetch algorithm catalog from `/api/algorithms`
- add metadata editing and starter templates
- support single algorithm creation

### Phase 3

- support nested `and` / `or` groups
- add live preview and validation
- generate JSON into hidden payload input

### Phase 4

- improve detail page with readable structure summary
- preserve advanced JSON for debugging

### Phase 5

- update tests
- run full verification

## Out of scope for MVP

- drag and drop editing
- pipeline node editing
- frontend unit test harness
- rich diff visualization for revisions

## Definition of done for MVP

- user can create a valid configuration without typing JSON
- user can add algorithms from catalog metadata
- user can build `and` and `or` groups visually
- builder shows validation and preview before save
- server submission still uses the existing payload contract
- detail page is readable without inspecting raw JSON