"""Experimental 30-day detection outlook — owner P4 Barış. Contract: docs/CONTRACT.md §7.5

Question: from the harmonized (MODIS-equivalent) detection history, will the detection level in a 1° cell
over the next 30 days be below or above normal?

Method (normal + persistence; adapted from P2 Bahtiyar's monthly prototype to a 30-day sliding window)
- Data: data/hotspots_harm.parquet, only `argentina`, daily Σ weight_harm, 1° cell (floor + 0.5).
- Target window W=30 days; the input window ends GAP=2 days before the target (the last NRT day may be incomplete).
- log1p(target) = normal[cell, window] + a · deviation[cell, input] + b · regional_deviation[input]
  normal = log1p mean of the same calendar window in past years; deviation = log1p(input) − the input's normal.
- Regional total: summing from the log scale gives a systematic underestimate (Argentina −24% in the backtest).
  So the model predicts a RATIO (Σ expected_geo / Σ normal_geo), and this ratio is multiplied by the
  arithmetic mean of the same window's totals over the last 10 years (test bias ≈ 0%).
- Backtest: 2015–2025, windows starting on the 15th of each month (132 start dates); each test year
  is fitted on earlier years only. Skill = 1 − MSE_model / MSE_normal (log), direction hit rate for |prediction| > 0.2.
- Range: 10%–90% quantiles of the regional-total log errors from the same backtest.
- NASA DATA ONLY. NASA POWER weather and a NASA MERRA-2 El Niño index were tried and did not improve it
  (branch p4/forecast-experiments, experiments/forecast/README.md).

This is an outlook for DETECTION counts, not a fire forecast (CONTRACT §8). Not a validated product.

Outputs
    data/deploy/forecast.parquet     live outlook per cell (committed to git, read by query.forecast())
    data/deploy/forecast_history.parquet  cell × past year: detections in the same 30-day window (for the chart)
    docs/forecast/metrics.json       test metrics + range quantiles
    docs/forecast/backtest.png       backtest: Argentina and La Rioja 30-day totals
    docs/forecast/backtest_dark.png  same, transparent background (the app's dark theme)
    docs/forecast/summary.md

Run (from the repo root):  python pipeline/forecast.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from sklearn.linear_model import LinearRegression

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from query import PRESETS  # noqa: E402

SRC = ROOT / "data" / "hotspots_harm.parquet"
OUT = ROOT / "data" / "deploy" / "forecast.parquet"
OUT_HIST = ROOT / "data" / "deploy" / "forecast_history.parquet"   # same window, past years (chart)
DOCS = ROOT / "docs" / "forecast"

REGION = "argentina"
DAY0 = pd.Timestamp("2003-01-01")      # both MODIS satellites (Terra-only period excluded)
W = 30                                 # days, target and input window
GAP = 2                                # days skipped between the end of the input window and the target start
ORIGIN_DAY = 15                        # backtest: the 15th of each month
TEST_YEARS = (2015, 2025)
NORMAL_YEARS = 10                      # arithmetic normal for scaling: last 10 full years
MIN_DEV = 0.2                          # "clear" prediction threshold for the direction hit rate (log)
SMALL_SELECTION = 100                  # selections with fewer cells use the (wider) La Rioja-scale range
LA_RIOJA = PRESETS["La Rioja (AR)"]
FEATURES = ["pdev", "rpdev"]


def load_daily() -> tuple[np.ndarray, pd.DataFrame, pd.Timestamp]:
    """Cell × day Σ weight_harm (cumulative). The last detection day may be incomplete in NRT → data_through = last day − 1."""
    t = pq.read_table(SRC, columns=["latitude", "longitude", "acq_date", "region", "weight_harm"],
                      filters=[("region", "=", REGION)]).to_pandas()
    if t.empty or t["weight_harm"].isna().any():
        raise ValueError(f"{SRC.name}: {REGION} boş ya da weight_harm NaN — önce harmonize.py")
    data_through = t["acq_date"].max() - pd.Timedelta(days=1)
    t = t[(t["acq_date"] >= DAY0) & (t["acq_date"] <= data_through)]
    t = t.assign(cell_lat=np.floor(t["latitude"]) + 0.5, cell_lon=np.floor(t["longitude"]) + 0.5,
                 di=(t["acq_date"] - DAY0).dt.days)
    cells = (t[["cell_lat", "cell_lon"]].drop_duplicates().sort_values(["cell_lat", "cell_lon"])
             .reset_index(drop=True))
    cells["ci"] = np.arange(len(cells))
    t = t.merge(cells, on=["cell_lat", "cell_lon"])
    n_days = (data_through - DAY0).days + 1
    daily = np.zeros((len(cells), n_days))
    np.add.at(daily, (t["ci"].to_numpy(), t["di"].to_numpy()), t["weight_harm"].to_numpy())
    cum = np.concatenate([np.zeros((len(cells), 1)), daily.cumsum(axis=1)], axis=1)
    return cum, cells, data_through


def window_sum(cum: np.ndarray, start: pd.Timestamp) -> np.ndarray | None:
    """Sum over days [start, start + W), per cell; None if outside the data coverage."""
    s = (start - DAY0).days
    if s < 0 or s + W > cum.shape[1] - 1:
        return None
    return cum[:, s + W] - cum[:, s]


def windows(cum: np.ndarray, cells: pd.DataFrame, starts: list[tuple[int, int, pd.Timestamp]]) -> pd.DataFrame:
    """Per-cell input and target window totals for each (year, key, target start)."""
    rows = []
    for year, key, start in starts:
        prev = window_sum(cum, start - pd.Timedelta(days=GAP + W))
        if prev is None:
            continue
        nxt = window_sum(cum, start)
        rows.append(pd.DataFrame({"ci": cells["ci"], "year": year, "key": key, "prev": prev,
                                  "next": np.nan if nxt is None else nxt}))
    return pd.concat(rows, ignore_index=True)


def add_deviations(d: pd.DataFrame, hist: pd.DataFrame) -> pd.DataFrame:
    """Normals only from `hist` rows (no leakage); deviations on the log1p scale."""
    hist = hist.assign(lp=np.log1p(hist["prev"]), ln=np.log1p(hist["next"]))
    norms = hist.groupby(["ci", "key"]).agg(nn=("ln", "mean"), pn=("lp", "mean"))
    d = d.join(norms, on=["ci", "key"])
    d["dev"] = np.log1p(d["next"]) - d["nn"]
    d["pdev"] = np.log1p(d["prev"]) - d["pn"]
    d["rpdev"] = d.groupby(["year", "key"])["pdev"].transform("mean")
    return d


def arith_normal(d_all: pd.DataFrame, year: int) -> pd.Series:
    """(ci, key) → mean of the same window's totals over the last NORMAL_YEARS years."""
    h = d_all[d_all["year"].between(year - NORMAL_YEARS, year - 1) & d_all["next"].notna()]
    return h.groupby(["ci", "key"])["next"].mean().rename("anorm")


