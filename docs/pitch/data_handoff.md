# P6 data handoff status — current DL_FIRE and historical archive

Cloud source: `P6_ibrahim.patch`, reference `8d5894c`, 14 November 2026, contract v1.2. The current local contract is v1.3; the rules excluding DL_FIRE and country-year inputs have not changed.

The historical download, size, SHA-256, ZIP and Python check results are the report of the earlier cloud session. The CSV and ZIP files are not inside the patch; the same checks were not re-run in this Windows workspace. The current P1/P4/P5 submission is recorded separately below. The P6 local status is in [test_notes.md](test_notes.md).

**The earlier v1.1 country-year submission is not the current pipeline input.**
`docs/CONTRACT.md` v1.2 §3 and §5 leave the country-year files out of scope.
The earlier 144 CSVs and the ZIP have been kept; this note records them as a historical
download archive. The source `data_download_manifest.csv` also describes the same historical archive.

## Current submission — completed on the P1 side

Source: Süleyman's message with reference `26fa38d`. It was reported that on the P1 machine, under `data/raw/`, only the following DL_FIRE ZIP inputs are present and there is no country-year CSV:

| Area | Input reported on P1 |
|---|---|
| argentina | `data/raw/argentina/Argentina-20261114T101801Z-1-001.zip` |
| aachen_eifel | `data/raw/aachen_eifel/Aachen-Eifel-20261114T101746Z-1-001.zip` |

Four sources, archive + NRT; Aachen/Eifel download box `(5.96, 50.44, 6.44, 50.83)`. Output `data/hotspots.parquet`: 7,082,663 rows, 2000-11-01 → 2026-11-13. It was reported that Barış took it from Drive and checked it, and that Yusuf did the app test with real data. **The P1 submission is complete; this does not mean that the full data is present on the P6 machine or that it was re-tested there.**

In the P1 full harmonized output, Hohes Venn April 2011=17.0 and August 2026=169.2 MODIS-equivalent; the April card is 1st among the 26 Aprils in 2001–2026, the mean of the other 25 Aprils ≈0.59 and the ratio ≈29×. Details in [pitch_facts.md](pitch_facts.md); the August dates of the active detections were confirmed as 14–17.

## Keep the historical archive separate from the ingest input

Keep the historical country-year ZIP and the unpacked CSVs **outside `data/raw/`**, for example under `data/archive/`; do not add them to git. Within the scope of this document no raw file was moved or deleted. The `data/raw/...` paths in the old manifest and package record are the historical locations reported in the cloud; they are not a current placement instruction.

- A ZIP at the root of `data/raw/` (e.g. `firms_country_archives_2000_2025.zip`) causes an explicit error in ingest's region-folder check.
- Country-year CSVs unpacked into a subfolder like `data/raw/belgium/`, however, are scanned; printing a warning does not automatically exclude them. They must not be kept here on the assumption that “the app already rejects them”.
- The valid DL_FIRE ZIPs stay in the `argentina` and `aachen_eifel` region folders above. This behavior was read from the `pipeline/ingest.py` source code; ingest was not run on this machine.

## Valid input

- Source: FIRMS DL_FIRE; `fire_archive_*` and `fire_nrt_*` CSV outputs.
- Four data streams: MODIS, VIIRS S-NPP, NOAA-20, NOAA-21.
- `data/raw/argentina/`: Argentina country selection.
- `data/raw/aachen_eifel/`: bbox `5.96, 50.44, 6.44, 50.83`.
- Period: November 2000–present; the available period for each satellite.
- NOAA-21 start: 2023-03-01; S-NPP end: 2026-11-02.
- DL_FIRE VIIRS headers can also be `brightness/bright_t31`;
  the instrument is determined from the satellite code, not from the column name.

The team's Drive archive is in this format and, according to the notice above, the P1/P4 submission is complete. The full parquet transfer and the runtime re-run in this Windows workspace of P6 have not been done yet. The counts Süleyman confirmed on the canonical parquet are used with source attribution; it is not claimed here that a local parquet check was done.

