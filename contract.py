"""Veri sözleşmesi v1.4 — sahibi P4 Barış. Belge: docs/CONTRACT.md

Sadece SABİTLER ve DOĞRULAYICI içerir; ingest/harmonize mantığı burada YOK.
Kullanım (pipeline/ veya app/ içinden):

    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from contract import validate_hotspots, SATELLITE_CODES, REGIONS

    validate_hotspots(df, stage="ingest")   # P1: parquet yazmadan önce
    validate_hotspots(df, stage="harm")     # P2: hotspots_harm.parquet yazmadan önce
"""
from __future__ import annotations

import re

import pandas as pd

CONTRACT_VERSION = "1.4"

# ---------------------------------------------------------------- sabit değer kümeleri

INSTRUMENTS = ["MODIS", "VIIRS"]
SATELLITES = ["Terra", "Aqua", "SNPP", "NOAA20", "NOAA21"]
SATELLITE_INSTRUMENT = {"Terra": "MODIS", "Aqua": "MODIS",
                        "SNPP": "VIIRS", "NOAA20": "VIIRS", "NOAA21": "VIIRS"}
CONFIDENCE_CLASSES = ["low", "nominal", "high"]
DAYNIGHT = ["D", "N"]
SOURCES = ["archive", "nrt"]

# FIRMS 'satellite' sütunundaki kodlar → kanonik ad. Burada olmayan kod → hata (sessizce atma).
SATELLITE_CODES = {
    "Terra": "Terra", "T": "Terra",
    "Aqua": "Aqua", "A": "Aqua",
    "N": "SNPP", "SNPP": "SNPP", "Suomi NPP": "SNPP",
    "N20": "NOAA20", "1": "NOAA20", "J1": "NOAA20", "NOAA-20": "NOAA20",
    "N21": "NOAA21", "2": "NOAA21", "J2": "NOAA21", "NOAA-21": "NOAA21",
}

# VIIRS confidence → sınıf. MODIS için: modis_confidence_class() (proje kuralı, FIRMS'te sayısal eşik yok)
VIIRS_CONFIDENCE_CLASS = {"l": "low", "n": "nominal", "h": "high",
                          "low": "low", "nominal": "nominal", "high": "high"}
MODIS_CONFIDENCE_CUTS = (30, 80)   # <30 low, 30–79 nominal, ≥80 high

# İndirme alanları (FIRMS indirme aracı / DL_FIRE). Alanlar ÇAKIŞMAZ → aynı tespit iki alanda olmaz.
# data/raw/<slug>/ klasör adı = region değeri. bbox = (lon_min, lat_min, lon_max, lat_max), None = ülke.
# FIRMS ülke-YIL dosyaları KULLANILMAZ: 2026 ve NOAA-21 içermiyorlar.
REGIONS: dict[str, tuple[float, float, float, float] | None] = {
    "argentina": None,                          # ülke (La Rioja + P2 eğitimi)
    "aachen_eifel": (5.96, 50.44, 6.44, 50.83),  # bbox, Hohes Venn dahil (Belçika tarafı da)
}
REGION_SLUG = re.compile(r"^[a-z0-9_]+$")

MOCK_VERSION = "MOCK"   # sahte verinin 'version' değeri → her satır sentetik olarak işaretli

# ---------------------------------------------------------------- şema

# sütun → (pandas dtype, null olabilir mi)
SCHEMA: dict[str, tuple[str, bool]] = {
    "latitude":         ("float64", False),
    "longitude":        ("float64", False),
    "acq_date":         ("datetime64[ns]", False),
    "acq_time":         ("int16", False),
    "datetime_utc":     ("datetime64[ns, UTC]", False),
    "year":             ("int16", False),
    "month":            ("int8", False),
    "instrument":       ("category", False),
    "satellite":        ("category", False),
    "confidence":       ("string", False),
    "confidence_class": ("category", False),
    "version":          ("string", False),
    "brightness":       ("float32", True),
    "brightness_2":     ("float32", True),
    "scan":             ("float32", True),
    "track":            ("float32", True),
    "frp":              ("float32", True),
    "daynight":         ("category", True),
    "type":             ("Int8", True),
    "source":           ("category", False),
    "region":           ("string", False),
    "weight_harm":      ("float32", True),
}
COLUMNS = list(SCHEMA)

CATEGORIES = {
    "instrument": INSTRUMENTS,
    "satellite": SATELLITES,
    "confidence_class": CONFIDENCE_CLASSES,
    "daynight": DAYNIGHT,
    "source": SOURCES,
}

# Tekrar anahtarı (aynı kaynak içinde birebir aynı gözlem). region ve source anahtarda YOK.
DEDUP_KEY = ["satellite", "datetime_utc", "lat4", "lon4"]   # lat4/lon4 = round(…, 4)