def origin_starts(data_through: pd.Timestamp) -> list[tuple[int, int, pd.Timestamp]]:
    return [(y, m, pd.Timestamp(y, m, ORIGIN_DAY)) for y in range(DAY0.year, data_through.year + 1)
            for m in range(1, 13)]


def backtest(cum: np.ndarray, cells: pd.DataFrame, data_through: pd.Timestamp) -> tuple[dict, pd.DataFrame]:
    d_all = windows(cum, cells, origin_starts(data_through)).merge(
        cells[["ci", "cell_lat", "cell_lon"]], on="ci")
    d_all["la_rioja"] = (d_all["cell_lon"].between(LA_RIOJA[0], LA_RIOJA[2])
                         & d_all["cell_lat"].between(LA_RIOJA[1], LA_RIOJA[3]))
    se_m = se_n = 0.0
    hits = n_dir = 0
    yearly, totals = {}, []
    for year in range(TEST_YEARS[0], TEST_YEARS[1] + 1):
        hist = d_all[(d_all["year"] < year) & d_all["next"].notna()]
        d = add_deviations(d_all[d_all["year"] <= year], hist).dropna(subset=FEATURES + ["nn", "dev"])
        train, test = d[d["year"] < year], d[d["year"] == year].copy()
        if train["year"].max() >= year:
            raise ValueError("test yılı eğitime karıştı")
        p = LinearRegression().fit(train[FEATURES], train["dev"]).predict(test[FEATURES])
        sm, sn = float(((test["dev"] - p) ** 2).sum()), float((test["dev"] ** 2).sum())
        se_m, se_n = se_m + sm, se_n + sn
        yearly[year] = round(1 - sm / sn, 3)
        big = np.abs(p) > MIN_DEV
        hits += int((np.sign(p[big]) == np.sign(test["dev"].to_numpy()[big])).sum())
        n_dir += int(big.sum())
        test["egeo"], test["ngeo"] = np.expm1(np.maximum(test["nn"] + p, 0.0)), np.expm1(test["nn"])   # count ≥ 0
        test = test.join(arith_normal(d_all, year), on=["ci", "key"])
        for scope, mask in [("argentina", test.index), ("la_rioja", test.index[test["la_rioja"]])]:
            g = test.loc[mask].groupby(["year", "key"])[["next", "egeo", "ngeo", "anorm"]].sum()
            g["pred"] = g["egeo"] / g["ngeo"] * g["anorm"]
            totals.append(g.assign(scope=scope))
    tot = pd.concat(totals).reset_index()

    metrics = {"skill_vs_normal": round(1 - se_m / se_n, 3),
               "direction_hit_rate": round(hits / n_dir, 3), "direction_n": n_dir,
               "yearly_skill": yearly, "test_years": list(TEST_YEARS),
               "n_origins": int(tot[["year", "key"]].drop_duplicates().shape[0]), "scopes": {}}
    for scope, g in tot.groupby("scope"):
        err = np.log1p(g["next"]) - np.log1p(g["pred"])
        metrics["scopes"][scope] = {
            "total_bias_pct": round(float((g["pred"].sum() / g["next"].sum() - 1) * 100), 1),
            "total_mae_log_model": round(float(np.abs(err).mean()), 3),
            "total_mae_log_normal": round(float(np.abs(np.log1p(g["next"]) - np.log1p(g["anorm"])).mean()), 3),
            "err_log_p10": round(float(err.quantile(0.1)), 3),
            "err_log_p90": round(float(err.quantile(0.9)), 3),
        }
    return metrics, tot


