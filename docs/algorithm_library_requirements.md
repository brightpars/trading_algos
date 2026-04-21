# Algorithm Library Requirements for SmartTrade / Algorithm Designer

## Purpose

This document defines a **broad algorithm library** for the Algorithm Designer Dashboard and SmartTrade ecosystem. The goal is to help a coder implement many known trading algorithms **in the same interface style** as the algorithms you already have, so the new algorithms can reuse the same helpers, data preparation, reporting, and signal-generation flow.

## Important framing

There is **no single universally fixed “complete list”** of all trading algorithms. Reputable overviews consistently group algorithmic trading into broad families such as **trend following, momentum, mean reversion, arbitrage/statistical arbitrage, market making/HFT, and execution algorithms such as VWAP and TWAP**. Academic and practitioner sources also distinguish **time-series momentum** from **cross-sectional momentum**, and broker/execution literature treats **VWAP, TWAP, participation-rate, and implementation shortfall** as execution algorithms rather than alpha-generating signal strategies. citeturn799880news12turn526753search0turn526753search3turn329530search0

Accordingly, this document is intentionally broad and organized into categories so your coder can implement the library systematically rather than as one flat, repetitive list. It includes:
- signal-generation strategies
- statistical arbitrage and relative-value strategies
- options/volatility strategies
- microstructure and market-making styles
- execution algorithms

## Recommended common interface

Every algorithm implementation should follow the **same contract** as your existing algorithms as much as possible.

Suggested common expectations:
- Accept normalized market data in the same format as existing algorithms
- Accept a structured parameter object / config
- Use shared helper utilities for indicators, statistics, filtering, and reporting
- Return:
  - raw intermediate metrics / indicator series
  - final state per bar or time point (`buy`, `sell`, `neutral`)
  - optional confidence / score
  - optional event markers
  - summary report payload compatible with your existing dashboard
- Support backtesting on a date/time range
- Support plotting/visualization through the existing dashboard pipeline
- Avoid arbitrary custom I/O patterns per algorithm

## Suggested implementation metadata for each algorithm

For each algorithm below, the coder should implement:
1. algorithm class / identifier
2. category
3. required input data
4. configurable parameters
5. intermediate calculations
6. final signal rule
7. optional filters
8. output/report fields
9. compatibility with your existing visualization/report helpers

## Library catalog


## Trend Following

### 1. Simple Moving Average Crossover
- **Core idea:** Buy when a short moving average crosses above a long moving average; sell on the opposite cross.
- **Typical inputs:** OHLCV close series, short window, long window
- **Signal style:** Discrete buy/sell on crossover
- **Implementation notes:** Baseline trend strategy; easy to fit existing helpers.

### 2. Exponential Moving Average Crossover
- **Core idea:** Like SMA crossover but uses EMAs for faster reaction.
- **Typical inputs:** OHLCV close series, short EMA, long EMA
- **Signal style:** Discrete buy/sell on crossover
- **Implementation notes:** Useful faster trend variant.

### 3. Triple Moving Average Crossover
- **Core idea:** Uses fast/medium/slow averages to reduce whipsaws.
- **Typical inputs:** OHLCV close series, 3 windows
- **Signal style:** Discrete buy/sell when ordering changes
- **Implementation notes:** Good for cleaner state machines.

### 4. Price vs Moving Average
- **Core idea:** Long when price is above a moving average and short/flat when below.
- **Typical inputs:** OHLCV close series, MA window
- **Signal style:** Stateful trend regime signal
- **Implementation notes:** Simple reusable primitive.

### 5. Moving Average Ribbon Trend
- **Core idea:** Uses a ribbon of multiple averages; signal from alignment and spread.
- **Typical inputs:** OHLCV close series, list of MA windows
- **Signal style:** Trend-strength signal plus buy/sell
- **Implementation notes:** Can expose score and final label.

