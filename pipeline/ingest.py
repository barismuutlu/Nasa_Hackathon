"""FIRMS CSV'lerini sözleşme şemasına çevirir → data/hotspots.parquet — sahibi P1 Süleyman.

Şema ve kurallar: docs/CONTRACT.md v1.2 (§1 şema, §2 eksik değer, §3 biçimler, §4 tekrar, §5 bölge, §7.1).
Sabitler contract.py'den gelir; burada yeniden tanımlanmaz.

Girdi: data/raw/<region>/ altındaki *.csv ve *.zip (zip içindeki alt klasörler dahil).
       Klasör adı = `region` değeri (contract.REGIONS: argentina, aachen_eifel).
       Kaynak = takımın Drive'ındaki DL_FIRE verisi (zip'ler açılmadan konabilir).

İki FIRMS biçimi de okunur (CONTRACT §3 tablosu):
  * DL_FIRE indirme aracı (fire_archive_* / fire_nrt_*): VIIRS'te de `brightness` + `bright_t31`
  * Ülke-yıl dosyaları (<ürün>_<yıl>_<Ülke>.csv): VIIRS `bright_ti4` + `bright_ti5`
    → okunur ama UYARI basılır: §5'e göre kullanılmaz (2026 ve NOAA-21 yok)
  Enstrüman = contract.SATELLITE_INSTRUMENT[satellite]; `confidence` biçimiyle (MODIS 0–100, VIIRS l/n/h)
  çapraz kontrol edilir.

Çıktılar:
  data/hotspots.parquet                 tam veri (git'e GİRMEZ)
  data/satellite_coverage.csv           bölge × uydu × kaynak ilk/son tarih + NRT kesimi (P2 için, git'e GİRMEZ)
  data/sample/hotspots_sample.parquet   La Rioja 2020 örneği (git'e girer)

Çalıştır (repo kökünden):  python pipeline/ingest.py
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- yol sabitleri
ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
OUT_PATH = ROOT / "data" / "hotspots.parquet"
COVERAGE_PATH = ROOT / "data" / "satellite_coverage.csv"
SAMPLE_DIR = ROOT / "data" / "sample"
SAMPLE_PATH = SAMPLE_DIR / "hotspots_sample.parquet"
# data/raw/ altında FIRMS OLMAYAN klasörler (başka script'lerin ham verisi) → bölge sayılmaz, atlanır
NON_FIRMS_DIRS = {"power": "pipeline/weather_power.py (NASA POWER hava verisi)"}

sys.path.insert(0, str(ROOT))
from contract import (  # noqa: E402
    CATEGORIES, COLUMNS, REGION_SLUG, REGIONS, SATELLITE_CODES, SATELLITE_INSTRUMENT,
    VIIRS_CONFIDENCE_CLASS, modis_confidence_class, validate_hotspots,
)

# ---------------------------------------------------------------- örnek & kontrol bölgeleri
# (lon_min, lat_min, lon_max, lat_max) — app/query.py PRESETS ile aynı
SAMPLE_BBOX = (-69.7, -31.9, -65.4, -27.6)  # La Rioja (AR)
SAMPLE_YEAR = 2020
VENN_BBOX = (5.95, 50.45, 6.25, 50.60)      # Hohes Venn

# ---------------------------------------------------------------- ham sütunlar
# Zorunlu alanlar (CONTRACT §2): okunamayan satır atılır ve sayılır. Başka sebeple satır atılmaz.
KEY_RAW = ["latitude", "longitude", "acq_date", "acq_time", "satellite"]
OTHER_RAW = ["confidence", "version", "scan", "track", "frp", "daynight"]
# parlaklık sütun çifti → (brightness, brightness_2)
BRIGHT_PAIRS = {"bright_ti4": ("bright_ti4", "bright_ti5"), "brightness": ("brightness", "bright_t31")}
STR = pd.StringDtype("pyarrow")  # str(STR) == "string"; python nesnesinden çok daha az bellek


# ================================================================ okuma

class _ZipMember:
    """Zip içindeki tek CSV'yi akış olarak açar (tamamını belleğe almadan)."""

    def __init__(self, zip_path: Path, name: str):
        self.zip_path, self.name = zip_path, name

    def __enter__(self):
        self._zf = zipfile.ZipFile(self.zip_path)
        self._f = self._zf.open(self.name)
        return self._f

    def __exit__(self, *exc):
        self._f.close()
        self._zf.close()