def plot_backtest(tot: pd.DataFrame, metrics: dict) -> None:
    """backtest.png (light background, README) + backtest_dark.png (transparent background, light text; the app's dark theme)."""
    for fname, fg, actual, grid, transparent in [("backtest.png", "#222222", "#222222", "#cccccc", False),
                                                  ("backtest_dark.png", "#e8e6e3", "#f2f2f2", "#555555", True)]:
        with plt.rc_context({"text.color": fg, "axes.labelcolor": fg, "xtick.color": fg, "ytick.color": fg,
                             "axes.edgecolor": fg}):
            fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
            for ax, (scope, title) in zip(axes, [("argentina", "Argentina"), ("la_rioja", "La Rioja (preset box)")]):
                g = tot[tot["scope"] == scope].sort_values(["year", "key"])
                x = pd.to_datetime(pd.DataFrame({"year": g["year"], "month": g["key"], "day": ORIGIN_DAY}))
                ax.plot(x, g["next"], color=actual, lw=2.2, label="Actual (harmonized, MODIS-eq.)")
                ax.plot(x, g["pred"], color="#21918c", lw=2, label="Outlook (next 30 days)")
                ax.plot(x, g["anorm"], color="#888888", lw=2, ls="--", label="Normal (10-year average)")
                ax.set_yscale("log")
                ax.set_title(title, loc="left", fontsize=13)
                ax.set_ylabel("Detections / 30 days")
                ax.grid(alpha=0.3, color=grid)
                if transparent:
                    ax.set_facecolor("none")
            leg = axes[0].legend(loc="upper right", fontsize=10)
            if transparent:
                leg.get_frame().set_facecolor("#222222")
                leg.get_frame().set_edgecolor("#555555")
            fig.suptitle(f"Experimental 30-day outlook — backtest {TEST_YEARS[0]}–{TEST_YEARS[1]} "
                         f"({metrics['n_origins']} start dates, each year fitted on earlier years only)\n"
                         f"Direction right {metrics['direction_hit_rate']:.0%} (chance 50%) · "
                         f"skill vs. normal {metrics['skill_vs_normal']:.2f}", fontsize=13)
            fig.tight_layout()
            fig.savefig(DOCS / fname, dpi=130, transparent=transparent)
            plt.close(fig)


