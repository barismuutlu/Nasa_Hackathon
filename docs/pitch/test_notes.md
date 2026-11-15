# P6 test notes and evidence status

P6 İbrahim · 14 November 2026 · Current contract v1.3.

Status: Yusuf's T01–T10 results have been recorded; T08 was tested manually, T06 by simulation, and the no-detection-area part of T09 has been tested. The P3 files for T11 arrived and the document/JSON review was done here. P6's local app re-run, real Cloud screenshots and the T12 rehearsal/recording are still pending.

## Sources and environments

| Source | Evidence / data | What P6 did |
|---|---|---|
| P5 Yusuf, reported app reference `2bc0e31` | AppTest + query API; full `data/hotspots_harm.parquet`; 7,082,663 rows; `is_mock=False`, `has_harm=True` | Entered the results relayed by the user below; did not re-run them on this machine |
| P1 Süleyman | Hohes Venn box, period and MODIS-only April baselines; source is the full parquet | Entered the count/filter definitions into the documents |
| P1 Süleyman, new submission `26fa38d` | Current DL_FIRE ZIPs; August harm 169.2; MCD64A1 overlaps | Updated the data handoff note and the supporting evidence with source attribution; did not move raw files |
| P4 Barış, `f0f0759` | Full-data query runs; Hohes Venn monthly harmonized 169, April 17; La Rioja annual totals; Cloud harmonized deploy notice | Recorded with source attribution |
| P3 Oğuzhan, `b4cbbd4`, supporting summary `c6f15ad` | `docs/validation/metrics.json`, `summary.md` and three real-data PNGs | Reviewed the JSON records, the summary and the chart contents; did not re-run the model |
| P6 local Windows environment | At first review no `.venv/Scripts/python.exe` and no `uv`; no full parquet; repo deploy parquet present | Python 3.12/pinned package validation and runtime tests were not done |

The coverage reported by P5 is 2000-11-01 → 2026-11-13; satellites Aqua, NOAA20, NOAA21, SNPP, Terra. The app commit and the data version are separate pieces of evidence; `2bc0e31` alone does not reproduce the 7,082,663-row file or the test run. The test time, the SHA-256 value of the full data file and the AppTest outputs were not given in this message.

## Order of the Cloud submissions

1. Yusuf: the public link reportedly opened in a private window without login; at that time a synthetic warning was reportedly expected.
2. Barış `0c8f808`: 139,779-row real deploy data; the harmonized weights were reportedly still empty.
3. Barış `f0f0759`: real + harmonized deploy reported as ready. This latest notice updates the earlier “harmonized not yet available” state.

URL: https://nasahackathon-6dh2dds5wpz3r6q9mz5zx3.streamlit.app/

P6's web access attempt in this session ended with the error “URL is not accessible via this tool”. No interactive browser tool was provided either. This does not show that the site is closed to users; P6 did not independently verify public access, the live data state or the private-window flow. No screenshot was taken.

The Cloud deploy covers only the prepared regions; a “tespit yok” (no detections) display outside the boxes may be related to data coverage. The row counts of the full data and of the deploy file do not have to be equal.

## T01–T12: expected and relayed observed results

Unless stated otherwise, the T01–T10 observations are Yusuf's report relayed through the user. T01–T10 are not marked as P6's local test. Box confirmed by P1: `lon 5.95–6.25, lat 50.45–50.60`, bounds inclusive; same as `query.PRESETS["Hohes Venn"]`.