### 6. Breakout (Donchian Channel)
- **Core idea:** Buy on breakout above rolling high; sell on breakdown below rolling low.
- **Typical inputs:** OHLCV high/low, lookback window
- **Signal style:** Discrete breakout entries/exits
- **Implementation notes:** Classic CTA-style rule.

### 7. Channel Breakout with Confirmation
- **Core idea:** Breakout must persist for N bars or exceed threshold.
- **Typical inputs:** OHLCV, lookback, confirmation bars/threshold
- **Signal style:** Buy/sell with confirmation
- **Implementation notes:** Reduces false breaks.

### 8. ADX Trend Filter
- **Core idea:** Use ADX to trade only when trend strength exceeds threshold.
- **Typical inputs:** OHLCV, ADX window, threshold
- **Signal style:** Trend filter plus directional signal
- **Implementation notes:** Often combined with other entries.

### 9. Parabolic SAR Trend Following
- **Core idea:** Enter/exit on Parabolic SAR flips.
- **Typical inputs:** OHLCV, SAR step/max
- **Signal style:** Buy/sell on SAR reversal
- **Implementation notes:** Good discrete signal generator.

### 10. SuperTrend
- **Core idea:** Trend signal based on ATR bands and direction flips.
- **Typical inputs:** OHLCV, ATR window, multiplier
- **Signal style:** Buy/sell on band flips
- **Implementation notes:** Widely used trend indicator strategy.

### 11. Ichimoku Trend Strategy
- **Core idea:** Uses cloud, baseline, conversion line, and lagging span for trend regime.
- **Typical inputs:** OHLCV, Ichimoku parameters
- **Signal style:** Buy/sell plus regime confidence
- **Implementation notes:** Multi-rule composite strategy.

### 12. MACD Trend Strategy
- **Core idea:** Trade MACD line crossing signal line or zero line.
- **Typical inputs:** OHLCV close, EMA params
- **Signal style:** Buy/sell on crossovers
- **Implementation notes:** Can return both event and oscillator state.

### 13. Linear Regression Trend
- **Core idea:** Use rolling regression slope/intercept to detect persistent trend.
- **Typical inputs:** OHLCV close, window
- **Signal style:** Trend-score converted to signal
- **Implementation notes:** Good quantitative primitive.

### 14. Time-Series Momentum
- **Core idea:** Trade an asset based on its own past return sign over a lookback window.
- **Typical inputs:** Price returns, lookback, holding period
- **Signal style:** Long/short or buy/sell based on own trailing return
- **Implementation notes:** Distinct from cross-sectional momentum.


## Momentum

### 15. Rate of Change Momentum
- **Core idea:** Buy when price ROC exceeds threshold; sell when below negative threshold.
- **Typical inputs:** OHLCV close, ROC window, thresholds
- **Signal style:** Momentum event signal
- **Implementation notes:** Simple momentum implementation.

### 16. Cross-Sectional Momentum
- **Core idea:** Rank a universe by past returns; buy winners, sell losers.
- **Typical inputs:** Universe price history, lookback, ranking size
- **Signal style:** Portfolio selection / long-short signal
- **Implementation notes:** Needs universe-level interface.

### 17. Relative Strength Momentum
- **Core idea:** Trade instruments with strongest recent relative performance.
- **Typical inputs:** Universe prices, lookback
- **Signal style:** Rank-based buy preference
- **Implementation notes:** Can be implemented as score output.

### 18. Dual Momentum
- **Core idea:** Combines absolute momentum and relative momentum.
- **Typical inputs:** Universe prices, benchmark/cash proxy, lookbacks
- **Signal style:** Asset selection and risk-off signals
- **Implementation notes:** Good for allocation layer.

### 19. Residual Momentum
- **Core idea:** Momentum after removing factor/market effects.
- **Typical inputs:** Returns, factor model inputs
- **Signal style:** Ranked momentum score
- **Implementation notes:** Requires risk-model helper.

### 20. Accelerating Momentum
- **Core idea:** Trade when momentum itself is strengthening.
- **Typical inputs:** Returns, multi-horizon ROC
- **Signal style:** Momentum-strength signal
- **Implementation notes:** Useful extension of ROC.

