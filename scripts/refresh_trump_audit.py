"""Refresh public Trump market facts on T7 without changing earlier snapshots.

Uses the repository's newer saved Trump tape as a seed, queries both Kalshi
partitions, and downloads complete tapes only where reported volume differs.
No credentials, portfolio endpoints, or order endpoints are used.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time

import pandas as pd
import requests

BASE = "https://api.elections.kalshi.com/trade-api/v2"
SERIES = ("KXTRUMPMENTION", "KXTRUMPMENTIONB")
CALENDAR = "https://media-cdn.factba.se/rss/json/trump/calendar-full.json"


def get(path, params=None):
    for attempt in range(5):
        try:
            response = requests.get(BASE + path, params=params, timeout=30)
            if response.status_code in {429, 500, 502, 503, 504}:
                response.raise_for_status()
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            if attempt == 4:
                raise
            time.sleep(1.5 * (attempt + 1))


def paginate(path, key, params):
    params = dict(params)
    seen = set()
    while True:
        response = get(path, params)
        yield from response[key]
        cursor = response.get("cursor")
        if not cursor:
            break
        if cursor in seen:
            raise RuntimeError(f"Repeated cursor at {path}")
        seen.add(cursor)
        params["cursor"] = cursor


def price(record, stem):
    dollars = record.get(stem + "_dollars")
    return float(dollars) * 100 if dollars is not None else record.get(stem)


def normalize_market(row):
    word = row.get("yes_sub_title") or (row.get("custom_strike") or {}).get("Word") or ""
    result = row.get("result", "")
    normalized = {k: row.get(k) for k in ["ticker", "event_ticker", "title", "status", "can_close_early"]}
    normalized.update({
        "yes_sub_title": word, "word_raw": word,
        "result": result, "series": row["ticker"].split("-")[0],
        "volume": float(row.get("volume_fp") or row.get("volume") or 0),
        "is_resolved": result in {"yes", "no"},
        "is_dnq": "does not qualify" in word.lower(), "source": "api", "subgroup": "trump",
    })
    for name in ["created_time", "open_time", "close_time", "occurrence_datetime", "settlement_ts", "expected_expiration_time"]:
        normalized[name] = pd.to_datetime(row.get(name), utc=True)
    for name in ["last_price", "yes_bid", "yes_ask"]:
        normalized[name] = price(row, name)
    return normalized


def run(destination, seed):
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "collection.json"
    if manifest_path.exists() and json.loads(manifest_path.read_text()).get("complete"):
        raise RuntimeError("Snapshot is complete; use a new destination to refresh again")
    manifest = {"started_utc": datetime.now(timezone.utc).isoformat(), "api_base": BASE, "seed": str(seed), "universe": SERIES, "complete": False}
    manifest["cutoff"] = get("/historical/cutoff")
    payloads, counts = [], {}
    for series in SERIES:
        (destination / f"{series}_series.json").write_text(json.dumps(get(f"/series/{series}")))
        for endpoint in ["/historical/markets", "/markets"]:
            rows = list(paginate(endpoint, "markets", {"series_ticker": series, "limit": 1000}))
            counts[f"{endpoint}:{series}"] = len(rows)
            payloads.extend([{**row, "_audit_endpoint": endpoint} for row in rows])
            print(endpoint, series, len(rows), flush=True)
    manifest["endpoint_counts"] = counts
    (destination / "api_markets.json").write_text(json.dumps(payloads))
    markets = pd.DataFrame(map(normalize_market, payloads)).drop_duplicates("ticker", keep="last")
    markets.to_parquet(destination / "markets.parquet", index=False)
    calendar_response = requests.get(CALENDAR, timeout=45)
    calendar_response.raise_for_status()
    calendar_response.json()
    (destination / "factbase_calendar.json").write_bytes(calendar_response.content)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    tape = pd.read_parquet(seed / "trades.parquet")
    resolved = markets[markets.is_resolved].copy()
    seed_volume = tape.groupby("ticker")["count"].sum()
    resolved["seed_volume"] = resolved.ticker.map(seed_volume).fillna(0)
    wanted = resolved[(resolved.volume - resolved.seed_volume).abs() > .01]
    cache = destination / "api_trades"
    cache.mkdir(exist_ok=True)
    cutoff = pd.Timestamp(manifest["cutoff"]["trades_created_ts"])

    def fetch(row):
        dest = cache / f"{row['ticker']}.parquet"
        if dest.exists():
            return
        records = []
        endpoints = []
        if row["open_time"] < cutoff:
            endpoints.append("/historical/trades")
        if row["close_time"] >= cutoff:
            endpoints.append("/markets/trades")
        for endpoint in endpoints:
            for trade in paginate(endpoint, "trades", {"ticker": row["ticker"], "limit": 1000}):
                records.append({"trade_id": trade["trade_id"], "ticker": row["ticker"],
                    "created_time": pd.Timestamp(trade["created_time"]),
                    "yes_price_cents": price(trade, "yes_price"),
                    "count": float(trade.get("count_fp") or trade.get("count") or 0),
                    "taker_side": trade.get("taker_side"), "source": endpoint})
        frame = pd.DataFrame(records, columns=tape.columns)
        frame.to_parquet(dest, index=False)

    errors = []
    print(f"Refreshing complete tapes for {len(wanted)} markets", flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fetch, row): row["ticker"] for row in wanted.to_dict("records")}
        for i, future in enumerate(as_completed(futures), 1):
            try:
                future.result()
            except Exception as exc:
                errors.append({"ticker": futures[future], "error": str(exc)})
            if i % 100 == 0 or i == len(futures):
                print(f"Downloaded {i}/{len(futures)}; errors {len(errors)}", flush=True)
    (destination / "trade_errors.json").write_text(json.dumps(errors, indent=2))
    if errors:
        raise RuntimeError("Download errors recorded; rerun this destination to resume")
    refreshed = [pd.read_parquet(p) for p in sorted(cache.glob("KX*.parquet"))]
    trades = pd.concat([tape, *refreshed], ignore_index=True).drop_duplicates("trade_id", keep="last")
    trades = trades[trades.ticker.isin(markets.ticker)]
    trades["created_time"] = pd.to_datetime(trades.created_time, utc=True)
    trades.to_parquet(destination / "trades.parquet", index=False)
    resolved["collected_volume"] = resolved.ticker.map(trades.groupby("ticker")["count"].sum()).fillna(0)
    resolved["volume_difference"] = resolved.collected_volume - resolved.volume
    resolved.to_parquet(destination / "trade_coverage.parquet", index=False)
    manifest.update({"finished_utc": datetime.now(timezone.utc).isoformat(), "complete": True,
        "market_rows": len(markets), "binary_resolved": int(markets.is_resolved.sum()),
        "trade_rows": len(trades), "trade_max_utc": str(trades.created_time.max()),
        "volume_mismatch_markets": int((resolved.volume_difference.abs() > .01).sum()),
        "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [
            destination / "markets.parquet", destination / "trades.parquet", destination / "api_markets.json", destination / "factbase_calendar.json"]}})
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--seed", type=Path, default=Path("/Volumes/T7/mention-markets/longshot-audit/2026-09-04"))
    args = parser.parse_args()
    run(args.destination, args.seed)
