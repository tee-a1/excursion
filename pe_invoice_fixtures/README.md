# PE Invoice Fixture Generator

Durable home for the daily AP-workflow test batch used to stress-test a
private-fund invoice processing system. Lives in this repo (not the
sandbox's `/tmp` scratchpad) because a daily routine firing for weeks needs
its generator code to survive container resets between firings — this repo
is the only persistent storage available in that environment.

This folder is unrelated to the rest of the `excursion` repo (the camping/
travel site) — it's just parked here because this was the repo attached to
the session that built it.

## What's here

- `lib.py` — PDF/email generation helpers (reused reportlab letterhead
  builder) and the fund reference data (5 funds, ex-coinvests, with real
  base currencies: MWP/MCO-I/MCP-III/MGE-I = GBP, MIP-I = USD).
- `scenarios.py` — a pool of invoice templates, each a fictional vendor
  tied to a fund and a specific thing worth testing (standard single-fund
  invoice, or a deliberate coding trap: fund-vs-ManCo misattribution,
  multi-GL split within one fund, NAV-period cutoff timing).
- `daily_batch.py` — orchestrator. Reads `log.json` (send history), picks
  2–3 scenarios for "today" favoring ones not used in the last 3 sends,
  builds the PDFs/emails into an output directory, and writes
  `manifest.json` (what was built, for composing the delivery email) plus
  `log_updated.json` (the history file to commit back over `log.json`).
- `log.json` — append-only history of what's been sent. Not present until
  the first real send; each firing commits its own entry back.
- `requirements.txt` — `reportlab`, `openpyxl`. The sandbox doesn't
  persist installed packages either, so install these fresh each firing.

## Running it

```
python3 -m pip install -r requirements.txt
python3 daily_batch.py <output_dir> [YYYY-MM-DD]
```

`daily_batch.py` only builds files — it does not send email or touch git.
The routine that calls it is responsible for emailing the manifest's items
as attachments, then committing `log_updated.json` over `log.json` and
pushing.

## Adding a new scenario

Write a `build_xxx(outdir, today, seq) -> dict` in `scenarios.py` matching
the existing builders' signature and return shape, and add it to the
`SCENARIOS` dict at the bottom of that file.
