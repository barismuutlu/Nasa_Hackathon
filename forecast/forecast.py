"""P2 — PROTOTİP: mevsimsel tespit görünümü (seasonal outlook). Sahibi: Bahtiyar. Ana pipeline'a bağlı DEĞİL.

Soru: Harmonize 26 yıllık takvim, önümüzdeki 12 ay için "beklenen tespit düzeyi" söyleyebilir mi?
Bu bir yangın tahmini DEĞİLDİR: hava durumu / yakıt nemi / tutuşma verisi yok. Sadece şunu kullanır:
  1) mevsimsellik  — hücrenin o takvim ayındaki tarihsel düzeyi (log1p ortalaması, "klimatoloji")
  2) kalıcılık     — son gözlenen ayın normalden sapması (hücre + bölge), öngörü ufku h'ye göre sönümlenir
Model (her ufuk h = 1..12 ay için ayrı, hücreler havuzlanmış EKK):
  log1p(y[c,t]) = klim[c, ay(t)] + a_h · sapma[c, t−h] + b_h · sapma_bölge[t−h] + hata
Birim: harmonize (MODIS-eşdeğeri) tespit / 1° hücre / ay. Harmonize seri şart: ham seride uydu sıçramaları
klimatolojiyi bozar.

Geriye dönük test (backtest): her test yılı Y için model sadece Y'den önceki yıllarla kurulur, Y'nin ayları
tahmin edilir; kıyas tabanı = sadece klimatoloji. Beceri = 1 − MSE_model / MSE_klimatoloji (log uzayı).
Beceri ≤ 0 ise model klimatolojiden iyi değildir ve öyle raporlanır.

Girdi : data/monthly_grid.parquet (P2 harmonize çıktısı)
Çıktı : forecast/out/outlook_cells.csv, outlook_region.csv, backtest.json, outlook_argentina.png
Çalıştırma (repo kökünden):  python forecast/forecast.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

GRID_PATH = Path("data/monthly_grid.parquet")
OUT = Path("forecast/out")
REGION = "argentina"
FIRST_YEAR = 2003            # Terra+Aqua tam yıl; öncesi Terra-only düzeltmeli dönem
TEST_YEARS = range(2015, 2026)
MAX_LEAD = 12
MIN_TOTAL = 200              # tüm dönemde bundan az harmonize tespiti olan 1° hücreler modele girmez
Q_LO, Q_HI = 0.10, 0.90


def load_matrix() -> tuple[pd.DataFrame, pd.Period]:
    """Satır = ay (Period), sütun = 1° hücre; değer = harmonize tespit. Son TAM ay ile biter."""
    g = pd.read_parquet(GRID_PATH)
    g = g[(g["region"] == REGION) & (g["year"] >= FIRST_YEAR)]
    g = g.assign(lat1=np.floor(g["cell_lat"]) + 0.5, lon1=np.floor(g["cell_lon"]) + 0.5,
                 t=pd.PeriodIndex.from_fields(year=g["year"], month=g["month"], freq="M"))
    m = g.pivot_table(index="t", columns=["lat1", "lon1"], values="n_harm", aggfunc="sum")
    last_full = m.index.max() - 1          # son ay kısmi (veri ayın ortasında bitiyor)
    idx = pd.period_range(f"{FIRST_YEAR}-01", last_full, freq="M")
    m = m.reindex(idx).fillna(0.0)         # ızgarada olmayan hücre-ay = 0 tespit
    return m.loc[:, m.sum() >= MIN_TOTAL], last_full


def climatology(logm: pd.DataFrame) -> pd.DataFrame:
    return logm.groupby(logm.index.month).mean()          # index = ay 1..12


def anomalies(logm: pd.DataFrame, clim: pd.DataFrame) -> pd.DataFrame:
    return logm - clim.reindex(logm.index.month).to_numpy()


def fit_lead(anom: pd.DataFrame, h: int) -> tuple[float, float]:
    """Havuzlanmış EKK: sapma[t] ~ a·sapma[t−h] + b·bölge_sapması[t−h] (sabit yok: sapmalar ~0 ortalamalı)."""
    y = anom.iloc[h:].to_numpy()
    x1 = anom.iloc[:-h].to_numpy()
    x2 = np.repeat(anom.iloc[:-h].mean(axis=1).to_numpy()[:, None], anom.shape[1], axis=1)
    X = np.column_stack([x1.ravel(), x2.ravel()])
    coef, *_ = np.linalg.lstsq(X, y.ravel(), rcond=None)
    return float(coef[0]), float(coef[1])


def backtest(m: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    logm = np.log1p(m)
    rows = []
    for year in TEST_YEARS:
        train = logm[logm.index.year < year]
        clim = climatology(train)
        an_all = anomalies(logm[logm.index.year <= year], clim)   # test ayının GEÇMİŞİ gerçek zamanda bilinir
        an_tr = an_all[an_all.index.year < year]
        test_idx = [t for t in an_all.index if t.year == year]
        for h in range(1, MAX_LEAD + 1):
            a, b = fit_lead(an_tr, h)
            for t in test_idx:
                src = an_all.loc[t - h]
                pred_an = a * src + b * src.mean()
                true_an = an_all.loc[t]
                # bölge toplamı (tespit biriminde) — klimatoloji ve model
                c_row = clim.loc[t.month]
                rows.append(dict(year=year, month=t.month, lead=h,
                                 se_model=float(((pred_an - true_an) ** 2).mean()),
                                 se_clim=float((true_an ** 2).mean()),
                                 reg_true=float(m.loc[t].sum()),
                                 reg_model=float(np.expm1(c_row + pred_an).clip(lower=0).sum()),
                                 reg_clim=float(np.expm1(c_row).sum())))
    bt = pd.DataFrame(rows)
    by_lead = bt.groupby("lead").agg(mse_model=("se_model", "mean"), mse_clim=("se_clim", "mean"))
    by_lead["skill"] = 1 - by_lead["mse_model"] / by_lead["mse_clim"]
    # bölge toplamı: log oran hatası → aralık için ampirik kantiller
    bt["reg_logerr"] = np.log((bt["reg_true"] + 1) / (bt["reg_model"] + 1))
    q = bt.groupby("lead")["reg_logerr"].quantile([Q_LO, Q_HI]).unstack()
    reg = bt.groupby("lead").apply(lambda d: pd.Series({
        "mae_model": float(np.abs(np.log((d.reg_true + 1) / (d.reg_model + 1))).mean()),
        "mae_clim": float(np.abs(np.log((d.reg_true + 1) / (d.reg_clim + 1))).mean())}), include_groups=False)
    summary = {
        "region": REGION, "unit": "harmonized (MODIS-equivalent) detections, 1deg cell-month, log1p",
        "train_from": FIRST_YEAR, "test_years": [TEST_YEARS.start, TEST_YEARS.stop - 1],
        "n_cells": int(m.shape[1]),
        "skill_by_lead": {int(k): round(float(v), 3) for k, v in by_lead["skill"].items()},
        "region_total_mae_log": {int(k): {"model": round(float(r.mae_model), 3), "climatology": round(float(r.mae_clim), 3)}
                                 for k, r in reg.iterrows()},
        "interval_logerr_q10_q90": {int(k): [round(float(r[Q_LO]), 3), round(float(r[Q_HI]), 3)] for k, r in q.iterrows()},
        "note": "skill = 1 - MSE_model/MSE_climatology; <= 0 means no better than climatology. "
                "Prototype: no weather/fuel/ignition inputs; not a fire prediction.",
    }
    return bt, summary


def outlook(m: pd.DataFrame, last_full: pd.Period, summary: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    logm = np.log1p(m)
    clim = climatology(logm)
    an = anomalies(logm, clim)
    src = an.loc[last_full]
    cells, region = [], []
    for h in range(1, MAX_LEAD + 1):
        t = last_full + h
        a, b = fit_lead(an, h)
        c_row = clim.loc[t.month]
        pred = np.expm1(c_row + a * src + b * src.mean()).clip(lower=0)
        base = np.expm1(c_row)
        lo, hi = summary["interval_logerr_q10_q90"][h]
        tot = float(pred.sum())
        region.append(dict(target=str(t), lead=h, expected=round(tot, 1), p10=round((tot + 1) * np.exp(lo) - 1, 1),
                           p90=round((tot + 1) * np.exp(hi) - 1, 1), climatology=round(float(base.sum()), 1),
                           ratio_to_normal=round(tot / float(base.sum()), 2)))
        for (lat, lon), v in pred.items():
            cells.append(dict(target=str(t), lead=h, cell_lat=lat, cell_lon=lon, expected=round(float(v), 2),
                              climatology=round(float(base[(lat, lon)]), 2)))
    return pd.DataFrame(cells), pd.DataFrame(region)


def plot(m: pd.DataFrame, reg: pd.DataFrame, summary: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    obs = m.sum(axis=1).iloc[-36:]
    x_obs = obs.index.to_timestamp()
    x_f = pd.PeriodIndex(reg["target"], freq="M").to_timestamp()
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 4.6), dpi=150, gridspec_kw={"width_ratios": [2.2, 1]})
    ax.plot(x_obs, obs.values / 1e3, color="#3b3834", lw=1.8, label="Observed (harmonized)")
    ax.fill_between(x_f, reg["p10"] / 1e3, reg["p90"] / 1e3, color="#d9742b", alpha=0.22, lw=0,
                    label="10–90% range (from backtest errors)")
    ax.plot(x_f, reg["expected"] / 1e3, color="#d9742b", lw=2.2, marker="o", ms=4, label="Outlook (expected)")
    ax.plot(x_f, reg["climatology"] / 1e3, color="#8a8984", lw=1.4, ls="--", label="Normal for the month")
    ax.axvline(x_obs[-1], color="#c3c2b7", lw=1)
    ax.set_ylabel("MODIS-equivalent detections / month (thousand)")
    ax.set_title("Argentina: 12-month detection outlook (prototype)", loc="left", fontsize=11)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    leads = sorted(summary["skill_by_lead"])
    sk = [summary["skill_by_lead"][h] for h in leads]
    ax2.bar(leads, sk, color=["#d9742b" if s > 0 else "#b8b5ad" for s in sk], width=0.7)
    ax2.axhline(0, color="#3b3834", lw=1)
    ax2.set_xlabel("Lead (months ahead)")
    ax2.set_ylabel("Skill vs. climatology (1 = perfect, 0 = none)")
    ax2.set_title(f"Backtest {summary['test_years'][0]}–{summary['test_years'][1]}", loc="left", fontsize=11)
    ax2.set_xticks(leads)
    for a_ in (ax, ax2):
        a_.spines[["top", "right"]].set_visible(False)
        a_.grid(axis="y", color="#ebeae6", lw=0.8)
        a_.set_axisbelow(True)
    fig.text(0.01, 0.01, "Source: NASA FIRMS MODIS C6.1 + VIIRS 375 m, harmonized (Method A). Seasonality + persistence only; "
             "no weather or fuel data. Not a fire prediction.", fontsize=7.5, color="#52514e")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / "outlook_argentina.png")


def main() -> None:
    if not GRID_PATH.exists():
        raise FileNotFoundError(f"{GRID_PATH} yok — önce: python pipeline/harmonize.py")
    OUT.mkdir(parents=True, exist_ok=True)
    m, last_full = load_matrix()
    print(f"{m.shape[1]} hücre (1°), {m.index[0]} → {last_full} (son tam ay)")
    bt, summary = backtest(m)
    cells, reg = outlook(m, last_full, summary)
    (OUT / "backtest.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    cells.to_csv(OUT / "outlook_cells.csv", index=False)
    reg.to_csv(OUT / "outlook_region.csv", index=False)
    plot(m, reg, summary)
    print("\nBeceri (1 − MSE_model/MSE_klim), ufka göre:", summary["skill_by_lead"])
    print("Bölge toplamı MAE (log):", {k: (v["model"], v["climatology"]) for k, v in summary["region_total_mae_log"].items()})
    print("\n== 12 aylık görünüm (bölge toplamı) ==")
    print(reg.to_string(index=False))


if __name__ == "__main__":
    main()
