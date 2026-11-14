"""P5 — Streamlit arayüzü: MODIS ↔ VIIRS yangın takvimi."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import folium
from folium.plugins import Draw
from streamlit_folium import st_folium

try:
    from query import PRESETS, get_hotspots, monthly_matrix, anomaly, to_csv_bytes, data_info
    USING_MOCK = bool(data_info().get("is_mock"))
except ImportError:
    # query.py (P4) gelene kadar geçici sahte API — aynı imzalar
    USING_MOCK = True
    PRESETS = {
        "Aachen/Eifel": (5.8, 50.2, 6.8, 50.9),
        "La Rioja": (-68.5, -30.5, -66.0, -28.0),
        "Hohes Venn": (5.95, 50.45, 6.25, 50.6),
    }

    @st.cache_resource
    def _mock_df():
        rng = np.random.default_rng(0)
        rows = []
        for name, (x0, y0, x1, y1) in PRESETS.items():
            for y in range(2000, 2027):
                for m in range(1, 13):
                    if (y, m) > (2026, 10):
                        continue
                    n_viirs = (y >= 2012) + (y >= 2018) + (y >= 2024)
                    base = rng.poisson(3 if name != "La Rioja" else 15)
                    if name == "Hohes Venn" and (y, m) in [(2011, 4), (2026, 8)]:
                        base += 40
                    for sat, inst, w in (
                        [("Terra", "MODIS", 1.0)] if y < 2012 else
                        [(s, "VIIRS", 1.0 / n_viirs) for s in ["SNPP", "NOAA20", "NOAA21"][:n_viirs]]
                    ):
                        k = 1 if inst == "MODIS" else 4  # VIIRS daha hassas
                        for _ in range(base * k):
                            rows.append((rng.uniform(y0, y1), rng.uniform(x0, x1),
                                         pd.Timestamp(y, m, rng.integers(1, 28)), y, m,
                                         inst, sat, rng.uniform(1, 50), w / k))
        return pd.DataFrame(rows, columns=["lat", "lon", "acq_date", "year", "month",
                                           "instrument", "satellite", "frp", "weight_harm"])

    _MOCK = _mock_df()

    def get_hotspots(geom, start=None, end=None, harmonized=False):
        from shapely.geometry import shape, box
        poly = box(*geom) if isinstance(geom, tuple) else shape(geom)
        x0, y0, x1, y1 = poly.bounds
        d = _MOCK[_MOCK.lon.between(x0, x1) & _MOCK.lat.between(y0, y1)]
        if start is not None:
            d = d[d.acq_date >= pd.Timestamp(start)]
        if end is not None:
            d = d[d.acq_date <= pd.Timestamp(end)]
        return d.reset_index(drop=True)

    def monthly_matrix(df, mode="raw"):
        g = df.groupby(["year", "month"])
        s = g.size() if mode == "raw" else g["weight_harm"].sum()
        return s.unstack("month").reindex(columns=range(1, 13)).fillna(0.0)

    def anomaly(matrix, year, month):
        v = float(matrix.loc[year, month])
        other = matrix[month].drop(year)
        mu, sd = float(other.mean()), float(other.std())
        z = (v - mu) / sd if sd > 0 else 0.0
        label = "çok yüksek" if z > 2 else "yüksek" if z > 1 else "düşük" if z < -1 else "normal"
        return {"value": v, "mean": mu, "std": sd, "z": z,
                "rank": int((matrix[month] > v).sum() + 1), "n_years": len(matrix), "label": label}

    def to_csv_bytes(df):
        return df.to_csv(index=False).encode("utf-8")


MONTHS = ["Oca/Jan", "Şub/Feb", "Mar", "Nis/Apr", "May", "Haz/Jun",
          "Tem/Jul", "Ağu/Aug", "Eyl/Sep", "Eki/Oct", "Kas/Nov", "Ara/Dec"]
MAX_POINTS = 5000

st.set_page_config(page_title="Yangın Takvimi / Fire Calendar", page_icon="🔥", layout="wide")


@st.cache_data(show_spinner="Veri yükleniyor / Loading…")
def load(geom_key, start, end, harmonized):
    import json
    geom = json.loads(geom_key) if geom_key.startswith("{") else tuple(json.loads(geom_key))
    return get_hotspots(geom, start=start, end=end, harmonized=harmonized)


# ---------- Kenar çubuğu ----------
with st.sidebar:
    st.header("Ayarlar / Settings")
    preset = st.selectbox("Bölge / Region", list(PRESETS))
    d0, d1 = st.date_input("Tarih aralığı / Date range",
                           value=(pd.Timestamp("2000-01-01"), pd.Timestamp("2026-11-14")),
                           min_value=pd.Timestamp("2000-01-01"), max_value=pd.Timestamp("2026-12-31"))
    mode_lbl = st.radio("Seri / Series", ["Ham / Raw", "Harmonize / Harmonized"], horizontal=True)
    mode = "raw" if mode_lbl.startswith("Ham") else "harm"
    st.caption("Ham: tüm uydular toplam. Harmonize: MODIS-eşdeğeri. "
               "/ Raw: all satellites summed. Harmonized: MODIS-equivalent.")
    if USING_MOCK:
        st.warning("Sahte veri (query.py yok) / Mock data")

st.title("🔥 Yangın Takvimi 2000–2026 / Fire Calendar")

# ---------- Harita ----------
import json
x0, y0, x1, y1 = PRESETS[preset]
if st.session_state.get("_preset") != preset:
    st.session_state["_preset"] = preset
    st.session_state["drawn"] = None
    st.session_state["view"] = ([(y0 + y1) / 2, (x0 + x1) / 2], 9)
geom_key = st.session_state.get("drawn") or json.dumps([x0, y0, x1, y1])

df = load(geom_key, pd.Timestamp(d0), pd.Timestamp(d1), mode == "harm")

col_map, col_cal = st.columns([1, 1])
with col_map:
    st.subheader("Harita / Map")
    center, zoom = st.session_state["view"]
    m = folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap")
    folium.Rectangle([[y0, x0], [y1, x1]], color="#440154", fill=False, weight=2).add_to(m)
    if st.session_state.get("drawn"):
        # çizilen alan yeniden yüklemeden sonra da görünsün
        folium.GeoJson(json.loads(st.session_state["drawn"]),
                       style_function=lambda _: {"color": "#21918c", "weight": 3, "fillOpacity": 0.1}).add_to(m)
    Draw(draw_options={"polyline": False, "circle": False, "marker": False,
                       "circlemarker": False, "polygon": True, "rectangle": True},
         edit_options={"edit": False}).add_to(m)
    pts = df.sample(MAX_POINTS, random_state=0) if len(df) > MAX_POINTS else df
    for r in pts[["lat", "lon"]].itertuples(index=False):
        folium.CircleMarker([r.lat, r.lon], radius=2, color="#fde725", fill=True,
                            fill_opacity=0.7, weight=0).add_to(m)
    out = st_folium(m, height=480, use_container_width=True,
                    returned_objects=["last_active_drawing", "center", "zoom"], key=f"map_{preset}")
    out = out or {}
    drawing = out.get("last_active_drawing")
    if drawing and drawing.get("geometry"):
        new_key = json.dumps(drawing["geometry"])
        if new_key != st.session_state.get("drawn"):
            st.session_state["drawn"] = new_key
            # kullanıcının baktığı yeri koru → harita başa dönmesin
            c = out.get("center")
            if c and out.get("zoom"):
                st.session_state["view"] = ([c["lat"], c["lng"]], out["zoom"])
            st.rerun()
    if st.session_state.get("drawn") and st.button("Çizimi temizle / Clear drawing"):
        st.session_state["drawn"] = None
        st.rerun()
    st.caption(f"{len(df):,} tespit / detections" + (f" (haritada {MAX_POINTS:,} örnek)" if len(df) > MAX_POINTS else ""))

with st.sidebar:
    st.download_button("CSV indir / Download", data=to_csv_bytes(df),
                       file_name=f"hotspots_{preset}_{mode}.csv", mime="text/csv",
                       disabled=df.empty)

# ---------- Takvim ----------
with col_cal:
    st.subheader("Aylık takvim / Monthly calendar")
    if df.empty:
        st.info("Bu bölgede tespit yok / No detections in this area")
        st.stop()
    mat = monthly_matrix(df, mode=mode)
    # seçili tarih aralığı dışındaki aylar = veri yok (NaN → gri), 0 değil
    shown = mat.astype(float).copy()
    # bitiş = seçili tarih ile verideki son tarihin küçüğü (henüz gelmemiş aylar gri)
    first = pd.Timestamp(d0).to_period("M")
    last = min(pd.Timestamp(d1), df["acq_date"].max()).to_period("M")
    for yy in shown.index:
        for mm in shown.columns:
            if not (first <= pd.Period(year=int(yy), month=int(mm), freq="M") <= last):
                shown.loc[yy, mm] = np.nan
    z = shown.values
    fig = go.Figure(go.Heatmap(
        z=z, x=MONTHS, y=mat.index.astype(str), colorscale="Viridis",
        zmin=0, zmax=float(np.nanmax(z)) if np.isfinite(z).any() else 1,
        hovertemplate="Yıl/Year %{y}<br>Ay/Month %{x}<br>Değer/Value %{z:.1f}<extra></extra>",
        colorbar=dict(title="Ham" if mode == "raw" else "MODIS-eşd."),
        hoverongaps=False,
    ))
    fig.update_layout(height=560, margin=dict(l=10, r=10, t=10, b=10),
                      plot_bgcolor="#cccccc", yaxis=dict(autorange="reversed", dtick=2))
    st.plotly_chart(fig, width="stretch")

# ---------- Anomali ----------
st.subheader("Anomali / Anomaly")
c1, c2, _ = st.columns([1, 1, 2])
years = list(mat.index)
yr = c1.selectbox("Yıl / Year", years, index=len(years) - 1)
mo = c2.selectbox("Ay / Month", range(1, 13), format_func=lambda i: MONTHS[i - 1])
a = anomaly(mat, yr, mo)
k1, k2, k3 = st.columns(3)
k1.metric("Değer / Value", f"{a['value']:.1f}", f"{a['value'] - a['mean']:+.1f} vs ort./mean")
k2.metric("z-skoru / z-score", f"{a['z']:.2f}")
k3.metric("Durum / Label", a["label"], f"sıra/rank {a['rank']}/{a['n_years']}", delta_color="off")
