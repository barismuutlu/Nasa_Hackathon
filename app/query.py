"""Veri katmanı — sahibi P4 Barış. API sözleşmesi: docs/CONTRACT.md §7.4.

P5 (app.py) parquet'i doğrudan okumaz; sadece bu modülü kullanır:
    from query import PRESETS, data_info, get_hotspots, monthly_matrix, anomaly, to_csv_bytes, forecast

Bu modül Streamlit'e bağımlı değildir (pipeline/ ve testlerden de kullanılabilir).
Önbellekleme (st.cache_data) app.py'nin işidir; burada sadece dosya okuması önbellekli.
"""
from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import shapely
from shapely.geometry import shape

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from contract import CONTRACT_VERSION, MOCK_VERSION, validate_hotspots  # noqa: E402

# Öncelik sırası: ilk bulunan dosya kullanılır (kök CLAUDE.md §4)
DATA_CANDIDATES = [
    ROOT / "data" / "hotspots_harm.parquet",          # P2 — harmonize, tam veri
    ROOT / "data" / "hotspots.parquet",               # P1 — ham, weight_harm NaN
    ROOT / "data" / "deploy" / "hotspots_deploy.parquet",  # Streamlit Cloud
    ROOT / "data" / "mock" / "hotspots_mock.parquet",      # P4 — sahte
]

# ad -> (lon_min, lat_min, lon_max, lat_max)
PRESETS: dict[str, tuple[float, float, float, float]] = {
    "Hohes Venn": (5.95, 50.45, 6.25, 50.60),
    "Aachen/Eifel": (5.96, 50.44, 6.44, 50.83),   # = indirme alanı (contract.REGIONS)
    "La Rioja (AR)": (-69.7, -31.9, -65.4, -27.6),
}

MONTH_LABELS = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]


# ---------------------------------------------------------------- yükleme

def data_path() -> Path:
    """Kullanılacak parquet yolu: $HOTSPOTS_PATH, yoksa DATA_CANDIDATES'ten ilk var olan."""
    env = os.environ.get("HOTSPOTS_PATH")
    if env:
        p = Path(env)
        if not p.exists():
            raise FileNotFoundError(f"HOTSPOTS_PATH bulunamadı: {p}")
        return p
    for p in DATA_CANDIDATES:
        if p.exists():
            return p
    raise FileNotFoundError(
        "Veri yok. `python data/mock/make_mock.py` çalıştır ya da data/hotspots*.parquet koy."
    )


@lru_cache(maxsize=2)
def _load(path_str: str, mtime: float) -> pd.DataFrame:
    df = pd.read_parquet(path_str, engine="pyarrow")
    try:
        validate_hotspots(df, stage="any", max_rows=200_000)  # tam kontrol P1/P2 yazarken yapıldı
    except ValueError as e:
        raise ValueError(f"{path_str} sözleşmeye uymuyor:\n{e}") from e
    return df


def load_hotspots() -> pd.DataFrame:
    """Tüm veri (önbellekli; dosya değişirse yeniden okunur). Değiştirme — kopyala."""
    p = data_path()
    return _load(str(p), p.stat().st_mtime)


def data_info() -> dict[str, Any]:
    """Uygulamada gösterilecek veri özeti (ör. 'MOCK VERİ' uyarısı için)."""
    p = data_path()
    df = load_hotspots()
    return {
        "path": str(p.relative_to(ROOT)) if p.is_relative_to(ROOT) else str(p),
        "is_mock": bool((df["version"] == MOCK_VERSION).any()) or "mock" in p.parts,
        "has_harm": bool(df["weight_harm"].notna().any()),
        "start": df["acq_date"].min(),
        "end": df["acq_date"].max(),
        "n_rows": len(df),
        "satellites": sorted(df["satellite"].astype(str).unique().tolist()),
        "satellite_ranges": _satellite_ranges(df),
        "contract": CONTRACT_VERSION,
    }


def _satellite_ranges(df: pd.DataFrame) -> dict[str, tuple[pd.Timestamp, pd.Timestamp]]:
    """Uydu → (ilk, son) tespit tarihi, VERİDEN. Grafikteki uydu değişim çizgileri için."""
    g = df.groupby("satellite", observed=True)["acq_date"].agg(["min", "max"]).sort_values("min")
    return {str(s): (r["min"], r["max"]) for s, r in g.iterrows()}


# ---------------------------------------------------------------- sorgular