| ID | Step | Expected | Observed / source / status | Person responsible |
|---|---|---|---|---|
| T01 | Open with real data; check source/coverage/satellites. | No synthetic warning; correct source and coverage. | ✅ Yusuf: no warning; 2000-11-01 → 2026-11-13; Aqua, NOAA20, NOAA21, SNPP, Terra. Full harmonized file, `is_mock=False`, `has_harm=True`. No P6 local re-run. | Barış / Yusuf |
| T02 | Hohes Venn, Raw, 1–30 April 2011; inspect CSV/overpasses. | 17 MODIS detections; three overpasses; all `type=0`. | ✅ Yusuf: 25 Apr Terra 9; 26 Apr Terra 5 + Aqua 3. P1 also confirmed the Belgian side. | Süleyman / Barış / Yusuf |
| T03 | Keep sensor/period baselines separate in the April comparison. | Same definition gives the same mean and rank. | ✅ Yusuf: MODIS-only 2001–2025, other 24 Aprils mean ≈0.67 → 25.5×. P1/P4: 2001–2026 raw mean 2.64 → 6.4×; harm mean 0.59 → 28.7×; both cards 1/26. The difference is not an error, it is a baseline difference. | Süleyman / Barış / Yusuf |
| T04 | Hohes Venn, Raw, 14–17 August 2026; count by `instrument`. | MODIS 105, VIIRS 1,794; about 17.1×. | ✅ Yusuf reported the same counts. P1 reported that all of the month's detections fall in this narrow range; P4 reported the same monthly raw total as 1,899. P6 did not re-query the date bounds. | Süleyman / Barış |
| T05 | Inspect the August cell in the narrow T04 date range. | Partial-month marker and the day range on hover. | ✅ Yusuf: • marker and day range present. Even though the count equals the full month, the date filter is a partial month. | Yusuf |
| T06 | Simulate the `has_harm=False` state; select Harmonized. | “Harmonize veri henüz hazır değil” (harmonized data not ready yet). | ✅ Yusuf: tested by simulation. This result does not mean that the weights are empty in the current real data. | Yusuf / Barış |
| T07 | La Rioja, same full coverage; compare annual raw/harmonized totals. | Harm total `Σ weight_harm`; raw and estimate units kept separate. | ✅ Yusuf: 2011 raw/harm 868/868; 2012 3,437/808; `monthly_matrix(...,"harm")` is the weight sum. P4 relayed additional years and the 2017 limitation; full table in `pitch_facts.md`. | Bahtiyar / Barış / Yusuf |
| T08 | Draw an area; try calendar/CSV matching and Clear drawing. | Same active area; clearing returns to the prepared region. | 🖐 Yusuf tested manually in the morning: matches, clearing returns to the region. Not repeated on P6's computer. | Yusuf |
| T09 | Inspect an area without detections and, separately, an out-of-coverage month. | Absence of detections kept separate from absence of data; no crash. | ✅ Yusuf: area without detections shows “Bu bölgede tespit yok” (no detections in this region), no crash. The out-of-coverage month sub-check was not separately verified in this report; pending. | Barış / Yusuf |
| T10 | Download CSV in raw/harmonized mode. | UTF-8; canonical fields; `weight_harm` preserved. | ✅ Yusuf: Hohes Venn April 2011, 17 rows in both modes; reads as UTF-8, `weight_harm` present. For other periods the CSV row count is not counted as the harm total. | Barış / Yusuf |
| T11 | Review the P3 JSON, summary and charts for fitness for the presentation. | `data="harm"`; method/region/split/scale/n explicit. | ✅ P6 document review: `b4cbbd4` files arrived; Argentina test 1deg: R²=0.7918, bias=+1.3674, bias %=+6.72, n=8,616. Sub-periods checked. The limit below applies to the transfer panel. Model not re-run. | Oğuzhan / İbrahim |
| T12 | Record the real screens, open offline and time it. | No synthetic visuals; source/area/date explicit; video opens offline; talk <4:00. | ⏳ Pending. Flow and shot plan in `demo.md`; recording and timed rehearsal not done. | İbrahim |

## T11 limitations and visual review

- Argentina 1deg `harm` metrics: 2022 R²=0.7052, bias %=+18.36, n=2,834; 2023–2024 R²=0.9291, bias %=-2.51, n=5,782. The +6.72% in the overall test should not hide the 2022 overestimate.
- The Aachen/Eifel test sample is small: `1deg/test` n=12; 2022 n=3. Because of a total of 7 MODIS detections in these three years, P3 asked that the region's 2022–2024 test R² not be used in the pitch; it was removed from the main metrics table. This internal check is not a claim of model success.
- `pred_vs_true.png` opened locally: left panel Argentina 2022–2024, right panel Aachen/Eifel 2012–2026 transfer. The transfer metrics on the right are not in `metrics.json` and, according to the P3 summary, await P4 approval. This must be resolved before the full two-panel figure is taken into the main presentation; P6 did not change the file.
- `venn_check.png` opened locally; monthly raw 17/1,899 and harmonized 17/169 labels were seen. It is a real-data calendar, not a screenshot of the live app.
- `annual_raw_vs_harm.png` opened locally; the region is Argentina, not La Rioja. Do not change the region label in offline use.
- The limitations that the August 169 MODIS-equivalent estimate is about 61% higher than the 105 MODIS reference, and that La Rioja 2017 is overestimated by about 32%, are kept.