### 21. RSI Momentum Continuation
- **Core idea:** Use RSI in continuation mode rather than mean reversion mode.
- **Typical inputs:** OHLCV close, RSI window, thresholds
- **Signal style:** Buy in strong uptrends, sell in downtrends
- **Implementation notes:** Different from RSI reversal use.

### 22. Stochastic Momentum
- **Core idea:** Use stochastic oscillator strength/cross for continuation.
- **Typical inputs:** OHLCV high/low/close, stoch params
- **Signal style:** Buy/sell on momentum cross
- **Implementation notes:** Can be noisy without filters.

### 23. CCI Momentum
- **Core idea:** Commodity Channel Index used for continuation breakout style entries.
- **Typical inputs:** OHLCV typical price, CCI window
- **Signal style:** Buy/sell on threshold crossings
- **Implementation notes:** Indicator-based momentum.

### 24. KST (Know Sure Thing)
- **Core idea:** Multi-horizon momentum oscillator strategy.
- **Typical inputs:** OHLCV close, multiple ROC windows
- **Signal style:** Buy/sell on KST/signal cross
- **Implementation notes:** Encapsulates several momentum horizons.

### 25. Volume-Confirmed Momentum
- **Core idea:** Trade momentum only when supported by abnormal volume.
- **Typical inputs:** OHLCV, volume filters
- **Signal style:** Buy/sell with volume confirmation
- **Implementation notes:** Common practical variant.


## Mean Reversion

### 26. Z-Score Mean Reversion
- **Core idea:** Buy when price/spread is far below rolling mean; sell when far above.
- **Typical inputs:** Price or spread series, window, std threshold
- **Signal style:** Reversion entries/exits
- **Implementation notes:** Core reusable reversion pattern.

### 27. Bollinger Bands Reversion
- **Core idea:** Fade moves outside Bollinger Bands back toward the mean.
- **Typical inputs:** OHLCV close, MA window, std multiplier
- **Signal style:** Buy low-band touches, sell high-band touches
- **Implementation notes:** Classic range strategy.

### 28. RSI Reversion
- **Core idea:** Buy oversold, sell overbought using RSI.
- **Typical inputs:** OHLCV close, RSI window, thresholds
- **Signal style:** Reversal entries
- **Implementation notes:** Popular baseline reversal strategy.

### 29. Stochastic Reversion
- **Core idea:** Use stochastic oscillator extremes for reversal.
- **Typical inputs:** OHLCV high/low/close, params
- **Signal style:** Buy/sell from extreme zones
- **Implementation notes:** Often range-market only.

### 30. CCI Reversion
- **Core idea:** Fade extreme CCI readings back to neutral.
- **Typical inputs:** OHLCV typical price, window, thresholds
- **Signal style:** Buy/sell from extremes
- **Implementation notes:** Alternative oscillator reversion.

### 31. Williams %R Reversion
- **Core idea:** Mean reversion using Williams %R overbought/oversold zones.
- **Typical inputs:** OHLCV high/low/close, window
- **Signal style:** Buy/sell from extremes
- **Implementation notes:** Simple oscillator implementation.

### 32. Intraday VWAP Reversion
- **Core idea:** Fade price deviations away from session VWAP.
- **Typical inputs:** Intraday OHLCV, VWAP state, thresholds
- **Signal style:** Buy/sell toward VWAP
- **Implementation notes:** Useful intraday strategy.

### 33. Opening Gap Fade
- **Core idea:** Fade opening gaps that historically close intraday.
- **Typical inputs:** Daily/intraday OHLCV, gap filters
- **Signal style:** Buy/sell against gap direction
- **Implementation notes:** Needs session-aware helper.

### 34. Range Reversion
- **Core idea:** Trade reversals inside identified range-bound regime.
- **Typical inputs:** OHLCV, range detector, support/resistance bands
- **Signal style:** Buy near support, sell near resistance
- **Implementation notes:** Best when combined with trend filter.

