# Pitch: verified numbers, baselines and limitations

P6 İbrahim · 14 November 2026 · Current contract v1.3.

## Source and validation level

- P1 Süleyman: geographic filter, raw counts, April coverage and MCD64A1 check relayed by the user; first reference `7ddfc51`, new submission `26fa38d`. The August harmonized monthly total was relayed with more precise display as 169.2.
- P1 final review (message with reference `9c8abb9`): the April overpasses and baseline table, August totals/harmonized estimate, MCD64A1 counts/dates/sensitivity and La Rioja annual totals were checked one by one against the data; no numerical difference was reported. This is P1's check report; it is not P6's local recomputation.
- P5 Yusuf: T01–T10 results with AppTest + query API; reported app reference `2bc0e31`. T08 tested manually, T06 by simulation. These records are not P6's local re-test; the app commit alone does not identify the version of the data file.
- P4 Barış: Hohes Venn and La Rioja counts queried with the full harmonized data in the `f0f0759` submission. The P2 implementation came with `f44bca1`.
- P3 Oğuzhan: [metrics.json](../validation/metrics.json), [summary.md](../validation/summary.md) and real-data charts that came with `b4cbbd4`; the MCD64A1 supporting summary was added with `c6f15ad`. The test metrics below are taken directly from the JSON records.
- P6 local check: documents, JSON and charts were reviewed. Because the full parquet and a Python 3.12 environment are not available on this machine, the counts or model tests were not re-run here.

## Geographic filter and data coverage

Hohes Venn: longitude 5.95–6.25, latitude 50.45–50.60; bounds inclusive, same box as `query.PRESETS["Hohes Venn"]`. Download area `aachen_eifel`; the box also covers the Belgian side. The full data coverage reported by P1/P5 is 2000-11-01 → 2026-11-13; the full harmonized data is 7,082,663 rows.

April 2000 is outside the data coverage. Aprils examined 2001–2026: 26 Aprils in total; comparison baseline excluding 2011 is 25 Aprils. Write this month coverage explicitly instead of “26 years”.

## April 2011: the same 17 detections, different comparison baselines

25 April: Terra 9; 26 April: Terra 5 + Aqua 3. In total 17 MODIS pixel detections, three overpasses; all `type=0` and on the Belgian side. Because the MODIS weight is 1 in April 2011, the harmonized total is also 17 MODIS-equivalent. If only German data had been taken, these detections would not have been visible.

| Series / period | 2011 value | Mean of the other Aprils | Times the mean | Rank |
|---|---:|---:|---:|---|
| MODIS only, 2001–2025; earlier comparison | 17 MODIS detections | 0.67; 24 reference Aprils | 25.5×; in the talk about 25× | Highest April of the examined period |
| MODIS only, 2001–2026 | 17 MODIS detections | 0.64; 25 reference Aprils | 26.6× | 1/26 |
| Raw, all satellites, 2001–2026 | 17 detections | 2.64; 25 reference Aprils | 6.4× | 1/26 |
| Harmonized, 2001–2026; main demo definition | 17 MODIS-equivalent | 0.59; 25 reference Aprils | 28.7×; in the talk about 29× | 1/26 |

Means and ratios are rounded for display; the times values are computed with the unrounded baseline. For example, do not change the 25.5× result by re-dividing by the old 0.67 display. Do not present the card's ≈29× value and the old MODIS-only ≈25× value as if they had the same baseline.

P3's new “0.64, about 27 times” correction corresponds to the **MODIS only, 2001–2026** definition in the table; it does not replace the harmonized card's ≈0.59 / ≈29× definition. P1/P4's series separation and the separate `modis` / `harm` rows of the P3 summary keep these apart. Safe wording that can be used without stating the baseline: “First among the 26 Aprils in 2001–2026; in the harmonized series, at most 3 MODIS-equivalent detections in the other years.”

Main presentation sentence:

> April 2011 has 17 MODIS-equivalent detections. The mean of the other 25 Aprils in 2001–2026 is about 0.59: at about 29 times that, this month is the highest of the 26 Aprils examined.

