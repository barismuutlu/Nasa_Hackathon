"""Sahte FIRMS verisi üretir (kök CLAUDE.md §3.1 şeması) — sahibi P4 Barış.

Amaç: gerçek veri (P1 12:30, P2 16:30) gelene kadar app.py ve query.py geliştirilebilsin.
Bilimsel değeri YOK. Gerçek veriyi taklit eden özellikler:
  * Uydu eklendikçe ham sayılar sıçrar (Aqua 2002, S-NPP 2012, NOAA-20 2018, NOAA-21 2024)
  * weight_harm doğru tanımla dolu (§3.3) → harmonize seride sıçrama yok
  * Hohes Venn'de Nisan 2011 (sadece MODIS) ve Ağustos 2026 (VIIRS) pikleri
  * La Rioja: güney yarımküre yangın sezonu (Ağu–Kas)

Çalıştır (repo kökünden):  python data/mock/make_mock.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent / "hotspots_mock.parquet"
RNG = np.random.default_rng(2026)
START = pd.Timestamp("2000-11-01")
END = pd.Timestamp("2026-11-13")
ARCHIVE_UNTIL = pd.Timestamp("2026-07-01")  # sonrası "nrt"

# uydu: (enstrüman, ilk tarih, MODIS-eşdeğerine göre hassasiyet, yerel geçiş saatleri gündüz/gece)
SATS = {
    "Terra": ("MODIS", "2000-11-01", 0.5, (10.5, 22.5)),
    "Aqua": ("MODIS", "2002-07-04", 0.5, (13.5, 1.5)),
    "SNPP": ("VIIRS", "2012-01-20", 3.0, (13.5, 1.5)),
    "NOAA20": ("VIIRS", "2018-04-01", 3.0, (12.7, 0.7)),
    "NOAA21": ("VIIRS", "2024-01-17", 3.0, (13.1, 1.1)),
}
VIIRS_START = pd.Timestamp(SATS["SNPP"][1])
K_MOCK = 1 / 3.0  # MODIS / VIIRS (tek uydu) — gerçek değeri P2 hesaplayacak

# bölge: bbox (lon_min, lat_min, lon_max, lat_max), aylık taban (MODIS-eşdeğeri), mevsim çarpanları Oca..Ara
REGIONS = {
    "La Rioja": ((-69.7, -31.9, -65.4, -27.6), 40.0,
                 [1.0, 0.8, 0.6, 0.4, 0.3, 0.4, 0.8, 1.6, 2.4, 2.6, 2.0, 1.4]),
    "Aachen/Eifel": ((5.9, 50.2, 7.0, 50.9), 1.5,
                     [0.3, 0.4, 1.2, 1.5, 0.8, 0.6, 0.9, 1.0, 0.6, 0.3, 0.2, 0.2]),
}

# olaylar: (merkez lon, lat, başlangıç, bitiş, toplam MODIS-eşdeğeri tespit)
EVENTS = [
    (6.08, 50.52, "2011-04-24", "2011-04-28", 120.0),  # Hohes Venn, Nisan 2011
    (6.10, 50.50, "2026-08-10", "2026-08-15", 90.0),   # Hohes Venn, Ağustos 2026
]


def sat_start(sat: str) -> pd.Timestamp:
    return pd.Timestamp(SATS[sat][1])


def sample_points(n, bbox, centers, spread):
    """n noktayı merkezler etrafında dağıt, bbox içine kırp."""
    lon_min, lat_min, lon_max, lat_max = bbox
    idx = RNG.integers(0, len(centers), n)
    c = np.asarray(centers)[idx]
    lon = np.clip(c[:, 0] + RNG.normal(0, spread, n), lon_min, lon_max)
    lat = np.clip(c[:, 1] + RNG.normal(0, spread, n), lat_min, lat_max)
    return lon, lat


def emit(rows, sat, n, days, lon, lat):
    """Bir uydu için n tespiti satır olarak ekle (henüz sütun bazlı)."""
    if n == 0:
        return
    rows.append(pd.DataFrame({
        "satellite": sat,
        "acq_date": RNG.choice(days, n),
        "lon": lon,
        "lat": lat,
    }))


def generate_counts() -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    months = pd.date_range(START, END, freq="MS")

    for name, (bbox, base, season) in REGIONS.items():
        lon_min, lat_min, lon_max, lat_max = bbox
        year_factor = {y: RNG.lognormal(0, 0.35) for y in range(START.year, END.year + 1)}
        for m0 in months:
            m1 = min(m0 + pd.offsets.MonthEnd(0), END)
            activity = base * season[m0.month - 1] * year_factor[m0.year] * RNG.gamma(4, 0.25)
            k = RNG.integers(1, 5)
            centers = np.column_stack([RNG.uniform(lon_min, lon_max, k), RNG.uniform(lat_min, lat_max, k)])
            for sat, (_, _, sens, _) in SATS.items():
                first = max(m0, sat_start(sat))
                if first > m1:
                    continue
                days = pd.date_range(first, m1, freq="D").values
                frac = len(days) / ((m0 + pd.offsets.MonthEnd(0)) - m0).days
                n = RNG.poisson(activity * sens * frac)
                emit(rows, sat, n, days, *sample_points(n, bbox, centers, 0.05))

    for lon_c, lat_c, d0, d1, total in EVENTS:
        days = pd.date_range(d0, d1, freq="D").values
        for sat, (_, _, sens, _) in SATS.items():
            if sat_start(sat) > pd.Timestamp(d0):
                continue
            n = RNG.poisson(total * sens)
            bbox = (lon_c - 0.15, lat_c - 0.08, lon_c + 0.15, lat_c + 0.08)
            emit(rows, sat, n, days, *sample_points(n, bbox, [(lon_c, lat_c)], 0.02))

    return pd.concat(rows, ignore_index=True)


def add_attributes(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    df["acq_date"] = pd.to_datetime(df["acq_date"]).dt.normalize()
    df["instrument"] = df["satellite"].map({s: v[0] for s, v in SATS.items()})
    is_modis = (df["instrument"] == "MODIS").to_numpy()

    # geçiş saati: %80 gündüz; UTC = yerel - lon/15
    day = RNG.random(n) < 0.8
    local = np.array([SATS[s][3][0] if d else SATS[s][3][1] for s, d in zip(df["satellite"], day)])
    utc = (local - df["lon"].to_numpy() / 15.0 + RNG.normal(0, 0.3, n)) % 24
    df["acq_time"] = (np.floor(utc) * 100 + np.floor((utc % 1) * 60)).astype("int16")
    df["daynight"] = np.where(day, "D", "N")

    # güven
    modis_conf = np.clip(RNG.beta(5, 2, n) * 100, 0, 100).astype(int)
    viirs_conf = RNG.choice(["l", "n", "h"], n, p=[0.1, 0.75, 0.15])
    df["confidence_raw"] = np.where(is_modis, modis_conf.astype(str), viirs_conf)
    modis_cat = np.where(modis_conf < 30, "low", np.where(modis_conf < 80, "nominal", "high"))
    viirs_cat = pd.Series(viirs_conf).map({"l": "low", "n": "nominal", "h": "high"}).to_numpy()
    df["confidence"] = np.where(is_modis, modis_cat, viirs_cat)

    # fiziksel değerler
    df["frp"] = np.where(is_modis, RNG.lognormal(2.5, 1.0, n), RNG.lognormal(1.5, 1.0, n))
    df["bright"] = np.where(is_modis, np.clip(310 + RNG.exponential(15, n), 300, 500),
                            np.clip(300 + RNG.exponential(15, n), 295, 367))
    scan = np.where(is_modis, RNG.uniform(1.0, 4.8, n), RNG.uniform(0.32, 0.8, n))
    df["scan"] = scan
    df["track"] = scan * RNG.uniform(0.6, 1.0, n)

    # kaynak
    archive = df["acq_date"] < ARCHIVE_UNTIL
    df["source"] = np.where(archive, "archive", "nrt")
    df["fire_type"] = pd.array(np.where(archive, 0, pd.NA), dtype="Int8")

    # weight_harm (§3.3)
    starts = np.array([sat_start(s) for s in ("SNPP", "NOAA20", "NOAA21")], dtype="datetime64[ns]")
    n_active = (df["acq_date"].to_numpy()[:, None] >= starts[None, :]).sum(axis=1)
    modis_w = np.where(df["acq_date"] < VIIRS_START, 1.0, 0.0)
    viirs_w = K_MOCK / np.maximum(n_active, 1)
    df["weight_harm"] = np.where(is_modis, modis_w, viirs_w)

    df["year"] = df["acq_date"].dt.year
    df["month"] = df["acq_date"].dt.month
    return df


def to_schema(df: pd.DataFrame) -> pd.DataFrame:
    cats = {
        "instrument": ["MODIS", "VIIRS"],
        "satellite": ["Terra", "Aqua", "SNPP", "NOAA20", "NOAA21"],
        "confidence": ["low", "nominal", "high"],
        "daynight": ["D", "N"],
        "source": ["archive", "nrt"],
    }
    out = pd.DataFrame({
        "lat": df["lat"].astype("float64"),
        "lon": df["lon"].astype("float64"),
        "acq_date": df["acq_date"].astype("datetime64[ns]"),
        "acq_time": df["acq_time"].astype("int16"),
        "year": df["year"].astype("int16"),
        "month": df["month"].astype("int8"),
        "instrument": pd.Categorical(df["instrument"], categories=cats["instrument"]),
        "satellite": pd.Categorical(df["satellite"], categories=cats["satellite"]),
        "confidence": pd.Categorical(df["confidence"], categories=cats["confidence"]),
        "confidence_raw": df["confidence_raw"].astype("string"),
        "frp": df["frp"].astype("float32"),
        "bright": df["bright"].astype("float32"),
        "scan": df["scan"].astype("float32"),
        "track": df["track"].astype("float32"),
        "daynight": pd.Categorical(df["daynight"], categories=cats["daynight"]),
        "fire_type": df["fire_type"].astype("Int8"),
        "source": pd.Categorical(df["source"], categories=cats["source"]),
        "weight_harm": df["weight_harm"].astype("float32"),
    })
    return out.sort_values(["acq_date", "acq_time"]).reset_index(drop=True)


def main() -> None:
    df = to_schema(add_attributes(generate_counts()))
    df.to_parquet(OUT, engine="pyarrow", compression="snappy", index=False)
    print(f"{OUT}  {len(df):,} satır  {OUT.stat().st_size / 1e6:.1f} MB")
    print(df.groupby(["year", "satellite"], observed=True).size().unstack(fill_value=0).to_string())


if __name__ == "__main__":
    main()
