# MODIS ↔ VIIRS Active Fire Detection Calendar

P6 İbrahim · 14 November 2026 · Contract v1.3. Numerical sources and scope: [pitch_facts.md](pitch_facts.md).

## Summary

When satellite detections increase, how do we separate the observed events from the changing observing system? Our calendar, developed from NASA FIRMS records, shows active fire detections in the 2000–2026 period by region and month. The raw series and the harmonized (MODIS-equivalent) estimate are examined together. A record is a thermal anomaly pixel in one satellite overpass; it is not a validated fire event.

## Problem and solution

MODIS and VIIRS have different resolutions and observation coverage. The addition of new satellites makes it harder to compare raw counts directly across years. Method A, developed with Argentina's 2012–2021 data, uses MODIS/VIIRS coefficients by latitude band, local season and satellite, together with the number of active VIIRS satellites. The harmonized count is the sum of the records' `weight_harm` weights; it is read as an estimate of the MODIS-equivalent detection count.

## Hohes Venn: detection increases that coincide with known events

**April 2011:** In three satellite overpasses on 25–26 April there are 17 MODIS pixel detections; Terra 14, Aqua 3. All are of the vegetation fire type and on the Belgian side. In the harmonized series the value is also 17. The harmonized mean of the other 25 Aprils in 2001–2026 is about 0.59: at about 29 times that, April 2011 is the highest of the 26 Aprils examined (1/26).

In the raw, all-satellite series the comparison mean for the same month is 2.64 and the ratio is 6.4 times. This difference shows the importance of stating clearly which series and comparison baseline were chosen. The earlier about 25 times statement belongs to the MODIS-only, 2001–2025 baseline.

**August 2026:** Monthly raw total 1,899 detections: 105 MODIS and 1,794 VIIRS. The harmonized monthly total in P1's latest notice is 169.2 MODIS-equivalent; in the talk, about 169 is said. P1 confirmed that all active detections are on 14–17 August. The VIIRS/MODIS ratio of about 17.1 times is not a universal coefficient. That the estimate is about 61% higher than the 105 MODIS reference also shows the limit of transfer to a large event.

**La Rioja:** While the raw annual total rises from 868 in 2011 to 3,437 in 2012, the harmonized series goes from 868 to 808. Limitation: the 2017 harmonized value is 3,236, the MODIS reference 2,447; an overestimate of about 32%.

These counts were relayed from P1/P4's full-data queries; P6 did not recompute them locally.

## Supporting burned area check with MCD64A1

9 of the 17 MODIS detections in April 2011 overlap, within a 3×3 pixel neighborhood (about 1.4 km width), with areas that NASA's MCD64A1 product marked as burned on 24–28 April. The time tolerance is ±16 days. In August 2026 the matches are 93/105 for MODIS and 1,674/1,794 for VIIRS; the product's reported burn dates are 15–23 August.

Source: **NASA MCD64A1 C6.1**, monthly burned area product, about 500 m. Presentation wording: “In April 2011 more than half of the detections (53%), and in August 2026 89% of the MODIS detections and 93% of the VIIRS detections, overlap at this neighborhood setting with areas the product mapped as burned in the same period — supporting evidence.”

This is **supporting evidence, not independent validation**: the MCD64A1 algorithm also uses MODIS active fire data. The number depends on the neighborhood setting; small burns can be missed. These dates are not to be confused with the active detection dates. Source: P1's message (`26fa38d`) and the P3 `summary.md` update (`c6f15ad`); details are in [pitch_facts.md](pitch_facts.md).

## Independent test

Source: `docs/validation/metrics.json`, `b4cbbd4`; `data="harm"`, `method="harm"`, `region="argentina"`, scale `1deg`.

| Test period | R² | Bias, detections/cell-month | Bias % | n, cell-months |
|---|---:|---:|---:|---:|
| 2022–2024 | 0.7918 | +1.3674 | +6.72 | 8,616 |
| 2022 | 0.7052 | +5.0232 | +18.36 | 2,834 |
| 2023–2024 | 0.9291 | -0.4244 | -2.51 | 5,782 |

The target is the MODIS detection count; R² is not the accuracy for validated fire events. 2022–2024 is the test period held out from coefficient training. Because NOAA-21 is not present in training, the NOAA-20 coefficients are used as a proxy. The 2022 overestimate, the small Aachen/Eifel sample and the overestimate in the large event are limitations of the method.

P3's long-period regional transfer results are not yet in `metrics.json` and await P4 approval; they are not used in place of the main presentation's R² value. The Aachen/Eifel 2022–2024 test metric is also not used in the pitch because of only 7 MODIS detections. Numbers must be given together with method, region, period, scale and n; it is not claimed that satellite jumps are fully removed. The [limitations slide](slides/limitations.md) keeps this distinction.

## Data, tools and demo

- NASA FIRMS MODIS C6.1 and VIIRS C2; DL_FIRE archive/NRT. Download areas `argentina` and `aachen_eifel`; the old country-year CSV files are not used.
- Hohes Venn display box: longitude 5.95–6.25, latitude 50.45–50.60, bounds inclusive. Aachen/Eifel download box `(5.96, 50.44, 6.44, 50.83)`; it is not a country border filter.
- Reported full data coverage 2000-11-01 → 2026-11-13. The deploy data on Cloud covers only the prepared areas; the same row count as the full data is not expected. The satellite coverage is taken in the app via `data_info()["satellite_ranges"]`.
- Python 3.12 and pinned `requirements.txt` versions; pandas, NumPy, PyArrow, Shapely, Streamlit, Folium and Plotly. The raw `version` field is preserved; the instrument is determined from the satellite code. The MCD64A1 supporting check is a separate flow; it is not mixed with the FIRMS counts.
- The [public demo](https://nasahackathon-6dh2dds5wpz3r6q9mz5zx3.streamlit.app/) reported by the team has been switched to real and harmonized data. P6 could not complete the live browser check in this session. The [demo flow](demo.md) and the [test notes](test_notes.md) keep the observation sources separate.
- The real-data P3 [Hohes Venn calendar](../validation/venn_check.png) can be used as offline support; it is not an app screenshot. Visuals state the “NASA FIRMS / Worldview” source information, region, date and series unit; the NASA logo and synthetic screenshots are not used.

The historical 144 country-year CSVs and the cloud environment report are kept as separate records in [data_handoff.md](data_handoff.md), [data_transfer_package.json](data_transfer_package.json) and [environment_check.md](environment_check.md).

## Impact and next steps

The calendar makes it possible to read regional detection patterns together with satellite coverage. The next steps are real Cloud screenshots, an offline demo recording and a timed rehearsal; then improving transfer to large events and to different regions.

## Team

| Role | Responsible | Contribution |
|---|---|---|
| P1 | Süleyman | Data engineering and raw counts |
| P2 | Bahtiyar | Harmonization |
| P3 | Oğuzhan | Independent test and validation |
| P4 | Barış | Leadership, contract, data and query layer |
| P5 | Yusuf | Interface and app tests |
| P6 | İbrahim | Presentation, project text, demo and test notes |
