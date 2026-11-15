# Data & Interface Contract v1.5

Owner: **P4 Barış**. Code counterpart: [`contract.py`](../contract.py) (constants + `validate_hotspots()`).
Changes → P4 first. Every change is recorded in the **Changelog** at the bottom.

Sources: FIRMS attribute table (earthdata.nasa.gov → FIRMS → Active Fire Data Attributes).
✅ Real CSV headers verified by P1 (v1.2, §3).

---

## 1. `data/hotspots.parquet` — canonical schema

One row = one **thermal anomaly pixel** (hotspot) detected by one satellite in one overpass.
A row is **NOT a verified wildfire event** (see §8 Terminology).

| # | Column | dtype | Required | FIRMS source | Note |
|---|---|---|---|---|---|
| 1 | `latitude` | float64 | ✅ | `latitude` | pixel center (MODIS 1 km, VIIRS 375 m) |
| 2 | `longitude` | float64 | ✅ | `longitude` | |
| 3 | `acq_date` | datetime64[ns] | ✅ | `acq_date` | **UTC** date, time 00:00 |
| 4 | `acq_time` | int16 | ✅ | `acq_time` | HHMM UTC (0–2359); losing the leading zero is not a problem |
| 5 | `datetime_utc` | datetime64[ns, UTC] | ✅ | derived | `acq_date + HH:MM` |
| 6 | `year` | int16 | ✅ | derived | year of `acq_date` (UTC) |
| 7 | `month` | int8 | ✅ | derived | 1–12 |
| 8 | `instrument` | category | ✅ | `instrument` / from columns | `MODIS` \| `VIIRS` |
| 9 | `satellite` | category | ✅ | `satellite` | `Terra` \| `Aqua` \| `SNPP` \| `NOAA20` \| `NOAA21` (§3) |
| 10 | `confidence` | string | ✅ | `confidence` | **original value, as is**: MODIS `"0"`–`"100"`, VIIRS `"l"`/`"n"`/`"h"` |
| 11 | `confidence_class` | category | ✅ | derived | `low` \| `nominal` \| `high` — MODIS: <30 / 30–79 / ≥80 (**project rule**, FIRMS gives no numeric threshold) |
| 12 | `version` | string | ✅ | `version` | e.g. `6.1`, `6.1NRT`, `2.0NRT`; mock data: `MOCK` |
| 13 | `brightness` | float32 | ⬜ | MODIS `brightness` / VIIRS `bright_ti4` | K. **Not comparable between the two instruments** (different channel/resolution) |
| 14 | `brightness_2` | float32 | ⬜ | MODIS `bright_t31` / VIIRS `bright_ti5` | K (FIRMS web service name: Brightness_2) |
| 15 | `scan` | float32 | ⬜ | `scan` | pixel size, km |
| 16 | `track` | float32 | ⬜ | `track` | pixel size, km |
| 17 | `frp` | float32 | ⬜ | `frp` | MW |
| 18 | `daynight` | category | ⬜ | `daynight` | `D` \| `N` |
| 19 | `type` | Int8 | ⬜ | `type` (archive only) | 0 vegetation fire (default), 1 volcano, 2 static source, 3 offshore; empty in NRT |
| 20 | `source` | category | ✅ | file name | `archive` \| `nrt` |
| 21 | `region` | string | ✅ | `data/raw/<region>/` folder name | download area slug (§5) |
| 22 | `weight_harm` | float32 | ⬜ | P2 | **NaN at ingest**; filled in P2 output, ≥ 0 (§6) |

- **Required** = column exists AND has no missing values. **⬜** = column exists but may be empty.
- Column order as in the table. No extra columns (if needed, ask P4 → added to the contract).
- **Open decision — `sensor` column:** none for now; `instrument` (sensor family) + `satellite`
  (platform) uniquely identify every data stream. To be revisited when İbrahim's new datasets arrive.

## 2. Missing values
- Numeric → `NaN`; `type` → `<NA>`; text → `<NA>` (empty string `""` is FORBIDDEN).
- A row whose required field (`latitude, longitude, acq_date, acq_time, satellite`) cannot be read **is dropped**
  and the count is written in the ingest summary. No row is dropped for any other reason.
- Unknown `satellite` code or unexpected column structure → `ValueError` (no silent dropping).

