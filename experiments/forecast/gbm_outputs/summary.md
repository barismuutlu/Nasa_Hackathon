# Experimental 2-month-ahead detection outlook

Owner: P4 Barış · script: `pipeline/forecast.py` · data through 2026-10 · target **2026-12**

This is an outlook for **detection counts** (harmonized, MODIS-equivalent), not a fire forecast.

Test 2022–2025 (training targets 2005–2021), Argentina, 1° cells:

| Scope | Method | Monthly-total R² (log) | Monthly-total error | Bias | Cell R² (log) |
|---|---|---|---|---|---|
| argentina | model | 0.43 | 45% | +5.5% | 0.70 |
| argentina | climatology | 0.39 | 60% | +23.9% | 0.59 |
| la_rioja | model | 0.67 | 57% | -9.7% | — |
| la_rioja | climatology | 0.63 | 62% | +8.1% | — |

Outlook: Argentina Σ pred = 2,322 vs normal 3,889 (last 10 years, same month); La Rioja box Σ pred = 77.2 vs normal 69.6.

Inputs (NASA only): harmonized NASA FIRMS detection history. Limits: no weather/drought inputs; one region; skill over the seasonal average is modest at the regional-total level and larger at the cell level. Harmonization coefficients are themselves an estimate (see docs/validation/).

NASA POWER weather (precipitation, max temperature, humidity anomalies) was tested: Argentina test error 44.9% → 47.2% with weather → not used (pre-set rule: accept only if error < 34%).
