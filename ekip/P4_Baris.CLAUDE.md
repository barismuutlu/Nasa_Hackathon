# P4 — Data Layer + LEAD: Barış

Shared rules, schema and schedule are in the root `CLAUDE.md`. This file covers only your role.

## Files you own
- `app/query.py`, `contract.py`, `docs/CONTRACT.md`, `tests/smoke_test.py`
- `CLAUDE.md`, `ekip/*`, `requirements.txt`, `.gitignore`
- `data/mock/`, `data/deploy/`

## Leadership
- Integration + quick decisions. Schema/API change requests come to you → decide within 5 min,
  write the decision into `docs/CONTRACT.md` (with the changelog), push it, announce it to the group.
- At every checkpoint (10:30, 13:00, 16:30, 19:00) a 5 min meeting: everyone "done / blocker / next".
- If someone is stuck for more than 15 min, help or reduce the scope.
- Enforce the Sunday 12:00 feature freeze.

## Task
1. **08:55** — push the repo skeleton: `CLAUDE.md`, `ekip/`, `.gitignore`, `requirements.txt`, folders.
   To everyone: the `cp`/`echo "@ekip/<file>" > CLAUDE.local.md` instruction.
2. **11:00** — `data/mock/hotspots_mock.parquet`: synthetic data with the CONTRACT §1 schema (`version="MOCK"`)
   (Aachen/Eifel + La Rioja, 2000–2026, all satellites, counts should increase when VIIRS is added,
   peak in the Venn in April 2011 & August 2026). `weight_harm` = simple fake value. → Yusuf (P5).
3. **`app/query.py`** — API: CONTRACT §7.4:
   - `PRESETS`: `"Aachen/Eifel": (5.9, 50.2, 7.0, 50.9)`, `"La Rioja (AR)": (-69.7, -31.9, -65.4, -27.6)`,
     `"Hohes Venn": (5.95, 50.45, 6.25, 50.60)`
   - `get_hotspots()` — bbox or GeoJSON Polygon (inside or not, with shapely), date filter.
     Read the parquet without `@st.cache_data` (so that query.py does not depend on Streamlit); caching is in P5.
   - `monthly_matrix()` — year × month pivot; missing month 0; if there is no satellite at all in that year (2000 January–October) NaN.
   - `anomaly()` — mean, std, z, rank relative to the other years of the same month; label:
     z>2 "çok yüksek" (very high), z>1 "yüksek" (high), |z|≤1 "normal", z<−1 "düşük" (low).
   - `to_csv_bytes()` — CSV download data.
4. **16:30** — working with real data (`hotspots_harm.parquet`).
5. **Sunday morning** — `data/deploy/`: only the preset regions for Streamlit Cloud, <50 MB → Yusuf.

## Submissions
| Time | What | To whom |
|---|---|---|
| 08:55 | Repo skeleton | everyone |
| 11:00 | Mock parquet + query.py first version | Yusuf (P5) |
| 16:30 | query.py with real data | Yusuf (P5) |
| Sunday 09:00 | `data/deploy/` | Yusuf (P5) |

## Before submission (Sunday, before the feature freeze)
- [ ] `README.md` to be translated into English (currently Turkish; the judges will read English). Fill in the placeholders:
      demo link, presentation link, R²/bias (docs/validation/metrics.json).
- [ ] Repo to be made public (the judges evaluate "the entire project").

## Done check
- [ ] `monthly_matrix(get_hotspots(PRESETS["Hohes Venn"]), "harm")` → 2011-04 and 2026-08 > 0
- [ ] Switching between mock and real data does not change a single line in app.py
- [ ] Region drawing (GeoJSON) and bbox give the same result (for a rectangle drawing)