## 3. Satellite / instrument names
| FIRMS code | `satellite` | `instrument` | Data start (approximate) |
|---|---|---|---|
| `Terra`, `T` | Terra | MODIS | 2000-11 |
| `Aqua`, `A` | Aqua | MODIS | 2002-07 |
| `SNPP`, `N` | SNPP | VIIRS | 2012-01 — **data stream stopped on 2026-11-02** (FIRMS announcement, verified in the data) |
| `N20`, `1` | NOAA20 | VIIRS | 2018-04 |
| `N21`, `2` | NOAA21 | VIIRS | **2023-03-01** (verified in the data) |

P1 derives the real first/last dates from the data → `data/satellite_coverage.csv` (§7.1).
The app does not hard-code dates; it takes them from `query.data_info()["satellite_ranges"]`.

**Instrument = `SATELLITE_INSTRUMENT[satellite]`** (from the satellite code). It is not inferred from the column name, because
the VIIRS column names differ between the two download formats (P1 verified with the real headers):

| Format | VIIRS brightness columns | MODIS | `satellite` (VIIRS) | `version` |
|---|---|---|---|---|
| DL_FIRE download tool (`fire_archive_*`, `fire_nrt_*`) | `brightness`, `bright_t31` | `brightness`, `bright_t31` | `SNPP`, `N20`, `N21` | `2`, `2.0NRT` (MODIS `6.2`, `6.1NRT`) |
| Country-year file (`viirs-snpp_2020_Belgium.csv`) | `bright_ti4`, `bright_ti5` | `brightness`, `bright_t31` | `N`, `N20` | — |

Both are mapped to `brightness` / `brightness_2`. The `confidence` format (number ↔ l/n/h) is
cross-checked against the instrument. **Country-year files are not used** (no 2026 and no NOAA-21, §5).

## 4. Duplicates and archive/NRT overlap
**4a. Exact duplicate** (same file, or downloaded twice from the same source):
key `(satellite, datetime_utc, round(latitude,4), round(longitude,4))` → the first one is kept.
- Different satellite **or** different time = different observation, NEVER merged.
- Neighboring pixels in the same overpass have different coordinates → they remain separate rows (these are legitimate observations).

**4b. archive ↔ NRT**: NRT and archive report the same detection **at a slightly different location**
(NRT is processed quickly), so point-to-point matching is unreliable → risk of double counting.
Rule: for each **(`region`, `satellite`)**, `cutoff = the latest acq_date in that region's archive`;
**all NRT rows** of that region-satellite with `acq_date ≤ cutoff` **are dropped**, later ones are kept.
Per region, because the regions' archives may end on different dates; a shared cutoff would wrongly delete
one region's NRT data (P1 finding, v1.2). Since regions do not overlap, there is no double counting.
P1 writes the cutoff and the number of dropped NRT rows for each region-satellite to `satellite_coverage.csv`.

## 5. Region names
- Source: **FIRMS download tool (DL_FIRE)**, 4 sources (MODIS C6.1, VIIRS S-NPP, NOAA-20, NOAA-21),
  archive + NRT, 2000-11 → today. The team's Drive archive is in this format.
- **FIRMS country-YEAR files are not used:** the last year is 2025 (no 2026) and there is no NOAA-21 → Hohes Venn
  August 2026 and the 2023 NOAA-21 jump would be lost.
- Slug: `^[a-z0-9_]+$`. Folder name = value: `data/raw/aachen_eifel/*.csv` → `region="aachen_eifel"`.
- Download areas **do not overlap** (`contract.REGIONS`):
  - `argentina` — country (La Rioja + P2 training)
  - `aachen_eifel` — bbox `5.96, 50.44, 6.44, 50.83` (lon_min, lat_min, lon_max, lat_max).
    Includes the Hohes Venn, the Belgian side is inside too (a box, not a border).
- `region` is not a filter in the app: the app filters **by coordinates** (`query.PRESETS`).
  `PRESETS["Aachen/Eifel"]` = the download box (so it does not show an area without data).

## 6. `weight_harm`
- **Meaning (contract):** for any set of rows, `Σ weight_harm` = an **estimate** of that set's
  harmonized (MODIS-equivalent) detection count. Values ≥ 0.
- **Ingest (P1):** `NaN` — "not harmonized yet". (Not 1.0: with 1.0 the harmonized mode
  would silently show the raw count.)
- **Harmonized (P2):** no NaN at all. **P2 decides the method** and documents it at the top of
  `pipeline/harmonize.py`. Initial proposal (Method A): MODIS rows 1 before the VIIRS period, 0 after;
  VIIRS rows `k / active_VIIRS_satellite_count`, `k = MODIS / VIIRS` (Argentina 2012–2021).
  The number of active satellites follows the start **and end** dates (SNPP ended on 2026-11-02).
