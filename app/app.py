"""P5 — Streamlit arayüzü: MODIS ↔ VIIRS aktif yangın tespit takvimi."""
import json

import folium
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import Draw, HeatMap
from streamlit_folium import st_folium

from query import PRESETS, MONTH_LABELS, data_info, get_hotspots, monthly_matrix, anomaly, to_csv_bytes

EN_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS = [tr if tr == en else f"{tr}/{en}" for tr, en in zip(MONTH_LABELS, EN_MONTHS)]
MAX_POINTS = 20000  # ısı katmanı tek dizi → 5000 ayrı işaretten çok daha hafif
LOW_MEAN, MAX_RATIO = 1.0, 100  # taban < 1 VE kat ≥ 100 ise "kat" yerine "normalde ≈0" (2011-04 harm 29× kalır)

st.set_page_config(page_title="Aktif Yangın Tespit Takvimi", page_icon="🔥", layout="wide")
# Streamlit'in sağ üstteki animasyonlu "çalışıyor" figürlerini gizle (profesyonel görünüm);
# yükleme bilgisi st.cache_data spinner'ı ("Veri yükleniyor / Loading…") ile veriliyor
st.markdown("""<style>
[data-testid="stStatusWidget"] {visibility: hidden; height: 0;}
</style>""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def info():
    return data_info()


@st.cache_data(show_spinner="Veri yükleniyor / Loading…")
def load(geom_key, start, end, harmonized):
    geom = json.loads(geom_key)
    geom = tuple(geom) if isinstance(geom, list) else geom
    return get_hotspots(geom, start=start, end=end, harmonized=harmonized)


def fmt(x, spec=".1f"):
    """NaN / None → '–' (anomali kartı çökmesin)."""
    if x is None or (isinstance(x, float) and not np.isfinite(x)):
        return "–"
    return format(x, spec)


INFO = info()

# ---------- Üst uyarı + başlık ----------
if INFO.get("is_mock"):
    st.warning("SENTETİK TEST VERİSİ / Synthetic test data")
st.title("🔥 Aktif Yangın Tespit Takvimi / Active Fire Detection Calendar")

# ---------- Kenar çubuğu ----------
with st.sidebar:
    st.header("Ayarlar / Settings")
    preset = st.selectbox("Bölge / Region", list(PRESETS))
    # ana kontrol: yıl aralığı kaydırıcısı (veri aylık; takvim seçici yıl gezintisinde zorluyordu)
    y_min, y_max = INFO["start"].year, INFO["end"].year
    y0, y1 = st.slider("Yıl aralığı / Year range", y_min, y_max, (y_min, y_max), key="years")
    d0 = max(pd.Timestamp(y0, 1, 1), INFO["start"]).date()
    d1 = min(pd.Timestamp(y1, 12, 31), INFO["end"]).date()
    # isteğe bağlı: gün bazında kesin tarih (iki ayrı, bağımsız alan)
    with st.expander("Kesin tarih / Exact dates"):
        exact = st.checkbox("Gün bazında filtrele / Filter by day", key="exact")
        e0 = st.date_input("Başlangıç / Start", value=d0, min_value=INFO["start"].date(),
                           max_value=INFO["end"].date(), format="YYYY-MM-DD", key="e0", disabled=not exact)
        e1 = st.date_input("Bitiş / End", value=d1, min_value=INFO["start"].date(),
                           max_value=INFO["end"].date(), format="YYYY-MM-DD", key="e1", disabled=not exact)
        if exact:
            if e0 > e1:
                st.warning("Başlangıç bitişten sonra / Start is after end")
            else:
                d0, d1 = e0, e1
    st.caption(f"Seçili / Selected: {d0:%Y-%m-%d} → {d1:%Y-%m-%d}")
    mode_lbl = st.radio("Seri / Series", ["Ham / Raw", "Harmonize / Harmonized"], horizontal=True)
    mode = "raw" if mode_lbl.startswith("Ham") else "harm"
    st.caption("Ham: tüm uyduların tespit sayısı. Harmonize: MODIS-eşdeğeri tahmin. "
               "/ Raw: detections from all satellites. Harmonized: MODIS-equivalent estimate.")

# ---------- Harita ----------
x0, y0, x1, y1 = PRESETS[preset]
if st.session_state.get("_preset") != preset:
    st.session_state["_preset"] = preset
    st.session_state["drawn"] = None
    st.session_state["map_ver"] = st.session_state.get("map_ver", 0) + 1
st.session_state.setdefault("map_ver", 0)


def reset_drawing():
    """Hazır bölgeye dön: çizimi sil + harita bileşeninin hafızasını sıfırla (yeni key)."""
    st.session_state["drawn"] = None
    st.session_state["map_ver"] += 1
geom_key = st.session_state.get("drawn") or json.dumps([x0, y0, x1, y1])

# harita: Harmonize'de sadece weight_harm > 0; grafikler: her zaman tüm veri
df_map = load(geom_key, pd.Timestamp(d0), pd.Timestamp(d1), mode == "harm")
df = load(geom_key, pd.Timestamp(d0), pd.Timestamp(d1), False)


def _bounds(geojson_str):
    """Çizilen geometrinin sınırları → harita oraya odaklansın (konum takibi gerekmez)."""
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


col_map, col_cal = st.columns([1, 1])
with col_map:
    st.subheader("Harita / Map")
    m = folium.Map(tiles="OpenStreetMap")
    folium.Rectangle([[y0, x0], [y1, x1]], color="#440154", fill=False, weight=2).add_to(m)
    # çizilen alan Draw aracının KENDİ katmanında → çöp kutusu onu silebilir
    drawn_fg = folium.FeatureGroup(name="drawn")
    if st.session_state.get("drawn"):
        g = json.loads(st.session_state["drawn"])
        # dış halkalar: Polygon → 1, MultiPolygon → her parçanın dış halkası
        polys = [g["coordinates"]] if g.get("type") == "Polygon" else g.get("coordinates", [])
        for ring in (poly[0] for poly in polys if poly):
            folium.Polygon([[lat, lon] for lon, lat in ring], color="#21918c", weight=3,
                           fill=True, fill_opacity=0.1).add_to(drawn_fg)
        m.fit_bounds(_bounds(st.session_state["drawn"]))
    else:
        m.fit_bounds([[y0, x0], [y1, x1]])
    drawn_fg.add_to(m)
    Draw(feature_group=drawn_fg,
         draw_options={"polyline": False, "circle": False, "marker": False,
                       "circlemarker": False, "polygon": True, "rectangle": True},
         edit_options={"edit": False, "remove": True}).add_to(m)
    pts = df_map.sample(MAX_POINTS, random_state=0) if len(df_map) > MAX_POINTS else df_map
    if len(pts):
        # tek ısı katmanı (viridis) — binlerce ayrı SVG işaret yerine
        HeatMap(pts[["latitude", "longitude"]].to_numpy().tolist(), radius=8, blur=10, min_opacity=0.35,
                gradient={0.2: "#3b528b", 0.45: "#21918c", 0.7: "#5ec962", 1.0: "#fde725"}).add_to(m)
    # sadece çizim olayları döner → kaydırma/yakınlaştırma sayfayı yeniden çalıştırmaz
    out = st_folium(m, height=480, use_container_width=True, returned_objects=["all_drawings"],
                    key=f"map_{preset}_{st.session_state['map_ver']}")
    drawings = (out or {}).get("all_drawings")
    if drawings is not None:  # None = henüz çizim olayı yok
        if drawings:
            new_key = json.dumps(drawings[-1]["geometry"])  # en son çizilen alan geçerli
            if new_key != st.session_state.get("drawn"):
                st.session_state["drawn"] = new_key
                st.rerun()
        elif st.session_state.get("drawn"):
            # çöp kutusuyla silindi → hazır bölgeye dön
            reset_drawing()
            st.rerun()
    if st.session_state.get("drawn"):
        st.button("↩ Bölgeye dön / Back to region", on_click=reset_drawing,
                  help=f"Çizimi sil, '{preset}' kutusuna dön / Clear drawing, back to preset")
    st.caption(f"{len(df_map):,} tespit / detections · ısı haritası / heat map"
               + (f" ({MAX_POINTS:,} örnek / sampled)" if len(df_map) > MAX_POINTS else ""))
    if preset == "Aachen/Eifel":
        st.caption("Not: Kutunun kuzeybatı köşesi (Aachen şehri, ≈50,73°K kuzeyi / 6,10°D batısı) indirme "
                   "kapsamı dışında; orada boş görünen alan 'tespit yok' değil 'veri yok' demektir. "
                   "/ Note: the NW corner (Aachen city) is outside the download area.")

with st.sidebar:
    # CSV sadece butona basılınca üretilir (her etkileşimde 1,5 sn / 20 MB üretmek yerine)
    st.download_button("CSV indir / Download", data=lambda: to_csv_bytes(df),
                       file_name=f"hotspots_{preset}_{mode}.csv", mime="text/csv",
                       disabled=df.empty)
    with st.expander("Veri / Data", expanded=False):
        st.markdown(
            f"- Kaynak / Source: `{INFO['path']}`\n"
            f"- Aralık / Range: {INFO['start']:%Y-%m-%d} → {INFO['end']:%Y-%m-%d}\n"
            f"- Uydular / Satellites: {', '.join(INFO['satellites'])}\n"
            f"- Satır / Rows: {INFO['n_rows']:,}\n"
            f"- Sözleşme / Contract: v{INFO.get('contract', '?')}")

# ---------- Takvim + Anomali (fragment) ----------
# st.fragment: hücre tıklaması / renk ölçeği / yıl-ay seçimi sadece bu bölümü yeniden çalıştırır,
# haritayı yeniden çizmez.
@st.fragment
def calendar_and_anomaly(df, mode, d0, d1):
    st.subheader("Aylık takvim / Monthly calendar")
    if mode == "harm" and not INFO.get("has_harm"):
        st.info("Harmonize veri henüz hazır değil / Harmonized data not ready yet")
        return
    if df.empty:
        st.info("Bu bölgede tespit yok / No detections in this area")
        return
    # tarih filtresi dışındaki aylar NaN (0 değil) → takvim, yıllık toplam ve anomali tabanı doğru
    mat = monthly_matrix(df, mode=mode, start=pd.Timestamp(d0), end=pd.Timestamp(d1))
    mat = mat.dropna(how="all")  # tamamen filtre dışı yıllar takvimde ve tabanda yok
    shown = mat.astype(float).copy()
    z = shown.values
    scale = st.radio("Renk ölçeği / Color scale",
                     ["Log", "Doğrusal / Linear", "Anomali (z) / Anomaly (z)"],
                     horizontal=True, key="scale",
                     help="Log: küçük olaylar (ör. Hohes Venn 2011-04 = 17) büyüklerin (1899) yanında "
                          "kaybolmasın. Anomali: her hücre aynı ayın diğer yıllarına göre z-skoru.")
    unit = "Ham" if mode == "raw" else "MODIS-eşd."
    if scale == "Log":
        # renk = log10(1+değer); çubuk etiketleri gerçek sayılar
        zc = np.log10(1 + np.clip(z, 0, None))
        top = float(np.nanmax(zc)) if np.isfinite(zc).any() else 1.0
        ticks = [v for v in [0, 1, 3, 10, 30, 100, 300, 1000, 3000, 10000, 30000, 100000]
                 if np.log10(1 + v) <= top + 1e-9]
        hm = dict(zmin=0, zmax=max(top, 1e-6),
                  colorbar=dict(title=unit, tickvals=[np.log10(1 + v) for v in ticks],
                                ticktext=[f"{v:,}" for v in ticks]))
    elif scale.startswith("Doğrusal"):
        zc = z
        hm = dict(zmin=0, zmax=float(np.nanmax(z)) if np.isfinite(z).any() else 1,
                  colorbar=dict(title=unit))
    else:
        # aynı takvim ayının diğer yıllarına göre z (query.anomaly ile aynı taban)
        zc = np.full_like(z, np.nan)
        for i, yy in enumerate(shown.index):
            for j, mm in enumerate(shown.columns):
                if np.isfinite(z[i, j]):
                    zz = anomaly(mat, yy, mm).get("z")
                    zc[i, j] = zz if zz is not None and np.isfinite(zz) else np.nan
        hm = dict(zmin=-3, zmax=3, colorbar=dict(title="z"))
    fig = go.Figure(go.Heatmap(
        z=zc, x=MONTHS, y=shown.index.astype(str), colorscale="Viridis",
        hoverinfo="skip", **hm,
    ))
    # Streamlit heatmap tıklamasını yakalamıyor → her hücreye görünmez tıklanabilir nokta
    hover_unit = "Tespit/Detections" if mode == "raw" else "MODIS-eşd. / MODIS-equiv."
    gy, gx = np.meshgrid(shown.index.astype(str), MONTHS, indexing="ij")
    # kısmi aylar: verinin / seçili aralığın ilk ve son ayı tam kapsanmıyorsa işaretle
    cov0 = max(pd.Timestamp(d0), INFO["start"])
    cov1 = min(pd.Timestamp(d1), INFO["end"])
    notes = np.full(z.shape, "", dtype=object)
    for i, yy in enumerate(shown.index):
        for j, mm in enumerate(shown.columns):
            if not np.isfinite(z[i, j]):
                continue
            m0 = pd.Timestamp(int(yy), int(mm), 1)
            m1 = m0 + pd.offsets.MonthEnd(0)
            a0, a1 = max(m0, cov0), min(m1, cov1)
            if a0 > m0 or a1 < m1:
                notes[i, j] = f"<br>⚠ kısmi ay / partial month: {a0:%d.%m}–{a1:%d.%m}"
    part = notes != ""
    if part.any():
        fig.add_trace(go.Scatter(
            x=gx[part], y=gy[part], mode="text", text=["•"] * int(part.sum()),
            textfont=dict(size=22, color="white"), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=gx.ravel(), y=gy.ravel(), mode="markers", showlegend=False,
        customdata=np.stack([z.ravel(), notes.ravel()], axis=-1),
        marker=dict(symbol="square", size=18, color="rgba(0,0,0,0)"),
        hovertemplate="Yıl/Year %{y}<br>Ay/Month %{x}<br>" + hover_unit + " %{customdata[0]:.1f}"
                      "%{customdata[1]}<extra></extra>",
    ))
    fig.update_layout(height=560, margin=dict(l=10, r=10, t=10, b=10), clickmode="event+select",
                      plot_bgcolor="#cccccc",
                      # y ekseni sadece veri yılları (1998–2028 boşluğu yok)
                      yaxis=dict(range=[int(shown.index.max()) + 0.5, int(shown.index.min()) - 0.5], dtick=2))
    ev = st.plotly_chart(fig, width="stretch", on_select="rerun", selection_mode="points", key="cal")
    st.caption("Bir hücreye tıkla → anomali kartı / Click a cell → anomaly card · "
               "• = kısmi ay, sayı tam aydan düşük olabilir / partial month")
    pts_sel = (ev or {}).get("selection", {}).get("points", []) if ev else []
    if pts_sel:
        p0 = pts_sel[0]
        sel = (int(p0["y"]), MONTHS.index(p0["x"]) + 1)
        if sel != st.session_state.get("_last_sel"):
            st.session_state["_last_sel"] = sel
            st.session_state["sel_year"], st.session_state["sel_month"] = sel

    st.subheader("Anomali / Anomaly")
    st.caption("tespit sayısı anomalisi / detection-count anomaly")
    c1, c2, _ = st.columns([1, 1, 2])
    years = [int(y) for y in mat.index]
    if st.session_state.get("sel_year") not in years:
        st.session_state["sel_year"] = 2026 if 2026 in years else years[-1]
    st.session_state.setdefault("sel_month", 8)
    yr = c1.selectbox("Yıl / Year", years, key="sel_year")
    mo = c2.selectbox("Ay / Month", list(range(1, 13)), format_func=lambda i: MONTHS[i - 1], key="sel_month")
    a = anomaly(mat, yr, mo)
    k1, k2, k3, k4 = st.columns(4)
    val, mean = a.get("value"), a.get("mean")
    # sıfıra yakın tabanda z anlamsız büyür → ana gösterim sıra + "ortalamanın kaç katı"
    ratio = val / mean if (fmt(val) != "–" and fmt(mean) != "–" and mean > 0) else None
    k1.metric("Tespit / Detections", fmt(val))
    k2.metric("Sıra / Rank", f"{a['rank']}/{a['n_years']}" if a.get("rank") is not None else "–",
              help="1 = bu ay için en yüksek yıl / 1 = highest year for this month")
    if ratio is not None and mean < LOW_MEAN and ratio >= MAX_RATIO:
        # taban ≈0 iken "2115×" anlamsız → normal ay seviyesini yaz
        k3.metric("Normal ay / Typical month", f"≈{mean:.1f}", "normalde ≈0 tespit/ay / normally ≈0 per month",
                  delta_color="off")
    else:
        k3.metric("Ortalamanın katı / × mean",
                  (f"{ratio:.0f}×" if ratio >= 10 else f"{ratio:.1f}×") if ratio is not None else "–")
    k4.metric("Durum / Label", a["label"])
    st.caption(f"Ortalama ± std / Mean ± std: {fmt(mean)} ± {fmt(a['std'])} ({a['n_years']} yıl / years)"
               f" · z = {fmt(a['z'], '.1f')}")


# ---------- Yıllık karşılaştırma (fragment) ----------
@st.fragment
def annual_chart(df, d0, d1):
    st.subheader("Yıllık toplam: Ham vs Harmonize / Annual total: Raw vs Harmonized")
    raw_y = monthly_matrix(df, "raw", start=pd.Timestamp(d0), end=pd.Timestamp(d1)).sum(axis=1, min_count=1).dropna()
    harm_y = monthly_matrix(df, "harm", start=pd.Timestamp(d0), end=pd.Timestamp(d1)).sum(axis=1, min_count=1).dropna()
    fy = go.Figure()
    fy.add_trace(go.Scatter(x=raw_y.index, y=raw_y.values, name="Ham / Raw", mode="lines+markers",
                            line=dict(color="#440154", width=3)))
    if harm_y.notna().any():
        fy.add_trace(go.Scatter(x=harm_y.index, y=harm_y.values, name="Harmonize / Harmonized",
                                mode="lines+markers", line=dict(color="#35b779", width=3)))
    def _frac_year(ts):
        return ts.year + (ts.day_of_year - 1) / 365.25


    # uydu geçiş tarihleri veriden (CONTRACT v1.2 §3) — sabit yazılmaz
    _ranges = INFO.get("satellite_ranges", {})
    _marks = [(_frac_year(_ranges[s][0]), lbl) for s, lbl in
              [("SNPP", "S-NPP"), ("NOAA20", "NOAA-20"), ("NOAA21", "NOAA-21")] if s in _ranges]
    if "SNPP" in _ranges and _ranges["SNPP"][1] < INFO["end"] - pd.Timedelta(days=3):
        _marks.append((_frac_year(_ranges["SNPP"][1]), "S-NPP bitti / ended"))
    for k, (xv, lbl) in enumerate(_marks):
        fy.add_vline(x=xv, line_dash="dash", line_color="#888")
        # etiketler sırayla üst/alt kademe → yakın tarihler (NOAA-21, S-NPP bitti) çakışmasın
        fy.add_annotation(x=xv, y=1.0 if k % 2 == 0 else 1.09, yref="paper", text=lbl,
                          showarrow=False, xanchor="right", yanchor="bottom",
                          font=dict(size=11, color="#666"), bgcolor="rgba(255,255,255,0.8)")
    log_y = st.toggle("Log eksen / Log axis", value=False, key="annual_log",
                      help="Log eksende aynı oranlı artış (ör. 4×) her seviyede aynı yükseklikte görünür; "
                           "2012 S-NPP sıçraması da belirginleşir.")
    fy.update_layout(height=420, margin=dict(l=10, r=10, t=70, b=10), hovermode="x unified",
                     xaxis_title="Yıl / Year",
                     yaxis=dict(title="Tespit / Detections" + (" (log)" if log_y else ""),
                                type="log" if log_y else "linear"),
                     legend=dict(orientation="h", y=-0.2))
    st.plotly_chart(fy, width="stretch")
    st.caption("Kısmi yıllar (ilk/son) eksik aylar nedeniyle düşük görünebilir. "
               "/ First and last years are partial.")


with col_cal:
    calendar_and_anomaly(df, mode, d0, d1)
if not df.empty:
    annual_chart(df, d0, d1)