## Historical country-year download (v1.1)

| Country | Product | CSV | Raw rows | First detection | Last detection |
|---|---|---:|---:|---|---|
| argentina | modis | 26 | 1,712,416 | 2000-11-01 | 2025-12-31 |
| argentina | viirs-jpss1 | 8 | 1,728,797 | 2018-04-01 | 2025-12-31 |
| argentina | viirs-snpp | 14 | 2,889,092 | 2012-01-20 | 2025-12-31 |
| belgium | modis | 26 | 13,140 | 2000-11-02 | 2025-12-30 |
| belgium | viirs-jpss1 | 8 | 35,357 | 2018-04-02 | 2025-12-31 |
| belgium | viirs-snpp | 14 | 62,163 | 2012-01-22 | 2025-12-31 |
| germany | modis | 26 | 55,526 | 2000-11-02 | 2025-12-30 |
| germany | viirs-jpss1 | 8 | 147,471 | 2018-04-01 | 2025-12-31 |
| germany | viirs-snpp | 14 | 249,977 | 2012-01-20 | 2025-12-31 |

144 CSVs, 6,893,939 raw rows, 554,614,725 bytes. 48 CSVs per country.
MODIS 2000–2025, S-NPP 2012–2025, NOAA-20 2018–2025.
Does not contain 2026 or NOAA-21. Row counts are not counts of unique detections or fire events.

Source: https://firms.modaps.eosdis.nasa.gov/data/country/yearly_summary_files.txt

The sizes matched the NASA listing; the SHA-256 values were generated locally.
The CSV check was re-run in the new Python 3.12 environment; no rows with a broken field count
and no empty values in the checked core fields.

## First downloaded CSV — historical header example only

`head -3 data/raw/belgium/modis_2011_Belgium.csv`:

```csv
latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,confidence,version,bright_t31,frp,daynight,type
51.1708,3.8039,308,1,1,2011-01-01,2131,Terra,MODIS,73,6.2,274.8,13.6,N,0
51.1698,3.8165,313.9,1,1,2011-01-04,1051,Terra,MODIS,52,6.2,272.7,17.9,D,2
```

The country-year VIIRS CSV header uses `bright_ti4/bright_ti5`. This difference shows that no assumption
can be made about the DL_FIRE headers. The raw MODIS `version`
values are `6.2`, `6.03`, `61.03`; VIIRS `2`. The data was not changed.

In the old Belgium CSV, in the latitude 50.45–50.60 and longitude 5.95–6.25 box,
17 raw MODIS detection rows were found for 25–26 April 2011. This pre-check
is not a current DL_FIRE pipeline check or scientific validation.

## Historical transfer package

Old location reported in the cloud `data/raw/firms_country_archives_2000_2025.zip`: 145,340,525 bytes. Current storage recommendation `data/archive/firms_country_archives_2000_2025.zip`; the ZIP and the country-year CSVs inside it are not kept under `data/raw/`.
The ZIP integrity check passed. SHA-256: `data_transfer_package.json`.
The package is the v1.1 archive; it must not be unpacked into the current v1.3 input folders. This note replaces the old
placement instructions inside the ZIP.
For this historical package the cloud report stated that no Drive/USB transfer was made; this statement does not mean that the current DL_FIRE submission is incomplete. No raw CSV or ZIP was added to git with this document change.

## Closing status of the cloud session / information to hand over

- Environment set up: Python 3.12.14, pinned package versions.
- Smoke test: 7 passed, 6 skipped, 0 errors; query checks on synthetic data.
- Environment report: `environment_check.md`.
- At cloud closing, the harmonized count was pending. In the subsequent P1 submission it was reported as April 17.0; August 169.2 MODIS-equivalent; raw August 105 MODIS + 1,794 VIIRS.
- The DL_FIRE/parquet submission pending at cloud closing was later completed on the P1/P4 side; P6's local transfer and runtime check are separate and still pending.
- `2026 Judging Criteria.docx` was not found in the workspace; not moved.
- Code and contract were not changed; the P6 changes are under `docs/pitch/`.
