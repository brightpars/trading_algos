You are working in `/home/mohammad/development/trading_algos`.

Goal:
Extend the simplified backtrace flow so requests can use a data-source reference and time range instead of requiring inline candles.

Assumptions:
- Inline-candle backtrace flow already works.
- The dashboard already has data source service patterns that can likely be reused.

What to build:
1. Extend request contract to support either:
   - inline candles, or
   - a data source reference with symbol/time-range parameters
2. Resolve candles before algorithm execution.
3. Keep single-algorithm synchronous execution.

Constraints:
- Preserve existing inline candle path.
- Validate that exactly one input mode is used.
- No broker integration.
- No batching in this round.

Testing:
- Inline mode still works.
- Data-source mode works.
- Invalid mixed/missing modes fail clearly.

Deliverable:
Backtrace requests can use either inline candles or data-source-backed candle retrieval.

