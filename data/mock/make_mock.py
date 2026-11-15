"""Generates SYNTHETIC TEST DATA (docs/CONTRACT.md v1.1 schema) — owner P4 Barış.

Purpose: let app.py and query.py be developed until the real data arrives (P1 12:30, P2 16:30).
NO scientific value. Every row has version="MOCK". Features that imitate the real data:
  * Raw counts jump as satellites are added (Aqua 2002, S-NPP 2012, NOAA-20 2018, NOAA-21 2023)
  * weight_harm filled with the correct definition (§3.3) → no jumps in the harmonized series
  * Detection peaks at Hohes Venn in April 2011 (MODIS only) and August 2026 (VIIRS)
  * S-NPP ends on 2026-11-02 (as in reality)
  * La Rioja: southern-hemisphere fire season (Aug–Nov)

Run (from the repo root):  python data/mock/make_mock.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from contract import CATEGORIES, COLUMNS, MOCK_VERSION, validate_hotspots  # noqa: E402

OUT = Path(__file__).resolve().parent / "hotspots_mock.parquet"
RNG = np.random.default_rng(2026)
START = pd.Timestamp("2000-11-01")
END = pd.Timestamp("2026-11-13")
ARCHIVE_UNTIL = pd.Timestamp("2026-07-01")  # after this: "nrt"

# satellite: (instrument, first date, last date, sensitivity relative to MODIS-equivalent, local overpass times day/night)
SATS = {
    "Terra": ("MODIS", "2000-11-01", None, 0.5, (10.5, 22.5)),
    "Aqua": ("MODIS", "2002-07-04", None, 0.5, (13.5, 1.5)),
    "SNPP": ("VIIRS", "2012-01-20", "2026-11-02", 3.0, (13.5, 1.5)),
    "NOAA20": ("VIIRS", "2018-04-01", None, 3.0, (12.7, 0.7)),
    "NOAA21": ("VIIRS", "2023-03-01", None, 3.0, (13.1, 1.1)),
}
VIIRS_START = pd.Timestamp(SATS["SNPP"][1])
K_MOCK = 1 / 3.0  # MODIS / VIIRS (single satellite) — P2 will compute the real value

# generation box: bbox (lon_min, lat_min, lon_max, lat_max), monthly base (MODIS-equivalent), seasonal factors Jan..Dec
# key = region value (contract.REGIONS). "argentina" is the whole country in reality; in the synthetic data only the La Rioja box.
REGIONS = {
    "argentina": ((-69.7, -31.9, -65.4, -27.6), 40.0,
                  [1.0, 0.8, 0.6, 0.4, 0.3, 0.4, 0.8, 1.6, 2.4, 2.6, 2.0, 1.4]),
    "aachen_eifel": ((5.96, 50.44, 6.44, 50.83), 1.5,
                     [0.3, 0.4, 1.2, 1.5, 0.8, 0.6, 0.9, 1.0, 0.6, 0.3, 0.2, 0.2]),
}

# synthetic detection clusters: (region, center lon, lat, start, end, total MODIS-equivalent detections)
EVENTS = [
    ("aachen_eifel", 6.08, 50.52, "2011-04-24", "2011-04-28", 120.0),  # Hohes Venn, April 2011
    ("aachen_eifel", 6.10, 50.50, "2026-08-10", "2026-08-15", 90.0),   # Hohes Venn, August 2026
]


def sat_start(sat: str) -> pd.Timestamp:
    return pd.Timestamp(SATS[sat][1])


def sat_end(sat: str) -> pd.Timestamp:
    return pd.Timestamp(SATS[sat][2]) if SATS[sat][2] else END


def sample_points(n, bbox, centers, spread):
    """Scatter n points around the centers, clipped to the bbox."""
    lon_min, lat_min, lon_max, lat_max = bbox
    idx = RNG.integers(0, len(centers), n)
    c = np.asarray(centers)[idx]
    lon = np.clip(c[:, 0] + RNG.normal(0, spread, n), lon_min, lon_max)
    lat = np.clip(c[:, 1] + RNG.normal(0, spread, n), lat_min, lat_max)
    return lon, lat


def emit(rows, region, sat, n, days, lon, lat):
    """Append n detections for one satellite as rows (still column-based)."""
    if n == 0:
        return
    rows.append(pd.DataFrame({
        "region": region,
        "satellite": sat,
        "acq_date": RNG.choice(days, n),
        "longitude": lon,
        "latitude": lat,
    }))


def generate_counts() -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    months = pd.date_range(START, END, freq="MS")

    for name, (bbox, base, season) in REGIONS.items():
        lon_min, lat_min, lon_max, lat_max = bbox
        year_factor = {y: RNG.lognormal(0, 0.10) for y in range(START.year, END.year + 1)}
        for m0 in months:
            m1 = min(m0 + pd.offsets.MonthEnd(0), END)
            activity = base * season[m0.month - 1] * year_factor[m0.year] * RNG.gamma(16, 1 / 16)
            k = RNG.integers(1, 5)
            centers = np.column_stack([RNG.uniform(lon_min, lon_max, k), RNG.uniform(lat_min, lat_max, k)])
            for sat, (_, _, _, sens, _) in SATS.items():
                first, last = max(m0, sat_start(sat)), min(m1, sat_end(sat))
                if first > last:
                    continue
                days = pd.date_range(first, last, freq="D").values
                frac = len(days) / ((m0 + pd.offsets.MonthEnd(0)) - m0).days
                n = RNG.poisson(activity * sens * frac)
                emit(rows, name, sat, n, days, *sample_points(n, bbox, centers, 0.05))

    for region, lon_c, lat_c, d0, d1, total in EVENTS:
        days = pd.date_range(d0, d1, freq="D").values
        for sat, (_, _, _, sens, _) in SATS.items():
            if sat_start(sat) > pd.Timestamp(d0) or sat_end(sat) < pd.Timestamp(d1):
                continue
            n = RNG.poisson(total * sens)
            bbox = (lon_c - 0.15, lat_c - 0.08, lon_c + 0.15, lat_c + 0.08)
            emit(rows, region, sat, n, days, *sample_points(n, bbox, [(lon_c, lat_c)], 0.02))

    return pd.concat(rows, ignore_index=True)


def add_attributes(df: pd.DataFrame) -> pd.DataFrame:
    n = len(df)
    df["acq_date"] = pd.to_datetime(df["acq_date"]).dt.normalize()
    df["instrument"] = df["satellite"].map({s: v[0] for s, v in SATS.items()})
    is_modis = (df["instrument"] == "MODIS").to_numpy()

    # overpass time: 80% daytime; UTC = local - lon/15
    day = RNG.random(n) < 0.8
    local = np.array([SATS[s][4][0] if d else SATS[s][4][1] for s, d in zip(df["satellite"], day)])
    utc = (local - df["longitude"].to_numpy() / 15.0 + RNG.normal(0, 0.3, n)) % 24
    df["acq_time"] = (np.floor(utc) * 100 + np.floor((utc % 1) * 60)).astype("int16")
    t = df["acq_time"].astype(int)
    df["datetime_utc"] = (df["acq_date"].dt.tz_localize("UTC")
                          + pd.to_timedelta(t // 100, "h") + pd.to_timedelta(t % 100, "min"))
    df["daynight"] = np.where(day, "D", "N")

    # confidence
    modis_conf = np.clip(RNG.beta(5, 2, n) * 100, 0, 100).astype(int)
    viirs_conf = RNG.choice(["l", "n", "h"], n, p=[0.1, 0.75, 0.15])
    df["confidence"] = np.where(is_modis, modis_conf.astype(str), viirs_conf)   # original value
    modis_cat = np.where(modis_conf < 30, "low", np.where(modis_conf < 80, "nominal", "high"))
    viirs_cat = pd.Series(viirs_conf).map({"l": "low", "n": "nominal", "h": "high"}).to_numpy()
    df["confidence_class"] = np.where(is_modis, modis_cat, viirs_cat)

    # physical values
    df["frp"] = np.where(is_modis, RNG.lognormal(2.5, 1.0, n), RNG.lognormal(1.5, 1.0, n))
    df["brightness"] = np.where(is_modis, np.clip(310 + RNG.exponential(15, n), 300, 500),
                                np.clip(300 + RNG.exponential(15, n), 295, 367))
    df["brightness_2"] = np.where(is_modis, RNG.normal(290, 8, n), RNG.normal(285, 8, n))
    scan = np.where(is_modis, RNG.uniform(1.0, 4.8, n), RNG.uniform(0.32, 0.8, n))
    df["scan"] = scan
    df["track"] = scan * RNG.uniform(0.6, 1.0, n)

    # source
    archive = df["acq_date"] < ARCHIVE_UNTIL
    df["source"] = np.where(archive, "archive", "nrt")
    df["type"] = pd.array(np.where(archive, 0, pd.NA), dtype="Int8")
    df["version"] = MOCK_VERSION

    # weight_harm (§3.3)
    viirs = ("SNPP", "NOAA20", "NOAA21")
    starts = np.array([sat_start(s) for s in viirs], dtype="datetime64[ns]")
    ends = np.array([sat_end(s) for s in viirs], dtype="datetime64[ns]")
    d = df["acq_date"].to_numpy()[:, None]
    n_active = ((d >= starts[None, :]) & (d <= ends[None, :])).sum(axis=1)
    modis_w = np.where(df["acq_date"] < VIIRS_START, 1.0, 0.0)
    viirs_w = K_MOCK / np.maximum(n_active, 1)
    df["weight_harm"] = np.where(is_modis, modis_w, viirs_w)

    df["year"] = df["acq_date"].dt.year
    df["month"] = df["acq_date"].dt.month
    return df


def to_schema(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    casts = {
        "latitude": "float64", "longitude": "float64", "acq_date": "datetime64[ns]",
        "acq_time": "int16", "year": "int16", "month": "int8",
        "confidence": "string", "version": "string", "region": "string",
        "brightness": "float32", "brightness_2": "float32", "scan": "float32", "track": "float32",
        "frp": "float32", "type": "Int8", "weight_harm": "float32",
    }
    for col, dtype in casts.items():
        df[col] = df[col].astype(dtype)
    for col, cats in CATEGORIES.items():
        df[col] = pd.Categorical(df[col], categories=cats)
    df["datetime_utc"] = df["datetime_utc"].astype("datetime64[ns, UTC]")
    return df[COLUMNS].sort_values("datetime_utc").reset_index(drop=True)


def main() -> None:
    df = to_schema(add_attributes(generate_counts()))
    validate_hotspots(df, stage="harm")
    df.to_parquet(OUT, engine="pyarrow", compression="snappy", index=False)
    print(f"{OUT}  {len(df):,} satır  {OUT.stat().st_size / 1e6:.1f} MB")
    print(df.groupby(["year", "satellite"], observed=True).size().unstack(fill_value=0).to_string())


if __name__ == "__main__":
    main()