def _parse_geom(geom) -> tuple[tuple[float, float, float, float], Any | None]:
    """bbox tuple ya da GeoJSON (Feature / Polygon / MultiPolygon) → (bbox, poligon|None)."""
    if isinstance(geom, str):
        if geom not in PRESETS:
            raise ValueError(f"Bilinmeyen hazır bölge: {geom!r}. Seçenekler: {list(PRESETS)}")
        geom = PRESETS[geom]
    if isinstance(geom, (tuple, list)) and len(geom) == 4:
        lon_min, lat_min, lon_max, lat_max = map(float, geom)
        if lon_min >= lon_max or lat_min >= lat_max:
            raise ValueError(f"Geçersiz bbox (lon_min, lat_min, lon_max, lat_max): {geom}")
        return (lon_min, lat_min, lon_max, lat_max), None
    if isinstance(geom, dict):
        g = geom.get("geometry", geom) if geom.get("type") == "Feature" else geom
        if g.get("type") not in ("Polygon", "MultiPolygon"):
            raise ValueError(f"Sadece Polygon/MultiPolygon destekleniyor, gelen: {g.get('type')}")
        poly = shape(g)
        return tuple(poly.bounds), poly  # type: ignore[return-value]
    raise ValueError(f"geom tanınmadı: {type(geom).__name__}")


def get_hotspots(geom, start=None, end=None, harmonized: bool = False) -> pd.DataFrame:
    """Bölge + tarih aralığındaki tespitler.

    geom: PRESETS anahtarı, bbox (lon_min, lat_min, lon_max, lat_max) ya da
          GeoJSON dict (streamlit-folium `last_active_drawing` doğrudan verilebilir).
    start, end: UTC tarih (dahil); None = sınırsız.
    Dönüş: CONTRACT §1 sütunları, aynı dtype'lar; 0 satır olabilir.
    harmonized: True → sadece harmonize seriye katkı veren satırlar (weight_harm > 0).
    """
    (lon_min, lat_min, lon_max, lat_max), poly = _parse_geom(geom)
    df = load_hotspots()
    m = df["longitude"].between(lon_min, lon_max) & df["latitude"].between(lat_min, lat_max)
    if start is not None:
        m &= df["acq_date"] >= pd.Timestamp(start)
    if end is not None:
        m &= df["acq_date"] <= pd.Timestamp(end)
    if harmonized:
        m &= df["weight_harm"].fillna(0) > 0
    out = df.loc[m]
    if poly is not None and len(out):
        inside = shapely.intersects_xy(poly,  # sınır dahil (bbox ile tutarlı)
                                         out["longitude"].to_numpy(), out["latitude"].to_numpy())
        out = out.loc[inside]
    return out.copy()


def monthly_matrix(df: pd.DataFrame, mode: str = "raw", start=None, end=None) -> pd.DataFrame:
    """Yıl × ay tablosu (index=yıl, columns=1..12).

    mode="raw":  tespit sayısı (tüm uydular — uydu eklenince sıçrar)
    mode="harm": Σ weight_harm (MODIS-eşdeğeri)
    Veri kapsamı dışındaki aylar (ör. 2000 Oca–Eki, gelecek aylar) NaN; kapsam içinde tespit yoksa 0.
    Harmonize veri yoksa (P2 öncesi) mode="harm" tamamen NaN döner.
    start, end: get_hotspots'a verilen tarih filtresinin AYNISI. Verilirse aralığın dışındaki aylar da NaN
    olur (0 değil) → yıllık toplam ve anomali tabanı filtrelenen yılları "0 tespit" saymaz.
    Aralığın kısmen dahil olduğu ilk/son ay dahil sayılır.
    """
    if mode not in ("raw", "harm"):
        raise ValueError(f"mode 'raw' ya da 'harm' olmalı, gelen: {mode!r}")
    full = load_hotspots()
    cov_start = full["acq_date"].min().to_period("M")
    cov_end = full["acq_date"].max().to_period("M")
    years = range(cov_start.year, cov_end.year + 1)

    if mode == "raw":
        agg = df.groupby(["year", "month"]).size()
    else:
        agg = df.groupby(["year", "month"])["weight_harm"].sum(min_count=1)
    mat = agg.unstack("month").reindex(index=years, columns=range(1, 13)).astype("float64")
    mat = mat.fillna(0.0)

    # kapsam dışı ve tarih filtresi dışı aylar NaN
    lo = max(cov_start, pd.Timestamp(start).to_period("M")) if start is not None else cov_start
    hi = min(cov_end, pd.Timestamp(end).to_period("M")) if end is not None else cov_end
    for y in years:
        for mth in range(1, 13):
            per = pd.Period(year=y, month=mth, freq="M")
            if per < lo or per > hi:
                mat.loc[y, mth] = np.nan

    if mode == "harm" and not full["weight_harm"].notna().any():
        mat[:] = np.nan
    mat.index.name = "year"
    mat.columns.name = "month"
    return mat


