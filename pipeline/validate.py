"""P3 — Harmonizasyon doğrulaması (sahibi: Oğuzhan). Sözleşme: docs/CONTRACT.md §7.3 (v1.2)

Çalıştır (repo kökünden):  python pipeline/validate.py

Soru: P2'nin weight_harm'ı (VIIRS → MODIS-eşdeğeri) eğitimde görmediği yıllarda (test 2022–2024)
MODIS'in gerçekten saydığı tespit sayısını ne kadar iyi tahmin ediyor?
  tahmin = hücre-ay içindeki VIIRS satırlarının Σ weight_harm
  gerçek = aynı hücre-aydaki MODIS (Terra+Aqua) satır sayısı (n_modis)
  Sadece en az bir tarafı > 0 olan hücre-aylar. Ölçek: 0.25° ve 1°.
Karşılaştırma tabanı: "raw_viirs" = ham VIIRS sayısı (harmonizasyon olmasaydı).

Çıktılar (docs/validation/):
  metrics.json          [{"method","region","split","scale","r2","bias","bias_pct","n","data"}]
                        data = "mock" (sentetik) | "raw" (P1, harmonize yok) | "harm" (P2) — v1.3
                        bias = ortalama(tahmin − gerçek) [tespit/hücre-ay]
                        bias_pct = (Σ tahmin / Σ gerçek − 1) × 100  [%]
  pred_vs_true.png      test yılları, log-log saçılım + 1:1
  annual_raw_vs_harm.png  Arjantin yıllık ham / harmonize / MODIS
  venn_check.png        Hohes Venn yıl×ay takvimi (ham + harmonize), Nisan 2011 & Ağustos 2026.
                        Sonuç z ile değil "N yılın en yüksek Nisanı, ortalamanın X katı" diye yazılır
                        (taban sıfıra yakınken z anlamsız büyür).
  summary.md            sunum için kısa özet (P6)

Girdi önceliği: $P3_INPUT → data/hotspots_harm.parquet (P2) → data/hotspots.parquet (P1, sadece ham
sayımlar: harmonize metrikleri/çizgileri atlanır) → data/mock/hotspots_mock.parquet (SENTETİK —
grafiklere filigran basılır, sonuçların bilimsel değeri yoktur).

Test bölünmesi ayrıca NOAA-21'e göre ikiye ayrılır (NOAA-21 2023-03-01'de başladı, eğitimde YOK →
P2 onun için proxy k kullanıyor): "test_2022" (S-NPP + NOAA-20) ve "test_2023-2024" (+ NOAA-21).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402

# ---------------------------------------------------------------- yollar & sabitler
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HARM_PATH = DATA / "hotspots_harm.parquet"
RAW_PATH = DATA / "hotspots.parquet"
GRID_PATH = DATA / "monthly_grid.parquet"
K_PATH = DATA / "k_factors.csv"
MOCK_PATH = DATA / "mock" / "hotspots_mock.parquet"
# P1 burned_area_check.py çıktısı (isteğe bağlı) — MCD64A1 destekleyici kanıt, metrik DEĞİL
BURN_PATH = Path(os.environ.get("P3_BURN", DATA / "burned_area_check.csv"))
BURN_STATUSES = {"burned_match", "unburned", "burned_other_time", "unknown", "no_data"}
BURN_GROUPS = {"venn_2011": (2011, 4), "venn_2026": (2026, 8)}
OUT = ROOT / "docs" / "validation"

TRAIN_YEARS = range(2012, 2022)   # 2012–2021 (P2 k'yı buradan öğrenir)
TEST_YEARS = range(2022, 2025)    # 2022–2024
SPLITS = {"train": TRAIN_YEARS, "test": TEST_YEARS,
          "test_2022": range(2022, 2023),          # NOAA-21 öncesi
          "test_2023-2024": range(2023, 2025)}     # NOAA-21 aktif (eğitimde olmayan uydu)
# Transfer bölgesi hiç eğitime girmedi (k sadece Arjantin'den) → tüm VIIRS yılları örneklem dışı.
# 2022–2024'te Aachen/Eifel'de çok az MODIS tespiti var (n çok küçük), bu yüzden ek dönem:
TRANSFER_SPLIT = ("transfer_2012-2026", range(2012, 2027))
TRANSFER_REGIONS = {"aachen_eifel"}
# metrics.json'a sadece CONTRACT §7.3 izinli split'ler yazılır (v1.4: transfer_2012-2026 onaylı).
JSON_SPLITS = set(SPLITS) | {TRANSFER_SPLIT[0]}
SCALES = {"0.25deg": 0.25, "1deg": 1.0}
# rapor bölgeleri → CONTRACT §5 region değerleri (contract.REGIONS ile aynı olmalı)
REPORT_REGIONS = {"argentina": ["argentina"], "aachen_eifel": ["aachen_eifel"]}
REGION_LABEL = {"argentina": "Arjantin (eğitim bölgesi)", "aachen_eifel": "Aachen/Eifel (transfer)"}
VENN_BOX = (5.95, 50.45, 6.25, 50.60)   # lon_min, lat_min, lon_max, lat_max
VENN_MONTHS = [(2011, 4), (2026, 8)]
VIIRS_LABEL = {"SNPP": "S-NPP", "NOAA20": "NOAA-20", "NOAA21": "NOAA-21"}
MONTH_TR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz", "Ağustos", "Eylül",
            "Ekim", "Kasım", "Aralık"]
VISIBLE_RATIO = 3.0   # "görünüyor" = o ayın değeri, aynı ayın diğer yıllarının ortalamasının ≥ 3 katı

NEED_COLS = ["latitude", "longitude", "year", "month", "instrument", "satellite",
             "region", "weight_harm", "version"]

plt.rcParams.update({"font.size": 14, "axes.titlesize": 16, "axes.labelsize": 14,
                     "legend.fontsize": 12, "figure.dpi": 110})
CMAP = plt.get_cmap("viridis")


# ---------------------------------------------------------------- yükleme

def pick_input() -> Path:
    env = os.environ.get("P3_INPUT")
    if env:
        if not Path(env).exists():
            raise FileNotFoundError(f"P3_INPUT bulunamadı: {env}")
        return Path(env).resolve()
    for p in (HARM_PATH, RAW_PATH, MOCK_PATH):
        if p.exists():
            return p
    raise FileNotFoundError(f"Girdi yok: {HARM_PATH}, {RAW_PATH}, {MOCK_PATH}")


def load_input(path: Path) -> pd.DataFrame:
    import pyarrow.parquet as pq
    cols = pq.read_schema(path).names
    missing = [c for c in NEED_COLS if c not in cols]
    if missing:
        raise ValueError(f"{path}: eksik sütun {missing} (CONTRACT §1)")
    df = pd.read_parquet(path, columns=NEED_COLS)
    n_nan = int(df["weight_harm"].isna().sum())
    if 0 < n_nan < len(df):
        raise ValueError(f"{path}: weight_harm kısmen NaN ({n_nan:,}/{len(df):,}) — "
                         "ya tamamen NaN (P1) ya hiç NaN yok (P2) olmalı (CONTRACT §6)")
    if (df["weight_harm"] < 0).any():
        raise ValueError(f"{path}: weight_harm < 0 değerler var")
    bad = set(df["instrument"].astype(str)) - {"MODIS", "VIIRS"}
    if bad:
        raise ValueError(f"beklenmeyen instrument: {bad}")
    have = set(df["region"].astype(str).unique())
    need = {r for regs in REPORT_REGIONS.values() for r in regs}
    if need - have:
        raise ValueError(f"{path}: rapor bölgeleri veride yok: {sorted(need - have)} "
                         f"(veride: {sorted(have)}) — CONTRACT §5")
    return df


def cell(x: pd.Series, size: float) -> pd.Series:
    """Hücre merkezi (CONTRACT §7.2 formülü, 0.25° için monthly_grid ile aynı)."""
    return np.floor(x / size) * size + size / 2


# ---------------------------------------------------------------- tahmin vs gerçek

def cell_month_table(df: pd.DataFrame, size: float) -> pd.DataFrame:
    """Hücre × ay: true (n_modis), pred (VIIRS Σ weight_harm), raw_viirs (n_viirs)."""
    is_modis = df["instrument"].astype(str).eq("MODIS")
    t = pd.DataFrame({
        "region": df["region"].astype(str),
        "year": df["year"].astype(int), "month": df["month"].astype(int),
        "cl": cell(df["latitude"], size), "cn": cell(df["longitude"], size),
        "true": is_modis.astype("int64"),
        "raw_viirs": (~is_modis).astype("int64"),
        "pred": df["weight_harm"].astype("float64").where(~is_modis, 0.0),
    })
    g = t.groupby(["region", "year", "month", "cl", "cn"], observed=True)[
        ["true", "raw_viirs", "pred"]].sum().reset_index()
    return g


def metrics(pred: np.ndarray, true: np.ndarray) -> dict:
    n = len(true)
    if n == 0:
        return {"r2": None, "bias": None, "bias_pct": None, "n": 0}
    ss_res = float(np.sum((true - pred) ** 2))
    ss_tot = float(np.sum((true - true.mean()) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else None
    st = float(true.sum())
    return {"r2": None if r2 is None else round(r2, 4),
            "bias": round(float(np.mean(pred - true)), 4),
            "bias_pct": None if st == 0 else round((float(pred.sum()) / st - 1) * 100, 2),
            "n": int(n)}


def compute_metrics(df: pd.DataFrame, has_harm: bool) -> tuple[list[dict], dict[str, pd.DataFrame]]:
    rows: list[dict] = []
    tables: dict[str, pd.DataFrame] = {}
    for scale, size in SCALES.items():
        tab = cell_month_table(df, size)
        tables[scale] = tab
        for split, years in list(SPLITS.items()) + [TRANSFER_SPLIT]:
            for rname, regs in REPORT_REGIONS.items():
                if split == TRANSFER_SPLIT[0] and rname not in TRANSFER_REGIONS:
                    continue   # Arjantin 2012–2021 eğitim → transfer dönemi anlamsız
                sub = tab[tab.year.isin(years) & tab.region.isin(regs)]
                methods = (("harm", "pred"),) * has_harm + (("raw_viirs", "raw_viirs"),)
                for method, col in methods:
                    s = sub[(sub[col] > 0) | (sub.true > 0)]
                    m = metrics(s[col].to_numpy(float), s.true.to_numpy(float))
                    rows.append({"method": method, "region": rname, "split": split,
                                 "scale": scale, **m})
    return rows, tables


def crosscheck_grid(tab025: pd.DataFrame) -> str:
    """P2 monthly_grid.n_modis ile kendi hesabımız tutuyor mu? (sadece varsa)"""
    if not GRID_PATH.exists():
        return "monthly_grid.parquet yok — çapraz kontrol atlandı"
    g = pd.read_parquet(GRID_PATH, columns=["year", "n_modis", "n_viirs"])
    mine = tab025.groupby("year")[["true", "raw_viirs"]].sum()
    theirs = g.groupby("year")[["n_modis", "n_viirs"]].sum()
    j = mine.join(theirs, how="outer").fillna(0)
    bad = j[(j.true != j.n_modis) | (j.raw_viirs != j.n_viirs)]
    if len(bad):
        raise ValueError(f"monthly_grid ile hotspots_harm yıllık sayıları tutmuyor:\n{bad}")
    return "monthly_grid.parquet yıllık n_modis/n_viirs ile tutarlı ✓"


# ---------------------------------------------------------------- grafikler

def watermark(fig, is_mock: bool) -> None:
    if is_mock:
        fig.text(0.5, 0.5, "SENTETİK TEST VERİSİ", ha="center", va="center", rotation=25,
                 fontsize=44, color="red", alpha=0.18, weight="bold")


def plot_pred_vs_true(tables: dict[str, pd.DataFrame], rows: list[dict], is_mock: bool,
                      has_harm: bool) -> None:
    method, col = ("harm", "pred") if has_harm else ("raw_viirs", "raw_viirs")
    fig, axes = plt.subplots(1, 2, figsize=(14, 6.5))
    colors = {"0.25deg": CMAP(0.25), "1deg": CMAP(0.8)}
    for ax, (rname, regs) in zip(axes, REPORT_REGIONS.items()):
        hi = 1
        split, years = (TRANSFER_SPLIT if rname in TRANSFER_REGIONS else ("test", TEST_YEARS))
        for scale, tab in tables.items():
            s = tab[tab.year.isin(years) & tab.region.isin(regs)]
            s = s[(s[col] > 0) | (s.true > 0)]
            m = next(r for r in rows if r["method"] == method and r["region"] == rname
                     and r["split"] == split and r["scale"] == scale)
            r2 = "—" if m["r2"] is None else f"{m['r2']:.2f}"
            bp = "—" if m["bias_pct"] is None else f"{m['bias_pct']:+.0f}%"
            ax.scatter(s.true + 1, s[col] + 1, s=14 if scale == "0.25deg" else 40,
                       alpha=0.45 if scale == "0.25deg" else 0.8, color=colors[scale],
                       edgecolor="none", label=f"{scale.replace('deg', '°')}: R²={r2}, bias={bp}, n={m['n']}")
            if len(s):
                hi = max(hi, s.true.max() + 1, s[col].max() + 1)
        ax.plot([1, hi * 1.3], [1, hi * 1.3], "k--", lw=1.2, label="1:1")
        ax.set(xscale="log", yscale="log", xlim=(0.8, hi * 1.3), ylim=(0.8, hi * 1.3),
               xlabel="Gerçek: MODIS tespit sayısı (+1)",
               ylabel=("Tahmin: harmonize VIIRS Σ weight_harm (+1)" if has_harm
                       else "Ham VIIRS tespit sayısı (+1) — harmonize YOK"),
               title=f"{REGION_LABEL[rname]} — {years.start}–{years.stop - 1}")
        for axis in (ax.xaxis, ax.yaxis):
            axis.set_major_locator(matplotlib.ticker.LogLocator(subs=(1, 2, 5) if hi < 300 else (1,)))
            axis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
            axis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.legend(loc="lower right", fontsize=11, framealpha=0.9)   # üst-sol: büyük olaylar orada
        ax.grid(alpha=0.3, which="both")
    fig.suptitle("Hücre-ay bazında tahmin vs gerçek (MODIS-eşdeğeri tespit sayısı)", fontsize=17)
    watermark(fig, is_mock)
    fig.tight_layout()
    fig.savefig(OUT / "pred_vs_true.png")
    plt.close(fig)


def plot_annual(df: pd.DataFrame, is_mock: bool, has_harm: bool) -> pd.DataFrame:
    a = df[df.region.astype(str) == "argentina"]
    is_modis = a["instrument"].astype(str).eq("MODIS")
    yearly = pd.DataFrame({
        "ham (tüm uydular)": a.groupby("year").size(),
        "sadece MODIS (Terra+Aqua)": a[is_modis].groupby("year").size(),
        "harmonize (Σ weight_harm)": a.groupby("year")["weight_harm"].sum(),
    }).fillna(0).sort_index()
    yearly.index = yearly.index.astype(int)
    if not has_harm:   # P1 verisi: harmonize çizgisi çizilmez
        yearly = yearly.drop(columns="harmonize (Σ weight_harm)")

    fig, ax = plt.subplots(figsize=(13, 6.5))
    styles = [dict(lw=2.5, ls="-", marker="o", ms=6), dict(lw=6, ls="-", marker="o", ms=9, alpha=0.6),
              dict(lw=2.5, ls="--", marker="o", ms=5)]   # MODIS kalın/yarı saydam, harmonize kesikli üstte
    for i, col in enumerate(yearly.columns):
        ax.plot(yearly.index, yearly[col], color=CMAP([0.05, 0.45, 0.85][i]), label=col, **styles[i])
    ax.axvspan(TEST_YEARS.start - 0.5, TEST_YEARS.stop - 0.5, color="grey", alpha=0.15,
               label="test yılları (2022–2024)")
    top = yearly.to_numpy().max()
    # uydu başlangıçları VERİDEN (sabit yazılmaz; CONTRACT §3)
    first = df[df.instrument.astype(str) == "VIIRS"].groupby("satellite", observed=True)["year"].min()
    for sat, y0 in first.sort_values().items():
        y0 = int(y0)
        ax.axvline(y0, color="k", ls=":", lw=1)
        ax.text(y0 + 0.1, top * 0.97, f"{VIIRS_LABEL.get(str(sat), sat)}\n{y0}", fontsize=11, va="top")
    last = yearly.index.max()
    ax.text(last, 0, "kısmi yıl", fontsize=10, ha="center", va="bottom")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", ".")))
    ax.set(xlabel="Yıl", ylabel="Tespit sayısı / yıl", ylim=(0, top * 1.05),
           title="Arjantin — yıllık tespit: ham vs harmonize vs MODIS")
    ax.legend(loc="center left", fontsize=11)
    ax.grid(alpha=0.3)
    watermark(fig, is_mock)
    fig.tight_layout()
    fig.savefig(OUT / "annual_raw_vs_harm.png")
    plt.close(fig)
    return yearly


def month_matrix(box: pd.DataFrame, values: pd.Series | None, ym_min, ym_max) -> pd.DataFrame:
    """query.monthly_matrix ile aynı kural (yıl × ay; kapsam dışı NaN, kapsamda tespit yok → 0),
    ama tüm veriyi ikinci kez belleğe almadan (7M satır)."""
    years = range(ym_min[0], ym_max[0] + 1)
    g = box.groupby(["year", "month"]).size() if values is None else \
        values.groupby([box["year"], box["month"]]).sum()
    mat = g.unstack("month").reindex(index=years, columns=range(1, 13)).astype("float64").fillna(0.0)
    for y in years:
        for mth in range(1, 13):
            if (y, mth) < ym_min or (y, mth) > ym_max:
                mat.loc[y, mth] = np.nan
    mat.index.name, mat.columns.name = "year", "month"
    return mat


def venn_check(df: pd.DataFrame, is_mock: bool, has_harm: bool,
               burn: pd.DataFrame | None = None) -> list[dict]:
    """Kutu ile (region değil). Anomali/sıra: uygulamayla aynı fonksiyon (query.anomaly)."""
    sys.path.insert(0, str(ROOT / "app"))
    import query  # noqa: E402

    lo0, la0, lo1, la1 = VENN_BOX
    ym = df["year"].astype(int) * 100 + df["month"].astype(int)
    ym_min, ym_max = divmod(int(ym.min()), 100), divmod(int(ym.max()), 100)
    box = df[df.longitude.between(lo0, lo1) & df.latitude.between(la0, la1)].copy()
    box["year"], box["month"] = box["year"].astype(int), box["month"].astype(int)
    is_modis = box["instrument"].astype(str).eq("MODIS")
    mats = {"raw": month_matrix(box, None, ym_min, ym_max),
            "modis": month_matrix(box, is_modis.astype(float), ym_min, ym_max)}
    if has_harm:
        mats["harm"] = month_matrix(box, box["weight_harm"].astype(float), ym_min, ym_max)
    results = []
    for mode, mat in mats.items():
        for y, m in VENN_MONTHS:
            a = query.anomaly(mat, y, m)
            v, mean = a["value"], a["mean"]
            ratio = (v / mean) if pd.notna(v) and pd.notna(mean) and mean > 0 else np.nan
            a["max_other"] = float(mat[m].drop(index=y, errors="ignore").max())
            visible = bool(pd.notna(v) and v > 0 and (mean == 0 or ratio >= VISIBLE_RATIO))
            results.append({"mode": mode, "year": y, "month": m, **a, "ratio": ratio,
                            "visible": visible, "text": venn_text(y, m, a, ratio, mode)})

    panels = ["raw", "harm" if has_harm else "modis"]
    fig, axes = plt.subplots(1, 2, figsize=(18, 9), sharey=True)
    vmax = max(float(np.nanmax(np.log1p(mats[p].to_numpy()))) for p in panels)   # ortak renk ölçeği
    titles = {"raw": "Ham (tüm uydular)", "harm": "Harmonize (MODIS-eşdeğeri)",
              "modis": "Sadece MODIS (Terra+Aqua)"}
    for ax, mode in zip(axes, panels):
        mat = mats[mode]
        im = ax.imshow(np.log1p(mat.to_numpy()), aspect="auto", cmap="viridis", vmin=0, vmax=vmax,
                       extent=(0.5, 12.5, mat.index.max() + 0.5, mat.index.min() - 0.5))
        for y, m in VENN_MONTHS:
            if y in mat.index:
                ax.add_patch(plt.Rectangle((m - 0.5, y - 0.5), 1, 1, fill=False,
                                           ec="red", lw=2.5))
                r = next(r for r in results if r["mode"] == mode and r["year"] == y
                         and r["month"] == m)
                ax.annotate(f"{MONTH_TR[m - 1]} {y}: {r['value']:.0f}\n{short_rank(r)}", (m, y),
                            xytext=(m - 5.5 if m > 6 else m + 0.8,
                                    y - 2.5 if y >= mat.index.max() - 1 else y), fontsize=12,
                            color="red", weight="bold", va="center",
                            arrowprops={"arrowstyle": "-", "color": "red"})
        ax.set_xticks(range(1, 13), query.MONTH_LABELS, fontsize=12)
        ax.set_title(titles[mode])
        ax.set_xlabel("Ay")
    axes[0].set_ylabel("Yıl")
    fig.colorbar(im, ax=axes, label="log(1 + tespit sayısı) — iki panelde aynı ölçek", shrink=0.8)
    fig.suptitle("Hohes Venn (lon 5.95–6.25, lat 50.45–50.60) — aylık tespit takvimi", fontsize=17)
    if burn is not None:
        parts = []
        for g, (y, m) in BURN_GROUPS.items():
            for inst, r in burn.loc[g].iterrows() if g in burn.index.get_level_values(0) else []:
                parts.append(f"{MONTH_TR[m - 1]} {y} {inst}: {r.burned_match}/{r.toplam}")
        fig.text(0.42, 0.005, "MCD64A1 yanmış alan pikseline düşen tespitler (3×3 px, ±16 gün; destekleyici, "
                 "bağımsız doğrulama değil): " + " · ".join(parts), ha="center", va="top", fontsize=12)
    watermark(fig, is_mock)
    fig.savefig(OUT / "venn_check.png", bbox_inches="tight")
    plt.close(fig)
    return results


def short_rank(r: dict) -> str:
    """Grafik etiketi: '26 yılın 1.si, ort. ×12'."""
    if r["rank"] is None:
        return r["label"]
    tail = ("diğer yıllarda tespit yok" if r["mean"] == 0
            else f"diğer yıllar en fazla {r['max_other']:.0f}")
    return f"{r['n_years']} yılın {r['rank']}.si, {tail}"


def venn_text(y: int, m: int, a: dict, ratio: float, mode: str = "raw") -> str:
    """'26 yılın en yüksek Nisanı, ortalamanın 12 katı' — z yerine (taban ~0 iken z anlamsız)."""
    if a["rank"] is None:
        return f"{MONTH_TR[m - 1]} {y}: {a['label']}"
    ay = MONTH_TR[m - 1]
    sira = "en yüksek" if a["rank"] == 1 else f"{a['rank']}. en yüksek"
    base = (f"diğer yılların hiçbirinde bu ayda tespit yok" if a["mean"] == 0
            else f"aynı ayın diğer yıllardaki ortalamasının (≈{a['mean']:.1f}) "
                 f"{format(ratio, ',.0f').replace(',', '.')} katı, diğer yılların en fazlası {a['max_other']:.0f}")
    unit = {"harm": "MODIS-eşdeğeri tespit", "modis": "MODIS tespiti"}.get(mode, "tespit")
    return f"{a['value']:.0f} {unit} — {a['n_years']} yılın {sira} {ay} ayı; {base}"


def test_year_breakdown(df: pd.DataFrame, has_harm: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Test yılları bölge × yıl: Σ harm (VIIRS) / Σ MODIS. Ayrıca 2022 aylık (Arjantin) —
    S-NPP 2022 Tem–Ağu ve Aqua 2022 Mar–Nis kesintileri oranı bozuyor mu? (P2 isteği)"""
    t = df[df.year.isin(TEST_YEARS)]
    is_modis = t["instrument"].astype(str).eq("MODIS")
    key = [t["region"].astype(str).rename("region"), t["year"].astype(int).rename("year")]
    yearly = pd.DataFrame({
        "modis": is_modis.groupby(key).sum(),
        "harm": t["weight_harm"].where(~is_modis, 0).astype(float).groupby(key).sum(),
    })
    if not has_harm:
        yearly["harm"] = np.nan
    yearly["oran"] = yearly.harm / yearly.modis.where(yearly.modis > 0)
    a = t[(t.region.astype(str) == "argentina") & (t.year == 2022)]
    am = a["instrument"].astype(str).eq("MODIS")
    sat = a.groupby(["month", "satellite"], observed=True).size().unstack(fill_value=0)
    monthly = pd.DataFrame({
        "modis": am.groupby(a["month"].astype(int)).sum(),
        "harm": a["weight_harm"].where(~am, 0).astype(float).groupby(a["month"].astype(int)).sum(),
    }).join(sat, how="left").reindex(range(1, 13)).fillna(0)
    if not has_harm:
        monthly["harm"] = np.nan
    monthly["oran"] = monthly.harm / monthly.modis.where(monthly.modis > 0)
    return yearly, monthly