### 35. Ornstein-Uhlenbeck Reversion
- **Core idea:** Model spread or price as OU process and trade toward equilibrium.
- **Typical inputs:** Price/spread series, OU params
- **Signal style:** Probabilistic reversion signal
- **Implementation notes:** Good for more advanced stat-arb.

### 36. Long-Horizon Reversal
- **Core idea:** Trade multi-month/long-term reversals rather than short-term mean reversion.
- **Typical inputs:** Returns, long lookback
- **Signal style:** Contrarian buy/sell
- **Implementation notes:** Distinct from short-term oscillators.

### 37. Volatility-Adjusted Reversion
- **Core idea:** Thresholds scale with realized volatility or ATR.
- **Typical inputs:** OHLCV, volatility estimator
- **Signal style:** Normalized reversal signal
- **Implementation notes:** Makes thresholds portable across assets.


## Statistical Arbitrage

### 38. Pairs Trading (Distance Method)
- **Core idea:** Trade divergence/convergence of historically correlated pair.
- **Typical inputs:** Two price series, normalized spread, thresholds
- **Signal style:** Long one / short the other
- **Implementation notes:** Canonical pairs strategy.

### 39. Pairs Trading (Cointegration)
- **Core idea:** Trade pair spread when cointegrated relationship deviates from equilibrium.
- **Typical inputs:** Two price series, cointegration / hedge ratio
- **Signal style:** Spread reversion entries/exits
- **Implementation notes:** More robust than simple correlation.

### 40. Basket Statistical Arbitrage
- **Core idea:** Trade one asset against a basket or multiple related assets.
- **Typical inputs:** Multi-asset prices, hedge weights, spread model
- **Signal style:** Spread signal
- **Implementation notes:** Generalizes pairs trading.

### 41. Kalman Filter Pairs Trading
- **Core idea:** Dynamically estimate hedge ratio and spread using Kalman filter.
- **Typical inputs:** Two price series, Kalman parameters
- **Signal style:** Adaptive spread signal
- **Implementation notes:** Useful when relationships drift.

### 42. Index Arbitrage
- **Core idea:** Trade mispricing between index future/ETF and underlying basket.
- **Typical inputs:** Index, futures/ETF, basket prices, carry costs
- **Signal style:** Arbitrage buy/sell
- **Implementation notes:** Needs multi-instrument pricing.

### 43. ETF-NAV Arbitrage
- **Core idea:** Trade ETF price deviations versus indicative NAV or fair value proxy.
- **Typical inputs:** ETF price, basket/NAV proxy
- **Signal style:** Arbitrage spread signal
- **Implementation notes:** Useful where basket data exists.

### 44. ADR Dual-Listing Arbitrage
- **Core idea:** Exploit price mismatch between dual-listed securities/ADRs.
- **Typical inputs:** Two market prices, FX, fees
- **Signal style:** Arbitrage entries
- **Implementation notes:** Requires cross-market normalization.

### 45. Convertible Arbitrage
- **Core idea:** Trade convertibles versus equity/credit/vol components.
- **Typical inputs:** Convertible data, equity price, rates, vol estimates
- **Signal style:** Relative value signal
- **Implementation notes:** Advanced; often institutional.

### 46. Merger Arbitrage
- **Core idea:** Trade target/acquirer spread around announced deals.
- **Typical inputs:** Deal terms, stock prices, probabilities, dates
- **Signal style:** Event-driven spread signal
- **Implementation notes:** Event-driven category.

### 47. Futures Cash-and-Carry Arbitrage
- **Core idea:** Exploit mispricing between spot and futures net of carry.
- **Typical inputs:** Spot, futures, rates, storage/dividend/carry
- **Signal style:** Arbitrage buy/sell
- **Implementation notes:** Important pricing-based strategy.

