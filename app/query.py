"""Data layer — owner P4 Barış. API contract: docs/CONTRACT.md §7.4.

P5 (app.py) does not read the parquet directly; it ONLY uses this module:
    from query import PRESETS, data_info, get_hotspots, monthly_matrix, anomaly, to_csv_bytes, forecast, seasonal_outlook

This module does not depend on Streamlit (it can also be used from pipeline/ and tests).
Caching (st.cache_data) is app.py's job; here ONLY the file read is cached.
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

# Priority order: the first file found is used (root CLAUDE.md §4)
DATA_CANDIDATES = [
    ROOT / "data" / "hotspots_harm.parquet",          # P2 — harmonized, full data
    ROOT / "data" / "hotspots.parquet",               # P1 — raw, weight_harm NaN
    ROOT / "data" / "deploy" / "hotspots_deploy.parquet",  # Streamlit Cloud
    ROOT / "data" / "mock" / "hotspots_mock.parquet",      # P4 — mock
]

# name -> (lon_min, lat_min, lon_max, lat_max)
PRESETS: dict[str, tuple[float, float, float, float]] = {
    "Hohes Venn": (5.95, 50.45, 6.25, 50.60),
    "Aachen/Eifel": (5.96, 50.44, 6.44, 50.83),   # = download area (contract.REGIONS)
    "La Rioja (AR)": (-69.7, -31.9, -65.4, -27.6),
}

MONTH_LABELS = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]


# ---------------------------------------------------------------- loading

def data_path() -> Path:
    """Parquet path to use: $HOTSPOTS_PATH, otherwise the first existing one from DATA_CANDIDATES."""
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
        validate_hotspots(df, stage="any", max_rows=200_000)  # full check was done when P1/P2 wrote it
    except ValueError as e:
        raise ValueError(f"{path_str} sözleşmeye uymuyor:\n{e}") from e
    return df


def load_hotspots() -> pd.DataFrame:
    """All data (cached; re-read if the file changes). Do not modify — copy."""
    p = data_path()
    return _load(str(p), p.stat().st_mtime)


def data_info() -> dict[str, Any]:
    """Data summary to show in the app (e.g. for the 'MOCK VERİ' warning)."""
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
    """Satellite → (first, last) detection date, FROM THE DATA. For the satellite-change lines in the chart."""
    g = df.groupby("satellite", observed=True)["acq_date"].agg(["min", "max"]).sort_values("min")
    return {str(s): (r["min"], r["max"]) for s, r in g.iterrows()}


# ---------------------------------------------------------------- queries

def _parse_geom(geom) -> tuple[tuple[float, float, float, float], Any | None]:
    """bbox tuple or GeoJSON (Feature / Polygon / MultiPolygon) → (bbox, polygon|None)."""
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
    """Detections within the region + date range.

    geom: PRESETS key, bbox (lon_min, lat_min, lon_max, lat_max) or
          GeoJSON dict (streamlit-folium `last_active_drawing` can be passed directly).
    start, end: UTC date (inclusive); None = unbounded.
    Returns: CONTRACT §1 columns, same dtypes; may have 0 rows.
    harmonized: True → ONLY rows that contribute to the harmonized series (weight_harm > 0).
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
        inside = shapely.intersects_xy(poly,  # boundary inclusive (consistent with bbox)
                                         out["longitude"].to_numpy(), out["latitude"].to_numpy())
        out = out.loc[inside]
    return out.copy()


def monthly_matrix(df: pd.DataFrame, mode: str = "raw", start=None, end=None) -> pd.DataFrame:
    """Year × month table (index=year, columns=1..12).

    mode="raw":  detection count (all satellites — jumps when a satellite is added)
    mode="harm": Σ weight_harm (MODIS-equivalent)
    Months outside the data coverage (e.g. 2000 Jan–Oct, future months) are NaN; 0 if no detection within coverage.
    If there is no harmonized data (before P2), mode="harm" returns all NaN.
    start, end: the SAME date filter passed to get_hotspots. If given, months outside the range also become NaN
    (not 0) → the yearly total and the anomaly baseline do not count filtered-out years as "0 detections".
    The first/last month partially covered by the range counts as included.
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

    # months outside coverage and outside the date filter are NaN
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
    """Anomaly of the selected month relative to the same calendar month in other years.

    rank: 1 = highest year for that month. label: "çok yüksek" (z>2), "yüksek" (z>1),
    "normal", "düşük" (z<-1), "tespit yok" (all 0), "veri yok".
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
    """CSV for st.download_button (UTF-8; the index is kept for indexed tables)."""
    keep_index = df.index.name is not None
    return df.to_csv(index=keep_index, lineterminator="\n").encode("utf-8")  # \n on Windows too


# ---------------------------------------------------------------- experimental 30-day outlook (v1.5)

FORECAST_PATH = ROOT / "data" / "deploy" / "forecast.parquet"            # pipeline/forecast.py (P4)
FORECAST_HISTORY = ROOT / "data" / "deploy" / "forecast_history.parquet"
FORECAST_METRICS = ROOT / "docs" / "forecast" / "metrics.json"
FORECAST_RATIO = 1.5    # ratio ≥ 1.5 → "above normal", ≤ 1/1.5 → "below normal", in between "near normal"
PROFILE_YEARS = 10      # seasonal profile and seasonal normal: last 10 full years


