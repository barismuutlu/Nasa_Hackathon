"""Streamlit Cloud için küçültülmüş veri üretir — sahibi P4 Barış.

Cloud'da data/hotspots*.parquet yok (git'e girmez, ~160 MB, bellek sınırı ~1 GB).
Bu script tam veriden sadece uygulamanın hazır bölgelerini (query.PRESETS) alır:
    data/deploy/hotspots_deploy.parquet   (git'e girer, query.py otomatik kullanır)

Kaynak önceliği query.py ile aynı: hotspots_harm.parquet (P2) varsa o, yoksa hotspots.parquet (P1).
Bahtiyar'ın harmonize verisi gelince bu script'i tekrar çalıştır → push → Cloud kendini günceller.

Çalıştır (repo kökünden):  python data/deploy/make_deploy.py
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "app"))
from contract import validate_hotspots  # noqa: E402
from query import PRESETS  # noqa: E402

SOURCES = [ROOT / "data" / "hotspots_harm.parquet", ROOT / "data" / "hotspots.parquet"]
OUT = ROOT / "data" / "deploy" / "hotspots_deploy.parquet"
MAX_MB = 50


def main() -> None:
    src = next((p for p in SOURCES if p.exists()), None)
    if src is None:
        raise FileNotFoundError("data/hotspots_harm.parquet ya da data/hotspots.parquet yok")
    df = pd.read_parquet(src)

    keep = pd.Series(False, index=df.index)
    for name, (lon0, lat0, lon1, lat1) in PRESETS.items():
        inside = df["longitude"].between(lon0, lon1) & df["latitude"].between(lat0, lat1)
        print(f"  {name:14s} {int(inside.sum()):>9,} satır")
        keep |= inside
    out = df.loc[keep].sort_values("datetime_utc").reset_index(drop=True)

    stage = "harm" if out["weight_harm"].notna().all() else "ingest"
    validate_hotspots(out, stage=stage)
    out.to_parquet(OUT, engine="pyarrow", compression="zstd", index=False)
    mb = OUT.stat().st_size / 1e6
    print(f"{src.name} → {OUT.relative_to(ROOT)}: {len(out):,} satır, {mb:.1f} MB, aşama={stage}")
    if mb > MAX_MB:
        raise ValueError(f"{mb:.0f} MB > {MAX_MB} MB — Cloud için çok büyük")


if __name__ == "__main__":
    main()
