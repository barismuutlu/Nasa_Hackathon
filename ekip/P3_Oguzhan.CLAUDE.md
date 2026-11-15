# P3 — ML & Validation: Oğuzhan

Shared rules and the schedule are in the root `CLAUDE.md`, the schema is in **`docs/CONTRACT.md`** (current version). This file covers only your role.

## Files you own (Claude writes ONLY to these)
- `pipeline/validate.py`
- `docs/validation/` (plots + metrics)

## Input / output
- Input: `data/monthly_grid.parquet`, `data/hotspots_harm.parquet`, `data/k_factors.csv` (P2).
  Until P2 is ready, set up the skeleton with mock/sample data.
- Outputs (`docs/validation/`, commit to git):
  - `metrics.json` — CONTRACT §7.3: `[{"method","region","split","scale","r2","bias","bias_pct","n"}]`
  - `pred_vs_true.png` — predicted (`n_harm` from VIIRS) vs actual (`n_modis`) scatter, log-log, 1:1 line
  - `annual_raw_vs_harm.png` — Argentina annual raw / harmonized / MODIS
  - `venn_check.png` — Hohes Venn calendar slice (April 2011, August 2026)

## Task
1. **Split** — Training 2012–2021 (P2 learns k from here), **Test 2022–2024**.
2. **Predicted vs actual** — in the test years, per cell × month:
   predicted = `Σ weight_harm` of the VIIRS rows, actual = `n_modis`.
   - Cell-months where at least one side is > 0. Also compute it aggregated to 1° (less noise).
3. **Metrics** — R², bias = mean(predicted − actual), bias % = Σ predicted / Σ actual − 1.
   Report Argentina (training region) and `aachen_eifel` (transfer) **separately**.
4. **Venn check** — Hohes Venn box (lon 5.95–6.25, lat 50.45–50.60):
   are April 2011 (MODIS-only period) and August 2026 (VIIRS) visible in the raw + harmonized counts?
   What is that month's anomaly z-score? Result: yes/no + numbers.
5. **If time allows: Method B** — logistic regression (scikit-learn): for a VIIRS detection,
   p(there is a MODIS detection on the same day within ±1 km). Features: `frp, brightness, scan, track, daynight,
   satellite, latitude band, season`. (Careful: `brightness` is not comparable between MODIS and VIIRS.) Weight = p / n_active_viirs. A vs B table with the same metrics.
   → tell Barış; if chosen, P2 integrates it.

## Submissions
| Time | What | To whom |
|---|---|---|
| 17:30 | First version of the metrics (Method A) | Barış |
| 19:00 | All of `docs/validation/` + 3-sentence summary ("R²=…, bias=…, Venn visible") | İbrahim (P6) |

## Done check
- [ ] The test years did not enter the k computation in any way (confirm with P2)
- [ ] Plots ready for the presentation: axis labels, units, large font, title
- [ ] `python pipeline/validate.py` regenerates all outputs with a single command

## Note for Claude
- Do not change `harmonize.py`; if there is a suggestion about the k method, give it to the user as a note.
- matplotlib for the plots, colormap viridis (consistent with the app).
- If R² comes out negative/very low, do not hide it — tell the user clearly; it is explained honestly in the pitch.
- Write the Venn result as "detection increase", not "fire detected" (CONTRACT §8).
