"""P3 — Harmonization validation (owner: Oğuzhan). Contract: docs/CONTRACT.md §7.3 (v1.2)

Run (from repo root):  python pipeline/validate.py

Question: how well does P2's weight_harm (VIIRS → MODIS-equivalent) predict the number of detections
MODIS actually counted, in years it did not see during training (test 2022–2024)?
  prediction = Σ weight_harm of the VIIRS rows within the cell-month
  truth      = number of MODIS (Terra+Aqua) rows in the same cell-month (n_modis)
  Only cell-months where at least one side is > 0. Scale: 0.25° and 1°.
Baseline: "raw_viirs" = raw VIIRS count (as if there were no harmonization).

Outputs (docs/validation/):
  metrics.json          [{"method","region","split","scale","r2","bias","bias_pct","n","data"}]
                        data = "mock" (synthetic) | "raw" (P1, not harmonized) | "harm" (P2) — v1.3
                        bias = mean(prediction − truth) [detections/cell-month]
                        bias_pct = (Σ prediction / Σ truth − 1) × 100  [%]
  pred_vs_true.png      test years, log-log scatter + 1:1
  annual_raw_vs_harm.png  Argentina annual raw / harmonized / MODIS
  venn_check.png        Hohes Venn year×month calendar (raw + harmonized), April 2011 & August 2026.
                        The result is stated not as z but as "highest April of N years, X times the mean"
                        (z grows meaninglessly large when the baseline is near zero).
  summary.md            short summary for the presentation (P6)

Input priority: $P3_INPUT → data/hotspots_harm.parquet (P2) → data/hotspots.parquet (P1, only raw
counts: harmonized metrics/lines are skipped) → data/mock/hotspots_mock.parquet (SYNTHETIC —
plots get a watermark, the results have no scientific value).

The test split is further divided by NOAA-21 (NOAA-21 started on 2023-03-01, NOT in training →
P2 uses a proxy k for it): "test_2022" (S-NPP + NOAA-20) and "test_2023-2024" (+ NOAA-21).
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

# ---------------------------------------------------------------- paths & constants
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
HARM_PATH = DATA / "hotspots_harm.parquet"
RAW_PATH = DATA / "hotspots.parquet"
GRID_PATH = DATA / "monthly_grid.parquet"
K_PATH = DATA / "k_factors.csv"
MOCK_PATH = DATA / "mock" / "hotspots_mock.parquet"
# P1 burned_area_check.py output (optional) — MCD64A1 supporting evidence, NOT a metric
BURN_PATH = Path(os.environ.get("P3_BURN", DATA / "burned_area_check.csv"))
BURN_STATUSES = {"burned_match", "unburned", "burned_other_time", "unknown", "no_data"}
BURN_GROUPS = {"venn_2011": (2011, 4), "venn_2026": (2026, 8)}
OUT = ROOT / "docs" / "validation"

TRAIN_YEARS = range(2012, 2022)   # 2012–2021 (P2 learns k from these)
TEST_YEARS = range(2022, 2025)    # 2022–2024
SPLITS = {"train": TRAIN_YEARS, "test": TEST_YEARS,
          "test_2022": range(2022, 2023),          # pre-NOAA-21
          "test_2023-2024": range(2023, 2025)}     # NOAA-21 active (satellite not in training)
# The transfer region never entered training (k only from Argentina) → all VIIRS years are out-of-sample.
# Aachen/Eifel has very few MODIS detections in 2022–2024 (n very small), hence an extra period:
TRANSFER_SPLIT = ("transfer_2012-2026", range(2012, 2027))
TRANSFER_REGIONS = {"aachen_eifel"}
# Only splits allowed by CONTRACT §7.3 are written to metrics.json (v1.4: transfer_2012-2026 approved).
JSON_SPLITS = set(SPLITS) | {TRANSFER_SPLIT[0]}
SCALES = {"0.25deg": 0.25, "1deg": 1.0}
# report regions → CONTRACT §5 region values (must match contract.REGIONS)
REPORT_REGIONS = {"argentina": ["argentina"], "aachen_eifel": ["aachen_eifel"]}
REGION_LABEL = {"argentina": "Argentina (training region)", "aachen_eifel": "Aachen/Eifel (transfer)"}
VENN_BOX = (5.95, 50.45, 6.25, 50.60)   # lon_min, lat_min, lon_max, lat_max
VENN_MONTHS = [(2011, 4), (2026, 8)]
VIIRS_LABEL = {"SNPP": "S-NPP", "NOAA20": "NOAA-20", "NOAA21": "NOAA-21"}
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
               "October", "November", "December"]
MONTH_ABBR = [m[:3] for m in MONTH_NAMES]
# query.anomaly() returns Turkish label values (P4 API) → English for our outputs
LABEL_EN = {"çok yüksek": "very high", "yüksek": "high", "normal": "normal", "düşük": "low",
            "tespit yok": "no detections", "veri yok": "no data"}
VISIBLE_RATIO = 3.0   # "visible" = that month's value is ≥ 3 times the mean of the same month in the other years

NEED_COLS = ["latitude", "longitude", "year", "month", "instrument", "satellite",
             "region", "weight_harm", "version"]

plt.rcParams.update({"font.size": 14, "axes.titlesize": 16, "axes.labelsize": 14,
                     "legend.fontsize": 12, "figure.dpi": 110})
CMAP = plt.get_cmap("viridis")


# ---------------------------------------------------------------- loading

def pick_input() -> Path:
    env = os.environ.get("P3_INPUT")
    if env:
        if not Path(env).exists():
            raise FileNotFoundError(f"P3_INPUT not found: {env}")
        return Path(env).resolve()
    for p in (HARM_PATH, RAW_PATH, MOCK_PATH):
        if p.exists():
            return p
    raise FileNotFoundError(f"No input: {HARM_PATH}, {RAW_PATH}, {MOCK_PATH}")


def load_input(path: Path) -> pd.DataFrame:
    import pyarrow.parquet as pq
    cols = pq.read_schema(path).names
    missing = [c for c in NEED_COLS if c not in cols]
    if missing:
        raise ValueError(f"{path}: missing columns {missing} (CONTRACT §1)")
    df = pd.read_parquet(path, columns=NEED_COLS)
    n_nan = int(df["weight_harm"].isna().sum())
    if 0 < n_nan < len(df):
        raise ValueError(f"{path}: weight_harm partly NaN ({n_nan:,}/{len(df):,}) — "
                         "must be either all NaN (P1) or no NaN at all (P2) (CONTRACT §6)")
    if (df["weight_harm"] < 0).any():
        raise ValueError(f"{path}: weight_harm has values < 0")
    bad = set(df["instrument"].astype(str)) - {"MODIS", "VIIRS"}
    if bad:
        raise ValueError(f"unexpected instrument: {bad}")
    have = set(df["region"].astype(str).unique())
    need = {r for regs in REPORT_REGIONS.values() for r in regs}
    if need - have:
        raise ValueError(f"{path}: report regions missing from data: {sorted(need - have)} "
                         f"(in data: {sorted(have)}) — CONTRACT §5")
    return df


def cell(x: pd.Series, size: float) -> pd.Series:
    """Cell center (CONTRACT §7.2 formula, same as monthly_grid for 0.25°)."""
    return np.floor(x / size) * size + size / 2


# ---------------------------------------------------------------- prediction vs truth

def cell_month_table(df: pd.DataFrame, size: float) -> pd.DataFrame:
    """Cell × month: true (n_modis), pred (VIIRS Σ weight_harm), raw_viirs (n_viirs)."""
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
                    continue   # Argentina 2012–2021 is training → transfer period meaningless
                sub = tab[tab.year.isin(years) & tab.region.isin(regs)]
                methods = (("harm", "pred"),) * has_harm + (("raw_viirs", "raw_viirs"),)
                for method, col in methods:
                    s = sub[(sub[col] > 0) | (sub.true > 0)]
                    m = metrics(s[col].to_numpy(float), s.true.to_numpy(float))
                    rows.append({"method": method, "region": rname, "split": split,
                                 "scale": scale, **m})
    return rows, tables


def crosscheck_grid(tab025: pd.DataFrame) -> str:
    """Does our own count match P2 monthly_grid.n_modis? (only if present)"""
    if not GRID_PATH.exists():
        return "monthly_grid.parquet missing — cross-check skipped"
    g = pd.read_parquet(GRID_PATH, columns=["year", "n_modis", "n_viirs"])
    mine = tab025.groupby("year")[["true", "raw_viirs"]].sum()
    theirs = g.groupby("year")[["n_modis", "n_viirs"]].sum()
    j = mine.join(theirs, how="outer").fillna(0)
    bad = j[(j.true != j.n_modis) | (j.raw_viirs != j.n_viirs)]
    if len(bad):
        raise ValueError(f"monthly_grid and hotspots_harm annual counts do not match:\n{bad}")
    return "monthly_grid.parquet consistent with annual n_modis/n_viirs ✓"


# ---------------------------------------------------------------- plots

def watermark(fig, is_mock: bool) -> None:
    if is_mock:
        fig.text(0.5, 0.5, "SYNTHETIC TEST DATA", ha="center", va="center", rotation=25,
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
               xlabel="Truth: MODIS detection count (+1)",
               ylabel=("Prediction: harmonized VIIRS Σ weight_harm (+1)" if has_harm
                       else "Raw VIIRS detection count (+1) — NOT harmonized"),
               title=f"{REGION_LABEL[rname]} — {years.start}–{years.stop - 1}")
        for axis in (ax.xaxis, ax.yaxis):
            axis.set_major_locator(matplotlib.ticker.LogLocator(subs=(1, 2, 5) if hi < 300 else (1,)))
            axis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
            axis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.legend(loc="lower right", fontsize=11, framealpha=0.9)   # upper left: large events are there
        ax.grid(alpha=0.3, which="both")
    fig.suptitle("Prediction vs truth per cell-month (MODIS-equivalent detection count)", fontsize=17)
    watermark(fig, is_mock)
    fig.tight_layout()
    fig.savefig(OUT / "pred_vs_true.png")
    plt.close(fig)


def plot_annual(df: pd.DataFrame, is_mock: bool, has_harm: bool) -> pd.DataFrame:
    a = df[df.region.astype(str) == "argentina"]
    is_modis = a["instrument"].astype(str).eq("MODIS")
    yearly = pd.DataFrame({
        "raw (all satellites)": a.groupby("year").size(),
        "MODIS only (Terra+Aqua)": a[is_modis].groupby("year").size(),
        "harmonized (Σ weight_harm)": a.groupby("year")["weight_harm"].sum(),
    }).fillna(0).sort_index()
    yearly.index = yearly.index.astype(int)
    if not has_harm:   # P1 data: harmonized line is not drawn
        yearly = yearly.drop(columns="harmonized (Σ weight_harm)")

    fig, ax = plt.subplots(figsize=(13, 6.5))
    styles = [dict(lw=2.5, ls="-", marker="o", ms=6), dict(lw=6, ls="-", marker="o", ms=9, alpha=0.6),
              dict(lw=2.5, ls="--", marker="o", ms=5)]   # MODIS thick/semi-transparent, harmonized dashed on top
    for i, col in enumerate(yearly.columns):
        ax.plot(yearly.index, yearly[col], color=CMAP([0.05, 0.45, 0.85][i]), label=col, **styles[i])
    ax.axvspan(TEST_YEARS.start - 0.5, TEST_YEARS.stop - 0.5, color="grey", alpha=0.15,
               label="test years (2022–2024)")
    top = yearly.to_numpy().max()
    # satellite start dates FROM THE DATA (not hard-coded; CONTRACT §3)
    first = df[df.instrument.astype(str) == "VIIRS"].groupby("satellite", observed=True)["year"].min()
    for sat, y0 in first.sort_values().items():
        y0 = int(y0)
        ax.axvline(y0, color="k", ls=":", lw=1)
        ax.text(y0 + 0.1, top * 0.97, f"{VIIRS_LABEL.get(str(sat), sat)}\n{y0}", fontsize=11, va="top")
    last = yearly.index.max()
    ax.text(last, 0, "partial year", fontsize=10, ha="center", va="bottom")
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.set(xlabel="Year", ylabel="Detections / year", ylim=(0, top * 1.05),
           title="Argentina — annual detections: raw vs harmonized vs MODIS")
    ax.legend(loc="center left", fontsize=11)
    ax.grid(alpha=0.3)
    watermark(fig, is_mock)
    fig.tight_layout()
    fig.savefig(OUT / "annual_raw_vs_harm.png")
    plt.close(fig)
    return yearly


def month_matrix(box: pd.DataFrame, values: pd.Series | None, ym_min, ym_max) -> pd.DataFrame:
    """Same rule as query.monthly_matrix (year × month; outside coverage NaN, no detection within coverage → 0),
    but without loading all the data into memory a second time (7M rows)."""
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
    """By box (not region). Anomaly/rank: same function as the app (query.anomaly)."""
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
    vmax = max(float(np.nanmax(np.log1p(mats[p].to_numpy()))) for p in panels)   # shared color scale
    titles = {"raw": "Raw (all satellites)", "harm": "Harmonized (MODIS-equivalent)",
              "modis": "MODIS only (Terra+Aqua)"}
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
                ax.annotate(f"{MONTH_NAMES[m - 1]} {y}: {r['value']:,.0f}\n{short_rank(r)}", (m, y),
                            xytext=(m - 5.5 if m > 6 else m + 0.8,
                                    y - 2.5 if y >= mat.index.max() - 1 else y), fontsize=12,
                            color="red", weight="bold", va="center",
                            arrowprops={"arrowstyle": "-", "color": "red"})
        ax.set_xticks(range(1, 13), MONTH_ABBR, fontsize=12)
        ax.set_title(titles[mode])
        ax.set_xlabel("Month")
    axes[0].set_ylabel("Year")
    fig.colorbar(im, ax=axes, label="log(1 + detection count) — same scale in both panels", shrink=0.8)
    fig.suptitle("Hohes Venn (lon 5.95–6.25, lat 50.45–50.60) — monthly detection calendar", fontsize=17)
    if burn is not None:
        parts = []
        for g, (y, m) in BURN_GROUPS.items():
            for inst, r in burn.loc[g].iterrows() if g in burn.index.get_level_values(0) else []:
                parts.append(f"{MONTH_NAMES[m - 1]} {y} {inst}: {r.burned_match:,}/{r.total:,}")
        fig.text(0.42, 0.005, "Detections on MCD64A1 burned-area pixels (3×3 px, ±16 days; supporting evidence, "
                 "not independent validation): " + " · ".join(parts), ha="center", va="top", fontsize=12)
    watermark(fig, is_mock)
    fig.savefig(OUT / "venn_check.png", bbox_inches="tight")
    plt.close(fig)
    return results


def ordinal(n: int) -> str:
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def short_rank(r: dict) -> str:
    """Plot label: '1st of 26 years, other years max 3'."""
    if r["rank"] is None:
        return LABEL_EN.get(r["label"], r["label"])
    tail = ("no detections in other years" if r["mean"] == 0
            else f"other years max {r['max_other']:.0f}")
    return f"{ordinal(r['rank'])} of {r['n_years']} years, {tail}"


def venn_text(y: int, m: int, a: dict, ratio: float, mode: str = "raw") -> str:
    """'highest April of 26 years, 12 times the mean' — instead of z (z is meaningless when the baseline is ~0)."""
    month = MONTH_NAMES[m - 1]
    if a["rank"] is None:
        return f"{month} {y}: {LABEL_EN.get(a['label'], a['label'])}"
    order = "highest" if a["rank"] == 1 else f"{ordinal(a['rank'])} highest"
    base = ("no detections in this month in any other year" if a["mean"] == 0
            else f"{ratio:,.0f} times the mean of the same month in other years (≈{a['mean']:.1f}), "
                 f"other years max {a['max_other']:.0f}")
    unit = {"harm": "MODIS-equivalent detections", "modis": "MODIS detections"}.get(mode, "detections")
    return f"{a['value']:,.0f} {unit} — {order} {month} of {a['n_years']} years; {base}"


def test_year_breakdown(df: pd.DataFrame, has_harm: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Test years region × year: Σ harm (VIIRS) / Σ MODIS. Also 2022 monthly (Argentina) —
    do the S-NPP 2022 Jul–Aug and Aqua 2022 Mar–Apr outages distort the ratio? (P2 request)"""
    t = df[df.year.isin(TEST_YEARS)]
    is_modis = t["instrument"].astype(str).eq("MODIS")
    key = [t["region"].astype(str).rename("region"), t["year"].astype(int).rename("year")]
    yearly = pd.DataFrame({
        "modis": is_modis.groupby(key).sum(),
        "harm": t["weight_harm"].where(~is_modis, 0).astype(float).groupby(key).sum(),
    })
    if not has_harm:
        yearly["harm"] = np.nan
    yearly["ratio"] = yearly.harm / yearly.modis.where(yearly.modis > 0)
    a = t[(t.region.astype(str) == "argentina") & (t.year == 2022)]
    am = a["instrument"].astype(str).eq("MODIS")
    sat = a.groupby(["month", "satellite"], observed=True).size().unstack(fill_value=0)
    monthly = pd.DataFrame({
        "modis": am.groupby(a["month"].astype(int)).sum(),
        "harm": a["weight_harm"].where(~am, 0).astype(float).groupby(a["month"].astype(int)).sum(),
    }).join(sat, how="left").reindex(range(1, 13)).fillna(0)
    if not has_harm:
        monthly["harm"] = np.nan
    monthly["ratio"] = monthly.harm / monthly.modis.where(monthly.modis > 0)
    return yearly, monthly


