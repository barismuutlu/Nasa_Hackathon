"""P5 — Streamlit UI: MODIS ↔ VIIRS active fire detection calendar (English-only, scientific layout)."""
import json

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
C_RAW, C_HARM = "#440154", "#21918c"  # viridis ends, used consistently for the two series
# calendar colour scale: fire palette, pale yellow = fewest detections → dark red = most
FIRE_SCALE = [[0.0, "#fff7c2"], [0.25, "#ffd84a"], [0.5, "#fe9b2d"], [0.75, "#d93806"], [1.0, "#7a0403"]]
C_FRAME = "#ff9f1c"  # region frame on satellite imagery
C_NODATA = "#2a2d36"  # calendar background (no data)

st.set_page_config(page_title="Active Fire Detection Calendar", page_icon=":material/local_fire_department:",
                   layout="wide")
st.markdown("""<style>
[data-testid="stStatusWidget"] {visibility: hidden; height: 0;}
.kicker {font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: .78rem;
         letter-spacing: .08em; text-transform: uppercase; color: #b5de2b; margin-bottom: -.4rem;}
.abstract {color: #b8b5c8; font-size: 1.0rem; line-height: 1.5; max-width: 980px; margin: -.4rem 0 .6rem 0;}
.figcap {color: #9a97ad; font-size: .86rem; line-height: 1.45; margin-top: -.3rem;}
.figcap b {color: #e8e6f0;}
[data-testid="stMetricValue"] {font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace;
                               font-variant-numeric: tabular-nums;}
[data-testid="stMetricLabel"] p {color: #9a97ad; text-transform: uppercase; font-size: .74rem; letter-spacing: .05em;}
[data-testid="stSidebar"] h3 {font-size: .8rem; text-transform: uppercase; letter-spacing: .08em;
                              color: #b5de2b; margin-top: .6rem;}
.dossier {font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; font-size: .84rem;
          font-variant-numeric: tabular-nums; line-height: 1.6; color: #d6d3e4;}
.dossier td {padding: 1px 14px 1px 0; border: none;}
.dossier tr {border: none;}
.dossier .k {color: #8a879c;}
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


def headline_metric():
    if MET is None:
        return None
    r = MET[(MET.method == "harm") & (MET.region == "argentina") & (MET.split == "test") & (MET.scale == "1deg")]
    return (float(r.iloc[0].r2), float(r.iloc[0].bias_pct)) if len(r) else None


def demo(preset_name, harm, year, month, annual_log=False):
    """Quick-start: region + series + selected cell in one click."""
    st.session_state["preset"] = preset_name
    st.session_state["mode_lbl"] = HARM if harm else RAW
    st.session_state["years"] = (INFO["start"].year, INFO["end"].year)
    st.session_state["exact"] = False
    st.session_state["scale"] = "Log"
    st.session_state["sel_year"], st.session_state["sel_month"] = year, month
    st.session_state["annual_log"] = annual_log


# ---------- Header ----------
if INFO.get("is_mock"):
    st.warning("SYNTHETIC TEST DATA — not for interpretation")
st.markdown('<div class="kicker">NASA Space Apps 2026 · FIRMS MODIS ↔ VIIRS</div>', unsafe_allow_html=True)
st.title("Active Fire Detection Calendar, 2000–2026")
st.markdown('<div class="abstract">Satellite active-fire detections (thermal anomalies) from NASA FIRMS, '
            'aggregated into a continuous monthly calendar. Each new VIIRS satellite inflates raw counts '
            '(2012, 2018, 2023); the harmonized series converts VIIRS detections into '
            '<b>MODIS-equivalent units</b> so that years remain comparable. A detection is a hot pixel, '
            'not a confirmed fire event.</div>', unsafe_allow_html=True)

_hm = headline_metric()
s1, s2, s3, s4 = st.columns(4)
with s1.container(border=True):
    st.metric("Coverage", f"{INFO['start'].year}–{INFO['end'].year}",
              f"{INFO['end'].year - INFO['start'].year + 1} years, monthly", delta_color="off")
with s2.container(border=True):
    st.metric("Satellites", len(INFO["satellites"]), "2 MODIS + 3 VIIRS", delta_color="off")
with s3.container(border=True):
    st.metric("Detections", f"{INFO['n_rows'] / 1e6:.2f} M", "active-fire pixels", delta_color="off")
with s4.container(border=True):
    if _hm:
        st.metric("Independent test", f"R² = {_hm[0]:.2f}", f"bias {_hm[1]:+.1f}% · Argentina 2022–24, 1°",
                  delta_color="off",
                  help="k calibrated on Argentina 2012–2021; 2022–2024 held out. 1° cell-month scale.")
    else:
        st.metric("Independent test", "–")

st.markdown('<div class="kicker">Quick start</div>', unsafe_allow_html=True)
q1, q2, q3 = st.columns(3)
q1.button("Hohes Venn · April 2011", width="stretch", on_click=demo, args=("Hohes Venn", True, 2011, 4),
          help="MODIS-only era: highest April in 26 years (harmonized)")
q2.button("Hohes Venn · August 2026", width="stretch", on_click=demo, args=("Hohes Venn", True, 2026, 8),
          help="Raw 1,899 vs harmonized 169 detections")
q3.button("La Rioja · satellite jumps", width="stretch", on_click=demo,
          args=("La Rioja (AR)", False, 2012, 4, True),
          help="Raw series steps up in 2012/2018/2023; harmonized stays level (annual chart, log axis)")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Settings")
    st.subheader("Region")
    preset = st.selectbox("Region", list(PRESETS), key="preset", label_visibility="collapsed")
    st.subheader("Series")
    mode_lbl = st.radio("Series", [RAW, HARM], horizontal=True, key="mode_lbl", label_visibility="collapsed")
    mode = "raw" if mode_lbl == RAW else "harm"
    st.caption("Raw: detection count, all satellites. Harmonized: MODIS-equivalent estimate.")
    st.subheader("Time")
    y_min, y_max = INFO["start"].year, INFO["end"].year
    st.session_state.setdefault("years", (y_min, y_max))
    y0, y1 = st.slider("Year range", y_min, y_max, key="years")
    d0 = max(pd.Timestamp(y0, 1, 1), INFO["start"]).date()
    d1 = min(pd.Timestamp(y1, 12, 31), INFO["end"]).date()
    with st.expander("Exact dates"):
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
    st.caption(f"Selected: {d0:%Y-%m-%d} → {d1:%Y-%m-%d}")

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
        f'padding:3px 7px;border-radius:3px;">{len(df_map):,}</div>'))).add_to(m)
    # drawn area lives in Draw's OWN layer → the trash tool can delete it
    drawn_fg = folium.FeatureGroup(name="drawn")
    if st.session_state.get("drawn"):
        g = json.loads(st.session_state["drawn"])
        polys = [g["coordinates"]] if g.get("type") == "Polygon" else g.get("coordinates", [])
        for ring in (poly[0] for poly in polys if poly):
            folium.Polygon([[lat, lon] for lon, lat in ring], color=C_HARM, weight=3,
                           fill=True, fill_opacity=0.1).add_to(drawn_fg)
    m.fit_bounds(AREA)
    drawn_fg.add_to(m)
    Draw(feature_group=drawn_fg,
         draw_options={"polyline": False, "circle": False, "marker": False,
                       "circlemarker": False, "polygon": True, "rectangle": True},
         edit_options={"edit": False, "remove": True}).add_to(m)
    pts = df_map.sample(MAX_POINTS, random_state=0) if len(df_map) > MAX_POINTS else df_map
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
    sampled = f"; heat layer from a {MAX_POINTS:,}-point sample" if len(df_map) > MAX_POINTS else ""
    figcap(1, "Detection density.",
           f"{len(df_map):,} {'harmonized (weight > 0)' if mode == 'harm' else 'raw'} detections, "
           f"{d0:%Y-%m-%d} → {d1:%Y-%m-%d}{sampled}. Frame: preset region; badge: detections shown. "
           "Basemap: Esri World Imagery. "
           "Draw a rectangle or polygon to analyse a custom area.")
    if preset == "Aachen/Eifel":
        st.caption("Note: the NW corner of the box (Aachen city, north of ≈50.73°N / west of 6.10°E) is outside "
                   "the download area; empty cells there mean no data, not zero detections.")

with st.sidebar:
    st.subheader("Statistics")
    _conf = df["confidence_class"].astype(str).value_counts() if len(df) else {}
    st.caption(f"Raw detections in selection: **{len(df):,}** · by FIRMS confidence")
    st.markdown('<table class="dossier" style="width:100%;text-align:center"><tr>' + "".join(
        f'<td style="padding:0"><span class="k">{_cls.upper()}</span><br>'
        f'<span style="font-size:1.15rem;font-weight:650">{int(_conf.get(_cls, 0)):,}</span></td>'
        for _cls in ["low", "nominal", "high"]) + "</tr></table>", unsafe_allow_html=True)
    st.subheader("Export")
    st.download_button("Download CSV", data=lambda: to_csv_bytes(df), icon=":material/download:",
                       file_name=f"hotspots_{preset}_{mode}.csv", mime="text/csv", disabled=df.empty)
    with st.expander("Data provenance"):
        st.markdown(
            f"- File: `{INFO['path']}`\n"
            f"- Range: {INFO['start']:%Y-%m-%d} → {INFO['end']:%Y-%m-%d}\n"
            f"- Satellites: {', '.join(INFO['satellites'])}\n"
            f"- Rows: {INFO['n_rows']:,}\n"
            f"- Data contract: v{INFO.get('contract', '?')}")


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
        fy.add_vline(x=xv, line_dash="dash", line_color="#888")
        fy.add_annotation(x=xv, y=1.0 if k % 2 == 0 else 1.09, yref="paper", text=lbl, showarrow=False,
                          xanchor="right", yanchor="bottom", font=dict(size=11, color="#666"),
                          bgcolor="rgba(255,255,255,0.8)")
    log_y = st.toggle("Log axis", key="annual_log",
                      help="On a log axis an equal ratio (e.g. 4×) has equal height at every level.")
    fy.update_layout(height=420, margin=dict(l=10, r=10, t=70, b=10), hovermode="x unified",
                     xaxis_title="Year",
                     yaxis=dict(title="Detections per year" + (" (log)" if log_y else ""),
                                type="log" if log_y else "linear"),
                     legend=dict(orientation="h", y=-0.2),
                     # light card on the dark page: the two viridis series colours need a white ground
                     template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                     font=dict(family='"Source Sans Pro", "Source Sans 3", sans-serif', size=13,
                               color="rgba(49,51,63,0.6)"),
                     hoverlabel=dict(bgcolor="#ffffff", font=dict(color="#1e1b2e")))
    fy.update_traces(marker=dict(size=8))
    fy.update_xaxes(showgrid=False, zeroline=False, ticks="", title_font=dict(size=15))
    fy.update_yaxes(gridcolor="#e6eaf1", zeroline=False, ticks="", title_font=dict(size=15))
    st.plotly_chart(fy, width="stretch", theme=None)
    figcap(3, "Annual totals.", "Dashed lines: start of each VIIRS satellite (from the data). Raw counts step up "
           "with every new sensor; the harmonized series should not. First and last years are partial.")


# ---------- Methods, validation, limitations ----------
def methods_section():
    st.subheader("Methods & validation")
    t1, t2, t3, t4 = st.tabs(["Method", "Validation", "Limitations", "Data sources"])
    with t1:
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
    with t2:
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
    with t3:
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
    with t4:
        st.markdown(
            "- **NASA FIRMS** active fire data (archive + NRT), downloaded via DL_FIRE.\n"
            "- **MODIS** Collection 6.1, Terra (2000-11 →) and Aqua (2002-07 →), 1 km pixels.\n"
            "- **VIIRS** 375 m: S-NPP (2012-01 → 2026-11-02), NOAA-20 (2018-04 →), NOAA-21 (2023-03 →).\n"
            "- Supporting check (not independent): MCD64A1 burned area for Hohes Venn — "
            "Apr 2011: 9/17 MODIS detections inside burned pixels; Aug 2026: 93/105 MODIS, 1,674/1,794 VIIRS.\n"
            f"- Loaded file: `{INFO['path']}` · {INFO['n_rows']:,} rows · data contract v{INFO.get('contract', '?')}.")


with col_cal.container(border=True):
    calendar_and_anomaly(df, mode, d0, d1)
if not df.empty:
    with st.container(border=True):
        annual_chart(df, d0, d1)
with st.container(border=True):
    methods_section()
