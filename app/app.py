"""P5 — Streamlit UI: MODIS ↔ VIIRS active fire detection calendar (English-only, scientific layout)."""
import base64
import json
from pathlib import Path

import folium
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import Draw, HeatMap
from streamlit_folium import st_folium

from query import PRESETS, data_info, get_hotspots, monthly_matrix, anomaly, to_csv_bytes

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MAX_POINTS = 20000  # heat layer is one array → far lighter than thousands of separate markers
LOW_MEAN, MAX_RATIO = 1.0, 100  # baseline < 1 AND ratio ≥ 100 → show "typical ≈0" instead of an absurd ratio
# query.anomaly() returns Turkish labels (contract) → English for display
LABEL_EN = {"çok yüksek": "very high", "yüksek": "high", "normal": "normal", "düşük": "low",
            "tespit yok": "no detections", "veri yok": "no data"}
RAW, HARM = "Raw", "Harmonized"
C_RAW, C_HARM = "#cdc4b2", "#e8833a"  # raw = pale sand, harmonized = theme orange (both read on the dark page)
# calendar colour scale: fire palette, pale yellow = fewest detections → dark red = most
FIRE_SCALE = [[0.0, "#fff7c2"], [0.25, "#ffd84a"], [0.5, "#fe9b2d"], [0.75, "#d93806"], [1.0, "#7a0403"]]
C_FRAME = "#ff9f1c"  # region frame on satellite imagery
C_DRAWN = "#21918c"  # user-drawn area: teal stays visible on top of the orange heat layer
C_NODATA = "#34322e"  # calendar background (no data)
LOGO = Path(__file__).parent / "assets" / "firewatch_logo.png"  # transparent PNG, sits on the page background

st.set_page_config(page_title="Active Fire Detection Calendar", page_icon=":material/local_fire_department:",
                   layout="wide")