- Method A is **an unverified hypothesis**; it is not presented as "correct" before the P3 metrics.

## 7. Pipeline interfaces
All scripts are run from the repo root: `python pipeline/<name>.py`. All have `main()` + `if __name__ == "__main__"`.

### 7.1 `pipeline/ingest.py` (P1)
| | |
|---|---|
| Input | `data/raw/<region>/*.csv` — DL_FIRE: archive (`fire_archive_*`), NRT (`fire_nrt_*`) |
| Output | `data/hotspots.parquet` — §1 schema, passes `validate_hotspots(df, "ingest")` |
| Output | `data/satellite_coverage.csv` — `region, satellite, source, first_date, last_date, n_rows, nrt_cutoff, n_nrt_dropped` (one row per region × satellite × source) |
| stdout | row counts per satellite × year, dropped rows (by reason) |

### 7.2 `pipeline/harmonize.py` (P2)
| | |
|---|---|
| Input | `data/hotspots.parquet`, `data/satellite_coverage.csv` |
| Output | `data/hotspots_harm.parquet` — §1 schema, passes `validate_hotspots(df, "harm")` |
| Output | `data/monthly_grid.parquet` — see below |
| Output | `data/k_factors.csv` — at least `k, n_modis, n_viirs, fallback` + the stratum columns P2 chooses |

`monthly_grid.parquet`:
| Column | dtype | Note |
|---|---|---|
| `cell_lat`, `cell_lon` | float64 | 0.25° cell center: `floor(x/0.25)*0.25 + 0.125` |
| `year` | int16 | |
| `month` | int8 | |
| `region` | string | |
| `n_terra`, `n_aqua`, `n_snpp`, `n_noaa20`, `n_noaa21` | int32 | raw count, per satellite |
| `n_modis`, `n_viirs` | int32 | totals |
| `n_harm` | float64 | `Σ weight_harm` |
Only cell-months with at least one detection are written (missing = 0).

### 7.3 `pipeline/validate.py` (P3)
| | |
|---|---|
| Input | `data/monthly_grid.parquet`, `data/hotspots_harm.parquet`, `data/k_factors.csv` (if missing, `data/hotspots.parquet` → raw counts only) |
| Output | `docs/validation/metrics.json` — `[{"data","method","region","split","scale","r2","bias","bias_pct","n"}]` |
| Output | `docs/validation/*.png` — `pred_vs_true.png`, `annual_raw_vs_harm.png`, `venn_check.png` |
| Output | `docs/validation/summary.md` — 3-sentence summary for İbrahim + year-by-year test breakdown |
| Split | training 2012–2021, test 2022–2024 |

`metrics.json` field values:
| Field | Allowed values |
|---|---|
| `data` | `"mock"` (synthetic) \| `"raw"` (P1, not harmonized) \| `"harm"` (P2 output) |
| `method` | `"harm"` (harmonized) \| `"raw_viirs"` (comparison without harmonization) |
| `split` | `"train"` (2012–2021) \| `"test"` (2022–2024) \| `"test_2022"` (before NOAA-21) \| `"test_2023-2024"` (NOAA-21 active, a satellite not in training) \| `"transfer_2012-2026"` (`aachen_eifel` only: since k is learned only from Argentina, all VIIRS years are out-of-sample; the 2022–24 test is very small in this region) |
| `region` | `contract.REGIONS` keys |

**Only outputs with `data = "harm"` are committed to the repo.** Metrics produced from synthetic or raw data
do not go into the presentation or the README.

