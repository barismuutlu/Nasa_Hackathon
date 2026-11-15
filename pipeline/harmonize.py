"""P2 — Harmonization (contract v1.1, docs/CONTRACT.md §6, §7.2).

METHOD (Method A, k ratio — unvalidated hypothesis; metrics in P3):
1. weight_harm = each detection's "MODIS-equivalent" contribution; Σ weight_harm = harmonized detection estimate.
2. MODIS row: 1.0 before the first S-NPP date, 0.0 after (in the VIIRS era, VIIRS carries the series).
   Pre-Aqua (2000-11 → 2002-07, the only MODIS = Terra): Terra row k_terra = Σ(Terra+Aqua)/Σ Terra,
   argentina 2003–2011, days when both are active (Aqua passes in the afternoon, catches more).
3. VIIRS row: k(lat_band, season, satellite) / n_active_viirs(day).
   - k = Σ MODIS / Σ VIIRS_sat; training: region="argentina", 2012–2021, only days when Terra + Aqua +
     that VIIRS satellite are active on the SAME DAY. 2022–2024 test → not used in training.
   - lat_band = |latitude| 10° slice; season = local season (in the southern hemisphere month +6).
   - n_MODIS < MIN_N_MODIS → bands are pooled for that season+satellite (fallback). Band absent
     from training → nearest band (fallback). NOAA21 absent in training period → NOAA20's k (fallback).
4. n_active_viirs: satellite_coverage.csv first–last date range, minus data outages
   (≥ MIN_OUTAGE_DAYS consecutive days with no detection in the training region; e.g. SNPP 2022-07-27…08-10).
   This way the harmonized series does not jump when a new satellite is added/dropped.
5. No filter: type=2 (static source, ~3–5% in AR) included. In NRT type is empty → a filter could not be
   applied after 2026-08 and the series would break; the same rule (no filter) applies to MODIS and VIIRS.

Input : data/hotspots.parquet, data/satellite_coverage.csv  (P1; for testing $HARM_INPUT_DIR)
Output: data/hotspots_harm.parquet, data/monthly_grid.parquet, data/k_factors.csv ($HARM_OUT_DIR)
Run (from repo root):  python pipeline/harmonize.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from contract import COLUMNS, validate_hotspots  # noqa: E402

# ---- Path constants -------------------------------------------------------
IN_DIR = Path(os.environ.get("HARM_INPUT_DIR", "data"))
OUT_DIR = Path(os.environ.get("HARM_OUT_DIR", "data"))
INPUT_PATH = IN_DIR / "hotspots.parquet"
COVERAGE_PATH = IN_DIR / "satellite_coverage.csv"
OUT_HOTSPOTS = OUT_DIR / "hotspots_harm.parquet"
OUT_GRID = OUT_DIR / "monthly_grid.parquet"
OUT_K = OUT_DIR / "k_factors.csv"

# ---- Parameters ------------------------------------------------------------
TRAIN_REGION = "argentina"
TRAIN_YEARS = (2012, 2021)          # inclusive; 2022–2024 test → NOT used in training (leakage)
MIN_N_MODIS = 500                   # below → bands are pooled. At 30, the 50-60 band (Germany/Belgium)
                                    # got k≈0.08 from Tierra del Fuego's ~50 detections.
MIN_OUTAGE_DAYS = 3                 # this many consecutive days without detections in the training region → outage
TERRA_TRAIN_YEARS = (2003, 2011)    # Terra-only weight: Terra+Aqua both active, pre-VIIRS
GRID = 0.25

VIIRS_SATS = ["SNPP", "NOAA20", "NOAA21"]
MODIS_SATS = ["Terra", "Aqua"]
SAT_PROXY = {"NOAA21": "NOAA20"}    # satellite with no training data → this satellite's k

SEASONS = {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
           6: "summer", 7: "summer", 8: "summer", 9: "autumn", 10: "autumn", 11: "autumn"}


# ---- Loading ---------------------------------------------------------------
def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    for p in (INPUT_PATH, COVERAGE_PATH):
        if not p.exists():
            raise FileNotFoundError(f"{p} yok — önce P1: python pipeline/ingest.py")
    df = pd.read_parquet(INPUT_PATH)
    validate_hotspots(df, "any")
    cov = pd.read_csv(COVERAGE_PATH, parse_dates=["first_date", "last_date"])
    need = {"satellite", "first_date", "last_date"}
    if not need <= set(cov.columns):
        raise ValueError(f"satellite_coverage.csv eksik sütun: {need - set(cov.columns)}")
    return df, cov


# ---- Helpers ---------------------------------------------------------------
def lat_band(lat: pd.Series) -> pd.Series:
    lo = (np.floor(lat.abs() / 10) * 10).astype(int)
    return lo.astype(str) + "-" + (lo + 10).astype(str)


def local_season(lat: pd.Series, month: pd.Series) -> pd.Series:
    m = month.astype(int)
    m_local = np.where(lat < 0, (m - 1 + 6) % 12 + 1, m)   # southern hemisphere: +6 months
    return pd.Series(m_local, index=lat.index).map(SEASONS)


def band_lo(band: str) -> int:
    return int(band.split("-")[0])


def active_days(df: pd.DataFrame, cov: pd.DataFrame) -> pd.DataFrame:
    """Day × satellite activity table (bool): coverage first–last range, minus outages."""
    # Satellite operating dates only from the training region: the first/last date of small regions
    # (aachen_eifel) is a sparse detection date, not a satellite operating date (P1 note).
    if "region" in cov.columns:
        cov = cov[cov["region"] == TRAIN_REGION]
        if cov.empty:
            raise ValueError(f"satellite_coverage.csv'de region={TRAIN_REGION} satırı yok")
    span = cov.groupby("satellite").agg(first=("first_date", "min"), last=("last_date", "max"))
    days = pd.date_range(df["acq_date"].min(), df["acq_date"].max(), freq="D")
    out = pd.DataFrame(False, index=days, columns=MODIS_SATS + VIIRS_SATS)
    ref = df.loc[df["region"] == TRAIN_REGION, ["acq_date", "satellite"]]
    for sat in out.columns:
        if sat not in span.index:
            continue
        on = (days >= span.loc[sat, "first"]) & (days <= span.loc[sat, "last"])
        d = ref.loc[ref["satellite"] == sat, "acq_date"].unique()
        if len(d):   # outage detection is reliable only in the large training region
            has = pd.Series(days.isin(d), index=days)
            run_len = has.groupby((has != has.shift()).cumsum()).transform("size")
            on &= ~((~has) & (run_len >= MIN_OUTAGE_DAYS)).to_numpy()
        out[sat] = on
    return out


# ---- k coefficients --------------------------------------------------------
def compute_k(df: pd.DataFrame, act: pd.DataFrame) -> pd.DataFrame:
    tr = df.loc[(df["region"] == TRAIN_REGION) & df["year"].between(*TRAIN_YEARS),
                ["acq_date", "satellite", "instrument", "_band", "_season"]]
    modis_ok = act[MODIS_SATS].all(axis=1)
    rows = []
    for sat in VIIRS_SATS:
        sub = tr[tr["acq_date"].isin(act.index[modis_ok & act[sat]])]
        if sub.empty:
            continue
        sub = sub.assign(is_m=sub["instrument"] == "MODIS", is_v=sub["satellite"] == sat)
        g = sub.groupby(["_band", "_season"])[["is_m", "is_v"]].sum()
        pooled = sub.groupby("_season")[["is_m", "is_v"]].sum()
        for (band, season), r in g.iterrows():
            n_m, n_v, fb = int(r.is_m), int(r.is_v), False
            if n_m < MIN_N_MODIS or n_v == 0:
                n_m, n_v, fb = int(pooled.loc[season, "is_m"]), int(pooled.loc[season, "is_v"]), True
            rows.append(dict(lat_band=band, season=season, satellite=sat, k=n_m / n_v,
                             n_modis=n_m, n_viirs=n_v, fallback=fb,
                             note="pooled_bands" if fb else ""))
    if not rows:
        raise ValueError(f"Eğitim verisi boş — {TRAIN_REGION} {TRAIN_YEARS}'de MODIS+VIIRS ortak gün yok")
    return pd.DataFrame(rows)


def complete_k(k: pd.DataFrame, needed: pd.DataFrame) -> pd.DataFrame:
    """Ensure a k exists for every (band, season, satellite) needed in application (proxy satellite / nearest band)."""
    k = k.copy()
    for sat, proxy in SAT_PROXY.items():
        if sat not in set(k["satellite"]):
            p = k[k["satellite"] == proxy].copy()
            p["satellite"], p["fallback"], p["note"] = sat, True, f"proxy_{proxy}"
            k = pd.concat([k, p], ignore_index=True)
    have = set(zip(k["lat_band"], k["season"], k["satellite"]))
    extra = []
    for band, season, sat in needed.itertuples(index=False):
        if (band, season, sat) in have:
            continue
        cand = k[(k["season"] == season) & (k["satellite"] == sat)]
        if cand.empty:
            raise ValueError(f"k bulunamadı: {sat} {season} — eğitimde hiç örnek yok")
        src = cand.iloc[(cand["lat_band"].map(band_lo) - band_lo(band)).abs().argsort().iloc[0]]
        extra.append(dict(src, lat_band=band, fallback=True, note=f"nearest_band_{src['lat_band']}"))
        have.add((band, season, sat))
    if extra:
        k = pd.concat([k, pd.DataFrame(extra)], ignore_index=True)
    return k.sort_values(["satellite", "lat_band", "season"]).reset_index(drop=True)


def compute_k_terra(df: pd.DataFrame, act: pd.DataFrame) -> dict:
    """Weight for the Terra-only period: Σ(Terra+Aqua) / Σ Terra (training region, 2003–2011)."""
    both = act.index[act["Terra"] & act["Aqua"]]
    m = df.loc[(df["region"] == TRAIN_REGION) & df["year"].between(*TERRA_TRAIN_YEARS)
               & (df["instrument"] == "MODIS") & df["acq_date"].isin(both), "satellite"].astype(str)
    n_terra, n_all = int((m == "Terra").sum()), len(m)
    if n_terra < MIN_N_MODIS:
        raise ValueError(f"Terra-only ağırlığı için yetersiz veri: {n_terra} Terra tespiti")
    return dict(lat_band="all", season="all", satellite="Terra", k=n_all / n_terra,
                n_modis=n_all, n_viirs=n_terra, fallback=False,
                note="terra_only_pre_aqua: k=(Terra+Aqua)/Terra, n_viirs=Terra sayısı")


# ---- weight_harm ------------------------------------------------------------
def compute_weights(df: pd.DataFrame, k: pd.DataFrame, act: pd.DataFrame, k_terra: float) -> pd.Series:
    w = pd.Series(np.nan, index=df.index, dtype="float64")
    sat = df["satellite"].astype(str)
    is_modis = df["instrument"] == "MODIS"

    snpp_first = act.index[act["SNPP"]].min() if act["SNPP"].any() else pd.Timestamp.max
    aqua_first = act.index[act["Aqua"]].min() if act["Aqua"].any() else pd.Timestamp.max
    pre_viirs = df["acq_date"] < snpp_first
    w[is_modis] = np.where(pre_viirs[is_modis], 1.0, 0.0)
    w[is_modis & pre_viirs & (sat == "Terra") & (df["acq_date"] < aqua_first)] = k_terra

    is_v = ~is_modis
    if is_v.any():
        v = df.loc[is_v, ["acq_date", "_band", "_season"]].assign(satellite=sat[is_v])
        kk = k.set_index(["lat_band", "season", "satellite"])["k"]
        k_vals = kk.reindex(pd.MultiIndex.from_frame(v[["_band", "_season", "satellite"]])).to_numpy()
        n_act = act[VIIRS_SATS].sum(axis=1).reindex(v["acq_date"]).fillna(0).to_numpy()
        w[is_v] = k_vals / np.maximum(n_act, 1)   # a satellite with a detection counts as at least 1 active that day

    if w.isna().any():
        raise ValueError(f"weight_harm'da {int(w.isna().sum())} NaN kaldı")
    if (w < 0).any():
        raise ValueError("weight_harm negatif değer içeriyor")
    return w.astype("float32")


# ---- Monthly grid (CONTRACT §7.2) ------------------------------------------
def monthly_grid(df: pd.DataFrame) -> pd.DataFrame:
    sat = df["satellite"].astype(str)
    g = pd.DataFrame({
        "cell_lat": np.floor(df["latitude"] / GRID) * GRID + GRID / 2,
        "cell_lon": np.floor(df["longitude"] / GRID) * GRID + GRID / 2,
        "year": df["year"], "month": df["month"], "region": df["region"],
        **{f"n_{s.lower()}": (sat == s).astype("int32") for s in MODIS_SATS + VIIRS_SATS},
        "n_modis": (df["instrument"] == "MODIS").astype("int32"),
        "n_viirs": (df["instrument"] == "VIIRS").astype("int32"),
        "n_harm": df["weight_harm"].astype("float64"),
    })
    out = g.groupby(["cell_lat", "cell_lon", "year", "month", "region"], as_index=False).sum()
    for c in out.columns:
        if c.startswith("n_") and c != "n_harm":
            out[c] = out[c].astype("int32")
    out["year"], out["month"] = out["year"].astype("int16"), out["month"].astype("int8")
    out["region"] = out["region"].astype("string")
    return out


# ---- Summary ----------------------------------------------------------------
def summary(df: pd.DataFrame) -> None:
    ar = df[df["region"] == TRAIN_REGION]
    if ar.empty:
        return
    y = pd.DataFrame({
        "raw_all": ar.groupby("year").size(),
        "modis": ar[ar["instrument"] == "MODIS"].groupby("year").size(),
        "harm": ar.groupby("year")["weight_harm"].sum(),
    }).fillna(0)
    y["harm/modis"] = (y["harm"] / y["modis"]).round(3)
    y["raw_yoy"] = y["raw_all"].pct_change().round(2)
    y["harm_yoy"] = y["harm"].pct_change().round(2)
    print(f"\n== {TRAIN_REGION} yıllık: ham vs harmonize ==")
    print(y.astype({"raw_all": int, "modis": int, "harm": int}).to_string())
    t = y.loc[TRAIN_YEARS[0]:TRAIN_YEARS[1]]
    diff = t["harm"].sum() / t["modis"].sum() - 1
    print(f"\nEğitim {TRAIN_YEARS[0]}–{TRAIN_YEARS[1]}: Σharm/ΣMODIS - 1 = {diff:+.2%} "
          f"({'OK' if abs(diff) < 0.10 else 'FAIL'} < %10)")
    for yr in (2002, 2003, 2012, 2018, 2023, 2024):
        if yr in y.index and yr - 1 in y.index:
            print(f"  {yr - 1}→{yr}: ham {y.loc[yr, 'raw_yoy']:+.0%}   harm {y.loc[yr, 'harm_yoy']:+.0%}")


# ---- main -------------------------------------------------------------------
def main() -> None:
    print(f"Girdi: {INPUT_PATH}, {COVERAGE_PATH}")
    df, cov = load()
    print(f"{len(df):,} satır, {df['acq_date'].min().date()} → {df['acq_date'].max().date()}, "
          f"bölgeler: {sorted(df['region'].unique())}")

    df["_band"] = lat_band(df["latitude"])
    df["_season"] = local_season(df["latitude"], df["month"])

    act = active_days(df, cov)
    for s in VIIRS_SATS + MODIS_SATS:
        a = act[s]
        if a.any():
            first, last = a[a].index.min(), a[a].index.max()
            print(f"  aktif {s:7s}: {first.date()} → {last.date()}, kesinti günü {int((~a[first:last]).sum())}")

    k = compute_k(df, act)
    needed = df.loc[df["instrument"] == "VIIRS", ["_band", "_season", "satellite"]].astype(str).drop_duplicates()
    k = complete_k(k, needed)
    kt = compute_k_terra(df, act)
    k = pd.concat([k, pd.DataFrame([kt])], ignore_index=True)
    print(f"  Terra-only ağırlığı (Aqua öncesi): {kt['k']:.3f}")
    df["weight_harm"] = compute_weights(df, k, act, kt["k"])

    grid = monthly_grid(df)
    df = df[COLUMNS]
    validate_hotspots(df, "harm")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    k.to_csv(OUT_K, index=False)
    df.to_parquet(OUT_HOTSPOTS, index=False)
    grid.to_parquet(OUT_GRID, index=False)

    print(f"\nYazıldı: {OUT_K} ({len(k)} satır, fallback {int(k['fallback'].sum())})")
    print(f"Yazıldı: {OUT_HOTSPOTS} ({len(df):,} satır)")
    print(f"Yazıldı: {OUT_GRID} ({len(grid):,} hücre-ay)")
    print("\n== k katsayıları ==")
    print(k.to_string(index=False))
    summary(df)


if __name__ == "__main__":
    main()
