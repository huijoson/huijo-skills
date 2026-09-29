#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIX Term Structure Monitor — data collector
================================================================
Data sources (both official CBOE, no API key required):
  1. Delayed quotes JSON : cdn.cboe.com/api/global/delayed_quotes/quotes/_VIX.json
  2. Daily history CSV   : cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv

Output: structured plain text on stdout.
  - Standalone use: just read it yourself.
  - Agent use: the text is injected into an LLM prompt that writes the narrative report.

Usage
-----
    python3 vix_term_structure.py               # human-readable report
    python3 vix_term_structure.py --json        # machine-readable JSON
    python3 vix_term_structure.py --no-cache    # force re-download of history CSVs

Environment
-----------
    VIX_CACHE_DIR   cache directory for history CSVs (default: ~/.cache/vix_term_structure)
    VIX_INSECURE=1  disable TLS certificate verification (only for broken corporate proxies)

Exit codes: 0 = ok, 1 = no usable data (both live quotes and cache failed).
"""

import argparse
import csv
import io
import json
import os
import ssl
import statistics as st
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
TAIPEI = timezone(timedelta(hours=8))
CACHE = os.environ.get("VIX_CACHE_DIR") or os.path.expanduser("~/.cache/vix_term_structure")
os.makedirs(CACHE, exist_ok=True)

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

if os.environ.get("VIX_INSECURE") == "1":
    CTX = ssl.create_default_context()
    CTX.check_hostname = False
    CTX.verify_mode = ssl.CERT_NONE
else:
    CTX = ssl.create_default_context()

QUOTE_URL = "https://cdn.cboe.com/api/global/delayed_quotes/quotes/{sym}.json"
HIST_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/{sym}_History.csv"

QUOTE_SYMS = ["_VIX", "_VIX3M", "_VIX9D", "_VIX6M", "_VIX1Y", "_VVIX"]
HIST_SYMS = ["VIX", "VIX3M", "VIX9D", "VIX6M", "VIX1Y", "SPX"]


def fetch(url, timeout=45):
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}
    )
    return urllib.request.urlopen(req, timeout=timeout, context=CTX).read()


# ----------------------------------------------------------------------
# 1. Live (delayed) quotes
# ----------------------------------------------------------------------
def get_quotes():
    quotes = {}
    for sym in QUOTE_SYMS:
        key = sym.lstrip("_")
        try:
            raw = fetch(QUOTE_URL.format(sym=sym)).decode("utf-8", "ignore")
            d = json.loads(raw)["data"]
            quotes[key] = {
                "last": d.get("close"),
                "prev": d.get("prev_day_close"),
                "chg": d.get("price_change"),
                "ts": d.get("last_trade_time"),
            }
        except Exception as e:  # noqa: BLE001 - degrade gracefully, report per-symbol
            quotes[key] = {"err": repr(e)[:80]}
    return quotes


# ----------------------------------------------------------------------
# 2. History CSVs (refresh each run, fall back to cache offline)
# ----------------------------------------------------------------------
def history(sym, use_cache=True):
    path = os.path.join(CACHE, f"{sym}.csv")
    if use_cache:
        try:
            blob = fetch(HIST_URL.format(sym=sym), 90)
            if len(blob) > 500:
                with open(path, "wb") as fh:
                    fh.write(blob)
        except Exception:
            pass  # offline / blocked -> use whatever is cached

    out = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for row in csv.DictReader(io.StringIO(fh.read())):
                try:
                    key = datetime.strptime(row["DATE"].strip(), "%m/%d/%Y").strftime("%Y-%m-%d")
                    # NOTE: SPX_History.csv columns are DATE,SPX -- there is no CLOSE column.
                    val = row.get("CLOSE") or row.get("SPX") or row.get("VVIX")
                    out[key] = float(val)
                except Exception:
                    pass
    return out


# ----------------------------------------------------------------------
# 3. Compute the snapshot
# ----------------------------------------------------------------------
def build_snapshot(use_cache=True):
    quotes = get_quotes()
    hist = {s: history(s, use_cache) for s in HIST_SYMS}

    days = sorted(set(hist["VIX"]) & set(hist["VIX3M"]))
    if not days:
        return None
    ratio_hist = [hist["VIX"][d] / hist["VIX3M"][d] for d in days]

    live_ok = all(
        isinstance(quotes.get(s, {}).get("last"), (int, float)) for s in ("VIX", "VIX3M")
    )
    if live_ok and quotes["VIX"]["last"] and quotes["VIX3M"]["last"]:
        vix = float(quotes["VIX"]["last"])
        vix3 = float(quotes["VIX3M"]["last"])
        asof = (quotes["VIX"].get("ts") or "")[:10]
        source = "CBOE delayed quote"
    else:
        vix, vix3 = hist["VIX"][days[-1]], hist["VIX3M"][days[-1]]
        asof, source = days[-1], "CBOE history CSV (live quote unavailable)"
    ratio = vix / vix3

    def q(sym):
        val = quotes.get(sym, {}).get("last")
        if isinstance(val, (int, float)):
            return float(val)
        if sym in hist and days[-1] in hist[sym]:
            return hist[sym][days[-1]]
        return None

    # consecutive days above 1.0
    streak = 0
    for r in reversed(ratio_hist):
        if r > 1.0:
            streak += 1
        else:
            break
    if ratio > 1.0 and streak == 0:
        streak = 1

    percentile = 100.0 * sum(1 for r in ratio_hist if r < ratio) / len(ratio_hist)

    # most recent un-inversion
    last_uninv = None
    for i in range(len(days) - 1, 0, -1):
        if ratio_hist[i] <= 1.0 and ratio_hist[i - 1] > 1.0:
            last_uninv = days[i]
            break
    days_since_uninv = None
    if last_uninv:
        days_since_uninv = (
            datetime.strptime(days[-1], "%Y-%m-%d") - datetime.strptime(last_uninv, "%Y-%m-%d")
        ).days

    # ------------------------------------------------------------------
    # 4. State classification -- the framework's 5 rules, in priority order
    # ------------------------------------------------------------------
    if ratio > 1.0 and streak >= 15:
        state_id, state, emoji = "RULE4", "倒掛持續三週以上", "🔴"
        action = ("按標普至少 5-10% 修正預期管理倉位；下跌途中抄底慎重，"
                  "多等強止跌型態與重要結構位置測試")
    elif ratio > 1.0 and vix >= 25:
        state_id, state, emoji = "RULE3", "近端恐慌已開始", "🟠"
        action = "降低 Beta／垃圾債／小盤股持倉"
    elif ratio > 1.0:
        state_id, state, emoji = "MILD_BACKWARDATION", "輕度倒掛（未達規則3/4門檻）", "🟠"
        action = "警戒但不急動；觀察是否持續 >1 及 VIX 是否衝破 25"
    elif vix < 16 and ratio < 0.90:
        state_id, state, emoji = "RULE1", "平靜＋保護便宜", "🟢"
        action = ("可維持正常倉位；適合買遠期價外 put 保護，"
                  "或把部分成長股利潤換成質量更高的大型公司")
    elif 16 <= vix <= 22 and 0.90 <= ratio <= 1.00:
        state_id, state, emoji = "RULE2", "正常偏緊張", "🟡"
        action = "正常偏緊張，倉位不動也可以；少做重倉／滿倉追高"
    else:
        state_id, state, emoji = "GENERAL_CONTANGO", "一般 contango", "⚪"
        action = "正常狀態，無特殊動作"

    rule5 = (
        ratio <= 1.0 and last_uninv and days_since_uninv is not None and days_since_uninv <= 5
    )
    if rule5:
        state += " ＋ 剛解除倒掛"
        action += "｜★ 倒掛剛解除（規則5）：恐慌消退、價格止跌，適合分批加倉"
        state_id += "+RULE5"

    curve = {
        s: q(s) for s in ("VIX9D", "VIX3M", "VIX6M", "VIX1Y", "VVIX")
    }

    return {
        "asof": asof,
        "source": source,
        "vix": vix,
        "vix3m": vix3,
        "ratio": ratio,
        "curve": curve,
        "percentile": percentile,
        "percentile_window": [days[0], days[-1], len(days)],
        "streak_days": streak,
        "last_uninversion": last_uninv,
        "days_since_uninversion": days_since_uninv,
        "rule5_active": bool(rule5),
        "state_id": state_id,
        "state": state,
        "emoji": emoji,
        "action": action,
    }


# ----------------------------------------------------------------------
# 5. Renderers
# ----------------------------------------------------------------------
def render_text(s):
    c = s["curve"]
    now = datetime.now(TAIPEI)
    lines = []
    lines.append(f"=== VIX 期限結構監看 | 報告時間 {now:%Y-%m-%d %H:%M} (台北) ===")
    lines.append(f"資料截止：{s['asof']}（{s['source']}）")
    lines.append("")
    lines.append(f"VIX          = {s['vix']:6.2f}")
    lines.append(f"VIX3M        = {s['vix3m']:6.2f}")
    direction = "倒掛 BACKWARDATION" if s["ratio"] > 1 else "升水 CONTANGO"
    lines.append(f"VIX/VIX3M    = {s['ratio']:.4f}   →  {direction}")
    lines.append("")
    for label, key in (("VIX9D", "VIX9D"), ("VIX6M", "VIX6M"), ("VIX1Y", "VIX1Y"), ("VVIX", "VVIX")):
        val = c.get(key)
        lines.append(f"{label:<12} = {val:6.2f}" if val else f"{label:<12} = n/a")
    lines.append("")
    w = s["percentile_window"]
    lines.append(f"比率歷史百分位 = {s['percentile']:.1f}%（越低＝市場越自滿）　"
                 f"統計區間 {w[0]} ~ {w[1]}（n={w[2]}）")
    lines.append(f"連續 >1 天數   = {s['streak_days']} 天")
    if s["last_uninversion"]:
        lines.append(f"上次倒掛解除   = {s['last_uninversion']}"
                     f"（距今 {s['days_since_uninversion']} 個日曆日）")
    lines.append("")
    lines.append(f"【狀態】{s['emoji']} {s['state']}")
    lines.append(f"【對應操作】{s['action']}")
    lines.append("")
    lines.append("--- 歷史統計參考（2009-09-18 起，n=3955）---")
    lines.append("比率>1（倒掛）發生頻率：7.6% 的交易日；中位持續 1 天，最長 43 天（2020-02~04）")
    lines.append("倒掛後 20 日 S&P：平均 +2.8%、勝率 71%；升水後：平均 +0.9%、勝率 67%")
    lines.append("倒掛後 20 日 VIX 自身：中位 -26%（均值回歸明顯）")
    lines.append("→ 倒掛是「確認現在很慌」的同步指標，不是提前報警；方向預測力弱")
    return "\n".join(lines)


def render_json(s):
    return json.dumps(s, indent=2, ensure_ascii=False)


def main():
    ap = argparse.ArgumentParser(description="VIX term structure monitor")
    ap.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    ap.add_argument("--no-cache", action="store_true",
                    help="skip refreshing history CSVs; use local cache only")
    args = ap.parse_args()

    snap = build_snapshot(use_cache=not args.no_cache)
    if snap is None:
        print("ERROR: no usable data (live quotes failed and no cached history).", file=sys.stderr)
        return 1
    print(render_json(snap) if args.json else render_text(snap))
    return 0


if __name__ == "__main__":
    sys.exit(main())