### 7.4 `app/query.py` (P4) — P5 uses only this
```python
PRESETS: dict[str, tuple[float, float, float, float]]
    # display boxes: "Hohes Venn", "Aachen/Eifel", "La Rioja (AR)"
MONTH_LABELS: list[str]                   # ["Oca", …, "Ara"]

data_info() -> dict
    # {"path": str, "is_mock": bool, "has_harm": bool, "start": Timestamp, "end": Timestamp,
    #  "n_rows": int, "satellites": list[str],
    #  "satellite_ranges": {satellite: (first_date, last_date)},   ← v1.2, for the satellite-change lines
    #  "contract": "1.5"}

get_hotspots(geom, start=None, end=None, harmonized=False) -> pd.DataFrame
    # geom: PRESETS name | (lon_min, lat_min, lon_max, lat_max) | GeoJSON Feature/Polygon/MultiPolygon
    # start/end: date-like, inclusive, UTC; harmonized=True → only weight_harm > 0
    # returns: §1 columns (same dtypes), may have 0 rows

monthly_matrix(df, mode="raw", start=None, end=None) -> pd.DataFrame
    # start/end = the same date filter given to get_hotspots → months outside the range NaN (v1.3, backward compatible)
    # index "year" (int, all years within the data coverage), columns "month" 1..12, float64
    # raw: row count (all satellites) | harm: Σ weight_harm
    # month outside coverage → NaN; within coverage with no detections → 0; if there is no harmonized data, harm → entirely NaN

anomaly(matrix, year, month) -> dict
    # {"value": float, "mean": float, "std": float, "z": float, "rank": int|None,
    #  "n_years": int, "label": str}
    # baseline = the other years of the same calendar month; rank 1 = highest
    # label: "çok yüksek" (very high; z>2) | "yüksek" (high; z>1) | "normal" | "düşük" (low; z<-1) | "tespit yok" (no detections) | "veri yok" (no data)

to_csv_bytes(df) -> bytes                 # UTF-8; if the index has a name, the index is written too

forecast(geom) -> dict | None             # v1.5, EXPERIMENTAL (§7.5). Only mode="model" (Argentina); otherwise None
seasonal_outlook(geom) -> dict | None     # v1.5: in the model region same as forecast(); otherwise mode="seasonal"; None if there is no data
    # shared dict:
    # "mode": "model"    → the region has an Argentina outlook cell: tested 30-day outlook
    #         "seasonal" → no cell but there is data (e.g. Hohes Venn): NO FORECAST, pred = seasonal normal
    # {"start", "end", "data_through": Timestamp,   30-day window (e.g. 2026-11-15 → 12-14)
    #  "pred", "p10", "p90": float,   model: expected + 80% interval (from test errors); seasonal: normal + past years 10–90%
    #  "normal": float,               mean of the same window over the last 10 years (MODIS-equiv.)
    #  "ratio": float (seasonal: NaN), "label": model → "below normal" (≤1/1.5×) | "near normal" | "above normal";
    #                                          seasonal → "quiet season" (normal < 1) | "seasonal normal",
    #  "history": Series year → detections in the same 30-day window (past years),
    #  "profile": Series calendar month 1..12 → monthly normal of the last 10 full years (get_hotspots + monthly_matrix),
    #  "n_cells", "skill", "direction_hit_rate", "backtest_years" (seasonal: 0 / None),
    #  "years_with_detections", "n_years" (seasonal only), "cells": DataFrame (§7.5 + "ratio"; seasonal: empty)}
    # cell selection: 1° cell CENTER inside geom; model values are independent of the hotspot file
```
Data file priority: `$HOTSPOTS_PATH` → `data/hotspots_harm.parquet` → `data/hotspots.parquet`
→ `data/deploy/hotspots_deploy.parquet` → `data/mock/hotspots_mock.parquet`.

### 7.5 `pipeline/forecast.py` (P4) — EXPERIMENTAL 30-day detection outlook (v1.5)
| | |
|---|---|
| Input | `data/hotspots_harm.parquet` (`argentina` only, daily Σ `weight_harm`) — NASA FIRMS only |
| Output | `data/deploy/forecast.parquet` — see below (small, goes into git) |
| Output | `data/deploy/forecast_history.parquet` — `cell_lat`, `cell_lon` float64, `year` int16, `detections` float64: Σ `weight_harm` of the same 30-day window in past years (chart) |
| Output | `docs/forecast/metrics.json`, `backtest.png`, `summary.md` |
| Method | P2 Bahtiyar's normal + persistence model, 30-day sliding window: `log1p(target) = normal + a·cell deviation + b·region deviation`; the input window ends 2 days before the target. Region total = ratio × arithmetic normal of the last 10 years (the log sum was biased by −24%) |
| Test | 2015–2025, the 15th of each month (132 start dates), each year using only earlier years; skill = 1 − MSE_model/MSE_normal |

`forecast.parquet` (a single 30-day window):
| Column | dtype | Note |
|---|---|---|
| `cell_lat`, `cell_lon` | float64 | 1° cell center: `floor(x) + 0.5` |
| `start`, `end` | datetime64[ns] | target window (inclusive), `end = start + 29 days` |
| `expected_geo` | float64 | `expm1(log forecast)`, ≥ 0 — only for the RATIO; if summed it comes out too low |
| `normal_geo` | float64 | `expm1(log normal)`, ≥ 0 |
| `normal` | float64 | arithmetic mean of the same window over the last 10 years (MODIS-equiv. detections), ≥ 0 |
| `region` | string | `argentina` |
| `data_through` | datetime64[ns] | last full day used (the last NRT day is skipped) |