def same_window(year: int, start: pd.Timestamp) -> pd.Timestamp:
    try:
        return start.replace(year=year)
    except ValueError:                                  # 29 February
        return start.replace(year=year, day=28)


def live_outlook(cum: np.ndarray, cells: pd.DataFrame,
                 data_through: pd.Timestamp) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Target: data_through + GAP + 1 → +W days. Normals from the same calendar window in past years."""
    start = data_through + pd.Timedelta(days=GAP + 1)
    end = start + pd.Timedelta(days=W - 1)
    tr = windows(cum, cells, origin_starts(data_through))
    tr = add_deviations(tr, tr[tr["next"].notna()]).dropna(subset=FEATURES + ["nn", "dev"])
    model = LinearRegression().fit(tr[FEATURES], tr["dev"])
    cal = windows(cum, cells, [(y, 0, same_window(y, start)) for y in range(DAY0.year + 1, start.year + 1)])
    hist = cal[(cal["year"] < start.year) & cal["next"].notna()]
    live = add_deviations(cal[cal["year"] == start.year].copy(), hist)
    if live[["pdev", "nn"]].isna().any().any():
        raise ValueError("canlı pencere için normal ya da girdi eksik")
    live["expected_geo"] = np.expm1(np.maximum(live["nn"] + model.predict(live[FEATURES]), 0.0))   # count ≥ 0
    live["normal_geo"] = np.expm1(live["nn"])
    anorm = hist[hist["year"] >= start.year - NORMAL_YEARS].groupby("ci")["next"].mean().rename("normal")
    out = live.join(anorm, on="ci").merge(cells, on="ci")
    out = out.assign(start=start.as_unit("ns"), end=end.as_unit("ns"), data_through=data_through.as_unit("ns"),
                     region=pd.array([REGION] * len(out), dtype="string"))
    out = out[["cell_lat", "cell_lon", "start", "end", "expected_geo", "normal_geo", "normal", "region",
               "data_through"]]
    out = out.astype({"cell_lat": "float64", "cell_lon": "float64", "expected_geo": "float64",
                      "normal_geo": "float64", "normal": "float64"})
    if out[["expected_geo", "normal_geo", "normal"]].isna().any().any() or (out["expected_geo"] < 0).any():
        raise ValueError("görünüm çıktısında NaN ya da negatif değer")
    print(f"  model: hücre sapması katsayısı {model.coef_[0]:.3f}, bölge sapması {model.coef_[1]:.3f}")
    past = hist.merge(cells, on="ci")[["cell_lat", "cell_lon", "year", "next"]].rename(columns={"next": "detections"})
    past = past.astype({"cell_lat": "float64", "cell_lon": "float64", "year": "int16", "detections": "float64"})
    return out.reset_index(drop=True), past.reset_index(drop=True)


def region_summary(out: pd.DataFrame, metrics: dict, mask) -> dict:
    """Same computation as query.forecast() (ratio × arithmetic normal, range from test-error quantiles)."""
    s = out.loc[mask]
    ratio = s["expected_geo"].sum() / s["normal_geo"].sum()
    pred = ratio * s["normal"].sum()
    sc = metrics["scopes"]["la_rioja" if len(s) < SMALL_SELECTION else "argentina"]
    return {"pred": pred, "normal": float(s["normal"].sum()), "ratio": ratio,
            "p10": float(np.expm1(np.log1p(pred) + sc["err_log_p10"])),
            "p90": float(np.expm1(np.log1p(pred) + sc["err_log_p90"]))}


def write_summary(metrics: dict, out: pd.DataFrame) -> None:
    start, end = out["start"].iloc[0].date(), out["end"].iloc[0].date()
    lr = (out["cell_lon"].between(LA_RIOJA[0], LA_RIOJA[2]) & out["cell_lat"].between(LA_RIOJA[1], LA_RIOJA[3]))
    ys = metrics["yearly_skill"].values()
    lines = [
        "# Experimental 30-day detection outlook",
        "",
        f"Owner: P4 Barış (method: P2 Bahtiyar) · `pipeline/forecast.py` · data through "
        f"{out['data_through'].iloc[0].date()} · outlook window **{start} → {end}**",
        "",
        "Outlook for **detection counts** (harmonized NASA FIRMS, MODIS-equivalent) — not a fire forecast.",
        "",
        f"Backtest {TEST_YEARS[0]}–{TEST_YEARS[1]}, Argentina 1° cells, {metrics['n_origins']} start dates "
        "(each year fitted on earlier years only):",
        f"- direction right **{metrics['direction_hit_rate']:.0%}** (chance 50%, n={metrics['direction_n']:,})",
        f"- skill vs. seasonal normal **{metrics['skill_vs_normal']:.2f}** (1 − MSE ratio, log scale); "
        f"positive in every year ({min(ys):.2f}–{max(ys):.2f})",
    ]
    for scope, m in metrics["scopes"].items():
        lines.append(f"- {scope} 30-day total: bias {m['total_bias_pct']:+.1f}%, error (log) "
                     f"{m['total_mae_log_model']:.2f} vs {m['total_mae_log_normal']:.2f} for the normal")
    lines += ["", "| Outlook | Expected | 80% range | Normal (10-yr avg) | Ratio |", "|---|---|---|---|---|"]
    for name, mask in [("Argentina", out.index), ("La Rioja box", out.index[lr])]:
        r = region_summary(out, metrics, mask)
        lines.append(f"| {name} | {r['pred']:,.0f} | {r['p10']:,.0f}–{r['p90']:,.0f} | {r['normal']:,.0f} | "
                     f"{r['ratio']:.2f}× |")
    lines += ["", "Inputs: NASA FIRMS only. NASA POWER weather and a NASA MERRA-2 El Niño index were tested and did "
              "not improve skill (branch `p4/forecast-experiments`).",
              "", "Data: NASA FIRMS (MODIS C6.1, VIIRS 375 m). Citations and licenses: README → "
              "\"Sources, citations and licenses\"."]
    (DOCS / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    cum, cells, data_through = load_daily()
    print(f"{REGION}: {len(cells)} hücre (1°), veri {DAY0.date()} → {data_through.date()}")
    metrics, tot = backtest(cum, cells, data_through)
    print(f"  test {TEST_YEARS}: beceri {metrics['skill_vs_normal']}, yön %{100 * metrics['direction_hit_rate']:.1f}"
          f" (n={metrics['direction_n']:,}), {metrics['n_origins']} başlangıç")
    for s, m in metrics["scopes"].items():
        print(f"  {s:10s} toplam sapma {m['total_bias_pct']:+.1f}%  hata(log) {m['total_mae_log_model']} "
              f"/ normal {m['total_mae_log_normal']}  aralık log [{m['err_log_p10']}, {m['err_log_p90']}]")
    plot_backtest(tot, metrics)
    out, past = live_outlook(cum, cells, data_through)
    out.to_parquet(OUT, engine="pyarrow", index=False)
    past.to_parquet(OUT_HIST, engine="pyarrow", index=False)
    meta = {"region": REGION, "cell_deg": 1.0, "window_days": W, "gap_days": GAP,
            "data_through": str(data_through.date()), "start": str(out["start"].iloc[0].date()),
            "end": str(out["end"].iloc[0].date()), "inputs": ["NASA FIRMS (harmonized)"],
            "method": "log1p(target) = normal + a·cell deviation + b·regional deviation (LinearRegression); "
                      "regional total = ratio to normal × 10-year arithmetic normal",
            "small_selection_cells": SMALL_SELECTION, **metrics}
    (DOCS / "metrics.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_summary(metrics, out)
    r = region_summary(out, metrics, out.index)
    print(f"→ {OUT.relative_to(ROOT)}: {meta['start']} → {meta['end']}, Arjantin beklenen {r['pred']:,.0f} "
          f"({r['p10']:,.0f}–{r['p90']:,.0f}), normal {r['normal']:,.0f}")


if __name__ == "__main__":
    main()