def find_raw_sources() -> list[tuple[str, str, callable]]:
    """(region, görünen ad, açıcı) listesi. data/raw/<region>/ altındaki CSV ve zip'ler."""
    if not RAW_DIR.exists():
        raise FileNotFoundError(f"{RAW_DIR} yok. FIRMS dosyalarını data/raw/<region>/ altına koy.")
    sources = []
    for p in sorted(RAW_DIR.rglob("*")):
        if not p.is_file() or p.suffix.lower() not in (".csv", ".zip"):
            continue
        rel = p.relative_to(RAW_DIR)
        if len(rel.parts) < 2:
            raise ValueError(f"data/raw/{rel}: dosya bir bölge klasöründe olmalı (data/raw/<region>/…) — CONTRACT §5")
        region = rel.parts[0]
        if region in NON_FIRMS_DIRS:
            continue
        if not REGION_SLUG.match(region):
            raise ValueError(f"data/raw/{region}/: klasör adı region slug'ı değil (a-z0-9_) — CONTRACT §5")
        if p.suffix.lower() == ".csv":
            sources.append((region, str(rel), lambda p=p: open(p, "rb")))
            continue
        with zipfile.ZipFile(p) as zf:
            names = sorted(n for n in zf.namelist() if n.lower().endswith(".csv"))
        for name in names:
            sources.append((region, f"{rel}::{name}", lambda p=p, name=name: _ZipMember(p, name)))
    if not sources:
        raise FileNotFoundError(f"{RAW_DIR} altında CSV/zip yok.")
    return sources


def _detect_source(name: str, header: list[str], version: pd.Series) -> str:
    base = Path(name.split("::")[-1]).name.lower()
    if re.search(r"(^|[^a-z])archive([^a-z]|$)", base):
        return "archive"
    if re.search(r"(^|[^a-z])nrt([^a-z]|$)", base):
        return "nrt"
    if "type" in header:  # ülke-yıl dosyaları: archive, `type` sütunu var
        print(f"  UYARI: {name}: ülke-yıl dosyası gibi görünüyor — CONTRACT §5'e göre kullanılmaz "
              f"(2026 ve NOAA-21 yok); DL_FIRE verisi kullan")
        return "archive"
    if len(version) and version.str.upper().str.endswith("NRT").all():
        return "nrt"
    raise ValueError(f"{name}: archive/nrt belirlenemedi (dosya adı, `type` sütunu, `version` ipucu yok)")


def _bad(name: str, col: str, values) -> ValueError:
    vals = pd.Series(values).astype(str).unique()[:10].tolist()
    return ValueError(f"{name}: `{col}` beklenmeyen değer(ler): {vals}")


