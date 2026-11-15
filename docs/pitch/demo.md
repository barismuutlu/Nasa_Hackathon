# Demo flow and real-data capture plan

P6 İbrahim · 14 November 2026. Status: flow ready; P6 live screen check, recording and timed rehearsal not done yet.

Public URL reported by the team: https://nasahackathon-6dh2dds5wpz3r6q9mz5zx3.streamlit.app/

## Before starting

- Check again that it opens in a private window without asking for login. The web tool in this session could not open the URL; this result does not mean that the site is closed to users.
- Record the source, coverage and satellites in the `Veri / Data` section. Latest P4 notice `f0f0759`: real + harmonized deploy. Old synthetic or non-harmonized submission messages are not used in place of the latest state.
- If there is a synthetic warning, do not take that screen into the presentation. If there is a harmonized-not-ready message, state that the flow continues with raw data and use the previously verified P3 calendar.
- Select a prepared region, clear the previous drawing. The deploy covers only the prepared boxes; do not generalize a no-detection display outside them as the region truly having no detections at all.
- Keep the whole data period for the April card and the annual comparisons. A 2011-04-only filter breaks the card's 26-April comparison baseline.

## Live flow of about 60 seconds

| Time | Action | Expected / talk |
|---|---|---|
| 00–10 s | `Region: Hohes Venn` → whole date coverage → `Harmonized` → `Log` | Real data; monthly unit is the MODIS-equivalent estimate. The Log color transform does not change the number on the card. |
| 10–25 s | Select the 2011-04 cell; use the Year/Month selectors if needed. | 17 MODIS-equivalent; rank 1/26; about 28.7× (rounded display may be 29×). Mean of the other 25 Aprils ≈0.59. |
| 25–35 s | Select `Raw` for the same coverage and month; then return to Harmonized. | Value again 17; raw mean 2.64 and ratio ≈6.4×. This is a comparison of different baselines. The old ≈25× number is not the card's definition. |
| 35–45 s | Show the Hohes Venn 2026-08 cell; keep the full month. | Raw 1,899 = 105 MODIS + 1,794 VIIRS; harmonized ≈169 MODIS-equivalent. 169 is not equal to the MODIS reference. |
| 45–60 s | Select `La Rioja (AR)`; switch to the `Annual totals: raw vs harmonized` chart over the whole date range. | 2011: 868/868; 2012: 3,437/808 (raw/harm). If the live flow runs long, show this transition with a previously captured real-data frame. |

Separate detail check: if 14–17 August is selected, according to the P1/P5 report the raw total is again 1,899; the cell must show a partial month with • and the day range on hover. Do not use this narrow filter at the same time as the main April card rehearsal; restore the whole period afterwards.

P1's precise monthly harmonized value is 169.2; in the chart/talk it is rounded to 169. If MCD64A1 is asked about, describe the April 9/17 overlap, with the 3×3 neighborhood ≈1.4 km width and ±16 days setting, as **supporting evidence**; add that it is not independent. Keep the product's burn dates separate from the FIRMS active detection dates. Slide text in [slides/limitations.md](slides/limitations.md), full scope in [pitch_facts.md](pitch_facts.md).

## Frames to capture

These are planned file names; not created yet. The capture date is assumed to be 14 November 2026; if the actual capture day differs, update the file name.

| Planned file | Content | Check |
|---|---|---|
| `img/2026-11-14_harm_HohesVenn_calendar.png` | Hohes Venn, whole period, Harmonized, Log calendar | No synthetic warning; region and series visible |
| `img/2026-11-14_harm_HohesVenn_2011-04_card.png` | April card | 17; 1/26; ≈29×; baseline 2001–2026, excluding 2011 |
| `img/2026-11-14_raw_HohesVenn_2011-04_card.png` | Raw card of the same month | 17; 1/26; ≈6.4×; same date/area |
| `img/2026-11-14_raw_harm_LaRioja_annual.png` | La Rioja annual comparison | Raw/harm units, region and 2011/2012 values explicit |

When a visual is captured, record the source path, data version/commit, date coverage, region, series and capture date in `img/SOURCES.md`. Source: “NASA FIRMS / Worldview”; if it is an app visual, also add the app URL. Do not use the NASA logo. These app frames do not replace a same-day/same-area MODIS–VIIRS Worldview layer comparison; that visual is still expected separately.

## If there is an internet or live data problem

- Priority is previously captured real app screens and the offline video. These do not exist yet; do not present them as if they did.
- The existing real-data [P3 Hohes Venn calendar](../validation/venn_check.png) provides support with the 17/1,899 raw and 17/169 harmonized monthly values. Say that it is not an app screen.
- The [P3 annual chart](../validation/annual_raw_vs_harm.png) is for **Argentina**; if it is used in place of the La Rioja screen, state clearly that the region has changed.
- Because the European transfer panel in `pred_vs_true.png` does not yet match an allowed JSON metric, do not use the full figure as a results slide. Describe the Argentina independent test with the numerical table in `pitch_facts.md`.
- If the P3 charts cannot be opened either, continue the talk with sourced number cards; do not produce new numbers.

## Rehearsal and submission log

| Check | Result |
|---|---|
| P6 public/private-window live check | Pending |
| Real app frames and source notes | Pending |
| Video recording and offline playback | Pending |
| Full talk timing, target 3:55 / upper limit 4:00 | Not measured yet |

The evidence and observation sources of the tests are in [test_notes.md](test_notes.md), the talk in [script.md](script.md), the numerical scope in [pitch_facts.md](pitch_facts.md).
