# P2 — Harmonization: Bahtiyar

Shared rules and the schedule are in the root `CLAUDE.md`, the schema is in **`docs/CONTRACT.md`** (current version). This file covers only your role.

## Files you own (Claude writes ONLY to these)
- `pipeline/harmonize.py`

## Input / output (CONTRACT §7.2)
- Input: `data/hotspots.parquet` + `data/satellite_coverage.csv` (P1). Until 12:30, develop with `data/sample/` + `data/mock/`.
- Outputs:
  - `data/hotspots_harm.parquet` — same schema, `weight_harm` filled → `validate_hotspots(df, "harm")` before writing
  - `data/monthly_grid.parquet` — CONTRACT §7.2 table
  - `data/k_factors.csv` — at least `k, n_modis, n_viirs, fallback` + the columns of the strata you choose

## Task
**You are the owner of the method** (CONTRACT §6). The contract only requires this: `Σ weight_harm` =
MODIS-equivalent detection estimate, values ≥ 0, no NaN. Describe the method you choose in 5–10 lines in the docstring
at the top of `harmonize.py` (P3 and P6 will read it from there). Method A below is a **starting suggestion**.
1. **Grid + month** — 0.25° cell (`cell_lat/cell_lon` = cell center), counts per cell × month × satellite.
2. **Helper columns** (do NOT WRITE them to the parquet, only in the computation):
   - `lat_band` = |lat| 10° slice: `"20-30"`, `"30-40"`, `"40-50"`, `"50-60"` …
   - `season` = local season: in the southern hemisphere shift the month by +6, then DJF=winter, MAM=spring,
     JJA=summer, SON=autumn.
3. **k coefficients** — Training: **Argentina, 2012–2021**. For each `(lat_band, season, satellite)`
   `k = Σ MODIS / Σ VIIRS_satellite` — only the months in which both MODIS and that VIIRS satellite were active.
   - Few samples (n_modis < 30): merge all bands for the same `season`+`satellite` → `fallback=True`.
   - Band not in the training data (e.g. if Germany 50-60 is empty): nearest band / season average, `fallback=True`.
4. **weight_harm** —
   - MODIS, date < S-NPP first date → 1.0; after that → 0.0
   - VIIRS → `k / n_active_viirs(acq_date)`, active satellite = between the **first AND last**
     date in `satellite_coverage.csv` (S-NPP ended on 2026-11-02)
   - Period in which Terra was the only MODIS (2000-11 → 2002-07): the harmonized series stays at half level →
     either Terra weight 2 or the calendar starts from 2003. Decision at the 10:30 meeting.
5. **Apply: everywhere** (outside Argentina as well).
6. **Print a summary** — for Argentina, annual raw total vs harmonized total; does the 2012/2018/2023 jump
   disappear in the harmonized series?

## Submissions
| Time | What | To whom |
|---|---|---|
| 14:30 | `k_factors.csv` first version | Oğuzhan (P3), Barış |
| 16:30 | `hotspots_harm.parquet` + `monthly_grid.parquet` | Barış (P4), Oğuzhan (P3) |

## Done check
- [ ] `weight_harm` is never NaN, all ≥ 0
- [ ] Argentina 2012–2021 `Σ weight_harm` ≈ `Σ MODIS` (difference < 10%)
- [ ] Every row in the k table has an `n_modis`, `n_viirs` value; fallbacks are flagged
- [ ] The raw annual series has the 2012/2018/2023 steps, the harmonized one does not (send the plot to P6)

## Note for Claude
- `pipeline/validate.py` belongs to Oğuzhan; test/metric code is not written there, and not here either.
- Do **not train** k on the test years (2022–2024) — data leakage.
- If the **meaning** of `weight_harm` (Σ = MODIS-equivalent) needs to change, do not write code; say "ask Barış".
  Changing the method is allowed, but update the docstring and notify Oğuzhan.
- Do not write the coefficient up as "validated"; validation happens with P3's metrics.
