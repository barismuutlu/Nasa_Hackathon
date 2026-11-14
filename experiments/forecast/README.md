# Forecast experiments (14 Nov 2026) — record only, NOT used by the app

Owner: P4 Barış. All inputs are NASA data (FIRMS via harmonized `monthly_grid`, NASA POWER / MERRA-2).
Scripts here are research notes; paths point to the author's machine and are not maintained.
The model that ships is `pipeline/forecast.py` on `main` (30-day outlook, method by P2 Bahtiyar).

| Experiment | Protocol | Result | Verdict |
|---|---|---|---|
| Gradient boosting (Poisson), 2 months ahead (`forecast_gbm_2month.py`) | test 2022–2025 | monthly-total error 45% vs 60% (count-mean baseline), but cell R²(log) 0.70 < 0.73 of log-mean baseline | not used |
| Same, 0.25° cells (16× rows) | test 2022–2025 | 47% | no gain |
| + NASA POWER local weather (precip., Tmax, RH anomalies) | test 2022–2025 | 45% → 47% (pre-set rule: accept if < 34%) | rejected |
| + NASA POWER weather, 1-month rolling (`test_weather_rolling.py`) | 2015–2025 rolling origin | skill 0.238 → 0.239 | rejected |
| + El Niño index from NASA MERRA-2 Niño 3.4 skin temp. (`enso_index.py`, `test_enso_rolling.py`) | 2015–2025 rolling, horizons 1–6 months | skill gain ≤ +0.004 at every horizon (pre-set rule ≥ +0.05) | rejected |
| 30-day window from the 15th, 2-day gap (`prototype_30day.py`) | 2015–2025 rolling, 132 origins | skill 0.232, direction 74%, total bias −0.1% after scaling fix | **shipped** (`pipeline/forecast.py`) |

Lesson: past detections already carry the information in past weather and ENSO at these horizons; a
forward-looking climate forecast (e.g. NASA GEOS-S2S) would be the next input to try.
Bug found: summing expm1(log predictions) underestimates regional totals (−24% Argentina, −44% La Rioja);
fixed by predicting the ratio to normal and scaling the 10-year arithmetic normal.