### 48. Reverse Cash-and-Carry Arbitrage
- **Core idea:** Opposite of cash-and-carry when futures underpriced.
- **Typical inputs:** Spot, futures, carry inputs
- **Signal style:** Arbitrage buy/sell
- **Implementation notes:** Mirror case.

### 49. Triangular Arbitrage (FX/Crypto)
- **Core idea:** Exploit inconsistent cross-rates among three pairs.
- **Typical inputs:** Three quoted exchange rates, fees
- **Signal style:** Instant arbitrage signal
- **Implementation notes:** Execution-sensitive.

### 50. Latency / Exchange Arbitrage
- **Core idea:** Exploit temporary price differences across venues.
- **Typical inputs:** Multi-venue quotes, latency data, fees
- **Signal style:** Very short-lived arbitrage signal
- **Implementation notes:** Infrastructure-heavy.

### 51. Funding/Basis Arbitrage
- **Core idea:** Trade spot-perp or spot-futures basis and funding differentials.
- **Typical inputs:** Spot, perp/futures prices, funding/basis
- **Signal style:** Carry/arbitrage signal
- **Implementation notes:** Common in crypto and futures.


## Volatility / Options

### 52. Volatility Breakout
- **Core idea:** Trade price breakout when volatility expands from compression.
- **Typical inputs:** OHLCV, ATR/volatility compression metrics
- **Signal style:** Buy/sell breakout signal
- **Implementation notes:** Can be implemented without options.

### 53. ATR Channel Breakout
- **Core idea:** Breakout using ATR-based dynamic bands.
- **Typical inputs:** OHLCV, ATR window, multiplier
- **Signal style:** Buy/sell on ATR-band break
- **Implementation notes:** Robust trend breakout variant.

### 54. Volatility Mean Reversion
- **Core idea:** Fade unusually high/low realized or implied volatility.
- **Typical inputs:** Volatility series, thresholds
- **Signal style:** Volatility reversion signal
- **Implementation notes:** May drive delta-neutral positions.

### 55. Delta-Neutral Volatility Trading
- **Core idea:** Trade volatility while hedging directional delta.
- **Typical inputs:** Option chain, underlying price, greeks
- **Signal style:** Volatility entry/exit signal
- **Implementation notes:** Options-support required.

### 56. Gamma Scalping
- **Core idea:** Maintain delta-neutral option position and scalp underlying around volatility.
- **Typical inputs:** Options greeks, underlying ticks
- **Signal style:** Hedging/trading actions
- **Implementation notes:** Advanced options workflow.

### 57. Volatility Risk Premium Capture
- **Core idea:** Systematically short or long implied vs realized volatility spread.
- **Typical inputs:** Options IV, realized vol estimates
- **Signal style:** Carry/vol signal
- **Implementation notes:** Common options systematic theme.

### 58. Dispersion Trading
- **Core idea:** Trade index options versus constituent options to isolate correlation/dispersion.
- **Typical inputs:** Index and constituent option vols
- **Signal style:** Relative value signal
- **Implementation notes:** Institutional/advanced.

### 59. Skew Trading
- **Core idea:** Trade relative richness/cheapness of downside vs upside implied vols.
- **Typical inputs:** Option surface/skew metrics
- **Signal style:** Options relative value signal
- **Implementation notes:** Surface-analytics heavy.

### 60. Term Structure Trading
- **Core idea:** Trade implied volatility across maturities.
- **Typical inputs:** Option/futures term structure
- **Signal style:** Relative value signal
- **Implementation notes:** Can also apply to futures curves.

### 61. Straddle Breakout Timing
- **Core idea:** Enter long-vol structures ahead of expected large move or realized-vol expansion.
- **Typical inputs:** Options IV/RV, event calendar
- **Signal style:** Volatility timing signal
- **Implementation notes:** Event-aware strategy.


## Microstructure / HFT / Market Making

### 62. Bid-Ask Market Making
- **Core idea:** Post both sides, capture spread, manage inventory.
- **Typical inputs:** Best bid/ask, order book, inventory, fees
- **Signal style:** Continuous quoting actions
- **Implementation notes:** Execution/inventory engine needed.

