# P5 — Interface: Yusuf

Shared rules and the schedule are in the root `CLAUDE.md`, the schema/API is in **`docs/CONTRACT.md`** (current version). This file covers only your role.

## Files you own (Claude writes ONLY to these)
- `app/app.py`
- `.streamlit/config.toml`

## Data access
Do **not read the parquet directly**. Only the `app/query.py` API (CONTRACT §7.4):
```python
from query import PRESETS, MONTH_LABELS, data_info, get_hotspots, monthly_matrix, anomaly, to_csv_bytes
```
If `data_info()["is_mock"]` is True, show a **"SYNTHETIC TEST DATA"** warning at the top of the page.
If `data_info()["has_harm"]` is False, the harmonized toggle should say "not ready yet".
Wrap heavy calls with `@st.cache_data`. If something is missing in the API → tell Barış, do not write to query.py.
Synthetic data is ready in `data/mock/` — `git pull` is enough.

## Task (Streamlit)
1. **Sidebar** — preset region selection (`PRESETS`: Aachen/Eifel, La Rioja, Hohes Venn),
   date range, **Raw / Harmonized** toggle (`mode="raw"` / `"harm"`), CSV download button.
2. **Map** — `streamlit-folium` + `folium.plugins.Draw` (rectangle/polygon). Drawn GeoJSON →
   `get_hotspots(geom)`. Points of the selected region (if there are too many, sample them, ≤5000).
3. **Calendar heatmap** — `plotly` `go.Heatmap`: x = month (Oca…Ara, i.e. Jan…Dec), y = year, color `viridis`,
   hover: year, month, value. NaN cells gray. Separate color scale when switching raw ↔ harmonized.
4. **Anomaly card** — `anomaly()` for the selected (year, month): `st.metric` value + z + label.
   Cell selection by clicking in the heatmap (if `plotly_events` is not available, a selectbox is enough).
5. **Explanation line** — "Raw: detection count of all satellites. Harmonized: MODIS-equivalent estimate."
   In the texts "detection", not "fire" (CONTRACT §8); anomaly card = detection count anomaly.
6. **Publishing (Sunday morning)** — Streamlit Cloud, main file `app/app.py`, data `data/deploy/`.

## Submissions
| Time | What | To whom |
|---|---|---|
| 13:00 | App up and running with mock data (map + calendar) | everyone |
| 16:30 | Raw calendar end-to-end with real data | Barış |
| 19:00 | MVP: map + drawing + calendar + anomaly + toggle + CSV | İbrahim (test) |
| Sunday 10:00 | Streamlit Cloud link | İbrahim (P6), Barış |

## Done check
- [ ] When Hohes Venn is selected, April 2011 and August 2026 stand out in the calendar
- [ ] In La Rioja, the 2012/2018/2023 jump disappears when switching Raw → Harmonized
- [ ] Does not crash when an empty region is drawn ("No detections in this area" message)
- [ ] First page load < 5 s (cache)

## Note for Claude
- Visual consistency: viridis, a single font, headings short in Turkish + English (the judges may be foreign).
- If a new package is needed, do not add it; say "tell Barış to add it to requirements".
- After the feature freeze (Sunday 12:00), bug fixes only.
