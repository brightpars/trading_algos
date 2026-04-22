## Parallel experiment execution and shared cache plan

### Goals
- Run multiple experiments concurrently in separate processes.
- Enforce a configurable runtime concurrency limit.
- Keep queue state accurate as soon as a worker finishes or is cancelled.
- Evolve market-data caching from process-local behavior toward a shared multi-process design.

### Current state
- `ExperimentService` now dispatches multiple experiments up to a configurable concurrency limit.
- Experiments are persisted with queued/running/completed/failed/cancelled state transitions.
- Worker completion and cancellation refill scheduler capacity automatically.
- Market data caching is now layered: process-local L1 plus shared Mongo-backed L2.
- Dispatch coordination now includes a persistent scheduler lease to prevent over-dispatch across multiple app instances.

### Target architecture
1. Replace single-running scheduling with slot-based scheduling using `max_concurrent_experiments`.
2. Extend `ExperimentRepository` with plural-running queries and atomic queue claiming.
3. Refactor `ExperimentService.dispatch_next_experiment()` into a slot-filling scheduler.
4. Return queue overview data with running counts, available slots, and concurrency metadata.
5. Update the UI to describe FIFO queueing with parallel capacity instead of one-by-one execution.
6. Use layered caching with in-memory L1, shared Mongo-backed L2, and same-key fill coordination.
7. Support runtime-editable concurrency settings without restarting the app.
8. Protect dispatch with a cross-instance scheduler lease when multiple dashboard instances are running.

### File-by-file implementation map

#### `src/trading_algos_dashboard/repositories/experiment_repository.py`
- Add `list_running_experiments()`.
- Add `count_running_experiments()`.
- Add `claim_next_queued_experiment(started_at=...)` using an atomic update contract.

#### `src/trading_algos_dashboard/services/experiment_service.py`
- Add `max_concurrent_experiments` constructor parameter.
- Replace single-dispatch logic with `dispatch_available_experiments()`.
- Launch experiments until scheduler capacity is full.
- Refill available slots after completion/failure/cancellation.
- Return queue overview with plural running experiments and summary counts.
- Read a runtime concurrency provider instead of only startup config.
- Use a scheduler lease manager to coordinate dispatch across app instances.

#### `src/trading_algos_dashboard/config.py`
- Add `experiment_max_concurrent_runs` config field backed by env.

#### `src/trading_algos_dashboard/app.py`
- Pass `experiment_max_concurrent_runs` into `ExperimentService`.
- Wire runtime scheduler settings and scheduler lease services into the app container.

#### `src/trading_algos_dashboard/repositories/experiment_runtime_settings_repository.py`
- Persist runtime-editable scheduler settings.

#### `src/trading_algos_dashboard/services/experiment_runtime_settings_service.py`
- Expose validated runtime scheduler settings with configured defaults.

#### `src/trading_algos_dashboard/repositories/experiment_scheduler_lease_repository.py`
- Persist a dispatch lease document for cross-instance coordination.

#### `src/trading_algos_dashboard/services/experiment_scheduler_lease_service.py`
- Acquire and release scheduler leases with expiration.

#### `src/trading_algos_dashboard/blueprints/experiments.py`
- Render queue/history pages using plural running experiments.
- Expose concurrency metadata to templates/runtime payloads.
- Save runtime concurrency updates submitted from the experiment form.

#### `src/trading_algos_dashboard/templates/experiments/new.html`
- Update text to describe FIFO queueing with a concurrency limit.
- Render an editable `max_concurrent_experiments` field.

#### `src/trading_algos_dashboard/templates/experiments/history.html`
- Render multiple running experiments.
- Show concurrency summary.

#### `src/trading_algos_dashboard/templates/experiments/detail.html`
- Update queued-runtime text to mention parallel execution slots.
- Show runtime slot usage summary.

#### `src/trading_algos_dashboard/static/js/experiment_runtime.js`
- Update queued messaging to mention available execution slots.
- Render running count / concurrency limit fields when present.

### Cache strategy for concurrent workers
- Keep `InMemoryMarketDataCache` as fast per-process L1 cache.
- Use a shared Mongo-backed L2 cache for multi-process reuse.
- Prefer explicit source labels such as `memory_cache`, `shared_cache`, and `dataserver`.
- Use lease-based stampede protection so concurrent same-key misses wait briefly for an in-flight shared-cache fill.

### Scheduler coordination strategy for concurrent app instances
- Use repository-backed queue claiming for experiment ownership.
- Use a separate short-lived scheduler lease so only one app instance performs slot-filling dispatch at a time.
- Release the lease after each dispatch pass so other instances can participate on later cycles.

### Recommended delivery phases
1. Scheduler concurrency and queue state.
2. UI/API updates for queue overview and runtime messaging.
3. Shared cache abstraction and Mongo-backed L2 cache.
4. Optional runtime-editable concurrency setting.
5. Optional but recommended cross-instance scheduler lease hardening.

### Implementation status
- Phase 1: implemented.
- Phase 2: implemented.
- Phase 3: implemented.
- Phase 4: implemented.
- Phase 5: implemented.

### Testing plan
- Repository tests for running-count and atomic queue claim.
- Service tests for slot-filling dispatch and refill on completion.
- Route/API tests for plural running experiments and concurrency summary.
- Cache tests for L1/L2 behavior and in-flight fill coordination.
- Scheduler tests for runtime concurrency providers and cross-instance lease behavior.