### 63. Inventory-Skewed Market Making
- **Core idea:** Adjust quotes based on inventory to stay balanced.
- **Typical inputs:** Order book, inventory target
- **Signal style:** Quote placement signals
- **Implementation notes:** Practical MM extension.

### 64. Order Book Imbalance Strategy
- **Core idea:** Trade short-term moves from depth imbalance.
- **Typical inputs:** Level 2 book, imbalance metrics
- **Signal style:** Short-horizon buy/sell
- **Implementation notes:** Needs high-frequency data.

### 65. Microprice Strategy
- **Core idea:** Use weighted bid/ask microprice to predict near-term direction.
- **Typical inputs:** Top-of-book prices and sizes
- **Signal style:** Short-horizon directional signal
- **Implementation notes:** Useful microstructure primitive.

### 66. Queue Position Strategy
- **Core idea:** Manage passive orders based on queue rank and fill probability.
- **Typical inputs:** Order book + own order state
- **Signal style:** Order amend/cancel actions
- **Implementation notes:** Execution-centric.

### 67. Liquidity Rebate Capture
- **Core idea:** Seek maker rebates while controlling adverse selection.
- **Typical inputs:** Fee schedule, book data, inventory
- **Signal style:** Quoting/actions
- **Implementation notes:** Venue-specific strategy.

### 68. Opening Auction Strategy
- **Core idea:** Trade around auction imbalance or expected open price.
- **Typical inputs:** Auction imbalance/feed, pre-open prices
- **Signal style:** Auction participation signal
- **Implementation notes:** Session-event strategy.

### 69. Closing Auction Strategy
- **Core idea:** Trade close auction flows or MOC imbalances.
- **Typical inputs:** Auction feed, near-close data
- **Signal style:** Auction participation signal
- **Implementation notes:** Common institutional use case.


## Pattern / Price Action

### 70. Support and Resistance Bounce
- **Core idea:** Buy at support, sell at resistance with tolerance bands.
- **Typical inputs:** OHLCV, detected levels
- **Signal style:** Reversal entries/exits
- **Implementation notes:** Can reuse level-detection helper.

### 71. Breakout Retest
- **Core idea:** Enter after breakout and successful retest of broken level.
- **Typical inputs:** OHLCV, levels, retest logic
- **Signal style:** Buy/sell after confirmation
- **Implementation notes:** Popular discretionary-to-systematic translation.

### 72. Pivot Point Strategy
- **Core idea:** Trade around daily/weekly pivot levels.
- **Typical inputs:** OHLCV, pivot formulas
- **Signal style:** Buy/sell near pivot interactions
- **Implementation notes:** Session-based rule system.

### 73. Opening Range Breakout
- **Core idea:** Trade break of initial session range.
- **Typical inputs:** Intraday OHLCV, opening range duration
- **Signal style:** Buy/sell breakout signal
- **Implementation notes:** Widely used intraday algorithm.

### 74. Inside Bar Breakout
- **Core idea:** Trade break of an inside-bar pattern.
- **Typical inputs:** OHLCV candle patterns
- **Signal style:** Pattern breakout signal
- **Implementation notes:** Simple candle-based rule.

### 75. Gap-and-Go
- **Core idea:** Trade in direction of significant opening gap with continuation filters.
- **Typical inputs:** Daily/intraday OHLCV, volume
- **Signal style:** Momentum continuation signal
- **Implementation notes:** Session-aware.

### 76. Trendline Break Strategy
- **Core idea:** Trade breaks of fitted trendlines/channels.
- **Typical inputs:** OHLCV, swing points, regression lines
- **Signal style:** Buy/sell on line break
- **Implementation notes:** Requires pattern extractor.

### 77. Volatility Squeeze Breakout
- **Core idea:** Trade expansion after Bollinger/Keltner squeeze.
- **Typical inputs:** OHLCV, BB/KC params
- **Signal style:** Breakout signal
- **Implementation notes:** Popular squeeze setup.


