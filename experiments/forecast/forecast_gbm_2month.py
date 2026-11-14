"""Deneysel tespit aktivitesi görünümü (2 ay ileri) — sahibi P4 Barış. Sözleşme: docs/CONTRACT.md §7.5

Soru: harmonize (MODIS-eşdeğeri) aylık seriden, 1° hücre başına 2 ay sonraki tespit sayısı
"mevsim ortalaması"ndan daha iyi tahmin edilebilir mi?

Yöntem
- Veri: data/monthly_grid.parquet, sadece `argentina`, n_harm (Σ weight_harm) 1° hücreye toplanır.
  Aachen/Eifel'de veri çok seyrek → görünüm yok.
- Ufuk 2 ay: son tam ay T ise hedef T+2 (veri ayın ortasında biter, yarım ay kullanılmaz).
  Özellikler sadece hedeften ≥ 2 ay önceki bilgi: gecikmeler (2, 3, 4, 12, 24 ay, log1p),
  12 aylık hareketli ortalama, hücre × takvim ayı log-ortalaması (klimatoloji), ay, hücre konumu.
  SADECE NASA VERİSİ (yarışma kuralı): NASA dışı girdi (ör. NOAA ONI) eklenmez.
  0,25° hücre (16× satır) iyileştirmedi (14 Kas deneyi).
- İsteğe bağlı `--weather`: NASA POWER aylık hava (P1, pipeline/weather_power.py → data/weather_power.parquet).
  Hücre-ay klimatolojisine göre anomaliler, yine hedeften ≥ 2 ay önce: yağış (t-2, t-3, 3 ay toplamı),
  maks. sıcaklık ve nem (t-2). Kabul kuralı (Barış, 14 Kas): Arjantin test hatası %34'ün altına inmezse kullanılmaz.
- Model: HistGradientBoostingRegressor(loss="poisson") → beklenen sayı; bölge toplamı = Σ hücre.
- Test: eğitim hedefleri 2005–2021 (klimatoloji de sadece ≤2021), test 2022–2025.
  Karşılaştırma tabanı: mevsim ortalaması (aynı hücre-ayın eğitim yılları ortalaması).
- Final: tüm tam aylarla yeniden eğitilir, T+2 tahmin edilir. "normal" = aynı takvim ayının
  son 10 tam yıl ortalaması (seri azalan trendli, 2003'ten ortalama "normal"i şişirir).

Bu bir TESPİT sayısı görünümüdür, yangın tahmini değildir (CONTRACT §8). Doğrulanmış bir ürün değil.

Çıktılar
    data/deploy/forecast.parquet   hücre × hedef ay (git'e girer, query.forecast() okur)
    docs/forecast/metrics.json     test metrikleri
    docs/forecast/forecast_test.png  test dönemi aylık toplam: gerçek / model / mevsim ortalaması
    docs/forecast/summary.md

Çalıştır (repo kökünden):  python pipeline/forecast.py [--weather]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import r2_score

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "app"))
from query import PRESETS  # noqa: E402

GRID = ROOT / "data" / "monthly_grid.parquet"
COVERAGE = ROOT / "data" / "satellite_coverage.csv"
OUT = ROOT / "data" / "deploy" / "forecast.parquet"
DOCS = ROOT / "docs" / "forecast"
WEATHER = ROOT / "data" / "weather_power.parquet"   # P1, NASA POWER (isteğe bağlı)

REGION = "argentina"
FIRST_YEAR = 2003          # iki MODIS uydusu (Terra-only dönem hariç)
HORIZON = 2                # ay
LAGS = [HORIZON, HORIZON + 1, HORIZON + 2, 12, 24]
TRAIN_END = 2021           # P3 bölünmesiyle aynı
TEST_YEARS = (2022, 2025)
NORMAL_YEARS = 10
SUBREGION = ("la_rioja", PRESETS["La Rioja (AR)"])
FEATURES = ["cell_lat", "cell_lon", "month", *[f"lag{L}" for L in LAGS], "ma12", "clim"]
WEATHER_COLS = ["prec_mm", "tmax_c", "rh_pct"]
WEATHER_FEATURES = ["prec_a2", "prec_a3", "prec3_a", "tmax_a2", "rh_a2"]
ACCEPT_ERROR_PCT = 34      # --weather kabul kuralı (Barış, 14 Kas): Arjantin aylık toplam test hatası
MIN_DAYS = 25              # daha az geçerli günlü ay (ör. içinde bulunulan ay) hava verisi sayılmaz
MODEL_DESC = "HistGradientBoostingRegressor(loss='poisson', max_iter=300, learning_rate=0.05)"


def last_complete_month() -> pd.Period:
    """Bölgenin en son tespit tarihi ay sonu değilse önceki ay (yarım ay kullanılmaz)."""
    cov = pd.read_csv(COVERAGE, parse_dates=["last_date"])
    last = cov.loc[cov["region"] == REGION, "last_date"].max()
    p = last.to_period("M")
    return p if last == p.to_timestamp(how="end").normalize() else p - 1


def build_panel(last: pd.Period) -> pd.DataFrame:
    """1° hücre × ay, FIRST_YEAR-01 → last + HORIZON. Tam aylar dışı (yarım ay + hedef) n_harm NaN."""
    g = pd.read_parquet(GRID, columns=["cell_lat", "cell_lon", "year", "month", "region", "n_harm"])
    g = g[g["region"] == REGION]
    if g.empty or g["n_harm"].isna().any():
        raise ValueError(f"{GRID.name}: {REGION} boş ya da n_harm NaN — önce harmonize.py")
    g = g.assign(cell_lat=np.floor(g["cell_lat"]) + 0.5, cell_lon=np.floor(g["cell_lon"]) + 0.5)
    s = g.groupby(["cell_lat", "cell_lon", "year", "month"], as_index=False)["n_harm"].sum()

    months = pd.period_range(f"{FIRST_YEAR}-01", last + HORIZON, freq="M")
    cal = pd.DataFrame({"year": months.year.astype("int16"), "month": months.month.astype("int8")})
    cells = s[["cell_lat", "cell_lon"]].drop_duplicates()
    d = cells.merge(cal, how="cross").merge(s, how="left", on=["cell_lat", "cell_lon", "year", "month"])
    d["period"] = pd.PeriodIndex.from_fields(year=d["year"], month=d["month"], freq="M")
    full = d["period"] <= last
    d.loc[full, "n_harm"] = d.loc[full, "n_harm"].fillna(0.0)   # tam ayda tespit yok = 0
    d.loc[~full, "n_harm"] = np.nan                                 # yarım ay / gelecek
    return d.sort_values(["cell_lat", "cell_lon", "period"]).reset_index(drop=True)


def add_features(d: pd.DataFrame, clim_until: int) -> pd.DataFrame:
    """Hedeften ≥ HORIZON ay önceki bilgi. Klimatoloji sadece ≤ clim_until yıllarından (sızıntı yok)."""
    d = d.copy()
    d["ly"] = np.log1p(d["n_harm"])
    gp = d.groupby(["cell_lat", "cell_lon"], sort=False)["ly"]
    for L in LAGS:
        d[f"lag{L}"] = gp.shift(L)
    d["ma12"] = gp.transform(lambda x: x.shift(HORIZON).rolling(12).mean())
    clim = (d[d["year"] <= clim_until].groupby(["cell_lat", "cell_lon", "month"])["ly"].mean()
            .rename("clim").reset_index())
    clim_c = (d[d["year"] <= clim_until].groupby(["cell_lat", "cell_lon", "month"])["n_harm"].mean()
              .rename("clim_count").reset_index())
    return d.merge(clim, how="left").merge(clim_c, how="left")


def add_weather(d: pd.DataFrame, clim_until: int) -> pd.DataFrame:
    """NASA POWER anomalileri (hücre × takvim ayı ortalamasına göre), hedeften ≥ HORIZON ay önce."""
    w = pd.read_parquet(WEATHER)
    want = ["cell_lat", "cell_lon", "year", "month", *WEATHER_COLS, "n_days"]
    if list(w.columns) != want:
        raise ValueError(f"{WEATHER.name} sütunları {list(w.columns)} ≠ {want}")
    w = w.astype({"year": "int16", "month": "int8"})
    w.loc[w["n_days"] < MIN_DAYS, WEATHER_COLS] = np.nan
    missing = d[["cell_lat", "cell_lon"]].drop_duplicates().merge(
        w[["cell_lat", "cell_lon"]].drop_duplicates(), how="left", indicator=True)
    if (n := int((missing["_merge"] == "left_only").sum())):
        raise ValueError(f"{WEATHER.name}: {n} hücre için hava verisi yok")
    d = d.merge(w.drop(columns="n_days"), how="left", on=["cell_lat", "cell_lon", "year", "month"])
    clim = (d[d["year"] <= clim_until].groupby(["cell_lat", "cell_lon", "month"])[WEATHER_COLS].mean()
            .add_suffix("_clim").reset_index())
    d = d.merge(clim, how="left")
    for c in WEATHER_COLS:
        d[c + "_anom"] = d[c] - d[c + "_clim"]
    gp = d.groupby(["cell_lat", "cell_lon"], sort=False)
    d["prec_a2"] = gp["prec_mm_anom"].shift(HORIZON)
    d["prec_a3"] = gp["prec_mm_anom"].shift(HORIZON + 1)
    d["prec3_a"] = gp["prec_mm_anom"].transform(lambda x: x.shift(HORIZON).rolling(3).sum())
    d["tmax_a2"] = gp["tmax_c_anom"].shift(HORIZON)
    d["rh_a2"] = gp["rh_pct_anom"].shift(HORIZON)
    return d


def fit(train: pd.DataFrame, feats: list[str]) -> HistGradientBoostingRegressor:
    m = HistGradientBoostingRegressor(loss="poisson", max_iter=300, learning_rate=0.05, random_state=0)
    return m.fit(train[feats], train["n_harm"])


def in_box(df: pd.DataFrame, box) -> pd.Series:
    lon0, lat0, lon1, lat1 = box
    return df["cell_lon"].between(lon0, lon1) & df["cell_lat"].between(lat0, lat1)


def score(te: pd.DataFrame, col: str, scope: str, method: str) -> dict:
    """Hücre-ay (log1p) ve bölge aylık toplamı metrikleri."""
    tot = te.groupby("period")[["n_harm", col]].sum()
    row = {"scope": scope, "method": method,
           "test": f"{TEST_YEARS[0]}-{TEST_YEARS[1]}",
           "monthly_total_r2_log": float(r2_score(np.log1p(tot["n_harm"]), np.log1p(tot[col]))),
           "monthly_total_mae_pct": float((tot[col] - tot["n_harm"]).abs().sum() / tot["n_harm"].sum() * 100),
           "bias_pct": float((tot[col].sum() / tot["n_harm"].sum() - 1) * 100),
           "n_months": int(len(tot))}
    if scope == REGION:
        row["cell_r2_log"] = float(r2_score(te["ly"], np.log1p(te[col])))
        row["cell_mae_log"] = float(np.mean(np.abs(te["ly"] - np.log1p(te[col]))))
        row["n_cell_months"] = int(len(te))
    return row


def evaluate(panel: pd.DataFrame, feats: list[str]) -> tuple[list[dict], pd.DataFrame]:
    d = add_features(panel, clim_until=TRAIN_END)
    if feats != FEATURES:
        d = add_weather(d, clim_until=TRAIN_END)
    train = d[(d["year"] <= TRAIN_END) & d["lag24"].notna() & d["n_harm"].notna()]
    test = d[d["year"].between(*TEST_YEARS)].copy()
    if train["year"].max() >= TEST_YEARS[0]:
        raise ValueError("test yılları eğitime karıştı")
    test["model"] = fit(train, feats).predict(test[feats])
    rows = []
    for scope, mask in [(REGION, pd.Series(True, index=test.index)), (SUBREGION[0], in_box(test, SUBREGION[1]))]:
        for col, method in [("model", "model"), ("clim_count", "climatology")]:
            rows.append(score(test[mask], col, scope, method))
    return rows, test


def plot_test(test: pd.DataFrame, rows: list[dict]) -> None:
    fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
    for ax, (scope, mask) in zip(axes, [("Argentina", pd.Series(True, index=test.index)),
                                         ("La Rioja (preset box)", in_box(test, SUBREGION[1]))]):
        tot = test[mask].groupby("period")[["n_harm", "model", "clim_count"]].sum()
        x = tot.index.to_timestamp()
        ax.plot(x, tot["n_harm"], color="#222222", lw=2.2, label="Actual (harmonized, MODIS-eq.)")
        ax.plot(x, tot["model"], color="#21918c", lw=2, label="Model, 2 months ahead")
        ax.plot(x, tot["clim_count"], color="#888888", lw=2, ls="--", label="Seasonal average (baseline)")
        ax.set_yscale("log")
        ax.set_title(scope, loc="left", fontsize=13)
        ax.set_ylabel("Detections / month")
        ax.grid(alpha=0.3)
    axes[0].legend(loc="upper right", fontsize=10)
    a = {(r["scope"], r["method"]): r for r in rows}
    fig.suptitle("Experimental 2-month-ahead outlook — test 2022–2025 (not used in training)\n"
                 f"Argentina monthly total error: model {a[(REGION, 'model')]['monthly_total_mae_pct']:.0f}% "
                 f"vs seasonal average {a[(REGION, 'climatology')]['monthly_total_mae_pct']:.0f}%",
                 fontsize=13)
    fig.tight_layout()
    fig.savefig(DOCS / "forecast_test.png", dpi=130)
    plt.close(fig)


def final_forecast(panel: pd.DataFrame, last: pd.Period, feats: list[str]) -> pd.DataFrame:
    target = last + HORIZON
    clim_until = last.year - 1 if last.month < 12 else last.year
    d = add_features(panel, clim_until=clim_until)
    if feats != FEATURES:
        d = add_weather(d, clim_until=clim_until)
    train = d[d["lag24"].notna() & d["n_harm"].notna()]
    pred_rows = d[d["period"] == target].copy()
    if feats != FEATURES and pred_rows[WEATHER_FEATURES].isna().all(axis=1).any():
        raise ValueError(f"{target} için hava özelliği yok — weather_power.parquet {last}'i kapsamıyor mu?")
    pred_rows["pred"] = fit(train, feats).predict(pred_rows[feats])

    full_years = range(target.year - NORMAL_YEARS, target.year)   # hedef ayın son 10 tam yılı
    normal = (d[(d["month"] == target.month) & d["year"].isin(full_years)]
              .groupby(["cell_lat", "cell_lon"])["n_harm"].mean().rename("normal").reset_index())
    out = pred_rows.merge(normal, how="left")[["cell_lat", "cell_lon", "year", "month", "pred", "normal"]]
    out = out.assign(region=pd.array([REGION] * len(out), dtype="string"),
                     trained_through=pd.Timestamp(last.to_timestamp(how="end").normalize()).as_unit("ns"))
    out = out.astype({"cell_lat": "float64", "cell_lon": "float64", "year": "int16", "month": "int8",
                      "pred": "float64", "normal": "float64"})
    if out[["pred", "normal"]].isna().any().any() or (out["pred"] < 0).any():
        raise ValueError("forecast çıktısında NaN ya da negatif değer")
    return out.reset_index(drop=True)


def write_summary(rows: list[dict], out: pd.DataFrame, last: pd.Period, weather: bool,
                  weather_test: dict | None = None) -> None:
    a = {(r["scope"], r["method"]): r for r in rows}
    t = out[["year", "month"]].iloc[0]
    lr = out[in_box(out, SUBREGION[1])]
    lines = [
        "# Experimental 2-month-ahead detection outlook",
        "",
        f"Owner: P4 Barış · script: `pipeline/forecast.py` · data through {last} · target "
        f"**{int(t['year'])}-{int(t['month']):02d}**",
        "",
        "This is an outlook for **detection counts** (harmonized, MODIS-equivalent), not a fire forecast.",
        "",
        f"Test {TEST_YEARS[0]}–{TEST_YEARS[1]} (training targets 2005–{TRAIN_END}), Argentina, 1° cells:",
        "",
        "| Scope | Method | Monthly-total R² (log) | Monthly-total error | Bias | Cell R² (log) |",
        "|---|---|---|---|---|---|",
    ]
    for (scope, method), r in a.items():
        cell = f"{r['cell_r2_log']:.2f}" if "cell_r2_log" in r else "—"
        lines.append(f"| {scope} | {method} | {r['monthly_total_r2_log']:.2f} | "
                     f"{r['monthly_total_mae_pct']:.0f}% | {r['bias_pct']:+.1f}% | {cell} |")
    lines += [
        "",
        f"Outlook: Argentina Σ pred = {out['pred'].sum():,.0f} vs normal {out['normal'].sum():,.0f} "
        f"(last {NORMAL_YEARS} years, same month); La Rioja box Σ pred = {lr['pred'].sum():,.1f} "
        f"vs normal {lr['normal'].sum():,.1f}.",
        "",
        ("Inputs (NASA only): harmonized NASA FIRMS detection history + NASA POWER monthly weather "
         "(precipitation, max temperature, humidity anomalies). Limits: one region; skill over the seasonal average is modest at the "
         if weather else
         "Inputs (NASA only): harmonized NASA FIRMS detection history. Limits: no weather/drought inputs; one region; skill over the seasonal average is modest at the ")
        + "regional-total level and larger at the cell level. Harmonization coefficients are themselves an "
        "estimate (see docs/validation/).",
    ]
    if weather_test:
        lines += ["", f"NASA POWER weather (precipitation, max temperature, humidity anomalies) was tested: "
                  f"Argentina test error {weather_test['error_pct_firms_only']:.1f}% → "
                  f"{weather_test['error_pct_with_weather']:.1f}% with weather → "
                  f"{'accepted' if weather_test['accepted'] else 'not used'} "
                  f"(pre-set rule: accept only if error < {ACCEPT_ERROR_PCT}%)."]
    (DOCS / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_rows(rows: list[dict], tag: str) -> None:
    for r in rows:
        extra = f"  hücre R²(log)={r['cell_r2_log']:.3f}" if "cell_r2_log" in r else ""
        print(f"  [{tag}] test {r['scope']:10s} {r['method']:12s} aylık toplam R²(log)={r['monthly_total_r2_log']:.3f}"
              f"  hata={r['monthly_total_mae_pct']:.0f}%  sapma={r['bias_pct']:+.1f}%{extra}")


def main() -> None:
    weather = "--weather" in sys.argv[1:]
    if weather and not WEATHER.exists():
        raise FileNotFoundError(f"--weather: {WEATHER.relative_to(ROOT)} yok (P1: pipeline/weather_power.py)")
    feats = FEATURES + WEATHER_FEATURES if weather else FEATURES
    DOCS.mkdir(parents=True, exist_ok=True)
    last = last_complete_month()
    panel = build_panel(last)
    print(f"{REGION}: {panel[['cell_lat', 'cell_lon']].drop_duplicates().shape[0]} hücre (1°), "
          f"son tam ay {last}, hedef {last + HORIZON}")

    rows, test = evaluate(panel, FEATURES)
    print_rows(rows, "sadece FIRMS")
    weather_test = None
    if weather:
        base = (rows, test)
        base_err = rows[0]["monthly_total_mae_pct"]
        rows, test = evaluate(panel, feats)
        print_rows(rows, "FIRMS + POWER")
        err = rows[0]["monthly_total_mae_pct"]
        accepted = err < ACCEPT_ERROR_PCT
        print(f"  Arjantin hata %{base_err:.1f} → %{err:.1f}  (kabul eşiği < %{ACCEPT_ERROR_PCT}) → "
              + ("KABUL: hava özellikli model yazılıyor" if accepted else "RET: sadece FIRMS modeli yazılıyor"))
        weather_test = {"error_pct_firms_only": base_err, "error_pct_with_weather": err,
                        "accept_if_below_pct": ACCEPT_ERROR_PCT, "accepted": accepted,
                        "features": WEATHER_FEATURES}
        if not accepted:
            weather, feats = False, FEATURES
            rows, test = base
    plot_test(test, rows)

    out = final_forecast(panel, last, feats)
    out.to_parquet(OUT, engine="pyarrow", index=False)
    inputs = ["NASA FIRMS (harmonized monthly_grid)"] + (["NASA POWER (pipeline/weather_power.py)"] if weather else [])
    meta = {"region": REGION, "cell_deg": 1.0, "horizon_months": HORIZON,
            "trained_through": str(last), "target": str(last + HORIZON),
            "train_targets": f"2005-{TRAIN_END}", "model": MODEL_DESC, "inputs": inputs,
            "features": feats, "normal": f"same calendar month, last {NORMAL_YEARS} full years",
            "metrics": rows, "weather_test": weather_test}
    (DOCS / "metrics.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_summary(rows, out, last, weather, weather_test)
    print(f"→ {OUT.relative_to(ROOT)} ({len(out)} hücre, Σ pred={out['pred'].sum():,.0f}, "
          f"Σ normal={out['normal'].sum():,.0f}), docs/forecast/")


if __name__ == "__main__":
    main()