def modis_confidence_class(conf: pd.Series) -> pd.Series:
    """MODIS 0–100 → low/nominal/high (proje kuralı, MODIS_CONFIDENCE_CUTS)."""
    c = pd.to_numeric(conf, errors="raise")
    lo, hi = MODIS_CONFIDENCE_CUTS
    return pd.Series(pd.cut(c, [-1, lo - 1, hi - 1, 100], labels=CONFIDENCE_CLASSES).astype(str),
                     index=conf.index)


def empty_frame() -> pd.DataFrame:
    """Şemaya uygun boş DataFrame (testler / boş sonuçlar için)."""
    data = {}
    for col, (dtype, _) in SCHEMA.items():
        if dtype == "category":
            data[col] = pd.Categorical([], categories=CATEGORIES[col])
        else:
            data[col] = pd.Series([], dtype=dtype)
    return pd.DataFrame(data)


# ---------------------------------------------------------------- doğrulama

def validate_hotspots(df: pd.DataFrame, stage: str = "ingest", max_rows: int | None = None) -> None:
    """Şemayı doğrular; sorun varsa TÜM sorunları listeleyen ValueError fırlatır.

    max_rows: None (varsayılan) = tüm satırlar. Sayı verilirse sütun/dtype/boş değer kontrolleri yine
    TÜM veride, satır-içi tutarlılık kontrolleri (zaman, aralık, slug…) rastgele max_rows satırda yapılır.
    P1/P2 yazarken None kullanır; query.py okurken hız için örneklem kullanır.

    stage="ingest": weight_harm tamamen NaN olmalı (P1 harmonize etmez).
    stage="harm":   weight_harm NaN içermez ve ≥ 0 (P2 çıktısı).
    stage="any":    weight_harm kontrol edilmez (query.py okurken).
    """
    if stage not in ("ingest", "harm", "any"):
        raise ValueError(f"stage 'ingest' | 'harm' | 'any' olmalı: {stage!r}")
    errs: list[str] = []

    missing = [c for c in COLUMNS if c not in df.columns]
    extra = [c for c in df.columns if c not in SCHEMA]
    if missing:
        errs.append(f"eksik sütun: {missing}")
    if extra:
        errs.append(f"sözleşmede olmayan sütun (önce P4'e sor): {extra}")

    for col, (dtype, nullable) in SCHEMA.items():
        if col not in df.columns:
            continue
        s = df[col]
        if str(s.dtype) != dtype:
            errs.append(f"{col}: dtype {s.dtype}, beklenen {dtype}")
        if not nullable and s.isna().any():
            errs.append(f"{col}: {int(s.isna().sum())} boş değer (zorunlu sütun)")
        if col in CATEGORIES and str(s.dtype) == "category":
            used = s.cat.categories[pd.unique(s.cat.codes[s.cat.codes >= 0])]
            bad = set(map(str, used)) - set(CATEGORIES[col])
            if bad:
                errs.append(f"{col}: izinsiz değer {sorted(bad)}")

    if not errs and len(df):
        if max_rows is not None and len(df) > max_rows:
            df = df.sample(max_rows, random_state=0)
        inst = df["satellite"].astype(str).map(SATELLITE_INSTRUMENT)
        if (inst != df["instrument"].astype(str)).any():
            errs.append("instrument ↔ satellite uyuşmuyor")
        if not df["latitude"].between(-90, 90).all() or not df["longitude"].between(-180, 180).all():
            errs.append("latitude/longitude aralık dışı")
        t = df["acq_time"]
        if not (t.between(0, 2359) & ((t % 100) < 60)).all():
            errs.append("acq_time HHMM değil")
        expect = df["acq_date"].dt.tz_localize("UTC") + pd.to_timedelta(t // 100, "h") + pd.to_timedelta(t % 100, "min")
        if (expect != df["datetime_utc"]).any():
            errs.append("datetime_utc ≠ acq_date + acq_time")
        if (df["acq_date"].dt.normalize() != df["acq_date"]).any():
            errs.append("acq_date saat içeriyor (00:00 olmalı)")
        if (df["year"] != df["acq_date"].dt.year).any() or (df["month"] != df["acq_date"].dt.month).any():
            errs.append("year/month ≠ acq_date")
        bad_regions = [r for r in df["region"].unique() if not REGION_SLUG.match(str(r))]
        if bad_regions:
            errs.append(f"region slug değil (a-z0-9_): {bad_regions[:5]}")
        typ = df["type"].dropna()
        if not typ.isin([0, 1, 2, 3]).all():
            errs.append("type 0–3 dışında")
        w = df["weight_harm"]
        if stage == "ingest" and w.notna().any():
            errs.append("weight_harm ingest aşamasında NaN olmalı (P2 doldurur)")
        if stage == "harm" and (w.isna().any() or (w < 0).any()):
            errs.append("weight_harm harm aşamasında NaN içeremez ve ≥ 0 olmalı")

    if errs:
        raise ValueError(f"Sözleşme v{CONTRACT_VERSION} ihlali ({stage}):\n  - " + "\n  - ".join(errs))