## P1/P3 MCD64A1 supporting check record

Results of `data/burned_area_check.csv` relayed by P1: 3×3 pixel neighborhood (≈1.4 km width), ±16 days. April MODIS 9/17; August MODIS 93/105, VIIRS 1,674/1,794. The product's burn dates are 24–28 April and 15–23 August respectively; the active August detections are 14–17 August. P1's single-pixel / 5×5 April comparison is 5/17 and 15/17. These results were not re-run by P6.

The new `summary.md` (`c6f15ad`) table gives the same totals: 9 matched + 8 unburned = 17; 93 + 12 = 105; 1,674 + 120 = 1,794. “Unburned” here is a class of the MCD64A1 check; it does not prove that the active detection is wrong. `unknown/no_data` is separate from it. Because the product also uses MODIS active fire input, this is supporting evidence only; it is not independent validation.

P3's final submission check was run with PowerShell `Select-String`: the table showed 9 (53%), 93 (89%), 1,674 (93%). The Git object ID of the local `venn_check.png` matched the `c6f15ad` version exactly; there are no local changes under `docs/validation/`. The source name was clarified in the presentation texts as “NASA MCD64A1 C6.1”. This check is file/submission consistency; it is not a re-run of the burned area analysis.

P1 also reported that the 17 records in the old Belgium country-year file match the DL_FIRE records one-to-one. This is consistency between two FIRMS downloads; it is not presented as an independent ground-truth check. It was kept separate from the numerical metrics; the new [limitations slide](slides/limitations.md) keeps the same framing.

## P1's final numerical review

Source: Süleyman's message with reference `9c8abb9`. The April overpasses, the 25.5× / 26.6× / 6.4× / 28.7× baselines and the 26-April coverage; August 105 + 1,794 = 1,899, harmonized 169.2 and about +61%; the MCD64A1 ratios/dates/sensitivity; the La Rioja 2011/2012/2017/2018/2023 values and the 2017 about +32% were checked against the data and no difference was reported. This is P1's report; P6 did not recompute on this machine.

The spatial wording was clarified: the remaining 8 detections are around the south/east of the matched ones; in a 5×5 neighborhood 6 more of them match. Since this was not measured against a burn perimeter map, the interpretation “at the burn edge” is not used. The numerical results were not changed.

## Check command in the P3 submission

The requested Python check was not run on this machine: there is no Python 3.12 virtual environment. The same JSON record was checked by reading it locally with PowerShell: `data=harm`, `method=harm`, `region=argentina`, `split=test`, `scale=1deg`; R²=0.7918, bias_pct=6.72, n=8,616. `summary.md` opens and the “Sunum için 3 cümle” (three sentences for the presentation) section is present. This is a file review; it is not a runtime/model test.

## Local re-run — not done yet

Only once a Python 3.12 virtual environment and the pinned `requirements.txt` are installed, at the repo root:

~~~powershell
.\.venv\Scripts\Activate.ps1
python --version
python tests/smoke_test.py
python -m streamlit run app/app.py
~~~

Expected: Python 3.12.x, pinned package check PASS and smoke exit code 0. ATLANDI (skipped) for missing files does not mean that data was tested. In the app, check the data path: `HOTSPOTS_PATH` → full harm → full raw → deploy → mock priority; the raw full file can shadow the deploy. “SENTETİK” (synthetic) screens are not taken into the presentation.

Check the April card with the whole period; if only the April 2011 date filter is selected, the 26-April baseline is not preserved. The reproduction command and the expected raw/harm outputs are in `pitch_facts.md`.

## Error / open check log

P6 did not do a local app test; no app error was reported in the results relayed by Yusuf. No code changes were made.

