"""P2 — PROTOTİP: 1 ay ileri tespit görünümü (one-month outlook). Sahibi: Bahtiyar. Ana pipeline'a bağlı DEĞİL.

Soru: Harmonize 26 yıllık takvim, GELECEK AY için "normalin altında / normal / üstünde" diyebilir mi?
Bu bir yangın tahmini DEĞİLDİR: hava durumu / kuraklık / yakıt nemi / tutuşma verisi yok. Kullandığı iki bilgi:
  1) mevsimsellik — hücrenin o takvim ayındaki tarihsel düzeyi (log1p ortalaması = "normal")
  2) kalıcılık    — son tam ayın normalden sapması (hücrenin kendisi + bölge ortalaması)
Model (hücreler havuzlanmış EKK, sabit yok):
  log1p(y[c, t]) = normal[c, ay(t)] + a · sapma[c, t−1] + b · sapma_bölge[t−1] + hata
Birim: harmonize (MODIS-eşdeğeri) tespit / 1° hücre / ay. Harmonize seri şart: ham seride 2012/2018/2023
uydu sıçramaları "normal"i bozar.

Neden sadece 1 ay: geriye dönük testte beceri 1 ayda ≈0.25, 2 ayda ≈0.13, 3+ ayda <0.1 (normalden farksız).

Geriye dönük test (2015–2025): her test yılı için model yalnız önceki yıllarla kurulur; kıyas = sadece normal.
  beceri   = 1 − MSE_model / MSE_normal (log uzayı; ≤ 0 → normalden iyi değil)
  yön isabeti = tahmin edilen sapmanın işareti gerçekleşenle aynı mı (şans = %50)

Girdi : data/monthly_grid.parquet (P2 harmonize çıktısı)
Çıktı : forecast/out/outlook_cells.csv, backtest.json, outlook_1month.png
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
MIN_TOTAL = 200              # tüm dönemde bundan az harmonize tespiti olan 1° hücreler modele girmez
BELOW, ABOVE = 0.67, 1.5     # beklenen / normal oranı: < 0.67 "below", > 1.5 "above", arası "near normal"
Q_LO, Q_HI = 0.10, 0.90


def load_matrix() -> tuple[pd.DataFrame, pd.Period, float]:
    """Satır = ay, sütun = 1° hücre, değer = harmonize tespit. Son TAM ay ile biter.
    Ayrıca hedef ayın (kısmi) şu ana kadarki bölge toplamını döndürür."""
    g = pd.read_parquet(GRID_PATH)
    g = g[(g["region"] == REGION) & (g["year"] >= FIRST_YEAR)]
    g = g.assign(lat1=np.floor(g["cell_lat"]) + 0.5, lon1=np.floor(g["cell_lon"]) + 0.5,
                 t=pd.PeriodIndex.from_fields(year=g["year"], month=g["month"], freq="M"))
    m = g.pivot_table(index="t", columns=["lat1", "lon1"], values="n_harm", aggfunc="sum")
    last_full = m.index.max() - 1          # son ay kısmi (veri ayın ortasında bitiyor)
    keep = m.loc[:last_full].sum() >= MIN_TOTAL
    partial = float(m.loc[last_full + 1, keep].sum())
    m = m.reindex(pd.period_range(f"{FIRST_YEAR}-01", last_full, freq="M")).fillna(0.0)
    return m.loc[:, keep], last_full, partial


def normal(logm: pd.DataFrame) -> pd.DataFrame:
    return logm.groupby(logm.index.month).mean()          # index = ay 1..12


def deviations(logm: pd.DataFrame, norm: pd.DataFrame) -> pd.DataFrame:
    return logm - norm.reindex(logm.index.month).to_numpy()


def fit(dev: pd.DataFrame) -> tuple[float, float]:
    y = dev.iloc[1:].to_numpy()
    x1 = dev.iloc[:-1].to_numpy()
    x2 = np.repeat(dev.iloc[:-1].mean(axis=1).to_numpy()[:, None], dev.shape[1], axis=1)
    coef, *_ = np.linalg.lstsq(np.column_stack([x1.ravel(), x2.ravel()]), y.ravel(), rcond=None)
    return float(coef[0]), float(coef[1])


def backtest(m: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    logm = np.log1p(m)
    rows = []
    for year in TEST_YEARS:
        norm = normal(logm[logm.index.year < year])
        dev = deviations(logm[logm.index.year <= year], norm)   # hedef ayın geçmişi gerçek zamanda bilinir
        a, b = fit(dev[dev.index.year < year])
        for t in (t for t in dev.index if t.year == year):
            src, true = dev.loc[t - 1], dev.loc[t]
            pred = a * src + b * src.mean()
            n_row = norm.loc[t.month]
            big = pred.abs() > 0.2                                # yön isabeti: sadece belirgin tahminler
            rows.append(dict(t=str(t), se_model=float(((pred - true) ** 2).mean()), se_norm=float((true ** 2).mean()),
                             hits=int((np.sign(pred[big]) == np.sign(true[big])).sum()), n_dir=int(big.sum()),
                             obs=float(m.loc[t].sum()), model=float(np.expm1(n_row + pred).clip(lower=0).sum()),
                             norm=float(np.expm1(n_row).sum())))
    bt = pd.DataFrame(rows)
    logerr = np.log((bt["obs"] + 1) / (bt["model"] + 1))
    summary = {
        "region": REGION, "lead_months": 1, "n_cells": int(m.shape[1]),
        "unit": "harmonized (MODIS-equivalent) detections per 1deg cell-month; errors in log1p space",
        "train_from": FIRST_YEAR, "test_years": [TEST_YEARS.start, TEST_YEARS.stop - 1], "n_test_months": len(bt),
        "skill_vs_normal": round(1 - bt["se_model"].mean() / bt["se_norm"].mean(), 3),
        "direction_hit_rate": round(bt["hits"].sum() / bt["n_dir"].sum(), 3),
        "direction_n": int(bt["n_dir"].sum()),
        "region_total_mae_log": {"model": round(float(np.abs(logerr).mean()), 3),
                                 "normal": round(float(np.abs(np.log((bt["obs"] + 1) / (bt["norm"] + 1))).mean()), 3)},
        "region_total_logerr_q10_q90": [round(float(logerr.quantile(Q_LO)), 3), round(float(logerr.quantile(Q_HI)), 3)],
        "note": "skill = 1 - MSE_model/MSE_normal; <= 0 means no better than the seasonal normal. Direction hit rate "
                "only for cells with |predicted deviation| > 0.2 (chance = 0.5). Prototype: seasonality + persistence "
                "only, no weather/drought/fuel inputs; not a fire prediction.",
    }
    return bt, summary


def outlook(m: pd.DataFrame, last_full: pd.Period, summary: dict) -> tuple[pd.DataFrame, dict]:
    logm = np.log1p(m)
    norm = normal(logm)
    dev = deviations(logm, norm)
    a, b = fit(dev)
    t = last_full + 1
    src = dev.loc[last_full]
    n_row = np.expm1(norm.loc[t.month])
    exp = np.expm1(norm.loc[t.month] + a * src + b * src.mean()).clip(lower=0)
    ratio = (exp + 1) / (n_row + 1)
    cells = pd.DataFrame({"target": str(t), "cell_lat": [c[0] for c in exp.index], "cell_lon": [c[1] for c in exp.index],
                          "expected": exp.round(2).to_numpy(), "normal": n_row.round(2).to_numpy(),
                          "ratio_to_normal": ratio.round(2).to_numpy()})
    cells["category"] = np.where(cells["ratio_to_normal"] < BELOW, "below normal",
                                 np.where(cells["ratio_to_normal"] > ABOVE, "above normal", "near normal"))
    lo, hi = summary["region_total_logerr_q10_q90"]
    tot = float(exp.sum())
    reg = dict(target=str(t), based_on=str(last_full), coef_cell=round(a, 3), coef_region=round(b, 3),
               expected=round(tot, 0), p10=round((tot + 1) * np.exp(lo) - 1, 0), p90=round((tot + 1) * np.exp(hi) - 1, 0),
               normal=round(float(n_row.sum()), 0), ratio_to_normal=round(tot / float(n_row.sum()), 2),
               cells=cells["category"].value_counts().to_dict())
    return cells, reg


def plot(cells: pd.DataFrame, reg: dict, bt: pd.DataFrame, summary: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.2), dpi=150, gridspec_kw={"width_ratios": [1, 2.3]})
    # sol: hücre haritası — beklenen / normal (iki uçlu: mavi = altında, gri = normal, kırmızı = üstünde)
    cmap = LinearSegmentedColormap.from_list("div", ["#2a6fb0", "#d9d6cf", "#c8320a"])
    sc = ax.scatter(cells["cell_lon"], cells["cell_lat"], c=np.log2(cells["ratio_to_normal"]).clip(-1.6, 1.6),
                    cmap=cmap, vmin=-1.6, vmax=1.6, marker="s", s=62, linewidths=0)
    ax.set_aspect(1.25)
    ax.set_xlabel("Longitude"), ax.set_ylabel("Latitude")
    ax.set_title(f"Outlook for {reg['target']}: expected vs. normal", loc="left", fontsize=11)
    cb = fig.colorbar(sc, ax=ax, shrink=0.75, ticks=[-1.585, -1, 0, 1, 1.585])
    cb.ax.set_yticklabels(["⅓×", "½×", "normal", "2×", "3×"])
    cb.outline.set_visible(False)
    # sağ: geriye dönük test — bölge toplamı, 1 ay önceden yapılan tahmin
    x = pd.PeriodIndex(bt["t"], freq="M").to_timestamp()
    ax2.plot(x, bt["obs"] / 1e3, color="#3b3834", lw=1.6, label="Observed (harmonized)")
    ax2.plot(x, bt["model"] / 1e3, color="#d9742b", lw=1.6, label="Outlook made one month earlier")
    ax2.plot(x, bt["norm"] / 1e3, color="#8a8984", lw=1.2, ls="--", label="Seasonal normal only")
    ax2.set_yscale("log")
    ax2.set_ylabel("MODIS-equivalent detections / month (thousand, log)")
    ax2.set_title(f"Backtest {summary['test_years'][0]}–{summary['test_years'][1]}: skill vs. normal "
                  f"{summary['skill_vs_normal']:.2f} · direction right {summary['direction_hit_rate']:.0%} "
                  "(chance 50%)", loc="left", fontsize=11)
    ax2.legend(frameon=False, fontsize=8.5, loc="upper left", ncols=3)
    for a_ in (ax, ax2):
        a_.spines[["top", "right"]].set_visible(False)
    ax2.grid(axis="y", color="#ebeae6", lw=0.8)
    ax2.set_axisbelow(True)
    fig.text(0.01, 0.01, "Source: NASA FIRMS MODIS C6.1 + VIIRS 375 m, harmonized (Method A), Argentina, 1° cells. "
             "Seasonality + last month's deviation only; no weather, drought or fuel data. Not a fire prediction.",
             fontsize=7.5, color="#52514e")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / "outlook_1month.png")


def main() -> None:
    if not GRID_PATH.exists():
        raise FileNotFoundError(f"{GRID_PATH} yok — önce: python pipeline/harmonize.py")
    OUT.mkdir(parents=True, exist_ok=True)
    for old in ("outlook_region.csv", "outlook_argentina.png"):      # 12 aylık ilk sürümün çıktıları
        (OUT / old).unlink(missing_ok=True)
    m, last_full, partial = load_matrix()
    print(f"{m.shape[1]} hücre (1°), {m.index[0]} → {last_full} (son tam ay)")
    bt, summary = backtest(m)
    cells, reg = outlook(m, last_full, summary)
    reg["observed_so_far_partial_month"] = round(partial, 0)
    summary["outlook"] = reg
    (OUT / "backtest.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    cells.to_csv(OUT / "outlook_cells.csv", index=False)
    plot(cells, reg, bt, summary)
    print(f"\nGeriye dönük test {summary['test_years']}: beceri {summary['skill_vs_normal']}, "
          f"yön isabeti {summary['direction_hit_rate']:.1%} (n={summary['direction_n']:,}), "
          f"bölge toplamı MAE(log) model {summary['region_total_mae_log']['model']} / normal {summary['region_total_mae_log']['normal']}")
    print(f"\n== Görünüm: {reg['target']} (dayanak: {reg['based_on']}) ==")
    print(f"beklenen {reg['expected']:,.0f}  (10–90%: {reg['p10']:,.0f} – {reg['p90']:,.0f}),  normal {reg['normal']:,.0f},  "
          f"oran {reg['ratio_to_normal']}")
    print(f"hücreler: {reg['cells']}   |   ayın şu ana kadarki gözlemi (kısmi): {partial:,.0f}")


if __name__ == "__main__":
    main()