The outlook is a **detection count** outlook, not a fire forecast (§8); it is presented with the "experimental" label and the test
figures. It cannot foresee extreme events. NASA POWER weather and the NASA MERRA-2 El Niño indicator were tried
and did not improve it (branch `p4/forecast-experiments`).

### 7.6 `pipeline/weather_power.py` (P1) — NASA POWER monthly weather (v1.5, optional input)
| | |
|---|---|
| Input | `data/hotspots.parquet` (`argentina` 1° cells) + NASA POWER daily point API (PRECTOTCORR, T2M_MAX, RH2M) |
| Output | `data/weather_power.parquet` (not in git, ~2 MB); raw responses `data/raw/power/` |
| Used by | — (tested in the experiment, §7.5; branch `p4/forecast-experiments`) |

| Column | dtype | Note |
|---|---|---|
| `cell_lat`, `cell_lon` | float64 | 1° cell center `floor(x) + 0.5` (same as §7.5) |
| `year` | int16 | |
| `month` | int8 | |
| `prec_mm` | float64 | monthly TOTAL precipitation, mm |
| `tmax_c` | float64 | monthly mean of the daily max. temperatures, °C |
| `rh_pct` | float64 | monthly mean relative humidity, % |
| `n_days` | int16 | number of valid days; the current month is partial  |

The value is not a cell mean but the value of the MERRA-2 box (0.5° × 0.625°) that contains the cell center; days are in POWER's
local solar time (LST), not UTC like FIRMS. **Result of 14 Nov:** test error 45% → 47%, the acceptance threshold set in advance
(< 34%) was not met; in the 30-day model the skill also went 0.238 → 0.239 → NOT USED in the outlook model.

## 8. Terminology (app, slides, project page)
| Correct | Wrong |
|---|---|
| "active fire detection", "thermal anomaly", "hotspot" | "fire" (for a single row) |
| "a rise in detections **coinciding** with known fire events in the Hohes Venn" | "the app detected a fire" |
| "harmonized (MODIS-equivalent) estimate" | "actual number of fires" |
| "k factor: calibrated in Argentina, test 2022–2024: R²=…" | "validated conversion factor" |

Anomaly labels are anomalies of the **detection count**, not a classification of fire events.

## 9. Mock data
`data/mock/hotspots_mock.parquet` is generated by `data/mock/make_mock.py`. Every row has
`version = "MOCK"` → its synthetic nature is visible in CSV exports too. If `data_info()["is_mock"]`
is True, the app shows a "SYNTHETIC TEST DATA" warning. It has no scientific value.

## Changelog
| Version | Change | Affected |
|---|---|---|
| 1.0 | Initial schema (CLAUDE.md §3) | everyone |
| 1.1 | `sensor` marked as an open decision; `lat/lon` → `latitude/longitude`; `bright` → `brightness`; `brightness_2` added; `confidence` is now the **original value** (formerly `confidence_raw`), class → `confidence_class`; `fire_type` → `type`; new: `datetime_utc`, `version`, `region`; archive/NRT rule changed to a per-satellite date cutoff; `satellite_coverage.csv` added; `weight_harm` method delegated to P2; `contract.py` validator | P1, P2, P3, P5 |
| 1.2 | P1 real-header findings: instrument from the satellite code (in DL_FIRE, VIIRS also uses `brightness`), download format table; NOAA-21 start 2023-03-01; regions = DL_FIRE download areas (`argentina` country, `aachen_eifel` bbox), country-year files not used; archive/NRT cutoff per **(region, satellite)**; `region` column in `satellite_coverage.csv`; `data_info()["satellite_ranges"]`; `PRESETS["Aachen/Eifel"]` = download box; `to_csv_bytes` uses `\n` on every OS | P1, P2, P5, P6 |
| 1.3 | `data` field in `metrics.json` (mock/raw/harm); allowed values for `method`, `split` (P3 proposal); `summary.md` an official output; only `data="harm"` metrics in the repo | P3, P6 |
| 1.4 | `split="transfer_2012-2026"` (aachen_eifel only; P3 proposal) | P3, P6 |
| 1.5 | EXPERIMENTAL 30-day outlook: `pipeline/forecast.py` (P4, method P2), `data/deploy/forecast.parquet`, `docs/forecast/`, `query.forecast(geom)` (§7.4, §7.5); NASA POWER weather input `pipeline/weather_power.py` (P1, §7.6) tested, not used. NASA data only. Existing API unchanged | P1, P2, P5, P6 |
