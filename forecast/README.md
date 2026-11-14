# forecast/ — EXPERIMENTAL

One-month **detection-level outlook** for Argentina, built on the harmonized monthly calendar.
Owner: P2 Bahtiyar. Not part of the pipeline, not shown in the app.

**Version used in the app:** `pipeline/forecast.py` (P4 Barış) — the same normal + persistence model on a
30-day rolling window, with a correction for the regional total (summing back-transformed log predictions
underestimates it: Argentina −24%, La Rioja −44%). This folder stays the monthly prototype.

This is **not a fire prediction**. It uses no weather, drought or fuel data — only
1. the seasonal normal of each 1° cell (same calendar month, 2003 onwards), and
2. last month's deviation from that normal (the cell itself and the regional mean).

Unit: harmonized (MODIS-equivalent) detections per 1° cell and month.

## Run

```bash
python forecast/forecast.py     # needs data/monthly_grid.parquet (output of pipeline/harmonize.py)
```

Outputs in `forecast/out/`: `outlook_cells.csv`, `backtest.json`, `outlook_1month.png`.

## Backtest (2015–2025, 132 months, 230 cells; each year fitted on earlier years only)

| Measure | Result | Reference |
|---|---|---|
| Skill vs. seasonal normal (1 − MSE ratio, log space) | 0.25 | 0 = no better than the normal |
| Direction right (above / below normal) | 75% | chance = 50% |
| Regional total, mean absolute log error | 0.48 | normal only: 0.53 |

Skill drops to 0.13 at two months and below 0.1 from three months on, hence the one-month horizon.

## Known miss

Outlook for November 2026: about 1,318 detections (10–90% range 838–3,617; normal about 2,698).
The first 13 days of the month already reached 1,904. Persistence cannot see a sudden change;
the outlook is therefore not shown in the app.
