# Talk of about four minutes

P6 İbrahim · 14 November 2026. Target 3:55; timed rehearsal not done yet. Source and full metrics: [pitch_facts.md](pitch_facts.md); click flow: [demo.md](demo.md).

Presenter note: Square brackets are not read aloud. Screens were not captured in this session. For the live demo, check the real and harmonized data status in advance. If there is no visual, continue with the verified number cards and P3's real-data calendar; do not use a synthetic screen.

## 00:00–00:30 · Problem

[Screen: “Why does the detection count change?”]

“If satellite detections increase in a region, how do we interpret that? The observed events may have changed; but the satellites making the observations are changing too. MODIS and VIIRS have different resolutions and observation coverage. When new satellites join, comparing the raw detection count directly with past years can be misleading. We want to read this long record while taking satellite coverage into account.”

## 00:30–01:00 · Same event, different numbers

[Screen: Hohes Venn, August 2026; raw 1,899, harmonized about 169.]

“In August 2026 there are 105 MODIS and 1,794 VIIRS detections in Hohes Venn. The raw total is 1,899; the VIIRS count is about 17 times the MODIS count. These are pixel detections, not a count of fire events. The ratio of this single example is not a universal coefficient either. The harmonized monthly estimate is about 169 MODIS-equivalent; this value does not exactly match the 105 MODIS reference either.”

## 01:00–01:50 · Method

[Screen: DL_FIRE → common schema → raw / MODIS-equivalent calendar.]

“Our inputs are FIRMS DL_FIRE archive and NRT records. In the Argentina and Aachen/Eifel areas we handle duplicates and source overlaps with common rules. Each record is a thermal anomaly pixel in one satellite overpass.

Bahtiyar's Method A implementation learns the ratios between MODIS and VIIRS from Argentina's 2012–2021 data. The coefficients vary by latitude band, local season and satellite; the number of active VIIRS satellites also enters the weight. The sum of these weights gives the MODIS-equivalent estimate.

We also keep the raw series. This way the user can see both the observed record count and the estimate converted to a common unit. We evaluate how well the conversion works against the MODIS reference in the years 2022–2024, which were not used in training. This method does not produce validated fire event counts.”

## 01:50–03:00 · Demo: April 2011 and La Rioja

[Hohes Venn → whole data period → Harmonized → Log → 2011-04. Do not use a narrow date filter; the 26-April baseline must be preserved.]

“Let's look at April 2011. In three overpasses on 25–26 April there are 17 MODIS pixel detections; all on the Belgian side. The harmonized total is also 17. The harmonized mean of the other 25 Aprils in 2001–2026 is about 0.59. At about 29 times that, this month is the highest of the 26 Aprils examined.

When we switch to the raw series the value is again 17, but the card's comparison mean is 2.64; the ratio is about 6.4 times. Because the raw baseline also includes detections from the VIIRS period. That is why it matters to state which series and baseline we use when interpreting the same month.

As additional support, 9 of the 17 detections overlap, within a neighborhood of about 1.4 kilometers, with areas that MCD64A1 marked as burned on 24–28 April. This is not independent validation; the product also uses MODIS active fire data.

In La Rioja the annual raw total rises from 868 in 2011 to 3,437 in 2012; the harmonized series goes from 868 to 808. This example is useful, but it does not mean a perfect match every year.”

[La Rioja (AR), whole date coverage, annual raw/harmonized chart. If the screen is not ready, use the number card. If needed, explain the 2017 limitation: 3,236 estimate, 2,447 MODIS; about 32% over.]

[MCD64A1 framing: source “NASA MCD64A1 C6.1”; say only “supporting evidence”. 3×3 pixels ≈1.4 km width; ±16 days matching. P1: single pixel 5/17, 3×3 9/17 (53%), 5×5 15/17. August: MODIS 93/105 (89%), VIIRS 1,674/1,794 (93%); product burn dates 15–23 August. Do not confuse these with the 14–17 August dates of the active detections. Do not present the overlap as R²/bias or as an independent validation metric.]

## 03:00–03:30 · Independent test and limit

[Screen: Argentina, 2022–2024, harm, 1° cell-month; R²=0.7918, bias=+1.3674 detections/cell-month, bias %=+6.72, n=8,616.]

“In Oğuzhan's independent test, in Argentina at the one-degree cell-month scale, R squared is about 0.79; the total deviation is plus 6.72 percent. The sample size is 8,616 cell-months. When 2022 is evaluated on its own, the overestimate is 18.36 percent. In Aachen/Eifel the sample is small and there is overestimation in the large event. That is why we do not say that we fully removed the satellite effect or that we transferred it to every region with the same success.”

[Source: docs/validation/metrics.json, b4cbbd4; main record data=harm, method=harm, region=argentina, split=test, scale=1deg. The “R²=0.79” value must not be confused with the European transfer result.]

## 03:30–03:55 · Impact

[Screen: “Raw detection · MODIS-equivalent estimate · Explicit coverage”.]

“Our goal is to evaluate the detection count together with the observing system when interpreting long-term satellite records. The calendar makes both series and the comparison baseline visible. Our next step is to improve transfer to large events and to different regions. We present every number together with its region, time, unit and limitations.”

## Alternative 60-second evidence narration

This alternative is not added to the main talk; when needed it replaces the evidence/demo section. Durations have not been measured yet.

> In April 2011, in Hohes Venn, there are 17 MODIS pixel detections in three overpasses; all on the Belgian side. The harmonized total is also 17. The harmonized mean of the other 25 Aprils in 2001–2026 is about 0.59: at about 29 times that, this month is the highest of the 26 Aprils. On the raw card, because of a different baseline, it shows about 6.4 times.
>
> In August 2026 there are 105 MODIS and 1,794 VIIRS detections; the raw difference of about 17 times is not a universal coefficient. The harmonized monthly estimate is about 169 MODIS-equivalent. In Argentina's 2022–2024 test, at the 1° cell-month scale, R² is about 0.79 and the total deviation +6.72%. The method enables useful comparisons; the overestimation limit in transfer to large events remains.

## Rehearsal check

- Full-length target 3:55, upper limit 4:00; no measured time yet.
- The April card must show Harmonized, the whole date coverage and 1/26. In the presentation, say “about 29 times” for 28.7×.
- Describe the old about 25 times only as the MODIS-only 2001–2025 comparison.
- P3's ≈27× correction is the MODIS-only 2001–2026 baseline; do not confuse it with the harmonized card's ≈29× value. If you are not going to explain the baseline, say “the highest of the 26 Aprils examined; at most 3 in the other years”.
- Label the August 169 value as a monthly MODIS-equivalent estimate; if 14–17 is selected, keep the partial-month marker.
- P1's precise monthly value is 169.2; the 169 in the talk and in the P3 chart is its rounded display.
- Do not present the Argentina test metric as Aachen/Eifel success. Do not use the transfer panel awaiting approval in the P3 chart as a presentation result.
- Real screenshots, offline video and timed rehearsal have not been completed yet.
