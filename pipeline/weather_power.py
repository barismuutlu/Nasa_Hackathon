"""NASA POWER daily weather data → 1° cell × month table — owner P1 Süleyman.

Purpose: local weather (drought) input for P4's EXPERIMENTAL "detection outlook 2 months ahead" model
(pipeline/forecast.py). P4 will add it to the contract in v1.5; the output columns are FIXED as below.

Cells:    from rows with region == "argentina" in data/hotspots.parquet
          cell_lat = floor(latitude) + 0.5, cell_lon = floor(longitude) + 0.5 (unique pairs).
Source:   NASA POWER daily point API (community=AG, no account needed); ONE request per cell,
          2003-01-01 → today. PRECTOTCORR (mm/day), T2M_MAX (°C), RH2M (%); -999 = missing.
          The value comes from the MERRA-2 box (0.5° × 0.625°) containing the cell center — it is NOT
          the average of the 1° cell. Days are POWER's local solar time (LST) days.
Raw response: data/raw/power/<cell_lat>_<cell_lon>.csv (NOT committed to git). Existing files are not re-downloaded:
          if interrupted, run again and it resumes where it left off. (ingest.py skips this folder.)

Output: data/weather_power.parquet (NOT committed to git), columns in this order:
  cell_lat float64, cell_lon float64, year int16, month int8,
  prec_mm  float64  monthly TOTAL precipitation (mm)
  tmax_c   float64  monthly mean of daily maximum temperatures (°C)
  rh_pct   float64  monthly mean relative humidity (%)
  n_days   int16    number of days on which all three parameters are valid
  All three values are computed ONLY from these n_days days. n_days < days in month → partial month
  (the current month is like this; prec_mm is not a full-month total for it). n_days = 0 → values are NaN.

Run (from repo root):  python pipeline/weather_power.py
                       python pipeline/weather_power.py --one   # La Rioja cell only, does not write parquet
"""
from __future__ import annotations

import argparse
import http.client
import re
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- path constants
ROOT = Path(__file__).resolve().parents[1]
HOTSPOTS_PATH = ROOT / "data" / "hotspots.parquet"
RAW_DIR = ROOT / "data" / "raw" / "power"
OUT_PATH = ROOT / "data" / "weather_power.parquet"

# ---------------------------------------------------------------- request settings
REGION = "argentina"
START = date(2003, 1, 1)
PARAMS = ["PRECTOTCORR", "T2M_MAX", "RH2M"]
EXPECTED_COLS = ["YEAR", "DOY", *PARAMS]
MISSING = -999.0
URL = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters={params}&community=AG"
       "&longitude={lon}&latitude={lat}&start={start}&end={end}&format=CSV")
MAX_WORKERS = 4
RETRIES = 3
RETRY_WAIT_S = 5
TIMEOUT_S = 120
LA_RIOJA = (-29.5, -66.5)  # (cell_lat, cell_lon) — stdout check and --one

OUT_SCHEMA = {
    "cell_lat": "float64", "cell_lon": "float64", "year": "int16", "month": "int8",
    "prec_mm": "float64", "tmax_c": "float64", "rh_pct": "float64", "n_days": "int16",
}
NET_ERRORS = (urllib.error.URLError, TimeoutError, ConnectionError, http.client.HTTPException)


# ---------------------------------------------------------------- cells
def argentina_cells() -> list[tuple[float, float]]:
    if not HOTSPOTS_PATH.exists():
        raise FileNotFoundError(f"{HOTSPOTS_PATH.relative_to(ROOT)} yok → önce python pipeline/ingest.py")
    df = pd.read_parquet(HOTSPOTS_PATH, columns=["region", "latitude", "longitude"])
    df = df[df["region"] == REGION]
    if df.empty:
        raise ValueError(f"hotspots.parquet içinde region == {REGION!r} satırı yok")
    cells = pd.DataFrame({"cell_lat": np.floor(df["latitude"].to_numpy()) + 0.5,
                          "cell_lon": np.floor(df["longitude"].to_numpy()) + 0.5}).drop_duplicates()
    cells = cells.sort_values(["cell_lat", "cell_lon"])
    return [(float(a), float(b)) for a, b in cells.itertuples(index=False)]


def raw_path(cell: tuple[float, float]) -> Path:
    return RAW_DIR / f"{cell[0]}_{cell[1]}.csv"


# ---------------------------------------------------------------- parsing
_LOC = re.compile(r"latitude\s+(-?\d+(?:\.\d+)?)\s+longitude\s+(-?\d+(?:\.\d+)?)")