st.markdown("""<style>
[data-testid="stStatusWidget"] {visibility: hidden; height: 0;}
.abstract {color: #c9c3b8; font-size: 1.0rem; line-height: 1.5; max-width: 980px; margin: -.4rem 0 .2rem 0;}
.facts {color: #a39d92; font-size: .92rem; line-height: 1.5; max-width: 980px; margin: 0 0 .8rem 0;}
.facts b {color: #ece7de; font-weight: 600;}
/* Site header: fixed bar with the logo; shrinks while the page scrolls (scroll-driven CSS, no JS).
   Browsers without animation-timeline keep the full-size bar. */
[data-testid="stMain"] {scroll-timeline: --page block;}
/* room for the fixed bar on top; no empty band under the footer (it sits on the page end, also on short pages) */
[data-testid="stMainBlockContainer"] {padding-top: 7.6rem; padding-bottom: 0; min-height: 100vh;
                                      display: flex; flex-direction: column;}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] {flex: 1 1 auto; min-height: calc(100vh - 7.6rem);}
[data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"] > div:has(> .st-key-sitefooter) {margin-top: auto;}
[data-testid="stHeader"] {background: transparent; height: 2.2rem;}
.sitebar {position: fixed; top: 0; left: 0; right: 0; z-index: 999980; height: 96px; padding: 0 5rem;
          display: flex; align-items: center; justify-content: space-between; gap: 1.5rem;
          background: #272522; border-bottom: 1px solid #3b3834; box-shadow: 0 2px 14px rgba(0,0,0,.35);
          animation: sitebar-shrink linear both; animation-timeline: --page; animation-range: 0 180px;}
.sitebar img {height: 72px; width: auto; display: block; pointer-events: none; user-select: none;
              animation: sitelogo-shrink linear both; animation-timeline: --page; animation-range: 0 180px;}
.sitebar .subtitle {color: #a39d92; font-size: 1.0rem; white-space: nowrap; margin-right: 1.5rem;
                    animation: sitesub-fade linear both; animation-timeline: --page; animation-range: 0 120px;}
@keyframes sitebar-shrink {to {height: 50px;}}
@keyframes sitelogo-shrink {to {height: 36px;}}
@keyframes sitesub-fade {to {opacity: 0;}}
@media (max-width: 768px) {.sitebar {padding: 0 1rem;} .sitebar .subtitle {display: none;}}
/* Site footer: separate band at the end of every page, links to the four info pages */
.st-key-sitefooter {margin-top: auto; padding: 1.1rem 1.4rem 1.2rem; background: #272522;
                    border-top: 1px solid #3b3834; border-radius: .6rem .6rem 0 0;}
.st-key-sitefooter button {color: #ece7de; text-decoration: underline; text-underline-offset: 3px;
                           text-decoration-color: #6f6a61;}
.st-key-sitefooter button:hover {color: #e8833a;}
.footnote {color: #a39d92; font-size: .88rem; margin-top: .2rem; text-align: center;}
.figcap {color: #a39d92; font-size: .86rem; line-height: 1.45; margin-top: -.3rem;}
.figcap b {color: #ece7de;}
[data-testid="stMetricValue"] {font-variant-numeric: tabular-nums;}
[data-testid="stMetricLabel"] p {color: #a39d92; font-size: .82rem;}
.dossier {font-size: .9rem; font-variant-numeric: tabular-nums; line-height: 1.6; color: #ddd7cc;}
.dossier td {padding: 1px 14px 1px 0; border: none;}
.dossier tr {border: none;}
.dossier .k {color: #948e83;}
</style>""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def info():
    return data_info()


@st.cache_data(show_spinner="Loading data…")
def load(geom_key, start, end, harmonized):
    geom = json.loads(geom_key)
    geom = tuple(geom) if isinstance(geom, list) else geom
    return get_hotspots(geom, start=start, end=end, harmonized=harmonized)


@st.cache_data(show_spinner=False)
def metrics_table():
    """Validation metrics (P3, docs/validation/metrics.json). None if not available."""
    try:
        return pd.read_json("docs/validation/metrics.json")
    except Exception:
        return None


def fmt(x, spec=".1f"):
    """NaN / None → '–' so cards never crash."""
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "–"
    return format(x, spec)


def figcap(n, title, text):
    st.markdown(f'<div class="figcap"><b>Fig. {n}. {title}</b> {text}</div>', unsafe_allow_html=True)


INFO = info()
MET = metrics_table()


def demo(preset_name, harm, year, month, annual_log=False, note="", highlight=True):
    """Main event: region + series + selected cell in one click; the month is highlighted on the map."""
    st.session_state["event"] = dict(preset=preset_name, year=year, month=month, note=note, highlight=highlight)
    st.session_state["preset"] = preset_name
    st.session_state["mode_lbl"] = HARM if harm else RAW
    st.session_state["years"] = (INFO["start"].year, INFO["end"].year)
    st.session_state["exact"] = False
    st.session_state["scale"] = "Log"
    st.session_state["sel_year"], st.session_state["sel_month"] = year, month
    st.session_state["annual_log"] = annual_log


# ---------- Info pages (opened from the footer links; ?page=<key>) ----------
def page_method():
    st.markdown(
        "**Harmonization (Method A).** MODIS is the common unit; historical MODIS data are not modified.\n\n"
        "- MODIS detections before 2012-01-20 (VIIRS S-NPP start): weight 1 "
        "(Terra-only period before Aqua, 2000-11 → 2002-07: weight 2.75, Terra+Aqua equivalent).\n"
        "- MODIS detections after 2012-01-20: weight 0 — the series is carried by VIIRS; "
        "MODIS is kept for validation only.\n"
        "- Each VIIRS detection: weight = *k* / *n*, where *k* = ΣMODIS / ΣVIIRS "
        "(per satellite × latitude band × local season; calibrated on Argentina 2012–2021, "
        "*k* ≈ 0.20–0.34) and *n* = number of VIIRS satellites active that day.\n"
        "- Harmonized count of any set of rows = Σ weight. Southern-hemisphere months are shifted by 6 "
        "so that a seasonal *k* transfers between hemispheres.")


def page_validation():
    if MET is None:
        st.info("Validation metrics not available (docs/validation/metrics.json).")
    else:
        rows = [("argentina", "test", "Argentina, held-out 2022–2024"),
                ("argentina", "test_2023-2024", "Argentina 2023–2024 (NOAA-21 not in training)"),
                ("argentina", "test_2022", "Argentina 2022"),
                ("aachen_eifel", "transfer_2012-2026", "Aachen/Eifel transfer 2012–2026")]
        out = []
        for reg, split, name in rows:
            r = {mth: MET[(MET.method == mth) & (MET.region == reg) & (MET.split == split)
                          & (MET.scale == "1deg")] for mth in ("harm", "raw_viirs")}
            if len(r["harm"]):
                out.append({"Evaluation (1° cell-month)": name,
                            "R² harmonized": round(float(r["harm"].iloc[0].r2), 2),
                            "Bias harmonized": f"{float(r['harm'].iloc[0].bias_pct):+.1f}%",
                            "R² raw VIIRS": round(float(r["raw_viirs"].iloc[0].r2), 1) if len(r["raw_viirs"]) else None,
                            "Bias raw VIIRS": f"{float(r['raw_viirs'].iloc[0].bias_pct):+.0f}%" if len(r["raw_viirs"]) else "–",
                            "n": int(r["harm"].iloc[0].n)})
        st.dataframe(pd.DataFrame(out), hide_index=True, width="stretch")
        st.markdown('<div class="figcap"><b>Table 1.</b> Prediction = harmonized VIIRS sum; reference = '
                    'MODIS count in the same 1° cell and month. bias = Σpred / Σref − 1. '
                    'R² is scale-dependent (higher at 1° than 0.25°). Source: docs/validation/metrics.json '
                    '(P3).</div>', unsafe_allow_html=True)


def page_limitations():
    st.markdown(
        "1. **2022 over-estimation (+18%)** in Argentina, concentrated in the fire season; the raw "
        "MODIS/VIIRS ratio of 2022 lies outside the training range. Annual uncertainty ≈ ±8–17%.\n"
        "2. **Transfer to Europe is weaker.** Aachen/Eifel R² = 0.79 is driven by a single event "
        "(Aug 2026); excluding it, R² = 0.37 with total bias −4.3%. For the large event the estimate "
        "is +61% (169 vs 105 MODIS).\n"
        "3. **Hypothesis, not validated:** *k* depends on fire size — a single large front yields "
        "disproportionately many VIIRS pixels (implied *k* 0.176 < all training *k* ≥ 0.20). "
        "Future work: condition *k* on cluster area / FRP; add a European training region.\n\n"
        "Detections are thermal anomalies, not confirmed fire events. Harmonized values are estimates.")


def page_sources():
    st.markdown(
        "- **NASA FIRMS** active fire data (archive + NRT), downloaded via DL_FIRE.\n"
        "- **MODIS** Collection 6.1, Terra (2000-11 →) and Aqua (2002-07 →), 1 km pixels.\n"
        "- **VIIRS** 375 m: S-NPP (2012-01 → 2026-11-02), NOAA-20 (2018-04 →), NOAA-21 (2023-03 →).\n"
        "- Supporting check (not independent): MCD64A1 burned area for Hohes Venn — "
        "Apr 2011: 9/17 MODIS detections inside burned pixels; Aug 2026: 93/105 MODIS, 1,674/1,794 VIIRS.\n"
        f"- Loaded file: `{INFO['path']}` · {INFO['n_rows']:,} rows · "
        f"{INFO['start']:%Y-%m-%d} → {INFO['end']:%Y-%m-%d} · satellites: {', '.join(INFO['satellites'])} · "
        f"data contract v{INFO.get('contract', '?')}.")


PAGES = {"method": ("Method", page_method), "validation": ("Validation", page_validation),
         "limitations": ("Limitations", page_limitations), "sources": ("Data sources", page_sources)}
# main-page widget keys: re-assigned while an info page is open so the selection survives the round trip
KEEP = ["preset", "mode_lbl", "years", "exact", "scale", "sel_year", "sel_month", "annual_log"]


def open_page(key=None):
    if key:
        st.query_params["page"] = key
    else:
        st.query_params.clear()


def site_footer():
    with st.container(key="sitefooter"):
        cols = st.columns([1, 1, 1, 1, 4])
        for c, (key, (label, _)) in zip(cols, PAGES.items()):
            c.button(label, key=f"foot_{key}", type="tertiary", on_click=open_page, args=(key,))
        st.markdown('<div class="footnote">Powered by NASA FIRMS active fire data (MODIS, VIIRS). '
                    'Made by Gravity False 9. © 2026, all rights reserved.</div>', unsafe_allow_html=True)


# ---------- Header ----------
if INFO.get("is_mock"):
    st.warning("SYNTHETIC TEST DATA — not for interpretation")
# fixed site header (plain <img>: fixed size, no hover "enlarge" button)
st.markdown(f'<div class="sitebar"><img alt="FireWatch" src="data:image/png;base64,'
            f'{base64.b64encode(LOGO.read_bytes()).decode()}">'
            '<div class="subtitle">Active Fire Detection Calendar, 2000–2026</div></div>', unsafe_allow_html=True)

# ---------- Info page instead of the calendar ----------
_page = st.query_params.get("page")
if _page in PAGES:
    for _k in KEEP:
        if _k in st.session_state:
            st.session_state[_k] = st.session_state[_k]
    st.button("← Back to the calendar", type="tertiary", on_click=open_page)
    st.header(PAGES[_page][0])
    PAGES[_page][1]()
    site_footer()
    st.stop()

st.markdown("**Main events**")
q1, q2, q3 = st.columns(3)
q1.button("Hohes Venn · April 2011", width="stretch", on_click=demo, args=("Hohes Venn", True, 2011, 4),
          kwargs=dict(note="April 2011, MODIS-only era: 17 detections on 25–26 April, the highest April in "
                           "26 years. The map shows that month only."),
          help="MODIS-only era: highest April in 26 years (harmonized)")
q2.button("Hohes Venn · August 2026", width="stretch", on_click=demo, args=("Hohes Venn", True, 2026, 8),
          kwargs=dict(note="August 2026, VIIRS era: 1,899 raw detections, 169 MODIS-equivalent after "
                           "harmonization, the highest August in 26 years. The map shows that month only."),
          help="Raw 1,899 vs harmonized 169 detections")
q3.button("La Rioja · satellite jumps", width="stretch", on_click=demo,
          args=("La Rioja (AR)", False, 2012, 4, True),
          kwargs=dict(note="La Rioja: raw annual totals step up when S-NPP (2012), NOAA-20 (2018) and NOAA-21 "
                           "(2023) start; the harmonized series stays level. See the annual chart below.",
                      highlight=False),
          help="Raw series steps up in 2012/2018/2023; harmonized stays level (annual chart, log axis)")
_ev = st.session_state.get("event")
if _ev and _ev["preset"] == st.session_state.get("preset", _ev["preset"]) and _ev["note"]:
    st.markdown(f'<div class="facts">{_ev["note"]}</div>', unsafe_allow_html=True)

# ---------- Controls (on the page, no sidebar) ----------
c_reg, c_ser, c_time, c_dates = st.columns([1.3, 1.3, 2.4, 1], vertical_alignment="bottom")
st.session_state.setdefault("preset", "La Rioja (AR)")   # opening region
preset = c_reg.selectbox("Region", list(PRESETS), key="preset")
mode_lbl = c_ser.radio("Series", [RAW, HARM], horizontal=True, key="mode_lbl",
                       help="Raw: detection count, all satellites. Harmonized: MODIS-equivalent estimate.")
mode = "raw" if mode_lbl == RAW else "harm"
y_min, y_max = INFO["start"].year, INFO["end"].year
st.session_state.setdefault("years", (y_min, y_max))
y0, y1 = c_time.slider("Year range", y_min, y_max, key="years")
d0 = max(pd.Timestamp(y0, 1, 1), INFO["start"]).date()
d1 = min(pd.Timestamp(y1, 12, 31), INFO["end"]).date()
with c_dates.popover("Exact dates", width="stretch"):
    exact = st.checkbox("Filter by day", key="exact")
    e0 = st.date_input("Start", value=d0, min_value=INFO["start"].date(),
                       max_value=INFO["end"].date(), format="YYYY-MM-DD", key="e0", disabled=not exact)
    e1 = st.date_input("End", value=d1, min_value=INFO["start"].date(),
                       max_value=INFO["end"].date(), format="YYYY-MM-DD", key="e1", disabled=not exact)
    if exact:
        if e0 > e1:
            st.warning("Start date is after end date")
        else:
            d0, d1 = e0, e1

# ---------- Map ----------
x0, y0, x1, y1 = PRESETS[preset]
if st.session_state.get("_preset") != preset:
    st.session_state["_preset"] = preset
    st.session_state["drawn"] = None
    st.session_state["map_ver"] = st.session_state.get("map_ver", 0) + 1
st.session_state.setdefault("map_ver", 0)


def reset_drawing():
    """Back to preset: clear drawing and reset the map component's memory (new key)."""
    st.session_state["drawn"] = None
    st.session_state["map_ver"] += 1


geom_key = st.session_state.get("drawn") or json.dumps([x0, y0, x1, y1])
# map: harmonized mode shows only weight_harm > 0; charts always use all rows
df_map = load(geom_key, pd.Timestamp(d0), pd.Timestamp(d1), mode == "harm")
df = load(geom_key, pd.Timestamp(d0), pd.Timestamp(d1), False)


def _bounds(geojson_str):
    """Bounds of the drawn geometry → map fits to it (no view tracking needed)."""
    pts = []

    def walk(c):
        if isinstance(c, (list, tuple)) and c and isinstance(c[0], (int, float)):
            pts.append(c)
        elif isinstance(c, (list, tuple)):
            for x in c:
                walk(x)
    walk(json.loads(geojson_str).get("coordinates", []))
    lons, lats = [q[0] for q in pts], [q[1] for q in pts]
    return [[min(lats), min(lons)], [max(lats), max(lons)]]


AREA = (_bounds(st.session_state["drawn"]) if st.session_state.get("drawn") else [[y0, x0], [y1, x1]])
AREA_TXT = (f"{AREA[0][0]:.2f}–{AREA[1][0]:.2f}° lat, {AREA[0][1]:.2f}–{AREA[1][1]:.2f}° lon"
            + (" (drawn)" if st.session_state.get("drawn") else ""))

# map on top (full width), calendar below
col_map, col_cal = st.container(), st.container()
with col_map.container(border=True):
    st.subheader("Spatial distribution")
    # main event selected → the heat layer shows only that month (otherwise the whole selected period)
    ev = st.session_state.get("event")
    ev_on = bool(ev and ev["highlight"] and ev["preset"] == preset and not st.session_state.get("drawn"))
    shown = (df_map[(df_map["year"] == ev["year"]) & (df_map["month"] == ev["month"])] if ev_on else df_map)
    m = folium.Map(tiles=None)
    _esri = "https://server.arcgisonline.com/ArcGIS/rest/services"
    folium.TileLayer(f"{_esri}/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}", name="Satellite",
                     attr="Imagery © Esri, Maxar, Earthstar Geographics").add_to(m)
    folium.TileLayer(f"{_esri}/Reference/World_Boundaries_and_Places/MapServer/tile/{{z}}/{{y}}/{{x}}",
                     name="Labels", attr="© Esri", overlay=True, control=False).add_to(m)
    # preset region: thin outline + corner brackets + detection-count badge
    folium.Rectangle([[y0, x0], [y1, x1]], color=C_FRAME, fill=False, weight=1, opacity=0.6).add_to(m)
    _dx, _dy = (x1 - x0) * 0.12, (y1 - y0) * 0.12
    for cx, cy, sx, sy in [(x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)]:
        folium.PolyLine([[cy + sy * _dy, cx], [cy, cx], [cy, cx + sx * _dx]], color=C_FRAME, weight=5).add_to(m)
    folium.Marker([y1, x1], icon=folium.DivIcon(icon_size=(0, 0), html=(
        '<div style="transform:translate(-100%,6px);display:inline-block;white-space:nowrap;'
        'background:#b3261e;color:#fff;font:600 12px ui-monospace,Menlo,monospace;'
        f'padding:3px 7px;border-radius:3px;">{len(shown):,}</div>'))).add_to(m)
    # drawn area lives in Draw's OWN layer → the trash tool can delete it
    drawn_fg = folium.FeatureGroup(name="drawn")
    if st.session_state.get("drawn"):
        g = json.loads(st.session_state["drawn"])
        polys = [g["coordinates"]] if g.get("type") == "Polygon" else g.get("coordinates", [])
        for ring in (poly[0] for poly in polys if poly):
            folium.Polygon([[lat, lon] for lon, lat in ring], color=C_DRAWN, weight=3,
                           fill=True, fill_opacity=0.1).add_to(drawn_fg)
    m.fit_bounds(AREA)
    drawn_fg.add_to(m)
    Draw(feature_group=drawn_fg,
         draw_options={"polyline": False, "circle": False, "marker": False,
                       "circlemarker": False, "polygon": True, "rectangle": True},
         edit_options={"edit": False, "remove": True}).add_to(m)
    pts = shown.sample(MAX_POINTS, random_state=0) if len(shown) > MAX_POINTS else shown
    if len(pts):
        HeatMap(pts[["latitude", "longitude"]].to_numpy().tolist(), radius=8, blur=10, min_opacity=0.35,
                gradient={0.2: "#7a0403", 0.45: "#d93806", 0.7: "#fe9b2d", 0.9: "#ffd84a", 1.0: "#fff7c2"}).add_to(m)
    # only drawing events are returned → pan/zoom does not rerun the page
    out = st_folium(m, height=480, use_container_width=True, returned_objects=["all_drawings"],
                    key=f"map_{preset}_{st.session_state['map_ver']}")
    drawings = (out or {}).get("all_drawings")
    if drawings is not None:
        if drawings:
            new_key = json.dumps(drawings[-1]["geometry"])
            if new_key != st.session_state.get("drawn"):
                st.session_state["drawn"] = new_key
                st.rerun()
        elif st.session_state.get("drawn"):
            reset_drawing()
            st.rerun()
    if st.session_state.get("drawn"):
        st.button("Back to region", icon=":material/undo:", on_click=reset_drawing,
                  help=f"Clear the drawing and return to the '{preset}' box")
    sampled = f"; heat layer from a {MAX_POINTS:,}-point sample" if len(shown) > MAX_POINTS else ""
    period = f"{MONTHS[ev['month'] - 1]} {ev['year']} only" if ev_on else f"{d0:%Y-%m-%d} → {d1:%Y-%m-%d}"
    figcap(1, "Detection density.",
           f"{len(shown):,} {'harmonized (weight > 0)' if mode == 'harm' else 'raw'} detections, "
           f"{period}{sampled}. Frame: preset region; badge: detections shown. "
           "Basemap: Esri World Imagery. Draw a rectangle or polygon to analyse a custom area.")
    if preset == "Aachen/Eifel":
        st.caption("Note: the NW corner of the box (Aachen city, north of ≈50.73°N / west of 6.10°E) is outside "
                   "the download area; empty cells there mean no data, not zero detections.")

c_stat, c_csv = st.columns([4, 1], vertical_alignment="center")
_conf = df["confidence_class"].astype(str).value_counts() if len(df) else {}
c_stat.markdown(f'<div class="facts" style="margin:0"><b>{len(df):,}</b> raw detections in selection, '
                f'{d0:%Y-%m-%d} → {d1:%Y-%m-%d} · FIRMS confidence: ' + " · ".join(
                    f"{_cls} {int(_conf.get(_cls, 0)):,}" for _cls in ["low", "nominal", "high"]) + "</div>",
                unsafe_allow_html=True)
c_csv.download_button("Download CSV", data=lambda: to_csv_bytes(df), icon=":material/download:", width="stretch",
                      file_name=f"hotspots_{preset}_{mode}.csv", mime="text/csv", disabled=df.empty)


# ---------- Calendar + selected cell (fragment) ----------
# st.fragment: cell clicks / colour scale / year-month changes rerun only this block, not the map.
@st.fragment
def calendar_and_anomaly(df, mode, d0, d1):
    st.subheader("Monthly calendar")
    if mode == "harm" and not INFO.get("has_harm"):
        st.info("Harmonized data not available yet")
        return
    if df.empty:
        st.info("No detections in this area")
        return
    s, e = pd.Timestamp(d0), pd.Timestamp(d1)
    # months outside the date filter are NaN (not 0) → calendar, totals and anomaly baseline stay correct
    mat = monthly_matrix(df, mode=mode, start=s, end=e).dropna(how="all")
    other = monthly_matrix(df, mode="harm" if mode == "raw" else "raw", start=s, end=e).dropna(how="all")
    shown = mat.astype(float).copy()
    z = shown.values
    scale = st.radio("Colour scale", ["Log", "Linear", "Anomaly (z)"], horizontal=True, key="scale",
                     help="Log keeps small events (Hohes Venn Apr 2011 = 17) visible next to large ones (1,899). "
                          "Anomaly: z-score of each cell against the same month in other years.")
    unit = "detections" if mode == "raw" else "MODIS-eq."
    if scale == "Log":
        zc = np.log10(1 + np.clip(z, 0, None))
        top = float(np.nanmax(zc)) if np.isfinite(zc).any() else 1.0
        ticks = [v for v in [0, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000, 30000, 100000]
                 if np.log10(1 + v) <= top + 1e-9]
        hm = dict(zmin=0, zmax=max(top, 1e-6),
                  colorbar=dict(title=unit, tickvals=[np.log10(1 + v) for v in ticks],
                                ticktext=[f"{v:,}" for v in ticks]))
    elif scale == "Linear":
        zc = z
        hm = dict(zmin=0, zmax=float(np.nanmax(z)) if np.isfinite(z).any() else 1, colorbar=dict(title=unit))
    else:
        zc = np.full_like(z, np.nan)
        for i, yy in enumerate(shown.index):
            for j, mm in enumerate(shown.columns):
                if np.isfinite(z[i, j]):
                    zz = anomaly(mat, yy, mm).get("z")
                    zc[i, j] = zz if zz is not None and np.isfinite(zz) else np.nan
        hm = dict(zmin=-3, zmax=3, colorbar=dict(title="z"))
    fig = go.Figure(go.Heatmap(z=zc, x=MONTHS, y=shown.index.astype(str), colorscale=FIRE_SCALE,
                               hoverinfo="skip", **hm))
    # Streamlit does not capture heatmap clicks → an invisible clickable marker on every cell
    gy, gx = np.meshgrid(shown.index.astype(str), MONTHS, indexing="ij")
    cov0, cov1 = max(s, INFO["start"]), min(e, INFO["end"])
    notes = np.full(z.shape, "", dtype=object)
    for i, yy in enumerate(shown.index):
        for j, mm in enumerate(shown.columns):
            if not np.isfinite(z[i, j]):
                continue
            m0 = pd.Timestamp(int(yy), int(mm), 1)
            m1 = m0 + pd.offsets.MonthEnd(0)
            a0, a1 = max(m0, cov0), min(m1, cov1)
            if a0 > m0 or a1 < m1:
                notes[i, j] = f"<br>Partial month: {a0:%d %b}–{a1:%d %b}"
    part = notes != ""
    if part.any():
        fig.add_trace(go.Scatter(x=gx[part], y=gy[part], mode="text", text=["•"] * int(part.sum()),
                                 textfont=dict(size=22, color="#1e1b2e"), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=gx.ravel(), y=gy.ravel(), mode="markers", showlegend=False,
        customdata=np.stack([z.ravel(), notes.ravel()], axis=-1),
        marker=dict(symbol="square", size=18, color="rgba(0,0,0,0)"),
        hovertemplate="%{x} %{y}<br>" + unit + ": %{customdata[0]:,.1f}%{customdata[1]}<extra></extra>"))
    fig.update_layout(height=560, margin=dict(l=10, r=10, t=10, b=10), clickmode="event+select",
                      plot_bgcolor=C_NODATA,
                      yaxis=dict(range=[int(shown.index.max()) + 0.5, int(shown.index.min()) - 0.5], dtick=2))
    ev = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points", key="cal")
    figcap(2, f"Monthly {'raw detections' if mode == 'raw' else 'harmonized (MODIS-equivalent) estimate'}.",
           f"{scale} colour scale. Grey = no data. • = partial month. Click a cell to inspect it.")
    pts_sel = (ev or {}).get("selection", {}).get("points", []) if ev else []
    if pts_sel:
        sel = (int(pts_sel[0]["y"]), MONTHS.index(pts_sel[0]["x"]) + 1)
        if sel != st.session_state.get("_last_sel"):
            st.session_state["_last_sel"] = sel
            st.session_state["sel_year"], st.session_state["sel_month"] = sel

    # ---- selected cell record ----
    st.subheader("Selected cell")
    c1, c2, _ = st.columns([1, 1, 2])
    years = [int(y) for y in mat.index]
    if st.session_state.get("sel_year") not in years:
        st.session_state["sel_year"] = 2026 if 2026 in years else years[-1]
    st.session_state.setdefault("sel_month", 8)
    yr = c1.selectbox("Year", years, key="sel_year")
    mo = c2.selectbox("Month", list(range(1, 13)), format_func=lambda i: MONTHS[i - 1], key="sel_month")
    a = anomaly(mat, yr, mo)
    val, mean = a.get("value"), a.get("mean")
    ratio = val / mean if (fmt(val) != "–" and fmt(mean) != "–" and mean > 0) else None
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Detections" if mode == "raw" else "MODIS-eq.", fmt(val))
    k2.metric("Rank", f"{a['rank']}/{a['n_years']}" if a.get("rank") is not None else "–",
              help="1 = highest year for this calendar month")
    if ratio is not None and mean < LOW_MEAN and ratio >= MAX_RATIO:
        k3.metric("Typical month", f"≈{mean:.1f}", "baseline ≈0 per month", delta_color="off")
    else:
        k3.metric("× baseline mean", (f"{ratio:.0f}×" if ratio >= 10 else f"{ratio:.1f}×")
                  if ratio is not None else "–")
    k4.metric("Anomaly", LABEL_EN.get(a["label"], a["label"]),
              help="Detection-count anomaly against the same month in other years, not a fire-event class")
    # record: both series side by side + context
    try:
        v_other = float(other.loc[yr, mo])
    except (KeyError, TypeError, ValueError):
        v_other = float("nan")
    v_raw, v_harm = (val, v_other) if mode == "raw" else (v_other, val)
    st.markdown(f"""<table class="dossier">
<tr><td class="k">Region</td><td>{preset}</td><td class="k">Area</td><td>{AREA_TXT}</td></tr>
<tr><td class="k">Month</td><td>{MONTHS[mo - 1]} {yr}</td><td class="k">Baseline</td>
    <td>{fmt(mean)} ± {fmt(a['std'])} (n = {a['n_years']} years) · z = {fmt(a['z'])}</td></tr>
<tr><td class="k">Raw</td><td>{fmt(v_raw, ',.0f')} detections</td><td class="k">Harmonized</td>
    <td>{fmt(v_harm, ',.1f')} MODIS-eq.</td></tr>
<tr><td class="k">Sources</td><td colspan="3">NASA FIRMS · MODIS C6.1 (Terra, Aqua) · VIIRS 375 m (S-NPP, NOAA-20, NOAA-21)</td></tr>
</table>""", unsafe_allow_html=True)


# ---------- Annual totals (fragment) ----------
@st.fragment
def annual_chart(df, d0, d1):
    st.subheader("Annual totals: raw vs harmonized")
    s, e = pd.Timestamp(d0), pd.Timestamp(d1)
    raw_y = monthly_matrix(df, "raw", start=s, end=e).sum(axis=1, min_count=1).dropna()
    harm_y = monthly_matrix(df, "harm", start=s, end=e).sum(axis=1, min_count=1).dropna()
    fy = go.Figure()
    fy.add_trace(go.Scatter(x=raw_y.index, y=raw_y.values, name="Raw (all satellites)", mode="lines+markers",
                            line=dict(color=C_RAW, width=2.5), hovertemplate="%{y:,.0f}"))
    if harm_y.notna().any():
        fy.add_trace(go.Scatter(x=harm_y.index, y=harm_y.values, name="Harmonized (MODIS-equivalent)",
                                mode="lines+markers", line=dict(color=C_HARM, width=2.5),
                                hovertemplate="%{y:,.0f}"))

    def _frac_year(ts):
        return ts.year + (ts.day_of_year - 1) / 365.25

    # satellite transitions from the data (CONTRACT v1.2 §3), not hard-coded
    rng = INFO.get("satellite_ranges", {})
    marks = [(_frac_year(rng[k][0]), lbl) for k, lbl in
             [("SNPP", "S-NPP"), ("NOAA20", "NOAA-20"), ("NOAA21", "NOAA-21")] if k in rng]
    if "SNPP" in rng and rng["SNPP"][1] < INFO["end"] - pd.Timedelta(days=3):
        marks.append((_frac_year(rng["SNPP"][1]), "S-NPP ends"))
    for k, (xv, lbl) in enumerate(marks):
        fy.add_vline(x=xv, line_dash="dot", line_width=1.2, line_color="#6f6a61")
        fy.add_annotation(x=xv, y=1.0 if k % 2 == 0 else 1.09, yref="paper", text=lbl, showarrow=False,
                          xanchor="right", yanchor="bottom", font=dict(size=11, color="#a39d92"))
    log_y = st.toggle("Log axis", key="annual_log",
                      help="On a log axis an equal ratio (e.g. 4×) has equal height at every level.")
    fy.update_layout(height=420, margin=dict(l=10, r=10, t=70, b=10), hovermode="x unified",
                     xaxis_title="Year",
                     yaxis=dict(title="Detections per year" + (" (log)" if log_y else ""),
                                type="log" if log_y else "linear"),
                     legend=dict(orientation="h", y=-0.2),
                     # same ground as the page and the calendar: transparent, warm grey text
                     template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                     font=dict(family='"Source Sans Pro", "Source Sans 3", sans-serif', size=13, color="#a39d92"),
                     hoverlabel=dict(bgcolor="#272522", bordercolor="#3b3834", font=dict(color="#ece7de")))
    fy.update_traces(marker=dict(size=8))
    fy.update_xaxes(showgrid=False, zeroline=False, ticks="", title_font=dict(size=15))
    fy.update_yaxes(gridcolor="#34322e", zeroline=False, ticks="", title_font=dict(size=15))
    st.plotly_chart(fy, width="stretch", theme=None)
    figcap(3, "Annual totals.", "Dashed lines: start of each VIIRS satellite (from the data). Raw counts step up "
           "with every new sensor; the harmonized series should not. First and last years are partial.")


with col_cal.container(border=True):
    calendar_and_anomaly(df, mode, d0, d1)
if not df.empty:
    with st.container(border=True):
        annual_chart(df, d0, d1)
site_footer()
