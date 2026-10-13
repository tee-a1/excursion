# -*- coding: utf-8 -*-
"""
Orchestrator for the daily AP test batch.

Usage:
    python3 daily_batch.py <output_dir> [YYYY-MM-DD]

Reads log.json (sent-history, committed alongside this file) to avoid
repeating the same scenario on back-to-back days, builds 2-3 invoices for
"today" (today's date if no date arg given), writes a manifest.json into
<output_dir> describing what was built (for the email step), and prints the
updated log.json back to stdout-adjacent log_updated.json in <output_dir>
so the caller can review + commit it.

This script only builds files locally — it does not send email or touch
git itself. The routine that calls it is responsible for: git pull first,
reading manifest.json to compose + send the email via Gmail, then
committing log_updated.json back over log.json and pushing.
"""
import sys
import os
import json
import random
from datetime import date, datetime, time, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from scenarios import SCENARIOS

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(HERE, "log.json")


def load_log():
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            return json.load(f)
    return {"sends": []}


def recent_scenario_ids(log, lookback=3):
    ids = []
    for entry in log["sends"][-lookback:]:
        ids.extend(entry.get("scenario_ids", []))
    return set(ids)


def pick_today_batch(log, rng):
    all_ids = list(SCENARIOS.keys())
    recent = recent_scenario_ids(log, lookback=3)
    available = [i for i in all_ids if i not in recent] or all_ids

    n = rng.choice([2, 2, 3])  # mostly 2, sometimes 3 — realistic daily AP trickle
    chosen = []
    pool = available[:]
    rng.shuffle(pool)
    while pool and len(chosen) < n:
        chosen.append(pool.pop())
    # top up from the full set if the "avoid recent" pool was too small
    while len(chosen) < n:
        candidate = rng.choice(all_ids)
        if candidate not in chosen:
            chosen.append(candidate)
    return chosen


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    today_date = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    # tz-aware datetime: builders use this for both display (.strftime) and email Date headers
    today = datetime.combine(today_date, time(9, 0), tzinfo=timezone.utc)
    os.makedirs(outdir, exist_ok=True)

    log = load_log()
    seq = len(log["sends"]) + 1  # monotonically increasing, used to vary invoice numbers/amounts

    rng = random.Random(f"{today_date.isoformat()}-{seq}")
    chosen_ids = pick_today_batch(log, rng)

    results = []
    for scenario_id in chosen_ids:
        builder = SCENARIOS[scenario_id]
        result = builder(outdir, today, seq)
        results.append(result)
        seq += 1

    manifest = {
        "date": today_date.isoformat(),
        "items": results,
    }
    with open(os.path.join(outdir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    log["sends"].append({
        "date": today_date.isoformat(),
        "scenario_ids": chosen_ids,
        "invoice_nos": [r["invoice_no"] for r in results],
    })
    with open(os.path.join(outdir, "log_updated.json"), "w") as f:
        json.dump(log, f, indent=2)

    print(f"Built {len(results)} invoices for {today_date.isoformat()}:")
    for r in results:
        print(f"  [{r['kind']:8s}] {r['fund']:8s} {r['vendor']:38s} {r['invoice_no']:16s} {r['amount']}")
    print(f"\nManifest: {os.path.join(outdir, 'manifest.json')}")
    print(f"Updated log (review, then commit over log.json): {os.path.join(outdir, 'log_updated.json')}")


if __name__ == "__main__":
    main()