def transfer_without_event(tables: dict[str, pd.DataFrame], has_harm: bool) -> dict[str, tuple]:
    """Transfer metric with / without the Venn event (2026-08) — does R² come from a single event?"""
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
    """MCD64A1 match summary (group × instrument). None if absent. NOT an independent validation:
    the MCD64A1 algorithm also uses MODIS active fire data (P1 note) → only a summary/figure note."""
    if not BURN_PATH.exists():
        return None
    b = pd.read_csv(BURN_PATH, usecols=["group", "instrument", "status"])
    bad = set(b.status) - BURN_STATUSES
    if bad:
        raise ValueError(f"{BURN_PATH}: unexpected status {sorted(bad)}")
    badg = set(b.group) - set(BURN_GROUPS)
    if badg:
        raise ValueError(f"{BURN_PATH}: unexpected group {sorted(badg)}")
    t = b.groupby(["group", "instrument"]).status.value_counts().unstack(fill_value=0) \
         .reindex(columns=sorted(BURN_STATUSES), fill_value=0)
    t["total"] = t[sorted(BURN_STATUSES)].sum(axis=1)
    t["known"] = t.total - t.unknown - t.no_data   # "unknown" ≠ "unburned"
    return t


def ratio_diagnostics(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Argentina, raw data: MODIS / (VIIRS per active VIIRS satellite) — per year and 2022 monthly.
    Independent of harmonization: is the 2022 deviation (P2: harm/MODIS=1.18) due to an outage, orbital drift,
    or specific to the year? Active satellite = VIIRS satellite with ≥1 detection in that region in that month."""
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
    y["ratio"] = y.modis / y.viirs1
    y["aqua_terra"] = y.Aqua / y.Terra
    r = (c.modis / c.viirs1).unstack(level=1)
    m2022 = (r.loc[2022] / r.loc[TRAIN_YEARS.start:TRAIN_YEARS.stop - 1].median()) \
        if 2022 in r.index else pd.Series(dtype=float)
    return y, m2022


# ---------------------------------------------------------------- summary

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
        lines += ["> ℹ️ No harmonized data (P2) — raw counts only. harm metrics and presentation "
                  "sentences are produced once the P2 output is available.", ""]
    if is_mock:
        lines += ["> ⚠️ **SYNTHETIC TEST DATA** — these numbers have no scientific value, "
                  "pipeline test only.", ""]
    lines += ["# Validation summary", "", f"Input: `{rel(input_path)}`  ",
              f"{grid_note}  ", f"{k_note}", "",
              "## Test (cell-month, harmonized vs raw VIIRS)", "",
              "test = 2022–2024; test_2022 = before NOAA-21; test_2023-2024 = NOAA-21 active "
              "(satellite not in training); transfer_2012-2026 = all VIIRS years of Aachen/Eifel "
              "(the region never entered training).", "",
              "| region | period | scale | method | R² | bias (detections/cell-month) | bias % | n |",
              "|---|---|---|---|---|---|---|---|"]
    for r in sorted((r for r in rows if r["split"] != "train"),
                    key=lambda r: (r["region"], r["split"], r["scale"], r["method"])):
        lines.append(f"| {r['region']} | {r['split']} | {r['scale']} | {r['method']} | {fmt(r['r2'])} | "
                         f"{fmt(r['bias'])} | {fmt(r['bias_pct'], '+.1f')} | {r['n']} |")
    yearly, monthly = breakdown
    lines += ["", "## Test years one by one (Σ harmonized VIIRS / Σ MODIS; 1.00 = perfect)", "",
              "| region | year | Σ MODIS | Σ harm | ratio |", "|---|---|---|---|---|"]
    for (reg, yr), r in yearly.iterrows():
        lines.append(f"| {reg} | {yr} | {r.modis:.0f} | {fmt(r.harm, '.1f')} | {fmt(r.ratio)} |")
    sat_cols = [c for c in monthly.columns if c not in ("modis", "harm", "ratio")]
    lines += ["", "### Argentina 2022 monthly (S-NPP Jul–Aug, Aqua Mar–Apr outages)", "",
              "| month | Σ MODIS | Σ harm | ratio | " + " | ".join(map(str, sat_cols)) + " |",
              "|---|---|---|---|" + "---|" * len(sat_cols)]
    for mth, r in monthly.iterrows():
        lines.append(f"| {MONTH_NAMES[mth - 1]} | {r.modis:.0f} | {fmt(r.harm, '.1f')} | {fmt(r.ratio)} | "
                     + " | ".join(f"{r[c]:.0f}" for c in sat_cols) + " |")
    yr, m22 = diag
    tr = yr.loc[TRAIN_YEARS.start:TRAIN_YEARS.stop - 1, "ratio"]
    lines += ["", "## 2022 deviation — diagnosis from raw data (Argentina)", "",
              "ratio = MODIS / (VIIRS per active VIIRS satellite). Independent of harmonization. "
              f"Training-year range {tr.min():.3f}–{tr.max():.3f} (median {tr.median():.3f}).", "",
              "| year | MODIS | VIIRS/satellite | ratio | ratio / training median | Aqua/Terra |",
              "|---|---|---|---|---|---|"]
    for yy, r in yr.iterrows():
        lines.append(f"| {yy}{' (test)' if yy in TEST_YEARS else ''} | {r.modis:.0f} | {r.viirs1:.0f} | "
                     f"{r.ratio:.3f} | {r.ratio / tr.median():.2f} | {r.aqua_terra:.2f} |")
    if len(m22):
        lines += ["", "2022 monthly ratio / training median of the same month (< 1 → fewer MODIS than expected): "
                  + ", ".join(f"{MONTH_ABBR[k - 1]} {v:.2f}" for k, v in m22.items())]
    lines += ["", "## Hohes Venn (box lon 5.95–6.25, lat 50.45–50.60)", "",
              f"'Visible' = value > 0 and ≥ {VISIBLE_RATIO:.0f} times the mean of the same month in the other years.", "",
              "| series | month | result | visible |", "|---|---|---|---|"]
    for v in venn:
        lines.append(f"| {v['mode']} | {v['year']}-{v['month']:02d} | {v['text']} | "
                     f"{'yes' if v['visible'] else 'no'} |")
    if burn is not None:
        lines += ["", "### Supporting evidence: MCD64A1 burned area (P1, `data/burned_area_check.csv`)", "",
                  "Does the detection fall on a pixel (3×3 neighbourhood ≈ 1.4 km) that MCD64A1 (monthly burned "
                  "area, ~500 m) marks as burned within ±16 days? **Not an independent validation**: the MCD64A1 "
                  "algorithm also uses MODIS active fire data and can miss small burns. "
                  "'unknown' (unknown/no_data) ≠ 'unburned'.", "",
                  "| event | instrument | matched | unburned | burned at another time | unknown | total |",
                  "|---|---|---|---|---|---|---|"]
        for (g, inst), r in burn.iterrows():
            y, m = BURN_GROUPS[g]
            lines.append(f"| {MONTH_NAMES[m - 1]} {y} | {inst} | {r.burned_match} "
                         f"({r.burned_match / r.total:.0%}) | {r.unburned} | {r.burned_other_time} | "
                         f"{r.unknown + r.no_data} | {r.total} |")

    if not has_harm:
        text = "\n".join(lines) + "\n"
        (OUT / "summary.md").write_text(text, encoding="utf-8")
        return text
    ar, gb = get("harm", "argentina"), get("harm", "aachen_eifel", split=TRANSFER_SPLIT[0])
    ar22, ar23 = get("harm", "argentina", split="test_2022"), get("harm", "argentina", split="test_2023-2024")
    vh = {(v["year"], v["month"]): v for v in venn if v["mode"] == "harm"}
    venn_ok = all(v["visible"] for v in vh.values())
    lines += ["", "## 3 sentences for the presentation (P6)", "",
              f"1. In Argentina (training region), for the years 2022–2024 not used in training, the harmonized "
              f"VIIRS estimate predicts the MODIS detection count at 1° cell-month scale with R²={fmt(ar['r2'])} "
              f"and a total bias of {fmt(ar['bias_pct'], '+.1f')}%.",
              f"   In 2023–2024, when NOAA-21 (never seen in training) is also active: "
              f"R²={fmt(ar23['r2'])}, total bias {fmt(ar23['bias_pct'], '+.1f')}% "
              f"(2022, before NOAA-21: R²={fmt(ar22['r2'])}, {fmt(ar22['bias_pct'], '+.1f')}%).",
              f"2. Transferred unchanged to Aachen/Eifel (2012–2026), the same coefficients give R²={fmt(gb['r2'])}, "
              f"total bias {fmt(gb['bias_pct'], '+.1f')}% (n={gb['n']} cell-months)"
              + (f"; this R² comes largely from a single event (August 2026): excluding that month "
                 f"R²={fmt(tr_ev['1deg'][1]['r2'])}, bias {fmt(tr_ev['1deg'][1]['bias_pct'], '+.1f')}%."
                 if tr_ev and "1deg" in tr_ev else "."),
              f"3. In the Hohes Venn, detection increases coinciding with known fire events "
              + ("are visible in the harmonized calendar in April 2011 and August 2026"
                 if venn_ok else "are NOT clearly visible in the harmonized calendar in both months")
              + ": " + "; ".join(f"{MONTH_NAMES[m - 1]} {y} → {v['text']}"
                                  for (y, m), v in vh.items()) + "."]
    # ---- limitations (honest reporting; P2 + P4 request)
    vm = {(v["mode"], v["year"], v["month"]): v["value"] for v in venn}
    h26, m26 = vm.get(("harm", 2026, 8)), vm.get(("modis", 2026, 8))
    yearly, monthly = breakdown
    y22 = yearly.loc[("argentina", 2022), "ratio"] if ("argentina", 2022) in yearly.index else np.nan
    hi_m = [f"{MONTH_ABBR[k - 1]} {r.ratio:.2f}" for k, r in monthly.iterrows() if r.ratio >= 1.15]
    lo_m = [f"{MONTH_ABBR[k - 1]} {r.ratio:.2f}" for k, r in monthly.iterrows() if r.ratio < 1.15]
    t1 = (tr_ev or {}).get("1deg")
    lines += ["", "## Limitations and future work", "",
              f"- **2022 (test) over-estimation:** in Argentina Σharm/ΣMODIS = {fmt(y22)}. The excess is in the "
              f"fire season ({', '.join(hi_m)}); the other months, including outage months, are close to 1 "
              f"({', '.join(lo_m)}). In the raw data, too, the 2022 MODIS/VIIRS ratio lies outside the training "
              "range (diagnosis table above) → not explained by the S-NPP/Aqua outages or a persistent orbital "
              "drift (2023–2024 return to normal).",
              f"- **Aachen/Eifel August 2026 (region transfer, single event, small n):** harm/MODIS = "
              f"{fmt(h26 / m26 if h26 and m26 else np.nan)} ({fmt(h26, '.0f')} / {fmt(m26, '.0f')}). "
              "Not caused by the fallback (P2: even with the 40–50° band k it is +50%); the event's implied k is "
              "0.176, all training k values are ≥ 0.20."]
    if t1:
        a, b = t1
        lines.append(f"- **Transfer R² is driven by a single event:** Aachen/Eifel 1° R²={fmt(a['r2'])} "
                     f"(n={a['n']}, bias {fmt(a['bias_pct'], '+.1f')}%); excluding 2026-08 R²={fmt(b['r2'])}, "
                     f"bias {fmt(b['bias_pct'], '+.1f')}% (n={b['n']}). So in ordinary periods the total level "
                     "holds but the cell-month pattern is weak; the large event is over-estimated.")
    lines += ["- **Interpretation (hypothesis, not validated):** k depends on fire size — on a single large fire "
              "front VIIRS (375 m) counts disproportionately many pixels compared with MODIS (1 km); k is "
              "stratified only by latitude band × season × satellite, so it cannot capture this.",
              "- **Future work:** condition k on fire size (area / total FRP of the same-day cluster of "
              "neighbouring detections); a second training region in Europe for transfer.",
              f"- **Sample size:** Aachen/Eifel has only "
              f"{int(yearly.loc['aachen_eifel', 'modis'].sum()) if 'aachen_eifel' in yearly.index.get_level_values(0) else '—'}"
              " MODIS detections in 2022–2024 → the regional test metric is statistically meaningless; "
              "hence transfer_2012-2026 is reported."]
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
        print("⚠️  Running on SYNTHETIC data. Results are for pipeline testing only.\n")
    if not has_harm:
        print("ℹ️  weight_harm empty (P1 data) → raw counts only; harm metrics skipped.\n")
    print(f"Input: {rel(input_path)}  ({len(df):,} rows)")

    k_note = (f"k_factors.csv: {len(pd.read_csv(K_PATH))} rows. Confirmed by P2: k only from Argentina 2012–2021 "
              "VIIRS, Terra-only weight from 2003–2011 → test years (2022–2024) did not enter k."
              if K_PATH.exists() else "k_factors.csv missing")

    rows, tables = compute_metrics(df, has_harm)
    data_kind = "mock" if is_mock else ("harm" if has_harm else "raw")
    for r in rows:
        r["data"] = data_kind
    grid_note = crosscheck_grid(tables["0.25deg"]) if has_harm and not is_mock else \
        "monthly_grid cross-check skipped (synthetic or non-harmonized input)"
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
        print("⚠️  Low/negative R² (test, harm): " +
              ", ".join(f"{r['region']} {r['scale']} R²={fmt(r['r2'])}" for r in weak) +
              " — do not hide it, explain it honestly in the pitch.")
    print(f"Written: {', '.join(sorted(p.name for p in OUT.iterdir()))}")


if __name__ == "__main__":
    main()
