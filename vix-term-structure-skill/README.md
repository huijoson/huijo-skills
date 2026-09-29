# VIX Term Structure

**A risk-tone and position-sizing lens based on the VIX/VIX3M ratio.**

Fetches official CBOE data, classifies the volatility term structure as contango or
backwardation, applies a five-rule framework, and reports independently verified
backtest statistics. Ships as a self-contained script with no API keys and no
dependencies beyond the Python standard library.

```bash
python3 scripts/vix_term_structure.py          # human-readable report
python3 scripts/vix_term_structure.py --json   # structured JSON
```

Example output:

```
=== VIX 期限結構監看 | 報告時間 2026-09-29 16:23 (台北) ===
資料截止：2026-09-28（CBOE delayed quote）

VIX          =  16.07
VIX3M        =  18.23
VIX/VIX3M    = 0.8815   →  升水 CONTANGO

比率歷史百分位 = 48.6%（越低＝市場越自滿）　統計區間 2009-09-18 ~ 2026-09-28（n=4282）
連續 >1 天數   = 0 天

【狀態】⚪ 一般 contango
【對應操作】正常狀態，無特殊動作
```

## Read this first

> This is a **risk-adjustment tool, not a trade trigger.** The framework's own author
> says so, and its backtest agrees.

Term structure does not predict tomorrow's direction. Backwardation is a
**coincident** indicator: it confirms "the market is frightened right now," it does
not warn in advance. Use it to calibrate how much risk you are willing to carry —
then require an independent reason before you actually change a position.

## What the ratio means

**Ratio = VIX / VIX3M** — 30-day vs 3-month implied volatility.

- **< 1.0 → contango** (normal upward slope). ~92% of trading days since 2009.
- **> 1.0 → backwardation** (inverted, near-term panic). ~7.6% of trading days.
- **Percentile** places today's reading against the full history: low = complacency,
  high = stress.

## The five rules

| # | Condition | Action |
|---|---|---|
| 4 | Ratio > 1.0 for **≥ 3 weeks** | Manage for an S&P drawdown of at least 5–10%. Wait for a confirmed bottom, don't catch the falling knife. |
| 3 | Ratio crosses above 1.0 **and** VIX quickly breaks 25 | Near-term panic has begun. Cut beta, high-yield credit, small caps. |
| 2 | VIX 16–22 **and** ratio 0.90–1.00 | Normally tense. Holding still is fine; don't chase heavily. |
| 1 | VIX < 16 **and** ratio < 0.90 | Calm, protection is cheap. Hold normal size; buy longer-dated OTM puts or rotate growth profits into quality large caps. |
| 5 | Ratio falls **from 1.1+ back below 1.0** | Panic receding, price stopped falling — suitable for staged accumulation. |

Priority order is 4 → 3 → mild backwardation → 1 → 2 → general contango.

## Key historical findings

Sample 2009-09-18 → 2026-09, n = 3,955.

- Ratio: min 0.710 | p5 0.792 | **median 0.883** | p95 1.018 | max 1.344
- Backwardation: **7.56% of days**, median duration **1 day**, longest **43 days**
  (COVID, Feb–Apr 2020, peak 1.344)
- Yearly frequency swings wildly: **0.0% in 2023** vs **>20% in 2011 / 2018 / 2020**

**Forward S&P returns after each regime**

| Horizon | After backwardation | After contango |
|---|---|---|
| 20 days | +2.79%, 71.0% win | +0.88%, 67.3% win |
| 60 days | +6.88%, 80.9% win | +2.70%, 75.1% win |
| 120 days | +12.83%, 91.3% win | +5.45%, 77.5% win |

VIX itself, 20 days after backwardation: **median −26.3%**.

**Backwardation is not a bearish signal** — historically it has marked a favourable
entry window for the following weeks and months. Treat it as confirmation of present
stress, not a forecast.

## Data sources

Official CBOE, no API key:

- Delayed quotes: `https://cdn.cboe.com/api/global/delayed_quotes/quotes/_VIX.json`
  (also `_VIX3M`, `_VIX9D`, `_VIX6M`, `_VIX1Y`, `_VVIX`)
- History CSVs: `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv`
  (also `VIX3M`, `VIX9D`, `VIX6M`, `VIX1Y`, `SPX`)

Ratio analysis is meaningful from **2009-09-18**, when VIX3M began.

## Notes and pitfalls

- `SPX_History.csv` has columns `DATE,SPX` — **there is no `CLOSE` column.** The
  script falls back correctly; naive reimplementations break here.
- VIX quote JSON often returns `percent_change: null` — compute it yourself.
- CBOE dashboard pages are JS-rendered and return empty shells to a plain fetch.
- The VIX **cash index** is not VIX futures or VIX ETPs (VXX/UVXY). This framework
  reads the cash index term structure.
- History CSVs are cached under `~/.cache/vix_term_structure` (override with
  `VIX_CACHE_DIR`) so the script still runs offline via `--no-cache`.

## Verification notes

The source framework's own figures were re-tested against CBOE history. Direction is
sound, but two specific numbers do not reproduce — most notably the claim that
4 weeks after an inversion SPY's median return is +1.45% (measured: **+3.66%**).
See `SKILL.md` for the full comparison. **Cite the re-measured numbers.**

## Layout

```
SKILL.md                        framework, rules, statistics, pitfalls
README.md                       this file
LICENSE                         MIT
scripts/vix_term_structure.py   collector + classifier (stdlib only)
```

## Requirements

Python 3.8+. Standard library only — no `pip install` needed.

## License

MIT. See `LICENSE`.

Statistics are provided for research and educational purposes. Nothing here is
investment advice.
