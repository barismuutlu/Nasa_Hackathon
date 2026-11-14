"""Uçtan uca duman testi — sahibi P4 Barış. Sözleşme: docs/CONTRACT.md v1.1

Çalıştır (repo kökünden):  python tests/smoke_test.py
Var olan pipeline çıktılarını sözleşmeye göre kontrol eder (olmayanlar "ATLANDI"),
sonra app/query.py API'sini o an seçili veri dosyasıyla uçtan uca dener.
Çıkış kodu: 0 = hepsi geçti, 1 = en az bir hata.
"""
from __future__ import annotations

import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))

from contract import COLUMNS, SCHEMA, validate_hotspots  # noqa: E402
import query  # noqa: E402

DATA = ROOT / "data"
results: list[tuple[str, str, str]] = []


def check(name: str):
    def deco(fn):
        try:
            msg = fn()
            results.append(("SKIP" if msg and msg.startswith("ATLANDI") else "PASS", name, msg or ""))
        except Exception as e:  # noqa: BLE001
            results.append(("FAIL", name, f"{type(e).__name__}: {e}"))
            traceback.print_exc()
        return fn
    return deco


def expect_error(fn) -> None:
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("ValueError bekleniyordu")


# ---------------------------------------------------------------- 1. doğrulayıcının kendisi

@check("contract: doğrulayıcı hatalı veriyi yakalıyor")
def _():
    df = query.load_hotspots().head(50).copy()
    expect_error(lambda: validate_hotspots(df.drop(columns=["latitude"]), "any"))
    expect_error(lambda: validate_hotspots(df.assign(weight_harm=np.float32(1.0)), "ingest"))
    bad = df.copy()
    bad["acq_time"] = bad["acq_time"] + 1
    expect_error(lambda: validate_hotspots(bad, "any"))  # datetime_utc artık tutmuyor


# ---------------------------------------------------------------- 2. pipeline çıktıları (varsa)

@check("P1 data/hotspots.parquet → sözleşme (ingest)")
def _():
    p = DATA / "hotspots.parquet"
    if not p.exists():
        return "ATLANDI (henüz yok)"
    df = pd.read_parquet(p)
    validate_hotspots(df, "ingest")
    key = df.assign(lat4=df.latitude.round(4), lon4=df.longitude.round(4))
    dups = key.duplicated(["satellite", "datetime_utc", "lat4", "lon4"]).sum()
    assert dups == 0, f"{dups} tekrar satır"
    return f"{len(df):,} satır"


@check("P1 data/satellite_coverage.csv sütunları")
def _():
    p = DATA / "satellite_coverage.csv"
    if not p.exists():
        return "ATLANDI (henüz yok)"
    need = {"satellite", "source", "first_date", "last_date", "n_rows", "nrt_cutoff", "n_nrt_dropped"}
    missing = need - set(pd.read_csv(p, nrows=0).columns)
    assert not missing, f"eksik: {missing}"


@check("P2 data/hotspots_harm.parquet → sözleşme (harm)")
def _():
    p = DATA / "hotspots_harm.parquet"
    if not p.exists():
        return "ATLANDI (henüz yok)"
    df = pd.read_parquet(p)
    validate_hotspots(df, "harm")
    src = DATA / "hotspots.parquet"
    if src.exists():
        n_src = len(pd.read_parquet(src, columns=["satellite"]))
        assert n_src == len(df), f"satır sayısı değişti: {n_src} → {len(df)}"
    return f"{len(df):,} satır, Σ weight_harm = {df.weight_harm.sum():,.0f}"


@check("P2 data/monthly_grid.parquet sütunları")
def _():
    p = DATA / "monthly_grid.parquet"
    if not p.exists():
        return "ATLANDI (henüz yok)"
    need = {"cell_lat", "cell_lon", "year", "month", "region", "n_terra", "n_aqua", "n_snpp",
            "n_noaa20", "n_noaa21", "n_modis", "n_viirs", "n_harm"}
    g = pd.read_parquet(p)
    missing = need - set(g.columns)
    assert not missing, f"eksik: {missing}"
    off = ((g.cell_lat - 0.125) / 0.25 % 1).abs().max()
    assert off < 1e-6, "cell_lat 0.25° hücre merkezi değil"