def transfer_without_event(tables: dict[str, pd.DataFrame], has_harm: bool) -> dict[str, tuple]:
    """Transfer metriği, Venn olayı (2026-08) dahil / hariç — R² tek olaydan mı geliyor?"""
    out = {}
    if not has_harm:
        return out
    name, years = TRANSFER_SPLIT
    for scale, tab in tables.items():
        t = tab[tab.region.isin(TRANSFER_REGIONS) & tab.year.isin(years)]
        t = t[(t.pred > 0) | (t.true > 0)]
        ex = t[~((t.year == 2026) & (t.month == 8))]
        out[scale] = (metrics(t.pred.to_numpy(float), t.true.to_numpy(float)),
                      metrics(ex.pred.to_numpy(float), ex.true.to_numpy(float)))
    return out


def burn_support() -> pd.DataFrame | None:
    """MCD64A1 eşleşme özeti (grup × enstrüman). Yoksa None. Bağımsız doğrulama DEĞİL:
    MCD64A1 algoritması MODIS aktif yangın verisini de kullanır (P1 notu) → sadece summary/figür notu."""
    if not BURN_PATH.exists():
        return None
    b = pd.read_csv(BURN_PATH, usecols=["group", "instrument", "status"])
    bad = set(b.status) - BURN_STATUSES
    if bad:
        raise ValueError(f"{BURN_PATH}: beklenmeyen status {sorted(bad)}")
    badg = set(b.group) - set(BURN_GROUPS)
    if badg:
        raise ValueError(f"{BURN_PATH}: beklenmeyen group {sorted(badg)}")
    t = b.groupby(["group", "instrument"]).status.value_counts().unstack(fill_value=0) \
         .reindex(columns=sorted(BURN_STATUSES), fill_value=0)
    t["toplam"] = t[sorted(BURN_STATUSES)].sum(axis=1)
    t["bilinen"] = t.toplam - t.unknown - t.no_data   # "bilinmiyor" ≠ "yanmamış"
    return t