| ID | Topic | Evidence / expected | Status / person responsible |
|---|---|---|---|
| A01 | Metrics record of the transfer panel | Present in `summary.md` and `pred_vs_true.png`; no allowed split/JSON record | Awaiting P3/P4 approval and contract-compliant output; P6 does not use it in the main presentation |
| A02 | P6 check of live screens and public access | Team reported public and real/harmonized; the web tool in this session could not open it | Screenshots and P6 re-run pending; İbrahim/Yusuf |
| A03 | T09 out-of-coverage month sub-check | The incoming report covers only the area without detections | Additional check pending; Barış/Yusuf |

## Relayed cloud checks — historical record

Source: `P6_ibrahim.patch`, earlier cloud reference `8d5894c`, contract v1.2. The results below are the cloud session's report; they were not reproduced in this Windows workspace. The current local contract is v1.3. This old report is separate from the new P5/P3 results in this document; it is not P6's local app re-run.

| Cloud check | Observation reported by Cloud | Usage limit / person responsible |
|---|---|---|
| Python and pinned packages | Python 3.12.14; 10 direct dependencies matched their pinned versions | Does not show that the local environment is installed. Details: `environment_check.md`; P4 Barış. |
| Smoke test | 7 checks passed, 6 skipped, 0 errors; query file `data/mock/hotspots_mock.parquet` | Synthetic check, not success on real data or of harmonization; P4 Barış. |
| Historical country-year CSVs | Germany, Belgium, Argentina: 48 per country, 144 files in total and 6,893,939 raw rows | Not the current DL_FIRE input; P1 Süleyman. |
| CSV fields | MODIS `brightness/bright_t31`; VIIRS `bright_ti4/bright_ti5`; `type` reported present in all historical files | Does not generalize to DL_FIRE or NRT headers/type completeness; P1/P4. |
| Raw version field | MODIS `6.2`, `6.03`, `61.03`; VIIRS `2`; values not changed | The publication collection wording must be confirmed separately; P4 Barış. |
| Structure and source sizes | No rows with a broken field count and no blanks in the checked core fields were found; the sizes of the 144 files matched the NASA listing | SHA-256 records are in the manifest; local files were not checked here; P1 Süleyman. |
| Historical Belgium pre-check | 17 MODIS rows for 25–26 April 2011 in the 50.45–50.60 latitude, 5.95–6.25 longitude box | Pre-check separate from P1's canonical parquet validation; not event validation. |
| Missing coverage | 2026 and NOAA-21 absent from the country-year archive; the earlier NOAA-21 start question was resolved in v1.2 as 1 March 2023 | Current inputs are only DL_FIRE archive/NRT; P1/P4. |
| Transfer package | ZIP integrity check reported as passed; bytes and SHA-256 in `data_transfer_package.json` | The ZIP or CSVs were not transferred with this patch; not unpacked into the current input folders; P1/P4. |
| Jury criteria document | `2026 Judging Criteria.docx` not found in the cloud workspace; not moved | Does not mean a local or Drive search was done; P6 İbrahim. |

The commands and move instructions of the old download flow are historical documents; they were not run in this merge. Fitness of the raw CSV structure does not replace ingest validation, coverage, deduplication or P3 scientific validation.

## Local document check and submission

- [x] P1 box/period confirmation, P4 harmonized counts and P5 observations entered with their sources.
- [x] P1 current input submission, the rule of keeping the historical archive outside `data/raw/`, and the MCD64A1 dependency/settings framing entered.
- [x] 26-April coverage and the about 25× / 26.6× / 6.4× / 28.7× baselines separated.
- [x] P3 metrics taken only from `data="harm"` JSON records, with area/split/scale/n; transfer panel separated.
- [x] Historical cloud environment report, P5 tests and P6 document review separated from each other.
- [ ] P6 local Python/runtime re-run and T08 manual re-run completed.
- [ ] Live Cloud screens, offline demo video and <4:00 rehearsal completed.
- [x] The user gave explicit push approval for the earlier bulk document submission (`9c8abb9`).

Earlier local check for the historical manifest: 144 records, 6,893,939 raw rows, 554,614,725 bytes; JSON/CSV internal consistency had matched. The source CSV/ZIP files or SHA-256 contents were not re-verified locally.
