## Legacy algorithm to new library mapping

This document summarizes the legacy algorithms that already existed before the large algorithm-library expansion, and maps them to the closest newly added standardized algorithm or combination method.

> Important: this is a **best-match mapping**, not proof of an exact one-to-one replacement or rename.

### Context

- Pre-existing algorithms before the last major expansion: **7**
- Newly added library entries in the later expansion: **133**
  - **121** algorithms
  - **12** combination methods
- Current total after that expansion: **140**

The old 7 were not counted inside the later `121 + 12` batch. They remain separate registrations, though some overlap conceptually with the newer library.

### Intended renamed forms

We are renaming the legacy algorithm identifiers to make the old-to-new conceptual mapping explicit.

| Previous key | Requested renamed key |
|---|---|
| `boundary_breakout` | `OLD_boundary_breakout_NEW_breakout_donchian_channel` |
| `double_red_confirmation` | `OLD_double_red_confirmation_NEW_channel_breakout_with_confirmation` |
| `low_anchored_boundary_breakout` | `OLD_low_anchored_boundary_breakout_NEW_breakout_donchian_channel` |
| `rolling_channel_breakout` | `OLD_rolling_channel_breakout_NEW_breakout_donchian_channel` |
| `close_high_channel_breakout` | `OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation` |
| `aggregate_boundary_and_channel` | `OLD_aggregate_boundary_and_channel_NEW_hard_boolean_gating_and_or_majority` |
| `aggregate_channel_dual_window` | `OLD_aggregate_channel_dual_window_NEW_weighted_linear_score_blend` |

These renamed forms are the requested names we are using to mark the legacy algorithms in relation to their closest newer standardized equivalents.

### Side-by-side mapping

| Old algorithm | Requested renamed key | Closest specific new algorithm/method | New family/type | Confidence | Reason |
|---|---|---|---|---|---|
| Boundary Breakout | `OLD_boundary_breakout_NEW_breakout_donchian_channel` | Breakout Donchian Channel | `trend` | Medium | Both are classic boundary/channel breakout trend systems based on recent highs/lows. |
| Double Red Confirmation | `OLD_double_red_confirmation_NEW_channel_breakout_with_confirmation` | Channel Breakout With Confirmation | `trend` | High | The defining feature is extra confirmation logic after a breakout, which matches this new name most directly. |
| Low-Anchored Boundary Breakout | `OLD_low_anchored_boundary_breakout_NEW_breakout_donchian_channel` | Breakout Donchian Channel | `trend` | Medium | Both use recent price bounds as breakout anchors; this is the nearest standardized breakout equivalent. |
| Rolling Channel Breakout | `OLD_rolling_channel_breakout_NEW_breakout_donchian_channel` | Breakout Donchian Channel | `trend` | High | This is the clearest replacement-style match: rolling-window channel breakout to rolling-window channel breakout. |
| Close/High Channel Breakout | `OLD_close_high_channel_breakout_NEW_channel_breakout_with_confirmation` | Channel Breakout With Confirmation | `trend` | Medium | Still a channel-breakout style algorithm; among the new names this is the closest non-legacy-specific breakout variant. |
| Aggregate Boundary and Channel | `OLD_aggregate_boundary_and_channel_NEW_hard_boolean_gating_and_or_majority` | Hard Boolean Gating (AND / OR / Majority) | `rule_based_combination` | Medium | The old algorithm combines child signals with explicit buy/sell logic; boolean gating is the closest structured combination method. |
| Aggregate Channel Dual Window | `OLD_aggregate_channel_dual_window_NEW_weighted_linear_score_blend` | Weighted Linear Score Blend | `rule_based_combination` | Low-Medium | It combines multiple child signals/windows; weighted blending is a plausible modern replacement, though not an exact structural match. |

### Short interpretation

#### Old trend algorithms

The legacy trend/breakout variants map most closely to these newly added standardized trend algorithms:

- `Breakout Donchian Channel`
- `Channel Breakout With Confirmation`

#### Old composite algorithms

The legacy aggregate/composite variants map most closely to these newly added combination methods:

- `Hard Boolean Gating (AND / OR / Majority)`
- `Weighted Linear Score Blend`

### Important nuance

The current `trend` catalog still contains the older trend algorithms alongside the newer trend-library entries. So for the old trend algorithms, the most exact current match is still the original legacy implementation itself.

This document instead answers a different question:

> Which newly added standardized algorithm or method is the closest conceptual match?

### Practical takeaway

- The old **5 trend algorithms** look like legacy predecessors of the expanded standardized `trend` library.
- The old **2 aggregate algorithms** look like legacy predecessors of the newer `rule_based_combination` framework.
- There is **conceptual overlap**, but not **counting overlap**.

### One-line summary

Document legacy-to-new algorithm mappings for the 7 pre-existing strategies against the later standardized library.