## Cross-Asset / Macro / Carry

### 78. Carry Trade (FX/Rates)
- **Core idea:** Go long higher carry assets and short lower carry assets.
- **Typical inputs:** Rates/yields, FX forwards/spot
- **Signal style:** Long/short carry signal
- **Implementation notes:** Cross-asset allocation strategy.

### 79. Yield Curve Steepener/Flattener
- **Core idea:** Trade changes in slope of rates curve.
- **Typical inputs:** Multi-maturity yields/futures
- **Signal style:** Relative value signal
- **Implementation notes:** Macro/rates oriented.

### 80. Curve Roll-Down Strategy
- **Core idea:** Harvest roll along the term structure.
- **Typical inputs:** Yield/futures curves, carry metrics
- **Signal style:** Carry/relative value signal
- **Implementation notes:** Common fixed-income systematic theme.

### 81. Commodity Term Structure / Roll Yield
- **Core idea:** Trade backwardation/contango effects.
- **Typical inputs:** Futures curve data
- **Signal style:** Carry signal
- **Implementation notes:** Commodity systematic family.

### 82. Risk-On / Risk-Off Regime
- **Core idea:** Allocate based on macro or cross-asset regime state.
- **Typical inputs:** Cross-asset returns/vol/macro inputs
- **Signal style:** Regime signal
- **Implementation notes:** Works as top-level filter.

### 83. Intermarket Confirmation
- **Core idea:** Trade one asset using signals from correlated assets (e.g., bonds, dollar, sector ETF).
- **Typical inputs:** Multiple asset time series
- **Signal style:** Confirmation-filtered signal
- **Implementation notes:** Useful framework feature.

### 84. Seasonality / Calendar Effects
- **Core idea:** Trade recurring calendar anomalies (month-end, turn-of-month, day-of-week, holiday).
- **Typical inputs:** Calendar + returns history
- **Signal style:** Scheduled buy/sell windows
- **Implementation notes:** Implementation should be modular.

### 85. Earnings Drift / Post-Event Momentum
- **Core idea:** Trade persistent drift after earnings or scheduled events.
- **Typical inputs:** Event calendar, surprise data, prices
- **Signal style:** Event-driven momentum signal
- **Implementation notes:** Needs event dataset.


## Fundamental / ML / Composite

### 86. Value Strategy
- **Core idea:** Buy relatively cheap assets by valuation, sell expensive ones.
- **Typical inputs:** Fundamental factors / ratios
- **Signal style:** Ranked buy/sell signal
- **Implementation notes:** Slower-frequency signal family.

### 87. Quality Strategy
- **Core idea:** Use profitability, balance-sheet, earnings-quality metrics.
- **Typical inputs:** Fundamental data
- **Signal style:** Ranked signal
- **Implementation notes:** Portfolio-style factor strategy.

### 88. Multi-Factor Composite
- **Core idea:** Combine value, momentum, quality, low-volatility, carry, etc.
- **Typical inputs:** Factor inputs and weights
- **Signal style:** Composite score + signal
- **Implementation notes:** Natural use case for your config builder.

### 89. Sentiment Strategy
- **Core idea:** Trade news, analyst, social, or options sentiment signals.
- **Typical inputs:** Sentiment feed + price data
- **Signal style:** Directional signal
- **Implementation notes:** Data-dependent external input.

### 90. Machine Learning Classifier
- **Core idea:** Model probability of next move/state and convert to trade signal.
- **Typical inputs:** Feature matrix, labels, model params
- **Signal style:** Probability/score + buy/sell
- **Implementation notes:** Should conform to same I/O contract.

### 91. Machine Learning Regressor
- **Core idea:** Predict future return or target and threshold into actions.
- **Typical inputs:** Feature matrix, regression target
- **Signal style:** Predicted return + signal
- **Implementation notes:** Useful when probability not desired.