def anomaly(matrix: pd.DataFrame, year: int, month: int) -> dict[str, Any]:
    """Seçili ayın, aynı takvim ayının diğer yıllarına göre anomalisi.

    rank: 1 = o ay için en yüksek yıl. label: "çok yüksek" (z>2), "yüksek" (z>1),
    "normal", "düşük" (z<-1), "tespit yok" (hep 0), "veri yok".
    """
    value = matrix.at[year, month] if year in matrix.index else np.nan
    base = matrix[month].drop(index=year, errors="ignore").dropna()
    res: dict[str, Any] = {"value": float(value) if pd.notna(value) else np.nan,
                           "mean": np.nan, "std": np.nan, "z": np.nan,
                           "rank": None, "n_years": int(len(base)) + (1 if pd.notna(value) else 0),
                           "label": "veri yok"}
    if pd.isna(value) or len(base) < 2:
        return res
    if value == 0 and (base == 0).all():
        res.update(mean=0.0, std=0.0, label="tespit yok")
        return res
    mean, std = float(base.mean()), float(base.std(ddof=1))
    z = (value - mean) / std if std > 0 else 0.0
    res.update(mean=mean, std=std, z=float(z), rank=int((base > value).sum()) + 1)
    res["label"] = ("çok yüksek" if z > 2 else "yüksek" if z > 1 else "düşük" if z < -1 else "normal")
    return res


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """st.download_button için CSV (UTF-8, index'li tablolar için index korunur)."""
    keep_index = df.index.name is not None
    return df.to_csv(index=keep_index, lineterminator="\n").encode("utf-8")  # Windows'ta da \n


# ---------------------------------------------------------------- deneysel 30 günlük görünüm (v1.5)

FORECAST_PATH = ROOT / "data" / "deploy" / "forecast.parquet"     # pipeline/forecast.py (P4)
FORECAST_METRICS = ROOT / "docs" / "forecast" / "metrics.json"
FORECAST_RATIO = 1.5    # oran ≥ 1.5 → "above normal", ≤ 1/1.5 → "below normal", arası "near normal"


@lru_cache(maxsize=2)
def _load_forecast(path_str: str, mtime: float) -> tuple[pd.DataFrame, dict]:
    import json
    f = pd.read_parquet(path_str, engine="pyarrow")
    if not FORECAST_METRICS.exists():
        raise FileNotFoundError(f"{FORECAST_METRICS} yok — python pipeline/forecast.py")
    return f, json.loads(FORECAST_METRICS.read_text(encoding="utf-8"))


def forecast(geom) -> dict[str, Any] | None:
    """Deneysel 30 günlük tespit görünümü (CONTRACT §7.5). Bölgede görünüm hücresi yoksa None.

    Hücre seçimi: 1° hücre MERKEZİ bölgenin içindeyse. Sadece Arjantin; hotspot dosyasından bağımsız.
    Bölge toplamı = (Σ expected_geo / Σ normal_geo) × Σ normal  (pipeline/forecast.py ile aynı hesap).
    """
    if not FORECAST_PATH.exists():
        return None
    f, meta = _load_forecast(str(FORECAST_PATH), FORECAST_PATH.stat().st_mtime)
    (lon_min, lat_min, lon_max, lat_max), poly = _parse_geom(geom)
    m = f["cell_lon"].between(lon_min, lon_max) & f["cell_lat"].between(lat_min, lat_max)
    if poly is not None:
        m &= shapely.contains_xy(poly, f["cell_lon"].to_numpy(), f["cell_lat"].to_numpy())
    cells = f.loc[m].reset_index(drop=True)
    if cells.empty:
        return None
    ratio = float(cells["expected_geo"].sum() / cells["normal_geo"].sum())
    normal = float(cells["normal"].sum())
    pred = ratio * normal
    scope = "la_rioja" if len(cells) < meta["small_selection_cells"] else "argentina"
    sc = meta["scopes"][scope]
    if ratio >= FORECAST_RATIO:
        label = "above normal"
    elif ratio <= 1 / FORECAST_RATIO:
        label = "below normal"
    else:
        label = "near normal"
    cells = cells.assign(ratio=(cells["expected_geo"] + 1) / (cells["normal_geo"] + 1))  # harita için, yumuşatılmış
    return {
        "start": cells["start"].iloc[0], "end": cells["end"].iloc[0],
        "data_through": cells["data_through"].iloc[0],
        "pred": pred,
        "p10": float(np.expm1(np.log1p(pred) + sc["err_log_p10"])),
        "p90": float(np.expm1(np.log1p(pred) + sc["err_log_p90"])),
        "normal": normal, "ratio": ratio, "label": label, "n_cells": len(cells),
        "skill": meta["skill_vs_normal"], "direction_hit_rate": meta["direction_hit_rate"],
        "backtest_years": tuple(meta["test_years"]),
        "cells": cells,
    }


# ---------------------------------------------------------------- hızlı kontrol

if __name__ == "__main__":
    info = data_info()
    print(info)
    venn = get_hotspots("Hohes Venn")
    for mode in ("raw", "harm"):
        mat = monthly_matrix(venn, mode)
        for y, m in ((2011, 4), (2026, 8)):
            a = anomaly(mat, y, m)
            print(f"Venn {mode:4s} {y}-{m:02d}: değer={a['value']:.1f} z={a['z']:.1f} "
                  f"sıra={a['rank']}/{a['n_years']} → {a['label']}")
