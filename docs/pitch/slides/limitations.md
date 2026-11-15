# Slide: Limitations and next step

P6 İbrahim · 14 November 2026. Real data sources: P3 `metrics.json` (`b4cbbd4`), `summary.md` (`c6f15ad`) and the P1/P4 submissions. This file is slide text; it is not a finished presentation file.

## Three points to show on screen

1. **2022 overestimate:** Argentina, 2022 independent test, 1° cell-month: total deviation **+18.36%**; R²=0.7052, n=2,834. At the same scale the 2023–2024 deviation is −2.51%; one year's error must not be hidden inside the overall average.
2. **Transfer to regions and large events is limited:** Hohes Venn August 2026 estimate **169.2 MODIS-equivalent**, MODIS reference 105; about **+61%**. Aachen/Eifel has only 7 MODIS detections in 2022–2024; we do not use this region's test R² for a success claim. La Rioja 2017 also has an overestimate of about +32%.
3. **Next step — hypothesis to be tested:** The coefficient may depend on fire size; this has not been validated yet. Conditioning on the area / total FRP of detection clusters and a second training region from Europe should be evaluated.

## Speaker notes

- Do not attribute the 2022 deviation solely to the S-NPP/Aqua outage or orbital drift; the P3 summary does not support this as an explanatory result.
- The `transfer_2012-2026` and large-event-excluded transfer R² results are not in the current `metrics.json`; P4 approval and a contract-compliant record are awaited. Do not use their numerical R² values on this slide.
- There is no separate calculation/method record in the JSON for the annual uncertainty band in P3's message; the numerical band was not added to this slide.
- Source **NASA MCD64A1 C6.1**. The overlap is only **supporting evidence**: 3×3 pixel neighborhood ≈1.4 km width, ±16 days; April 9/17 (53%), August MODIS 93/105 (89%), VIIRS 1,674/1,794 (93%). The product also uses MODIS active fire input; it is not independent validation or event classification accuracy. It is not added to the R²/bias table.
- Every R² must be accompanied by region, test period, scale and n. The phrases “real fire count” and “satellite jumps fully removed” are not used.
