# P1 — Data Engineer: Süleyman

Shared rules and the schedule are in the root `CLAUDE.md`, the schema is in **`docs/CONTRACT.md`** (current version). This file covers only your role.

## Files you own (Claude writes ONLY to these)
- `pipeline/ingest.py`
- `data/sample/` (sample output)

## Input / output (CONTRACT §7.1)
- Input: `data/raw/<region>/*.csv` — folder name = `region` value (`argentina`, `aachen_eifel`)
- Output: `data/hotspots.parquet` — CONTRACT §1, `validate_hotspots(df, "ingest")` before writing
- Output: `data/satellite_coverage.csv` — `satellite, source, first_date, last_date, n_rows, nrt_cutoff, n_nrt_dropped`

## Task
1. **Data** (CONTRACT §5) — the team's Drive archive (DL_FIRE, 4 sources, archive + NRT, 2000-11 → today):
   `data/raw/argentina/`, `data/raw/aachen_eifel/`. FIRMS country-year files are NOT USED (no 2026 and no NOAA-21).
   - Instrument = `SATELLITE_INSTRUMENT[satellite]` (in DL_FIRE, VIIRS also uses the `brightness` column).
   - archive/NRT cutoff per **(region, satellite)**; `region` column in `satellite_coverage.csv`.
2. **Reading** — take the constants from `contract.py`, do not write them yourself:
   - Instrument from the columns: `brightness` → MODIS, `bright_ti4` → VIIRS.
   - `satellite` → via `SATELLITE_CODES`; unknown code → `ValueError`.
   - `confidence` = **original value, string** (MODIS `"85"`, VIIRS `"n"`).
     `confidence_class`: MODIS → `modis_confidence_class()`, VIIRS → `VIIRS_CONFIDENCE_CLASS`.
   - `brightness` = MODIS `brightness` / VIIRS `bright_ti4`; `brightness_2` = `bright_t31` / `bright_ti5`.
   - `version` = FIRMS `version` (string), `type` = archive `type` (`<NA>` in NRT).
   - `datetime_utc` = `acq_date` + `acq_time` (HHMM), UTC.
   - `source`: `archive` in the file name → `"archive"`, `nrt` → `"nrt"`.
   - `weight_harm` = NaN (float32). Do not harmonize, that is P2's job.
3. **Duplicate removal** (CONTRACT §4)
   - 4a: key `(satellite, datetime_utc, round(latitude,4), round(longitude,4))` → the first one stays.
   - 4b: for each satellite `cutoff = last acq_date in the archive`; that satellite's NRT rows with `acq_date ≤ cutoff` are dropped.
   - **Never** merge rows with a different satellite or a different time.
4. **Print a summary** — row counts per satellite × year, dropped rows by reason,
   `satellite_coverage.csv` → notify Bahtiyar (the S-NPP last date should be ~2026-11-02).

## First thing: header check
When you download the first real CSV, print the header row and the distinct values in the `satellite`, `confidence`, `version`
fields, and compare them with CONTRACT §1/§3. If there is a difference, **tell Barış first**,
then move on to the code (the contract was written from the documentation; the real file has not been seen).

## Submissions
| Time | What | To whom |
|---|---|---|
| 11:30 | `data/sample/hotspots_sample.parquet` (La Rioja 2020) + header check result | everyone, Barış |
| 12:30 | `data/hotspots.parquet` full data (Drive/USB) | everyone |
| 12:30 | `data/satellite_coverage.csv` | Bahtiyar (P2) |

## Done check
- [ ] `validate_hotspots(df, "ingest")` passes without errors
- [ ] `duplicated().sum() == 0` on the key; archive/NRT cutoff dates in the summary
- [ ] Is there a MODIS detection in the Hohes Venn (lon 5.95–6.25, lat 50.45–50.60) in April 2011? → tell Barış
- [ ] `python pipeline/ingest.py` runs from start to finish in a clean environment

## Note for Claude
- Import `contract.py` (root CLAUDE.md §3.2), do not change it. A situation that does not fit the contract → ask Barış.
- Only pandas/pyarrow/numpy. If a new package is needed, do not write it; say "tell Barış".
- Read large CSVs with `usecols` + `dtype`; read `confidence` as a **string** (`dtype={"confidence": str}`).