@check("P2 data/k_factors.csv sütunları")
def _():
    p = DATA / "k_factors.csv"
    if not p.exists():
        return "ATLANDI (henüz yok)"
    missing = {"k", "n_modis", "n_viirs", "fallback"} - set(pd.read_csv(p, nrows=0).columns)
    assert not missing, f"eksik: {missing}"


@check("P3 docs/validation/metrics.json alanları")
def _():
    p = ROOT / "docs" / "validation" / "metrics.json"
    if not p.exists():
        return "ATLANDI (henüz yok)"
    m = pd.read_json(p)
    missing = {"method", "region", "split", "scale", "r2", "bias", "bias_pct", "n"} - set(m.columns)
    assert not missing, f"eksik: {missing}"


# ---------------------------------------------------------------- 3. query.py uçtan uca

@check("query.data_info()")
def _():
    info = query.data_info()
    assert info["contract"] == "1.1"
    return f"{info['path']}  mock={info['is_mock']}  harm={info['has_harm']}  {info['n_rows']:,} satır"


@check("query.get_hotspots(PRESETS) → şema korunuyor")
def _():
    out = []
    for name in query.PRESETS:
        df = query.get_hotspots(name)
        assert list(df.columns) == COLUMNS, "sütun sırası/adları değişti"
        for col, (dtype, _) in SCHEMA.items():
            assert str(df[col].dtype) == dtype, f"{col}: {df[col].dtype} ≠ {dtype}"
        out.append(f"{name}={len(df):,}")
    return ", ".join(out)


@check("query: GeoJSON dikdörtgen == bbox, boş bölge çökmez")
def _():
    lo0, la0, lo1, la1 = query.PRESETS["Aachen/Eifel"]
    ring = [[lo0, la0], [lo1, la0], [lo1, la1], [lo0, la1], [lo0, la0]]
    gj = {"type": "Feature", "geometry": {"type": "Polygon", "coordinates": [ring]}}
    assert len(query.get_hotspots(gj)) == len(query.get_hotspots((lo0, la0, lo1, la1)))
    empty = query.get_hotspots((0.0, 0.0, 0.5, 0.5))
    m = query.monthly_matrix(empty)
    assert len(empty) == 0 and np.nanmax(m.to_numpy()) == 0
    assert query.anomaly(m, int(m.index[-2]), 6)["label"] == "tespit yok"


@check("query.monthly_matrix + anomaly (Hohes Venn)")
def _():
    df = query.get_hotspots("Hohes Venn")
    msgs = []
    for mode in ("raw", "harm"):
        m = query.monthly_matrix(df, mode)
        assert list(m.columns) == list(range(1, 13)) and m.index.name == "year"
        if mode == "harm" and not query.data_info()["has_harm"]:
            assert m.isna().all().all()
            msgs.append("harm=NaN (P2 öncesi, beklenen)")
            continue
        total = float(np.nansum(m.to_numpy()))
        expect = len(df) if mode == "raw" else float(df.weight_harm.sum())
        assert abs(total - expect) < 1e-3 * max(1, expect), f"{mode}: matris toplamı {total} ≠ {expect}"
        for y, mo in ((2011, 4), (2026, 8)):
            if y in m.index:
                a = query.anomaly(m, y, mo)
                assert set(a) == {"value", "mean", "std", "z", "rank", "n_years", "label"}
                msgs.append(f"{mode} {y}-{mo:02d}: {a['value']:.0f} ({a['label']})")
    return "; ".join(msgs)


@check("query.to_csv_bytes")
def _():
    m = query.monthly_matrix(query.get_hotspots("Hohes Venn"))
    b = query.to_csv_bytes(m)
    assert b.startswith(b"year,1,2,3"), b[:30]
    raw = query.to_csv_bytes(query.get_hotspots("Hohes Venn").head(5))
    assert raw.split(b"\n")[0].decode() == ",".join(COLUMNS)


# ---------------------------------------------------------------- rapor

if __name__ == "__main__":
    width = max(len(n) for _, n, _ in results)
    for status, name, msg in results:
        icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️ "}[status]
        print(f"{icon} {name.ljust(width)}  {msg}")
    n_fail = sum(s == "FAIL" for s, _, _ in results)
    print(f"\n{len(results) - n_fail}/{len(results)} geçti/atlandı, {n_fail} hata")
    sys.exit(1 if n_fail else 0)
