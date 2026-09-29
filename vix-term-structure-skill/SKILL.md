---
name: vix-term-structure
description: Monitor the VIX term structure (VIX/VIX3M ratio) to set risk tone and position sizing. Fetches official CBOE data, classifies contango vs backwardation, applies the five-rule framework, and reports historical backtest statistics. Use when asked about VIX term structure, VIX backwardation/contango, volatility regime, risk tone, or whether volatility signals warrant de-risking.
license: MIT
---

# VIX Term Structure — Risk Tone & Position Sizing

A self-contained framework for reading volatility term structure as a **risk-tone and
position-sizing input**. Originates from a 視野環球財經 (Rhino Finance) member-only
video, *「用 VIX 期限結構定調風險和倉位」*, with the statistics independently
re-validated against CBOE history.

## The single most important caveat

> **This is a risk-adjustment tool, NOT a trade trigger.**

The framework's own author states this explicitly. Term structure does not tell you
what the market does tomorrow. Backwardation is a **coincident** indicator — it
confirms "things are scary right now," it does not warn ahead of time. Any output
that reads like a buy/sell signal is a misreading. Never use the ratio as the sole
condition for entering or exiting a position.

## Core definitions

- **Ratio = VIX / VIX3M** (30-day vs 3-month implied volatility)
- **Ratio < 1.0 → contango** (upward sloping): near-term vol < 3-month vol. The
  normal state, roughly 92% of trading days.
- **Ratio > 1.0 → backwardation** (inverted): near-term panic exceeds forward
  expectations. ~7.6% of trading days since 2009.
- **Percentile of the ratio** frames whether the current reading is extreme
  relative to history. Low percentile = complacency; high = stress.

## Workflow

### 1. Run the collector

```bash
python3 scripts/vix_term_structure.py            # human-readable report
python3 scripts/vix_term_structure.py --json     # structured JSON
python3 scripts/vix_term_structure.py --no-cache # offline, use cached CSVs
```

Exit code 0 = data OK, 1 = no usable data. The script downloads CBOE history CSVs
into `~/.cache/vix_term_structure` (override with `VIX_CACHE_DIR`) and falls back
to the cache when offline, so it is safe to run repeatedly.

### 2. Read the JSON fields

| Field | Meaning |
|---|---|
| `vix`, `vix3m`, `ratio` | Headline numbers |
| `curve` | VIX9D / VIX3M / VIX6M / VIX1Y / VVIX — the full term structure |
| `percentile` | Where today's ratio sits in the full history (0–100) |
| `streak_days` | Consecutive days with ratio > 1.0 |
| `last_uninversion`, `days_since_uninversion` | Most recent flip back below 1.0 |
| `state_id`, `state`, `action` | Classified regime + prescribed response |

### 3. Apply the five rules (evaluated in priority order)

| # | Condition | Action |
|---|---|---|
| 4 | Ratio > 1.0 for **≥ 3 weeks** | Manage positions for an S&P drawdown of at least 5–10%. Be cautious buying the dip mid-decline; wait for a confirmed bottoming pattern and a test of a significant structural level. |
| 3 | Ratio crosses above 1.0 **and** VIX breaks 25 quickly | Near-term panic has begun. Reduce beta, high-yield credit, and small caps. |
| 2 | VIX 16–22 **and** ratio 0.90–1.00 | Normally tense. Holding still is fine; avoid heavy or fully-loaded chasing. |
| 1 | VIX < 16 **and** ratio < 0.90 | Calm and protection is cheap. Hold normal size; buy longer-dated OTM puts, or rotate some growth-stock profits into higher-quality large caps. |
| 5 | Ratio falls **from 1.1+ back below 1.0** | Panic is receding and price has stopped falling — suitable for staged accumulation. |

Rules are checked 4 → 3 → mild backwardation → 1 → 2 → general contango, matching
the script's `state_id` output. `state_id` values:
`RULE1`, `RULE2`, `RULE3`, `RULE4`, `MILD_BACKWARDATION`, `GENERAL_CONTANGO`,
optionally suffixed with `+RULE5` when an un-inversion happened within 5 days.

### 4. Report it

Lead with the regime and what it implies for risk — not with a price prediction.
Combine the term structure with fundamentals and price structure before concluding.

## Data sources

All official CBOE, no API key:

```
# Delayed quote JSON (one symbol per request)
https://cdn.cboe.com/api/global/delayed_quotes/quotes/_VIX.json
https://cdn.cboe.com/api/global/delayed_quotes/quotes/_VIX3M.json   # _VIX9D _VIX6M _VIX1Y _VVIX
# Fields: data.close, data.prev_day_close, data.last_trade_time (ISO)

# Daily history CSV (DATE,OPEN,HIGH,LOW,CLOSE)
https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv
https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX3M_History.csv
https://cdn.cboe.com/api/global/us_indices/daily_prices/SPX_History.csv
```

Coverage: VIX 1990–, VIX3M 2009-09-18–, VIX6M 2008–, VIX9D 2011–, VIX1Y 2007–, SPX 1975–.
**The effective sample for ratio analysis starts 2009-09-18** (VIX3M's inception).

### Pitfalls

- **`SPX_History.csv` columns are `DATE,SPX` — there is no `CLOSE` column.** Generic
  parsers must fall back. The script handles this; naive reimplementations break here.
- VIX quotes often return `percent_change: null`. Compute it from
  `price_change / prev_day_close` yourself.
- The CBOE dashboard pages and thetrading.tools are JS-rendered — fetching the HTML
  yields an empty shell. Use the CSV/JSON endpoints above.
- The `last_trade_time` is a delayed quote, not a live tick. Label the report with
  the data date rather than implying real-time.
- The VIX cash index and VIX futures/ETPs (VXX, UVXY) are different instruments.
  This framework reads the **cash index term structure**; do not substitute a futures
  ETF price and expect the same ratio to behave identically.

## Historical statistics

Measured over 2009-09-18 → 2026-09, n = 3,955 (verified independently):

**Distribution of the ratio**
min 0.710 | p5 0.792 | **median 0.883** | p95 1.018 | max 1.344 | mean 0.893

**Backwardation episodes**
- 7.56% of trading days (299 / 3,955); the other 92.44% are contango.
- 94–105 episodes depending on how single-day events are grouped; **median duration
  1 day**, mean 3.2 days, longest **43 days** (2020-02-24 → 2020-04-23, peak 1.344).
- Frequency varies enormously by year: **0.0% in 2023**, 0.8% in 2017 and 2021,
  versus above 20% in 2011, 2018, and 2020.

**Highest peaks on record**
2020 COVID 1.344 | 2018-02 Volmageddon 1.327 | 2015-08 CNY devaluation 1.308 |
2025-04 tariffs 1.274 | 2011-07 US downgrade 1.260

**Forward S&P returns, conditional on regime**

| Horizon | After backwardation (n=324) | After contango (n≈3,937) |
|---|---|---|
| 20 days | +2.79% mean, 71.0% win | +0.88% mean, 67.3% win |
| 60 days | +6.88% mean, 80.9% win | +2.70% mean, 75.1% win |
| 120 days | +12.83% mean, 91.3% win | +5.45% mean, 77.5% win |

**VIX itself, 20 days after backwardation**: median **−26.3%**, mean −17.3% —
strong mean reversion.

> **Key conclusion: backwardation is not a bearish signal. It has historically marked
> a favourable short-to-medium-term entry window.** It is a coincident indicator —
> it confirms current fear, it does not forecast it. Directional predictive power is weak.

### Validation notes on the original framework's claims

The source material's specific figures were re-tested. Directionally sound, but two
numbers do not hold up:

| Claim in source | Re-measured | Verdict |
|---|---|---|
| 28 full inversions 2013–2026, 23 during ≥5% S&P drawdowns | 85 episodes (grouping differs); 42/85 began with drawdown ≥5% (49%) | Direction right, numbers don't reconcile |
| Only 7 were followed by another 5% drop within 30 days | 22/85 (26%) | Understated |
| 2018–2026, 4 weeks after inversion SPY median +1.45% vs +1.69% after contango | Inversion median **+3.66%**, contango **+1.63%** | Contango figure matches; inversion figure is badly off |
| Buying after un-inversion beats buying at first inversion | 1-month win rate 76.2% vs 70.5%, but median 2.38% vs 2.56%. 3-month win rate 77.1% vs 72.4%, median 4.45% vs 4.75% | Higher win rate holds; "much better average gain" does not |

**When citing this framework, use the re-measured numbers, not the source's.**

## Design intent

The value here is a **disciplined, repeatable risk lens**, not alpha. Two properties
make it worth running: it makes complacency vs stress explicit and numeric, and its
own backtest argues against overreacting to it. Use it to calibrate sizing, then
require an independent reason before changing a position.

## Files

```
SKILL.md                        this file
README.md                       quick-start and framework summary
LICENSE                         MIT
scripts/vix_term_structure.py   data collector / classifier
```
