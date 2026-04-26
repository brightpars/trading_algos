You are working in `/home/mohammad/development/trading_algos`.

Goal:
Extend the simplified backtrace feature to support executing multiple algorithm runs in one request.

Assumptions:
- Single-run backtrace execution already works.
- Persistence and API/UI already exist.

What to build:
1. Add batch request/result contracts.
2. Reuse the single-run runtime service internally rather than duplicating logic.
3. Support multiple algorithms and/or multiple symbols/requests in one submission.
4. Return per-item success/failure results.

Constraints:
- Keep failures isolated per item.
- Preserve single-run API if already present.
- No broker integration.
- No async queueing unless absolutely necessary.

Testing:
- Multi-item success case.
- Mixed success/failure case.
- Stable aggregated result shape.

Deliverable:
A batch-capable simplified backtrace feature built on top of the single-run path.