def parse_power_csv(text: str, cell: tuple[float, float]) -> pd.DataFrame:
    """POWER CSV response → daily table (date + PARAMS, -999 → NaN). Unexpected format → ValueError."""
    tag = f"POWER {cell[0]}_{cell[1]}"
    lines = text.splitlines()
    try:
        end = next(i for i, ln in enumerate(lines) if ln.strip() == "-END HEADER-")
    except StopIteration:
        raise ValueError(f"{tag}: '-END HEADER-' satırı yok (hata yanıtı?): {text[:200]!r}") from None
    loc = _LOC.search("\n".join(lines[:end]))
    if not loc or (float(loc.group(1)), float(loc.group(2))) != cell:
        raise ValueError(f"{tag}: başlıktaki konum hücreyle uyuşmuyor: {loc.group(0) if loc else 'yok'}")
    body = "\n".join(lines[end + 1:])
    if not body.strip():
        raise ValueError(f"{tag}: boş yanıt (başlıktan sonra tablo yok)")
    df = pd.read_csv(StringIO(body))
    if list(df.columns) != EXPECTED_COLS:
        raise ValueError(f"{tag}: beklenmeyen sütunlar {list(df.columns)} ≠ {EXPECTED_COLS}")
    if df.empty:
        raise ValueError(f"{tag}: boş yanıt (0 gün)")
    for col in ("YEAR", "DOY"):
        if not pd.api.types.is_integer_dtype(df[col]):
            raise ValueError(f"{tag}: {col} tam sayı değil")
    dates = pd.to_datetime((df["YEAR"] * 1000 + df["DOY"]).astype(str), format="%Y%j")
    if dates.iloc[0] != pd.Timestamp(START) or not (dates.diff().dropna() == pd.Timedelta(days=1)).all():
        raise ValueError(f"{tag}: günler {START} başlayıp kesintisiz ardışık değil")
    out = df[PARAMS].astype("float64").mask(lambda x: x == MISSING)
    if (out["PRECTOTCORR"] < 0).any():
        raise ValueError(f"{tag}: negatif yağış (-999 dışı)")
    out.insert(0, "date", dates)
    return out


def monthly(daily: pd.DataFrame, cell: tuple[float, float]) -> pd.DataFrame:
    """Daily → monthly. Values only from days on which all three parameters are valid; a month with no valid day is NaN."""
    valid = daily[daily[PARAMS].notna().all(axis=1)]
    agg = (valid.groupby([valid["date"].dt.year.rename("year"), valid["date"].dt.month.rename("month")])
           .agg(prec_mm=("PRECTOTCORR", "sum"), tmax_c=("T2M_MAX", "mean"),
                rh_pct=("RH2M", "mean"), n_days=("PRECTOTCORR", "size")))
    months = daily["date"].dt.to_period("M").unique()
    agg = agg.reindex(pd.MultiIndex.from_arrays([months.year, months.month], names=["year", "month"]))
    agg["n_days"] = agg["n_days"].fillna(0)
    agg = agg.reset_index()
    agg.insert(0, "cell_lon", cell[1])
    agg.insert(0, "cell_lat", cell[0])
    return agg


# ---------------------------------------------------------------- download
def fetch(cell: tuple[float, float], end: date) -> str:
    url = URL.format(params=",".join(PARAMS), lat=cell[0], lon=cell[1],
                     start=START.strftime("%Y%m%d"), end=end.strftime("%Y%m%d"))
    last: Exception | None = None
    for attempt in range(1, RETRIES + 1):
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT_S) as r:
                return r.read().decode("utf-8")
        except NET_ERRORS as e:
            last = e
            if attempt < RETRIES:
                time.sleep(RETRY_WAIT_S)
    raise RuntimeError(f"POWER {cell[0]}_{cell[1]}: {RETRIES} denemede indirilemedi — {last}")


def download_cell(cell: tuple[float, float], end: date) -> None:
    """Download → validate → save (first .part, then rename: a partial file never enters the cache)."""
    text = fetch(cell, end)
    parse_power_csv(text, cell)  # an invalid response is not written to disk
    path = raw_path(cell)
    tmp = path.with_suffix(".part")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def download_missing(cells: list[tuple[float, float]], end: date) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    todo = [c for c in cells if not raw_path(c).exists()]
    print(f"Ham yanıt: {RAW_DIR.relative_to(ROOT)} — {len(cells) - len(todo)} hücre hazır, "
          f"{len(todo)} indirilecek (en fazla {MAX_WORKERS} paralel)")
    if not todo:
        return
    errors: list[str] = []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futs = {ex.submit(download_cell, c, end): c for c in todo}
        for i, fut in enumerate(as_completed(futs), 1):
            try:
                fut.result()
            except Exception as e:  # noqa: BLE001 — all are collected, error raised at the end
                errors.append(f"{futs[fut]}: {type(e).__name__}: {e}")
            if i % 25 == 0 or i == len(todo):
                print(f"  {i}/{len(todo)} ({time.time() - t0:.0f} sn, {len(errors)} hata)")
    if errors:
        raise RuntimeError(f"{len(errors)} hücre indirilemedi (inenler kaydedildi, tekrar çalıştır):\n  "
                           + "\n  ".join(errors[:10]))