That the raw card shows about 6.4× and the harmonized card 28.7× is a baseline difference; it is not an error. The raw baseline also includes VIIRS Aprils. This change does not mean “the fire was really five times more severe” or that the method is validated on its own.

## August 2026: monthly total and event window

| Measure | Value | Source / coverage |
|---|---:|---|
| MODIS | 105 pixel detections | P1/P5: 14–17 August; P1 reported that all of the month's detections in the same box fall in this range |
| VIIRS | 1,794 pixel detections | Same event window |
| Raw total | 1,899 detections | P4 and P3: the whole month of August |
| Harmonized total | 169.2 MODIS-equivalent; in the talk about 169 | P1 new full-data notice; P4/P3 summary and chart round to a whole number |
| Raw VIIRS/MODIS ratio | About 17.1× | 1,794 / 105; not a universal coefficient |

P1's final confirmation: all August active detections in the box are on 14–17 August. P4's earlier 13–25 August check range contains this narrow range. These are **not the same date field as the 15–23 August burn dates** of the MCD64A1 product given below. P6 did not re-query the date bounds locally. In the main demo, label the 169.2 estimate with its monthly unit. When 14–17 August is selected, even though the result is the same number, the cell must be marked as a partial month because of the date selection.

This is not a paired same-overpass experiment. Sensor, resolution, number of satellites and observation coverage can affect the raw ratio. Do not say “VIIRS is always 17 times more sensitive”. The about 169 estimate is about 61% above the 105 MODIS reference; for this event no exact match or perfect correction is claimed.

## MCD64A1 burned area: supporting evidence

Source: P1's message with reference `26fa38d`; method description of `pipeline/burned_area_check.py`; the supporting table in P3's `summary.md` updated with `c6f15ad`. Separate output `data/burned_area_check.csv`; this CSV was not re-run on P6's machine and was not added to git.

Visual and slide source name: **NASA MCD64A1 C6.1** (monthly burned area, about 500 m). P3's refreshed [venn_check.png](../validation/venn_check.png) chart contains these supporting counts as a footnote; P6 does not change the chart.

Matching setting: the MCD64A1 pixel the detection falls in and a **3×3 pixel neighborhood (about 1.4 km width)** around it; **±16 days** between the active detection date and the product's burn date. This approximate distance is not a circular radius or an exact fire perimeter.

| Period / instrument | Matched / total active detections | Burn dates reported in the MCD64A1 product |
|---|---:|---|
| April 2011 / MODIS | 9/17 (53%) | 24–28 April 2011 |
| August 2026 / MODIS | 93/105 (89%) | 15–23 August 2026 |
| August 2026 / VIIRS | 1,674/1,794 (93%) | 15–23 August 2026 |

Presentation sentence:

> 9 of the 17 MODIS detections in April 2011 overlap, within a 3×3 pixel neighborhood (about 1.4 km), with areas that NASA's MCD64A1 product marked as burned on 24–28 April. This is supporting evidence; it is not independent validation.

The MCD64A1 algorithm also uses MODIS active fire data; it can miss small burns. Do not say “validated” or “proven”. The April match depends on the setting: 5/17 at a single pixel, 9/17 at 3×3, 15/17 at 5×5 (P1 notice; time tolerance ±16 days). According to P1's final location description, the remaining 8 detections are around the south/east of the matched ones; in a 5×5 neighborhood 6 of these 8 detections also match. Since no measurement was made against a burn perimeter map, these are not described as “at the burn edge”. Not matching is not evidence of a false active detection. `unknown` / `no_data` is not the same as “unburned”. These overlap ratios are not presented as independent classification accuracy or as a harmonization test metric.

That the 17 rows in the old Belgium country-year file are the same as the new DL_FIRE output is, as reported by P1, **a consistency check between two FIRMS downloads**; it is not independent sensor or fire event validation.

## La Rioja: annual examples

Results relayed by P4 from the full-data `query.py` query:

| Year | Raw, all satellites | Harmonized, MODIS-equivalent | MODIS-only reference |
|---|---:|---:|---:|
| 2011 | 868 | 868 | 868 |
| 2012 | 3,437 | 808 | 731 |
| 2018 | 7,240 | 931 | 1,057 |
| 2023 | 10,728 | 985 | 907 |