@lru_cache(maxsize=2)
def _load_forecast(path_str: str, mtime: float) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    import json
    f = pd.read_parquet(path_str, engine="pyarrow")
    if not (FORECAST_METRICS.exists() and FORECAST_HISTORY.exists()):
        raise FileNotFoundError("docs/forecast/metrics.json ya da forecast_history.parquet yok — python pipeline/forecast.py")
    h = pd.read_parquet(FORECAST_HISTORY, engine="pyarrow")
    return f, h, json.loads(FORECAST_METRICS.read_text(encoding="utf-8"))


def _same_window(year: int, start: pd.Timestamp) -> pd.Timestamp:
    try:
        return start.replace(year=year)
    except ValueError:                                  # 29 February
        return start.replace(year=year, day=28)


def _seasonal_profile(df: pd.DataFrame, last_full_year: int) -> pd.Series:
    """Calendar month → monthly mean over the last PROFILE_YEARS full years (MODIS-equiv. or raw count)."""
    mode = "harm" if df["weight_harm"].notna().any() else "raw"
    mat = monthly_matrix(df, mode)
    rows = mat.loc[(mat.index > last_full_year - PROFILE_YEARS) & (mat.index <= last_full_year)]
    prof = rows.mean().reindex(range(1, 13)).fillna(0.0)
    prof.index.name = "month"
    return prof.rename("normal")


def forecast(geom) -> dict[str, Any] | None:
    """Experimental 30-day detection outlook (CONTRACT §7.5) — tested model, Argentina ONLY.

    If the region has no outlook cell (1° cell CENTER inside geom) → None → the app falls back to seasonal_outlook(geom).
    Region total = (Σ expected_geo / Σ normal_geo) × Σ normal (same computation as pipeline/forecast.py).
    """
    r = _outlook(geom)
    return r if r is not None and r["mode"] == "model" else None


def seasonal_outlook(geom) -> dict[str, Any] | None:
    """For regions without a model (e.g. Hohes Venn), the SEASONAL NORMAL of the same 30-day window — NOT A FORECAST.

    pred = normal; "history" (past years) and "profile" (12 months) are for the chart. None if the region has no data at all.
    Can also be called in the model region (Argentina): then it returns the forecast() result (mode="model").
    """
    return _outlook(geom)


def _outlook(geom) -> dict[str, Any] | None:
    """Shared computation for forecast() / seasonal_outlook(). mode = "model" | "seasonal"."""
    if not FORECAST_PATH.exists():
        return None
    f, h, meta = _load_forecast(str(FORECAST_PATH), FORECAST_PATH.stat().st_mtime)
    (lon_min, lat_min, lon_max, lat_max), poly = _parse_geom(geom)
    m = f["cell_lon"].between(lon_min, lon_max) & f["cell_lat"].between(lat_min, lat_max)
    if poly is not None:
        m &= shapely.contains_xy(poly, f["cell_lon"].to_numpy(), f["cell_lat"].to_numpy())
    cells = f.loc[m].reset_index(drop=True)
    start, end, data_through = f["start"].iloc[0], f["end"].iloc[0], f["data_through"].iloc[0]
    last_full_year = start.year - 1
    det = get_hotspots(geom)
    base = {"start": start, "end": end, "data_through": data_through,
            "profile": _seasonal_profile(det, last_full_year) if len(det) else pd.Series(
                0.0, index=pd.RangeIndex(1, 13, name="month"), name="normal")}

    if not cells.empty:                                           # ---- model mode (Argentina)
        ratio = float(cells["expected_geo"].sum() / cells["normal_geo"].sum())
        normal = float(cells["normal"].sum())
        pred = ratio * normal
        sc = meta["scopes"]["la_rioja" if len(cells) < meta["small_selection_cells"] else "argentina"]
        label = ("above normal" if ratio >= FORECAST_RATIO else
                 "below normal" if ratio <= 1 / FORECAST_RATIO else "near normal")
        hist = (h.merge(cells[["cell_lat", "cell_lon"]], on=["cell_lat", "cell_lon"])
                .groupby("year")["detections"].sum())
        cells = cells.assign(ratio=(cells["expected_geo"] + 1) / (cells["normal_geo"] + 1))  # map, smoothed
        return {**base, "mode": "model", "pred": pred,
                "p10": float(np.expm1(np.log1p(pred) + sc["err_log_p10"])),
                "p90": float(np.expm1(np.log1p(pred) + sc["err_log_p90"])),
                "normal": normal, "ratio": ratio, "label": label, "n_cells": len(cells),
                "skill": meta["skill_vs_normal"], "direction_hit_rate": meta["direction_hit_rate"],
                "backtest_years": tuple(meta["test_years"]),
                "history": hist.rename("detections"), "cells": cells}

    if det.empty:                                                 # no data was downloaded for this area
        return None
    w = det["weight_harm"] if det["weight_harm"].notna().any() else pd.Series(1.0, index=det.index)
    years = range(int(det["year"].min()) + 1, start.year)           # first year may be partial
    hist = pd.Series({y: float(w[det["acq_date"].between(_same_window(y, start),
                                                         _same_window(y, start) + pd.Timedelta(days=29))].sum())
                      for y in years}, name="detections")
    hist.index.name = "year"
    normal = float(hist.loc[hist.index > last_full_year - PROFILE_YEARS].mean())
    return {**base, "mode": "seasonal", "pred": normal,
            "p10": float(hist.quantile(0.1)), "p90": float(hist.quantile(0.9)),
            "normal": normal, "ratio": float("nan"),
            "label": "quiet season" if normal < 1 else "seasonal normal",
            "n_cells": 0, "skill": None, "direction_hit_rate": None, "backtest_years": None,
            "years_with_detections": int((hist > 0).sum()), "n_years": len(hist),
            "history": hist, "cells": cells}


# ---------------------------------------------------------------- quick check

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