def read_one(region: str, name: str, opener) -> tuple[pd.DataFrame, int]:
    """Tek FIRMS CSV'si → (§1 şemasında DataFrame, okunamadığı için atılan satır sayısı)."""
    with opener() as f:
        header = [c.strip().lower() for c in pd.read_csv(f, nrows=0).columns]

    pair = [k for k in BRIGHT_PAIRS if k in header]
    if len(pair) != 1:
        raise ValueError(f"{name}: tam olarak biri olmalı: `brightness` | `bright_ti4` (başlık: {header})")
    b1, b2 = BRIGHT_PAIRS[pair[0]]
    missing = [c for c in KEY_RAW + OTHER_RAW + [b1, b2] if c not in header]
    if missing:
        raise ValueError(f"{name}: beklenen sütun(lar) yok {missing}; başlık: {header}")
    usecols = set(KEY_RAW + OTHER_RAW + [b1, b2] + (["type"] if "type" in header else []))

    with opener() as f:
        raw = pd.read_csv(
            f, usecols=lambda c: c.strip().lower() in usecols,
            # zorunlu alanlar metin olarak okunur → okunamayan değer satır atılarak sayılır (§2)
            dtype={**{c: str for c in KEY_RAW}, "confidence": str, "version": str, "daynight": str,
                   "scan": "float32", "track": "float32", "frp": "float32",
                   b1: "float32", b2: "float32", "type": "Int8"},
            keep_default_na=False, na_values=[""],
        )
    raw.columns = [c.strip().lower() for c in raw.columns]

    # --- zorunlu alanlar: okunamayan → at
    lat = pd.to_numeric(raw["latitude"], errors="coerce")
    lon = pd.to_numeric(raw["longitude"], errors="coerce")
    acq_date = pd.to_datetime(raw["acq_date"].str.strip(), format="%Y-%m-%d", errors="coerce")
    t = pd.to_numeric(raw["acq_time"].str.strip(), errors="coerce")
    sat_code = raw["satellite"].str.strip()
    ok = (lat.between(-90, 90) & lon.between(-180, 180) & acq_date.notna()
          & t.between(0, 2359) & (t % 100 < 60) & sat_code.notna() & (sat_code != ""))
    n_bad = int((~ok).sum())
    if n_bad:
        raw, lat, lon, acq_date, t, sat_code = (x[ok] for x in (raw, lat, lon, acq_date, t, sat_code))
    if raw.empty:
        print(f"  boş    {name} (atılan: {n_bad})")
        return pd.DataFrame(), n_bad

    # --- uydu & enstrüman (bilinmeyen kod → hata, sessiz atma yok)
    satellite = sat_code.map(SATELLITE_CODES)
    if satellite.isna().any():
        raise _bad(name, "satellite (contract.SATELLITE_CODES'ta yok)", sat_code[satellite.isna()])
    instrument = satellite.map(SATELLITE_INSTRUMENT)
    is_modis = (instrument == "MODIS").to_numpy()
    if b1 == "bright_ti4" and is_modis.any():
        raise ValueError(f"{name}: `bright_ti4` (VIIRS) var ama MODIS uydusu satırı da var")

    # --- güven: orijinal değer korunur, sınıf türetilir
    conf = raw["confidence"]
    if conf.isna().any():
        raise ValueError(f"{name}: {int(conf.isna().sum())} satırda `confidence` boş (zorunlu sütun)")
    conf_class = pd.Series(pd.NA, index=raw.index, dtype="object")
    if is_modis.any():
        num = pd.to_numeric(conf[is_modis], errors="coerce")
        if num.isna().any() or not num.between(0, 100).all():
            raise _bad(name, "confidence (MODIS 0–100 bekleniyor)", conf[is_modis][num.isna() | ~num.between(0, 100)])
        conf_class[is_modis] = modis_confidence_class(conf[is_modis])
    if (~is_modis).any():
        mapped = conf[~is_modis].str.strip().str.lower().map(VIIRS_CONFIDENCE_CLASS)
        if mapped.isna().any():
            raise _bad(name, "confidence (VIIRS l/n/h bekleniyor)", conf[~is_modis][mapped.isna()])
        conf_class[~is_modis] = mapped

    # --- diğer alanlar
    version = raw["version"].str.strip()
    if version.isna().any():
        raise ValueError(f"{name}: {int(version.isna().sum())} satırda `version` boş (zorunlu sütun)")
    dn = raw["daynight"].str.strip().str.upper()
    if not dn.dropna().isin(CATEGORIES["daynight"]).all():
        raise _bad(name, "daynight", dn[dn.notna() & ~dn.isin(CATEGORIES["daynight"])])
    if "type" in raw:
        ftype = raw["type"].astype("Int8")
        if not ftype.dropna().isin([0, 1, 2, 3]).all():
            raise _bad(name, "type", ftype[ftype.notna() & ~ftype.isin([0, 1, 2, 3])])
    else:
        ftype = pd.Series(pd.NA, index=raw.index, dtype="Int8")
    source = _detect_source(name, header, version)

    acq_date = acq_date.astype("datetime64[ns]")
    hhmm = t.astype("int16")
    n = len(raw)
    df = pd.DataFrame({
        "latitude": lat.astype("float64"),
        "longitude": lon.astype("float64"),
        "acq_date": acq_date,
        "acq_time": hhmm,
        "datetime_utc": (acq_date.dt.tz_localize("UTC") + pd.to_timedelta(hhmm // 100, unit="h")
                         + pd.to_timedelta(hhmm % 100, unit="min")),
        "year": acq_date.dt.year.astype("int16"),
        "month": acq_date.dt.month.astype("int8"),
        "instrument": pd.Categorical(instrument, categories=CATEGORIES["instrument"]),
        "satellite": pd.Categorical(satellite, categories=CATEGORIES["satellite"]),
        "confidence": conf.astype(STR),
        "confidence_class": pd.Categorical(conf_class, categories=CATEGORIES["confidence_class"]),
        "version": version.astype(STR),
        "brightness": raw[b1].astype("float32"),
        "brightness_2": raw[b2].astype("float32"),
        "scan": raw["scan"].astype("float32"),
        "track": raw["track"].astype("float32"),
        "frp": raw["frp"].astype("float32"),
        "daynight": pd.Categorical(dn, categories=CATEGORIES["daynight"]),
        "type": ftype.astype("Int8"),
        "source": pd.Categorical([source] * n, categories=CATEGORIES["source"]),
        "region": pd.Series([region] * n, index=raw.index, dtype=STR),
        "weight_harm": np.full(n, np.nan, dtype="float32"),
    })[COLUMNS].reset_index(drop=True)

    sats = ",".join(sorted(df["satellite"].astype(str).unique()))
    print(f"  oku    [{region}] {name.split('::')[-1].split('/')[-1]}: {n:>9,} satır  {source:7s} {sats:11s} "
          f"{df['acq_date'].min():%Y-%m-%d} → {df['acq_date'].max():%Y-%m-%d}"
          + (f"  (okunamayan {n_bad} satır atıldı)" if n_bad else ""), flush=True)
    return df, n_bad


# ================================================================ tekrar & çakışma (CONTRACT §4)

def drop_nrt_overlap(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """4b: her (region, satellite) için cutoff = o bölgenin archive'indeki son acq_date;
    o bölge-uydunun acq_date ≤ cutoff NRT satırları atılır."""
    keys = ["region", "satellite"]
    is_arch = df["source"] == "archive"
    cutoff = df.loc[is_arch].groupby(keys, observed=True)["acq_date"].max().rename("nrt_cutoff")
    row_cut = df[keys].join(cutoff, on=keys)["nrt_cutoff"]
    drop = (~is_arch) & row_cut.notna() & (df["acq_date"] <= row_cut)

    info = cutoff.to_frame().join(df.loc[drop].groupby(keys, observed=True).size().rename("n_nrt_dropped"))
    info["n_nrt_dropped"] = info["n_nrt_dropped"].fillna(0).astype(int)
    info = info.reset_index()
    info["satellite"] = info["satellite"].astype(str)
    info["region"] = info["region"].astype(str)
    print("\n4b archive↔NRT kesimi (bölge × uydu):")
    print(info.to_string(index=False))

    nrt_only = df.loc[~is_arch, keys].drop_duplicates().astype(str).merge(
        info[keys], how="left", indicator=True).query("_merge == 'left_only'")
    for reg, sat in nrt_only[keys].itertuples(index=False):
        print(f"  NOT: [{reg}] {sat}: archive yok → NRT satırlarının hepsi kalır")
    return df.loc[~drop], info


def check_region_bbox(df: pd.DataFrame) -> None:
    """contract.REGIONS'ta bbox'ı olan bölgelerde kutu dışı satır → UYARI (yanlış klasör belirtisi).
    Satır atılmaz (CONTRACT §2)."""
    for reg, bbox in REGIONS.items():
        if bbox is None:
            continue
        lon0, lat0, lon1, lat1 = bbox
        r = df[df["region"] == reg]
        out = ~(r["longitude"].between(lon0, lon1) & r["latitude"].between(lat0, lat1))
        if out.any():
            print(f"  UYARI: [{reg}] {int(out.sum())} satır contract.REGIONS kutusu {bbox} dışında")


def drop_exact_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """4a: anahtar (satellite, datetime_utc, round(lat,4), round(lon,4)) → ilki kalır (archive önce)."""
    key = df[["satellite", "datetime_utc"]].assign(lat4=df["latitude"].round(4), lon4=df["longitude"].round(4))
    order = np.argsort(df["source"].cat.codes.to_numpy(), kind="stable")  # archive < nrt
    dup_sorted = key.iloc[order].duplicated(keep="first").to_numpy()
    dup = np.empty(len(df), dtype=bool)
    dup[order] = dup_sorted
    by_src = df.loc[dup, "source"].value_counts().to_dict()
    print(f"\n4a birebir tekrar: {int(dup.sum()):,} satır atıldı (kaynak: {by_src})")
    return df.loc[~dup]


# ================================================================ özet

def coverage_table(df: pd.DataFrame, nrt_info: pd.DataFrame) -> pd.DataFrame:
    """CONTRACT §7.1: her bölge × uydu × kaynak bir satır."""
    g = df.groupby(["region", "satellite", "source"], observed=True)
    cov = pd.DataFrame({
        "first_date": g["acq_date"].min().dt.date,
        "last_date": g["acq_date"].max().dt.date,
        "n_rows": g.size(),
    }).reset_index()
    for c in ("region", "satellite", "source"):
        cov[c] = cov[c].astype(str)
    cov = cov.merge(nrt_info, on=["region", "satellite"], how="left")
    cov["nrt_cutoff"] = cov["nrt_cutoff"].dt.date
    cov["n_nrt_dropped"] = cov["n_nrt_dropped"].fillna(0).astype(int)
    return cov[["region", "satellite", "source", "first_date", "last_date", "n_rows", "nrt_cutoff", "n_nrt_dropped"]]


def print_summary(df: pd.DataFrame, cov: pd.DataFrame) -> None:
    print(f"\n{len(df):,} satır, {df['acq_date'].min():%Y-%m-%d} → {df['acq_date'].max():%Y-%m-%d}")
    print("\nUydu × yıl satır sayısı:")
    print(df.groupby(["year", "satellite"], observed=False).size().unstack("satellite", fill_value=0).to_string())
    print("\nBölge × uydu satır sayısı:")
    print(df.groupby(["region", "satellite"], observed=False).size().unstack("satellite", fill_value=0).to_string())
    print("\nUydu kapsamı (data/satellite_coverage.csv):")
    print(cov.to_string(index=False))

    missing = [r for r in REGIONS if r not in set(df["region"].unique())]
    if missing:
        print(f"\nNOT: contract.REGIONS'taki şu bölgeler veride yok: {missing}")

    vlon0, vlat0, vlon1, vlat1 = VENN_BBOX
    venn = df[df["longitude"].between(vlon0, vlon1) & df["latitude"].between(vlat0, vlat1)]
    for (y, m, inst) in ((2011, 4, "MODIS"), (2026, 8, "MODIS"), (2026, 8, "VIIRS")):
        n = int(((venn["year"] == y) & (venn["month"] == m) & (venn["instrument"] == inst)).sum())
        print(f"Hohes Venn {y}-{m:02d} {inst}: {n} tespit")


def write_sample(df: pd.DataFrame) -> None:
    lon0, lat0, lon1, lat1 = SAMPLE_BBOX
    s = df[df["longitude"].between(lon0, lon1) & df["latitude"].between(lat0, lat1) & (df["year"] == SAMPLE_YEAR)]
    if s.empty:
        print(f"\nUYARI: örnek bölgede ({SAMPLE_BBOX}, {SAMPLE_YEAR}) veri yok → {SAMPLE_PATH.name} yazılmadı")
        return
    s = s.reset_index(drop=True)
    validate_hotspots(s, "ingest")
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    s.to_parquet(SAMPLE_PATH, engine="pyarrow", compression="snappy", index=False)
    print(f"\nÖrnek → {SAMPLE_PATH.relative_to(ROOT)}: {len(s):,} satır "
          f"({SAMPLE_PATH.stat().st_size / 1e6:.2f} MB) {s['satellite'].value_counts().to_dict()}")


# ================================================================ main

def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows konsolu (cp1252) Türkçe karakterde patlamasın

    print(f"Okuma: {RAW_DIR.relative_to(ROOT)}")
    for d, owner in NON_FIRMS_DIRS.items():
        if (RAW_DIR / d).exists():
            print(f"  atlandı: data/raw/{d}/ — FIRMS değil, {owner}")
    parts, n_unreadable = [], 0
    for region, name, opener in find_raw_sources():
        part, n_bad = read_one(region, name, opener)
        n_unreadable += n_bad
        if len(part):
            parts.append(part)
    if not parts:
        raise ValueError("Hiç satır okunamadı.")
    df = pd.concat(parts, ignore_index=True)
    del parts
    print(f"Toplam okunan: {len(df):,} satır; zorunlu alanı okunamadığı için atılan: {n_unreadable:,}")

    check_region_bbox(df)
    df, nrt_info = drop_nrt_overlap(df)
    df = drop_exact_duplicates(df)
    df = df.sort_values(["datetime_utc", "satellite", "latitude", "longitude"], kind="stable").reset_index(drop=True)

    validate_hotspots(df, "ingest")
    df.to_parquet(OUT_PATH, engine="pyarrow", compression="snappy", index=False)
    print(f"\nYazıldı → {OUT_PATH.relative_to(ROOT)} ({OUT_PATH.stat().st_size / 1e6:.1f} MB), "
          f"validate_hotspots(df, 'ingest') geçti")

    cov = coverage_table(df, nrt_info)
    cov.to_csv(COVERAGE_PATH, index=False)
    print_summary(df, cov)
    write_sample(df)


if __name__ == "__main__":
    main()