In 2012 the raw series roughly quadruples while the harmonized value goes from 868 to 808. This visual example does not replace an independent test metric. Limitation: in 2017 harmonized 3,236, MODIS 2,447; the estimate is about 32% above the reference.

## P3: independent test results

Source `docs/validation/metrics.json`, commit `b4cbbd4`. In all rows below `data="harm"`, scale `1deg`. The target is the MODIS detection count; it is not a validated fire count. `n` is the number of cell-month samples. `bias` is in detections/cell-month units, `bias_pct` is the total relative deviation.

| Region | Method | Split / period | R² | Bias | Bias % | n |
|---|---|---|---:|---:|---:|---:|
| argentina | harm | test / 2022–2024 | 0.7918 | +1.3674 | +6.72 | 8,616 |
| argentina | raw_viirs | test / 2022–2024 | -74.8202 | +159.8763 | +785.90 | 8,616 |
| argentina | harm | test_2022 / 2022 | 0.7052 | +5.0232 | +18.36 | 2,834 |
| argentina | harm | test_2023-2024 / 2023–2024 | 0.9291 | -0.4244 | -2.51 | 5,782 |

The training region is Argentina, the period for the VIIRS coefficients is 2012–2021; according to P2/P3 confirmation, 2022–2024 did not enter the coefficients. A separate 2003–2011 training range is used for the Terra-only early-period correction. There are no direct training samples for NOAA-21; the method uses the NOAA-20 coefficients as a proxy.

Main test sentence: “In the independent 2022–2024 test in Argentina, at the 1° cell-month scale, R² is about 0.79; total deviation +6.72%; n=8,616.” Do not hide the +18.36% overestimate in 2022. Per P3's latest guidance, the Aachen/Eifel 2022–2024 test R² is not used in the pitch: there are only 7 MODIS detections in this period and the sample is insufficient.

`summary.md` and `pred_vs_true.png` also contain `transfer_2012-2026` results. This split is not among the allowed values of the current contract and not in `metrics.json`; the P3 summary states that P4 approval is awaited. Therefore the transfer R² is not taken into the main presentation; the two-panel `pred_vs_true.png` as a whole is not considered ready for the presentation.

The limitations slide is in [slides/limitations.md](slides/limitations.md). Because there is no separate calculation/method record in the current JSON for the annual uncertainty band in P3's message, this band was not added to the slide as a numerical result.

## Data and method rules

Inputs are only FIRMS DL_FIRE archive/NRT; download areas `argentina` and `aachen_eifel`. The old country-year CSV files are out of scope. The Method A implementation divides the MODIS/VIIRS coefficients for latitude band, local season and satellite by the number of active VIIRS satellites; `Σ weight_harm` is the MODIS-equivalent estimate. Transfer across regions and events is limited; it is not claimed that the satellite effect is fully removed.

A pixel detection is not a fire event; three overpasses do not mean three fires. The FIRMS vegetation fire type is not independent event validation. The anomaly label refers to the detection count. Synthetic screenshots and the NASA logo are not used.

## Reproduction and visuals

With a Python 3.12 + pinned `requirements.txt` environment active and the real harmonized data ready, at the repo root:

~~~powershell
python -c "import sys; sys.path.insert(0,'app'); import query; v=query.get_hotspots('Hohes Venn'); [print(m, query.anomaly(query.monthly_matrix(v,m),2011,4)) for m in ('raw','harm')]"
~~~

Expected, per P1/P4 notice: raw value=17, mean≈2.64, rank=1, n_years=26; harm value=17, mean≈0.59, rank=1, n_years=26. This command was not run here.

The real-data P3 calendar [venn_check.png](../validation/venn_check.png) was visually reviewed locally. Live Cloud screenshots and the rehearsal have not yet been completed by P6; the flow is in [demo.md](demo.md), the status in [test_notes.md](test_notes.md). The historical 144-CSV manifest and the cloud environment report are kept in [data_handoff.md](data_handoff.md) and [environment_check.md](environment_check.md); they are not used in place of current pipeline/test evidence.
