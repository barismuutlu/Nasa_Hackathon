"""NASA verisinden El Niño göstergesi (Niño 3.4 yüzey sıcaklığı) — sahibi P4 Barış. DENEYSEL.

Neden: Arjantin'de El Niño / La Niña ile yangın aktivitesi arasındaki ilişki iklim literatüründe biliniyor
(El Niño → kuzeydoğuda yağışlı, La Niña → kurak). Görünüm modeli ileriye dönük bir iklim sinyaline ihtiyaç duyuyor.

SADECE NASA VERİSİ (yarışma kuralı): NASA POWER (NASA LaRC) daily point API, parametre TS =
MERRA-2 (NASA GMAO) Earth Skin Temperature; okyanusta deniz yüzeyi sıcaklığına karşılık gelir.
Niño 3.4 kutusu (5°K–5°G, 170°B–120°B) içinde 10 nokta: enlem ±2,5; boylam −167,5 … −127,5 (10° arayla).

Çıktı: data/deploy/enso_index.csv (küçük, git'e girer) — year, month, ts_c (10 noktanın aylık ortalaması, °C),
n_days (geçerli gün; içinde bulunulan ay kısmi). Anomali modelde, sadece geçmiş yıllara göre hesaplanır.
Ham yanıtlar: data/raw/power_enso/<lat>_<lon>.csv (git dışı; varsa tekrar indirilmez).

Çalıştır (repo kökünden):  python pipeline/enso_index.py
"""
from __future__ import annotations

import io
import time
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "power_enso"
OUT = ROOT / "data" / "deploy" / "enso_index.csv"

LATS = [-2.5, 2.5]
LONS = [-167.5, -157.5, -147.5, -137.5, -127.5]
START = "20020101"
URL = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=TS&community=RE"
       "&longitude={lon}&latitude={lat}&start={start}&end={end}&format=CSV")


def fetch(lat: float, lon: float, end: str) -> pd.DataFrame:
    path = RAW / f"{lat}_{lon}.csv"
    if not path.exists():
        url = URL.format(lat=lat, lon=lon, start=START, end=end)
        for attempt in range(3):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    path.write_bytes(r.read())
                break
            except OSError:
                if attempt == 2:
                    raise
                time.sleep(5)
    text = path.read_text(encoding="utf-8")
    if "-END HEADER-" not in text:
        raise ValueError(f"{path.name}: NASA POWER başlığı yok")
    df = pd.read_csv(io.StringIO(text.split("-END HEADER-", 1)[1].lstrip()))
    if list(df.columns) != ["YEAR", "MO", "DY", "TS"]:
        raise ValueError(f"{path.name}: beklenmeyen sütunlar {list(df.columns)}")
    df["TS"] = df["TS"].where(df["TS"] > -900)
    return df


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    end = date.today().strftime("%Y%m%d")
    days = []
    for lat in LATS:
        for lon in LONS:
            d = fetch(lat, lon, end)
            days.append(d.assign(lat=lat, lon=lon))
    d = pd.concat(days)
    daily = d.groupby(["YEAR", "MO", "DY"])["TS"].agg(["mean", "count"])
    daily = daily[daily["count"] == len(LATS) * len(LONS)]           # 10 noktanın hepsi geçerli olan günler
    m = daily.groupby(level=["YEAR", "MO"]).agg(ts_c=("mean", "mean"), n_days=("mean", "size")).reset_index()
    m = m.rename(columns={"YEAR": "year", "MO": "month"})
    m["ts_c"] = m["ts_c"].round(3)
    m.to_csv(OUT, index=False, lineterminator="\n")
    print(f"{len(LATS) * len(LONS)} nokta, {m['year'].min()}-{m['month'].iloc[0]:02d} → "
          f"{m['year'].iloc[-1]}-{m['month'].iloc[-1]:02d}, {len(m)} ay → {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