def ratio_diagnostics(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Arjantin, ham veri: MODIS / (aktif VIIRS uydusu başına VIIRS) — yıl bazında ve 2022 aylık.
    Harmonizasyondan bağımsız: 2022 sapması (P2: harm/MODIS=1.18) kesintiden mi, yörünge kaymasından mı,
    yoksa yıla özgü mü? Aktif uydu = o ay o bölgede ≥1 tespiti olan VIIRS uydusu."""
    a = df[(df.region.astype(str) == "argentina") & df.year.between(TRAIN_YEARS.start, TEST_YEARS.stop - 1)]
    c = a.groupby([a.year.astype(int), a.month.astype(int), a.satellite.astype(str)]).size() \
         .unstack(fill_value=0)
    for sat in ("Terra", "Aqua", "SNPP", "NOAA20", "NOAA21"):
        if sat not in c:
            c[sat] = 0
    v = c[["SNPP", "NOAA20", "NOAA21"]]
    c["viirs1"] = v.sum(axis=1) / (v > 0).sum(axis=1).replace(0, np.nan)
    c["modis"] = c.Terra + c.Aqua
    y = c.groupby(level=0)[["Terra", "Aqua", "modis", "viirs1"]].sum()
    y["oran"] = y.modis / y.viirs1
    y["aqua_terra"] = y.Aqua / y.Terra
    r = (c.modis / c.viirs1).unstack(level=1)
    m2022 = (r.loc[2022] / r.loc[TRAIN_YEARS.start:TRAIN_YEARS.stop - 1].median()) \
        if 2022 in r.index else pd.Series(dtype=float)
    return y, m2022


# ---------------------------------------------------------------- özet

def rel(p: Path) -> str:
    return str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p)


def fmt(v, spec=".2f"):
    return "—" if v is None or (isinstance(v, float) and np.isnan(v)) else format(v, spec)


def write_summary(rows, venn, is_mock, input_path, grid_note, k_note, breakdown, diag,
                  tr_ev=None, burn=None) -> str:
    def get(method, region, scale="1deg", split="test"):
        return next(r for r in rows if r["method"] == method and r["region"] == region
                    and r["split"] == split and r["scale"] == scale)

    has_harm = any(r["method"] == "harm" for r in rows)
    lines = []
    if not has_harm:
        lines += ["> ℹ️ Harmonize veri (P2) yok — sadece ham sayımlar. harm metrikleri ve "
                  "sunum cümleleri P2 çıktısı gelince üretilir.", ""]
    if is_mock:
        lines += ["> ⚠️ **SENTETİK TEST VERİSİ** — bu sayıların bilimsel değeri yoktur, "
                  "sadece pipeline testi.", ""]
    lines += [f"# Doğrulama özeti", "", f"Girdi: `{rel(input_path)}`  ",
              f"{grid_note}  ", f"{k_note}", "",
              "## Test (hücre-ay, harmonize vs ham VIIRS)", "",
              "test = 2022–2024; test_2022 = NOAA-21 öncesi; test_2023-2024 = NOAA-21 aktif "
              "(eğitimde olmayan uydu); transfer_2012-2026 = Aachen/Eifel'in tüm VIIRS yılları "
              "(bölge eğitime hiç girmedi).", "",
              "| bölge | dönem | ölçek | yöntem | R² | bias (tespit/hücre-ay) | bias % | n |",
              "|---|---|---|---|---|---|---|---|"]
    for r in sorted((r for r in rows if r["split"] != "train"),
                    key=lambda r: (r["region"], r["split"], r["scale"], r["method"])):
        lines.append(f"| {r['region']} | {r['split']} | {r['scale']} | {r['method']} | {fmt(r['r2'])} | "
                         f"{fmt(r['bias'])} | {fmt(r['bias_pct'], '+.1f')} | {r['n']} |")
    yearly, monthly = breakdown
    lines += ["", "## Test yılları tek tek (Σ harmonize VIIRS / Σ MODIS; 1.00 = mükemmel)", "",
              "| bölge | yıl | Σ MODIS | Σ harm | oran |", "|---|---|---|---|---|"]
    for (reg, yr), r in yearly.iterrows():
        lines.append(f"| {reg} | {yr} | {r.modis:.0f} | {fmt(r.harm, '.1f')} | {fmt(r.oran)} |")
    sat_cols = [c for c in monthly.columns if c not in ("modis", "harm", "oran")]
    lines += ["", "### Arjantin 2022 aylık (S-NPP Tem–Ağu, Aqua Mar–Nis kesintileri)", "",
              "| ay | Σ MODIS | Σ harm | oran | " + " | ".join(map(str, sat_cols)) + " |",
              "|---|---|---|---|" + "---|" * len(sat_cols)]
    for mth, r in monthly.iterrows():
        lines.append(f"| {MONTH_TR[mth - 1]} | {r.modis:.0f} | {fmt(r.harm, '.1f')} | {fmt(r.oran)} | "
                     + " | ".join(f"{r[c]:.0f}" for c in sat_cols) + " |")
    yr, m22 = diag
    tr = yr.loc[TRAIN_YEARS.start:TRAIN_YEARS.stop - 1, "oran"]
    lines += ["", "## 2022 sapması — ham veriden tanı (Arjantin)", "",
              "oran = MODIS / (aktif VIIRS uydusu başına VIIRS). Harmonizasyondan bağımsız. "
              f"Eğitim yılları aralığı {tr.min():.3f}–{tr.max():.3f} (medyan {tr.median():.3f}).", "",
              "| yıl | MODIS | VIIRS/uydu | oran | oran / eğitim medyanı | Aqua/Terra |",
              "|---|---|---|---|---|---|"]
    for yy, r in yr.iterrows():
        lines.append(f"| {yy}{' (test)' if yy in TEST_YEARS else ''} | {r.modis:.0f} | {r.viirs1:.0f} | "
                     f"{r.oran:.3f} | {r.oran / tr.median():.2f} | {r.aqua_terra:.2f} |")
    if len(m22):
        lines += ["", "2022 aylık oran / aynı ayın eğitim medyanı (< 1 → MODIS beklenenden az): "
                  + ", ".join(f"{MONTH_TR[k - 1][:3]} {v:.2f}" for k, v in m22.items())]
    lines += ["", "## Hohes Venn (kutu lon 5.95–6.25, lat 50.45–50.60)", "",
              f"'Görünüyor' = değer > 0 ve aynı ayın diğer yıllar ortalamasının ≥ {VISIBLE_RATIO:.0f} katı.", "",
              "| seri | ay | sonuç | görünüyor |", "|---|---|---|---|"]
    for v in venn:
        lines.append(f"| {v['mode']} | {v['year']}-{v['month']:02d} | {v['text']} | "
                     f"{'evet' if v['visible'] else 'hayır'} |")
    if burn is not None:
        lines += ["", "### Destekleyici kanıt: MCD64A1 yanmış alan (P1, `data/burned_area_check.csv`)", "",
                  "Tespit, MCD64A1'in (aylık yanmış alan, ~500 m) ±16 gün içinde yanmış işaretlediği bir "
                  "piksele (3×3 komşuluk ≈ 1,4 km) düşüyor mu? **Bağımsız doğrulama değildir**: MCD64A1 "
                  "algoritması MODIS aktif yangın verisini de kullanır ve küçük yanıkları kaçırabilir. "
                  "'bilinmiyor' (unknown/no_data) ≠ 'yanmamış'.", "",
                  "| olay | enstrüman | eşleşti | yanmamış | başka zamanda yanık | bilinmiyor | toplam |",
                  "|---|---|---|---|---|---|---|"]
        for (g, inst), r in burn.iterrows():
            y, m = BURN_GROUPS[g]
            lines.append(f"| {MONTH_TR[m - 1]} {y} | {inst} | {r.burned_match} "
                         f"({r.burned_match / r.toplam:.0%}) | {r.unburned} | {r.burned_other_time} | "
                         f"{r.unknown + r.no_data} | {r.toplam} |")

    if not has_harm:
        text = "\n".join(lines) + "\n"
        (OUT / "summary.md").write_text(text, encoding="utf-8")
        return text
    ar, gb = get("harm", "argentina"), get("harm", "aachen_eifel", split=TRANSFER_SPLIT[0])
    ar22, ar23 = get("harm", "argentina", split="test_2022"), get("harm", "argentina", split="test_2023-2024")
    vh = {(v["year"], v["month"]): v for v in venn if v["mode"] == "harm"}
    venn_ok = all(v["visible"] for v in vh.values())
    lines += ["", "## Sunum için 3 cümle (P6)", "",
              f"1. Arjantin'de (eğitim bölgesi), eğitimde kullanılmayan 2022–2024 yıllarında harmonize "
              f"VIIRS tahmini MODIS tespit sayısını 1° hücre-ay ölçeğinde R²={fmt(ar['r2'])} ile, "
              f"toplamda {fmt(ar['bias_pct'], '+.1f')}% sapmayla tahmin ediyor.",
              f"   Eğitimde hiç olmayan NOAA-21'in de aktif olduğu 2023–2024'te: "
              f"R²={fmt(ar23['r2'])}, toplam sapma {fmt(ar23['bias_pct'], '+.1f')}% "
              f"(2022, NOAA-21 öncesi: R²={fmt(ar22['r2'])}, {fmt(ar22['bias_pct'], '+.1f')}%).",
              f"2. Aynı katsayılar Aachen/Eifel'e (transfer, 2012–2026) taşındığında R²={fmt(gb['r2'])}, "
              f"toplam sapma {fmt(gb['bias_pct'], '+.1f')}% (n={gb['n']} hücre-ay)"
              + (f"; bu R² büyük ölçüde tek olaydan (Ağustos 2026): o ay hariç R²={fmt(tr_ev['1deg'][1]['r2'])}, "
                 f"sapma {fmt(tr_ev['1deg'][1]['bias_pct'], '+.1f')}%." if tr_ev and "1deg" in tr_ev else "."),
              f"3. Hohes Venn'de bilinen yangın olaylarıyla örtüşen tespit artışı "
              + ("Nisan 2011 ve Ağustos 2026'da harmonize takvimde görünüyor"
                 if venn_ok else "harmonize takvimde her iki ayda da belirgin DEĞİL")
              + ": " + "; ".join(f"{MONTH_TR[m - 1]} {y} → {v['text']}"
                                  for (y, m), v in vh.items()) + "."]
    # ---- sınırlamalar (dürüst raporlama; P2 + P4 isteği)
    vm = {(v["mode"], v["year"], v["month"]): v["value"] for v in venn}
    h26, m26 = vm.get(("harm", 2026, 8)), vm.get(("modis", 2026, 8))
    yearly, monthly = breakdown
    y22 = yearly.loc[("argentina", 2022), "oran"] if ("argentina", 2022) in yearly.index else np.nan
    hi_m = [f"{MONTH_TR[k - 1][:3]} {r.oran:.2f}" for k, r in monthly.iterrows() if r.oran >= 1.15]
    lo_m = [f"{MONTH_TR[k - 1][:3]} {r.oran:.2f}" for k, r in monthly.iterrows() if r.oran < 1.15]
    t1 = (tr_ev or {}).get("1deg")
    lines += ["", "## Sınırlamalar ve gelecek çalışma", "",
              f"- **2022 (test) fazla tahmin:** Arjantin'de Σharm/ΣMODIS = {fmt(y22)}. Fazlalık yangın "
              f"sezonunda ({', '.join(hi_m)}); kesinti ayları dahil diğer aylar 1'e yakın ({', '.join(lo_m)}). "
              "Ham veride de 2022'de MODIS/VIIRS oranı eğitim aralığının dışında (yukarıdaki tanı tablosu) → "
              "S-NPP/Aqua kesintisi ya da kalıcı yörünge kayması ile açıklanmıyor (2023–2024 normale dönüyor).",
              f"- **Aachen/Eifel Ağustos 2026 (bölge aktarımı, tek olay, n küçük):** harm/MODIS = "
              f"{fmt(h26 / m26 if h26 and m26 else np.nan)} ({fmt(h26, '.0f')} / {fmt(m26, '.0f')}). "
              "Fallback'ten değil (P2: 40–50 bandının k'sıyla bile +%50); olayın örtük k'sı 0.176, "
              "eğitimdeki tüm k'lar ≥ 0.20."]
    if t1:
        a, b = t1
        lines.append(f"- **Transfer R² tek olaydan etkileniyor:** Aachen/Eifel 1° R²={fmt(a['r2'])} "
                     f"(n={a['n']}, bias {fmt(a['bias_pct'], '+.1f')}%); 2026-08 hariç R²={fmt(b['r2'])}, "
                     f"bias {fmt(b['bias_pct'], '+.1f')}% (n={b['n']}). Yani olağan dönemde toplam seviye "
                     "tutuyor, hücre-ay deseni zayıf; büyük olayda fazla tahmin.")
    lines += ["- **Yorum (hipotez, doğrulanmadı):** k yangın büyüklüğüne bağlı — tek büyük yangın "
              "cephesinde VIIRS (375 m) MODIS'e (1 km) göre orantısız çok piksel sayıyor; k sadece enlem "
              "bandı × mevsim × uyduya göre katmanlı olduğu için bunu yakalayamıyor.",
              "- **Gelecek çalışma:** k'yı yangın büyüklüğüne (aynı gün komşu tespit kümesinin alanı / "
              "toplam FRP) göre koşullamak; transfer için Avrupa'dan ikinci bir eğitim bölgesi.",
              f"- **Örneklem:** Aachen/Eifel'de 2022–2024'te toplam "
              f"{int(yearly.loc['aachen_eifel', 'modis'].sum()) if 'aachen_eifel' in yearly.index.get_level_values(0) else '—'}"
              " MODIS tespiti → bölge test metriği istatistiksel olarak anlamsız; bu yüzden "
              "transfer_2012-2026 raporlandı."]
    text = "\n".join(lines) + "\n"
    (OUT / "summary.md").write_text(text, encoding="utf-8")
    return text


# ---------------------------------------------------------------- main

def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    input_path = pick_input()
    df = load_input(input_path)
    is_mock = bool((df["version"].astype(str) == "MOCK").any())
    has_harm = bool(df["weight_harm"].notna().all())
    if is_mock:
        print("⚠️  SENTETİK veriyle çalışılıyor. Sonuçlar sadece pipeline testi içindir.\n")
    if not has_harm:
        print("ℹ️  weight_harm boş (P1 verisi) → sadece ham sayımlar; harm metrikleri atlanıyor.\n")
    print(f"Girdi: {rel(input_path)}  ({len(df):,} satır)")

    k_note = (f"k_factors.csv: {len(pd.read_csv(K_PATH))} satır. P2 teyidi: k sadece Arjantin 2012–2021 "
              "VIIRS'ten, Terra-only ağırlığı 2003–2011'den → test yılları (2022–2024) k'ya girmedi."
              if K_PATH.exists() else "k_factors.csv yok")

    rows, tables = compute_metrics(df, has_harm)
    data_kind = "mock" if is_mock else ("harm" if has_harm else "raw")
    for r in rows:
        r["data"] = data_kind
    grid_note = crosscheck_grid(tables["0.25deg"]) if has_harm and not is_mock else \
        "monthly_grid çapraz kontrolü atlandı (sentetik ya da harmonize olmayan girdi)"
    json_rows = [r for r in rows if r["split"] in JSON_SPLITS]
    (OUT / "metrics.json").write_text(json.dumps(json_rows, indent=2, ensure_ascii=False),
                                      encoding="utf-8")

    plot_pred_vs_true(tables, rows, is_mock, has_harm)
    plot_annual(df, is_mock, has_harm)
    burn = burn_support()
    venn = venn_check(df, is_mock, has_harm, burn)
    print(write_summary(rows, venn, is_mock, input_path, grid_note, k_note,
                        test_year_breakdown(df, has_harm), ratio_diagnostics(df),
                        transfer_without_event(tables, has_harm), burn))

    weak = [r for r in rows if r["method"] == "harm" and r["split"] == "test"
            and (r["r2"] is None or r["r2"] < 0.5)]
    if weak:
        print("⚠️  Düşük/negatif R² (test, harm): " +
              ", ".join(f"{r['region']} {r['scale']} R²={fmt(r['r2'])}" for r in weak) +
              " — saklama, pitch'te dürüstçe anlat.")
    print(f"Yazıldı: {', '.join(sorted(p.name for p in OUT.iterdir()))}")


if __name__ == "__main__":
    main()