# ---------------------------------------------------------------- table
def build_table(cells: list[tuple[float, float]]) -> tuple[pd.DataFrame, int]:
    parts, n_partial = [], 0
    for c in cells:
        daily = parse_power_csv(raw_path(c).read_text(encoding="utf-8"), c)
        nan = daily[PARAMS].isna()
        n_partial += int((nan.any(axis=1) & ~nan.all(axis=1)).sum())
        parts.append(monthly(daily, c))
    out = pd.concat(parts, ignore_index=True).astype(OUT_SCHEMA)[list(OUT_SCHEMA)]
    return out.sort_values(["cell_lat", "cell_lon", "year", "month"], ignore_index=True), n_partial


def validate_output(df: pd.DataFrame) -> None:
    if list(df.columns) != list(OUT_SCHEMA):
        raise ValueError(f"sütunlar {list(df.columns)} ≠ {list(OUT_SCHEMA)}")
    bad = {c: str(df[c].dtype) for c, t in OUT_SCHEMA.items() if str(df[c].dtype) != t}
    if bad:
        raise ValueError(f"dtype uyuşmuyor: {bad}")
    if df.empty:
        raise ValueError("çıktı boş")
    if df.duplicated(["cell_lat", "cell_lon", "year", "month"]).any():
        raise ValueError("aynı hücre-ay birden fazla satır")
    if not df["month"].between(1, 12).all() or (df["n_days"] < 0).any() or (df["n_days"] > 31).any():
        raise ValueError("month/n_days aralık dışı")


def print_summary(df: pd.DataFrame, n_partial: int) -> None:
    ym = df["year"].astype(int) * 100 + df["month"].astype(int)
    per_cell = df.groupby(["cell_lat", "cell_lon"]).size()
    print(f"\nHücre: {len(per_cell)}  |  ay aralığı: {ym.min() // 100}-{ym.min() % 100:02d} → "
          f"{ym.max() // 100}-{ym.max() % 100:02d}  |  satır: {len(df):,}")
    if per_cell.nunique() != 1:
        print(f"  UYARI: hücreler farklı sayıda ay içeriyor ({sorted(per_cell.unique())}) — "
              "ham yanıtlar farklı günlerde indirilmiş olabilir")
    print("NaN sayıları:", {c: int(df[c].isna().sum()) for c in ("prec_mm", "tmax_c", "rh_pct")})
    dim = pd.to_datetime(pd.DataFrame({"year": df["year"], "month": df["month"], "day": 1})).dt.days_in_month
    short = df[df["n_days"] < dim]
    print(f"Kısmi ay (n_days < ayın gün sayısı): {len(short)} hücre-ay — "
          f"{sorted(set(zip(short['year'].astype(int), short['month'].astype(int))))[:5]}")
    if n_partial:
        print(f"  NOT: {n_partial} günde parametrelerden bazıları eksik → o günler aylık değere girmedi")
    lr = df[(df["cell_lat"] == LA_RIOJA[0]) & (df["cell_lon"] == LA_RIOJA[1])]
    print(f"\nLa Rioja hücresi {LA_RIOJA}, Ekim 2026:")
    print(lr[(lr["year"] == 2026) & (lr["month"] == 10)].to_string(index=False))


# ---------------------------------------------------------------- main
def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--one", action="store_true", help="sadece La Rioja hücresi; parquet yazılmaz")
    args = ap.parse_args()

    today = date.today()
    cells = [LA_RIOJA] if args.one else argentina_cells()
    if not args.one and LA_RIOJA not in cells:
        raise ValueError(f"La Rioja hücresi {LA_RIOJA} hücre listesinde yok")
    print(f"Bölge: {REGION}  |  1° hücre: {len(cells)}  |  aralık: {START} → {today} (bugün)")

    download_missing(cells, today)
    df, n_partial = build_table(cells)
    validate_output(df)
    print_summary(df, n_partial)
    if args.one:
        print("\n--one: parquet yazılmadı. Son 3 ay:\n" + df.tail(3).to_string(index=False))
        return
    df.to_parquet(OUT_PATH, index=False)
    print(f"\nYazıldı: {OUT_PATH.relative_to(ROOT)}  ({OUT_PATH.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
