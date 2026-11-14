# Experimental 30-day detection outlook

Owner: P4 Barış (method: P2 Bahtiyar) · `pipeline/forecast.py` · data through 2026-11-12 · outlook window **2026-11-15 → 2026-12-14**

Outlook for **detection counts** (harmonized NASA FIRMS, MODIS-equivalent) — not a fire forecast.

Backtest 2015–2025, Argentina 1° cells, 132 start dates (each year fitted on earlier years only):
- direction right **74%** (chance 50%, n=16,710)
- skill vs. seasonal normal **0.23** (1 − MSE ratio, log scale); positive in every year (0.12–0.29)
- argentina 30-day total: bias -0.1%, error (log) 0.42 vs 0.52 for the normal
- la_rioja 30-day total: bias -11.6%, error (log) 0.48 vs 0.50 for the normal

| Outlook | Expected | 80% range | Normal (10-yr avg) | Ratio |
|---|---|---|---|---|
| Argentina | 2,877 | 1,500–5,446 | 3,662 | 0.79× |
| La Rioja box | 247 | 114–463 | 274 | 0.90× |

Inputs: NASA FIRMS only. NASA POWER weather and a NASA MERRA-2 El Niño index were tested and did not improve skill (branch `p4/forecast-experiments`).