### 92. Regime-Switching Strategy
- **Core idea:** Use HMM or similar to detect regime and switch sub-strategies.
- **Typical inputs:** Returns, vol, macro features
- **Signal style:** Regime label plus delegated signal
- **Implementation notes:** Excellent meta-strategy.

### 93. Ensemble / Voting Strategy
- **Core idea:** Combine outputs of multiple sub-strategies via voting or weighting.
- **Typical inputs:** Child strategy outputs, weights/rules
- **Signal style:** Composite final signal
- **Implementation notes:** Very aligned with your new framework.


## Execution Algorithms

### 94. TWAP
- **Core idea:** Split order evenly across time between start and end.
- **Typical inputs:** Parent order size, start/end time
- **Signal style:** Execution slices / schedule
- **Implementation notes:** Execution algo, not alpha strategy.

### 95. VWAP
- **Core idea:** Schedule slices against expected volume curve to track VWAP.
- **Typical inputs:** Parent order, historical/real-time volume curve
- **Signal style:** Execution schedule
- **Implementation notes:** Execution benchmark algorithm.

### 96. POV / Participation Rate
- **Core idea:** Trade as a fixed percentage of market volume.
- **Typical inputs:** Parent order, target participation, market volume
- **Signal style:** Dynamic child orders
- **Implementation notes:** Execution-style algorithm.

### 97. Implementation Shortfall / Arrival Price
- **Core idea:** Optimize execution versus decision price while balancing impact and risk.
- **Typical inputs:** Parent order, urgency/risk settings, market data
- **Signal style:** Adaptive execution schedule
- **Implementation notes:** Benchmark-driven execution algo.

### 98. Iceberg / Hidden Size
- **Core idea:** Expose partial displayed size while retaining larger hidden quantity.
- **Typical inputs:** Parent order, clip size
- **Signal style:** Order placement actions
- **Implementation notes:** Microstructure execution logic.

### 99. Sniper / Opportunistic Execution
- **Core idea:** Trade aggressively only when liquidity or price conditions are favorable.
- **Typical inputs:** Liquidity and spread conditions
- **Signal style:** Adaptive execution actions
- **Implementation notes:** Useful advanced execution family.

## Implementation guidance for the coder

### A. Reuse-first principle
The coder should first inspect the already-implemented algorithms and identify:
- the exact algorithm base class or interface
- helper methods for indicator calculation
- signal/state encoding conventions
- report-generation helpers
- visualization payload builders
- parameter validation pattern
- registration/discovery mechanism

All new algorithms should fit into that same architecture.

### B. Registration / discovery
Each algorithm should be discoverable by the Algorithm Designer Dashboard through the same registration system as the existing algorithms, so they can appear automatically in the library/configuration builder.

### C. Parameter schema
Each algorithm should expose a machine-readable parameter schema so the dashboard can:
- auto-generate parameter forms
- validate user input
- save configs
- publish configs to SmartTrade
- show defaults and descriptions

### D. Output normalization
Even if the internal math differs, all algorithms should emit normalized outputs so they can be composed using your framework’s AND / OR / pipeline / voting logic.

Suggested normalized output per bar:
- timestamp
- signal label: `buy`, `sell`, `neutral`
- numeric score (optional)
- confidence (optional)
- reason codes / triggered rule names (optional)

### E. Composition readiness
Algorithms should be implemented so they can later be combined easily into composite configurations:
- hard signal output
- optional soft score
- optional filter-only mode
- optional regime-only mode

### F. Practical rollout suggestion
Because this library is large, the coder may implement it in phases:
1. core trend + momentum + mean reversion set
2. statistical arbitrage set
3. volatility/options set
4. microstructure / execution set
5. macro / factor / ML / composite set

## Final note

This catalog is intentionally broader than a typical retail “top 10 strategies” list. It reflects the main families repeatedly cited in mainstream, academic, and execution-oriented references, including trend following, mean reversion, momentum, statistical arbitrage, market making/HFT, and benchmark-oriented execution algorithms. citeturn799880news12turn799880search6turn526753search0turn329530search0