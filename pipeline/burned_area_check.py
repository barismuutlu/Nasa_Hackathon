"""MCD64A1 yanmış alan kontrolü — DESTEKLEYİCİ kanıt — sahibi P1 Süleyman (P4 onayı, 2026-11-14).

Soru: Hohes Venn tespitleri (Nisan 2011, Ağustos 2026), MCD64A1 C6.1'in (aylık yanmış alan, ~500 m)
aynı dönemde yanmış olarak işaretlediği piksellere düşüyor mu?

UYARI: MCD64A1 bağımsız "gerçek" değildir — algoritması MODIS aktif yangın verisini de kullanır ve
küçük/kısa yanıkları kaçırabilir. Sonuç "destekleyici kanıt" olarak sunulur (CONTRACT §8).
Ana şemaya ve CONTRACT'a dokunmaz; çıktı ayrı dosyadır.

Ortam: ana requirements.txt + requirements-enrich.txt (pyhdf, SADECE bu dosya kullanır; içeride import edilir).

Girdi:
  data/hotspots.parquet                 (P1 ingest)
  MCD64A1 C6.1 HDF4 dosyaları           İbrahim'in indirdiği zip (Avrupa karoları h18v03/h18v04).
    İlk çalıştırmada --zip ile ver: sadece gereken ay/karo dosyaları data/external/mcd64a1/ altına
    çıkarılır (2,2 GB'ın tamamı kopyalanmaz). Sonraki çalıştırmalarda --zip gerekmez.
Çıktı:
  data/burned_area_check.csv            tespit başına bir satır (git'e GİRMEZ) → P3 Oğuzhan

Çalıştır (repo kökünden):
  pip install -r requirements-enrich.txt
  python pipeline/burned_area_check.py --zip "<…>/MCD64A1_061-20261114_105345-001.zip"
  python pipeline/burned_area_check.py            # dosyalar çıkarıldıktan sonra

Seçilen tespitler (grup): venn_2011 / venn_2026 = Hohes Venn kutusu (query.PRESETS), 2011-04 / 2026-08,
tümü (örnekleme yok).

Eşleştirme (ayarlanabilir: --tol-days, --ring):
  * Uzamsal: tespitin düştüğü MCD64A1 pikseli + `ring` komşuluk (ring=1 → 3×3 ≈ 1,4 km;
    MODIS aktif yangın pikseli nadirde ~1 km, kenarda daha büyük; VIIRS 375 m).
  * Zamansal: |yanma tarihi − acq_date| ≤ tol_days (16). acq_date ± tol_days'in değdiği tüm aylık
    granüllere bakılır (ay/yıl sınırı dahil). Burn Date = granül yılının gün numarası (artık yıl %Y%j).
  * Burn Date (HDF öznitelikleri): valid_range 0–366, 0 = yanmamış, _FillValue -1 = haritalanmamış,
    water -2. Başka değer = geçersiz.
  * QA (HDF "QA Legend"): bit0 kara(1)/su(0), bit1 geçerli veri, bit2 kısaltılmış haritalama dönemi,
    bit3 yeniden etiketlenmiş, bit5–7 özel kod (yanmamış hücreler için; 5 = kalıcı sıcak nokta).
  * Hizalama testi: her HDF'nin StructMetadata köşe koordinatları (UpperLeftPointMtrs) hesaplanan
    karo köşesiyle, CoreMetadata başlangıç tarihi granül ayıyla aynı olmalı; değilse ValueError.

Durum (status) — "bilinmiyor" ile "yanmamış" ayrı tutulur:
  burned_match       pencerede ±tol_days içinde yanma var                          → matched = True
  unknown            eşleşme yok VE beklenen kayıtlardan biri eksik / -1 / geçersiz → matched = <NA>
  burned_other_time  pencerede yanma var ama ±tol_days dışında, tüm kayıtlar geçerli → matched = False
  unburned           tüm beklenen kayıtlar geçerli ve yanmamış (0) ya da su (-2)   → matched = False
  no_data            gereken granüllerin hiçbiri yok                               → matched = <NA>
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------- yol sabitleri
ROOT = Path(__file__).resolve().parents[1]
HOTSPOTS_PATH = ROOT / "data" / "hotspots.parquet"
MCD64_DIR = ROOT / "data" / "external" / "mcd64a1"
OUT_PATH = ROOT / "data" / "burned_area_check.csv"

# ---------------------------------------------------------------- MODIS sinüzoidal ızgara (HDF StructMetadata)
SPHERE_R = 6371007.181          # ProjParams[0]
TILE_M = 1111950.5196666666     # karo kenarı (m) = 2·π·R / 36
NPIX = 2400                     # 500 m ürün: karo başına 2400×2400
PIX_M = TILE_M / NPIX           # ≈ 463.31 m
SDS = {"burn": "Burn Date", "unc": "Burn Date Uncertainty", "qa": "QA",
       "first_day": "First Day", "last_day": "Last Day"}

# ---------------------------------------------------------------- seçim & eşleştirme ayarları
TOL_DAYS = 16
RING = 1
VENN_BBOX = (5.95, 50.45, 6.25, 50.60)          # (lon_min, lat_min, lon_max, lat_max) = query.PRESETS
GROUPS = {"venn_2011": (2011, 4), "venn_2026": (2026, 8)}

OUT_COLUMNS = [
    "det_id", "group", "latitude", "longitude", "acq_date", "satellite", "instrument", "region",
    "burn_date", "burn_doy", "burn_uncertainty", "qa", "days_diff", "matched", "status",
    "n_pixels", "n_px_burned_in_tol", "n_records_missing", "n_records_unmapped_invalid",
    "n_px_persistent_hotspot", "tol_days", "ring",
]


# ================================================================ ızgara

def to_pixel(lat, lon) -> tuple[np.ndarray, np.ndarray]:
    """Enlem/boylam → global (satır, sütun) MCD64A1 500 m pikseli (karo = indeks // 2400)."""
    phi, lam = np.radians(np.asarray(lat, float)), np.radians(np.asarray(lon, float))
    x, y = SPHERE_R * lam * np.cos(phi), SPHERE_R * phi
    gcol = np.floor((x + 18 * TILE_M) / PIX_M).astype("int64")
    grow = np.floor((9 * TILE_M - y) / PIX_M).astype("int64")
    return grow, gcol


def pixel_center(grow, gcol) -> tuple[np.ndarray, np.ndarray]:
    """Global (satır, sütun) → piksel merkezinin enlem/boylamı."""
    y = 9 * TILE_M - (np.asarray(grow) + 0.5) * PIX_M
    x = -18 * TILE_M + (np.asarray(gcol) + 0.5) * PIX_M
    phi = y / SPHERE_R
    return np.degrees(phi), np.degrees(x / (SPHERE_R * np.cos(phi)))


def detection_pixels(det: pd.DataFrame, ring: int) -> pd.DataFrame:
    grow, gcol = to_pixel(det["latitude"], det["longitude"])
    offs = [(dr, dc) for dr in range(-ring, ring + 1) for dc in range(-ring, ring + 1)]
    k = len(offs)
    return pd.DataFrame({
        "det_id": np.repeat(det["det_id"].to_numpy(), k),
        "grow": np.repeat(grow, k) + np.tile([o[0] for o in offs], len(det)),
        "gcol": np.repeat(gcol, k) + np.tile([o[1] for o in offs], len(det)),
    })


def candidate_months(det: pd.DataFrame, tol_days: int) -> pd.DataFrame:
    acq = pd.to_datetime(det.set_index("det_id")["acq_date"])
    lo = (acq - pd.Timedelta(days=tol_days)).dt.to_period("M")
    hi = (acq + pd.Timedelta(days=tol_days)).dt.to_period("M")
    return pd.DataFrame([(d, p) for d in acq.index for p in pd.period_range(lo[d], hi[d], freq="M")],
                        columns=["det_id", "period"])


# ================================================================ tespit seçimi

def select_detections(df: pd.DataFrame) -> pd.DataFrame:
    lon0, lat0, lon1, lat1 = VENN_BBOX
    venn = df[df["longitude"].between(lon0, lon1) & df["latitude"].between(lat0, lat1)]
    det = pd.concat([venn[(venn["year"] == y) & (venn["month"] == m)].assign(group=g)
                     for g, (y, m) in GROUPS.items()], ignore_index=True)
    det["det_id"] = (det["satellite"].astype(str) + "|" + det["datetime_utc"].dt.strftime("%Y-%m-%dT%H:%M")
                     + "|" + det["latitude"].round(4).astype(str) + "|" + det["longitude"].round(4).astype(str))
    if det["det_id"].duplicated().any():
        raise ValueError("det_id tekil değil (CONTRACT §4a anahtarıyla tekil olmalıydı)")
    cols = ["det_id", "group", "latitude", "longitude", "acq_date", "satellite", "instrument", "region"]
    return det[cols].astype({"satellite": str, "instrument": str, "region": str})


# ================================================================ HDF okuma

def granule_name(h: int, v: int, period: pd.Period) -> str:
    doy = date(period.year, period.month, 1).timetuple().tm_yday
    return f"MCD64A1.A{period.year}{doy:03d}.h{h:02d}v{v:02d}.061."


def ensure_granules(needed: pd.DataFrame, zip_path: Path | None) -> dict[tuple, Path]:
    """needed: (h, v, period). Eksik HDF'leri zip'ten çıkarır (sadece gerekenler). → {(h,v,period): yol}"""
    MCD64_DIR.mkdir(parents=True, exist_ok=True)
    found: dict[tuple, Path] = {}
    members: list[str] = []
    if zip_path is not None:
        with zipfile.ZipFile(zip_path) as zf:
            members = [n for n in zf.namelist() if n.lower().endswith(".hdf")]
    for h, v, p in needed.itertuples(index=False):
        prefix = granule_name(h, v, p)
        local = sorted(MCD64_DIR.glob(prefix + "*.hdf"))
        if not local and members:
            hit = [n for n in members if Path(n).name.startswith(prefix)]
            if len(hit) > 1:
                raise ValueError(f"Zip'te aynı granül için birden çok dosya: {hit}")
            if hit:
                with zipfile.ZipFile(zip_path) as zf:
                    (MCD64_DIR / Path(hit[0]).name).write_bytes(zf.read(hit[0]))
                local = sorted(MCD64_DIR.glob(prefix + "*.hdf"))
        if len(local) > 1:
            raise ValueError(f"{MCD64_DIR} içinde aynı granül için birden çok dosya: {local}")
        if local:
            found[(h, v, p)] = local[0]
        else:
            print(f"  EKSİK granül: {prefix}*.hdf (zip'te/klasörde yok) → bu ayın kayıtları 'eksik' sayılır")
    return found


def check_alignment(struct_meta: str, core_meta: str, h: int, v: int, period: pd.Period, name: str) -> None:
    """Hizalama testi: HDF köşe koordinatı ve tarih, hesaplanan karo/ay ile aynı olmalı."""
    ul = re.search(r"UpperLeftPointMtrs=\(([^)]+)\)", struct_meta)
    xdim = re.search(r"XDim=(\d+)", struct_meta)
    ydim = re.search(r"YDim=(\d+)", struct_meta)
    beg = re.search(r"RANGEBEGINNINGDATE.*?VALUE\s*=\s*\"([^\"]+)\"", core_meta, re.S)
    if not (ul and xdim and ydim and beg):
        raise ValueError(f"{name}: StructMetadata/CoreMetadata okunamadı")
    x0, y0 = (float(s) for s in ul.group(1).split(","))
    ex, ey = -18 * TILE_M + h * TILE_M, 9 * TILE_M - v * TILE_M
    if abs(x0 - ex) > 1 or abs(y0 - ey) > 1 or int(xdim.group(1)) != NPIX or int(ydim.group(1)) != NPIX:
        raise ValueError(f"{name}: hizalama hatası — UL=({x0},{y0}) beklenen=({ex:.3f},{ey:.3f}), "
                         f"dim={xdim.group(1)}×{ydim.group(1)}")
    if pd.Period(beg.group(1), freq="M") != period:
        raise ValueError(f"{name}: tarih uyuşmuyor — RANGEBEGINNINGDATE={beg.group(1)}, beklenen {period}")


def _open_sd(path: Path):
    """HDF4'ü aç. HDF4 C kütüphanesi Windows'ta ASCII olmayan yolları (ör. 'Рабочий стол') açamıyor →
    geçici olarak dosyanın klasörüne geçip ASCII dosya adıyla açılır (OS göreli yolu Unicode çözer)."""
    from pyhdf.SD import SD, SDC
    if str(path).isascii():
        return SD(str(path), SDC.READ)
    old = Path.cwd()
    try:
        os.chdir(path.parent)
        return SD(path.name, SDC.READ)
    finally:
        os.chdir(old)


def read_records(px: pd.DataFrame, months: pd.DataFrame, zip_path: Path | None) -> pd.DataFrame:
    """Gereken (piksel, ay) kayıtlarını HDF'lerden okur → (grow, gcol, period, burn, unc, qa, first_day, last_day)."""
    try:
        import pyhdf.SD  # noqa: F401 — sadece bu script; ana ortamda yok
    except ImportError as e:
        raise ImportError("pyhdf yok → pip install -r requirements-enrich.txt (sadece bu script için)") from e

    need = px.merge(months, on="det_id")[["grow", "gcol", "period"]].drop_duplicates()
    need["h"], need["v"] = need["gcol"] // NPIX, need["grow"] // NPIX
    granules = ensure_granules(need[["h", "v", "period"]].drop_duplicates(), zip_path)
    rows, attrs_shown = [], False
    for (h, v, p), path in sorted(granules.items(), key=lambda kv: (kv[0][2], kv[0][0], kv[0][1])):
        sd = _open_sd(path)
        try:
            ga = sd.attributes()
            check_alignment(ga["StructMetadata.0"], ga.get("CoreMetadata.0", ""), h, v, p, path.name)
            sub = need[(need["h"] == h) & (need["v"] == v) & (need["period"] == p)]
            line, samp = (sub["grow"] % NPIX).to_numpy(), (sub["gcol"] % NPIX).to_numpy()
            rec = sub[["grow", "gcol", "period"]].copy()
            for col, sds in SDS.items():
                ds = sd.select(sds)
                rec[col] = ds.get()[line, samp].astype("int64")
                if not attrs_shown and col == "burn":
                    print(f"  Burn Date öznitelikleri: {ds.attributes()}")
                    attrs_shown = True
                ds.endaccess()
            rows.append(rec)
            print(f"  oku   {path.name}: {len(rec):,} piksel (hizalama ✅)")
        finally:
            sd.end()
    if not rows:
        return pd.DataFrame(columns=["grow", "gcol", "period", *SDS])
    return pd.concat(rows, ignore_index=True)


# ================================================================ değerlendirme

def evaluate(det: pd.DataFrame, rec: pd.DataFrame, tol_days: int = TOL_DAYS, ring: int = RING) -> pd.DataFrame:
    """Her tespit için durum (bkz. modül açıklaması). Tespit satır sayısı korunur."""
    det = det.assign(acq_date=pd.to_datetime(det["acq_date"]))
    acq = det.set_index("det_id")["acq_date"]
    exp = detection_pixels(det, ring).merge(candidate_months(det, tol_days), on="det_id")
    m = exp.merge(rec, on=["grow", "gcol", "period"], how="left", indicator=True)
    m["acq_date"] = m["det_id"].map(acq)

    b = m["burn"]
    m["cat"] = np.select(
        [m["_merge"] == "left_only", b.between(1, 366), b == 0, b == -2, b == -1],
        ["missing", "burned", "unburned", "water", "unmapped"], default="invalid")
    burned = m["cat"] == "burned"
    m["burn_dt"] = pd.NaT
    if burned.any():
        key = (m.loc[burned, "period"].dt.year * 1000 + m.loc[burned, "burn"].astype("int64")).astype(str)
        m.loc[burned, "burn_dt"] = pd.to_datetime(key, format="%Y%j")
    m["burn_dt"] = pd.to_datetime(m["burn_dt"])
    m["days_diff"] = (m["burn_dt"] - m["acq_date"]).dt.days
    m["in_tol"] = burned & (m["days_diff"].abs() <= tol_days)
    m["persistent"] = ((m["qa"].fillna(0).to_numpy("int64") >> 5) & 7) == 5  # QA bit5–7 özel kod 5

    def n_px(mask: pd.Series) -> pd.Series:
        return m.loc[mask, ["det_id", "grow", "gcol"]].drop_duplicates().groupby("det_id").size()

    g = m.groupby("det_id")
    agg = pd.DataFrame({
        "n_records": g.size(),
        "n_records_missing": g["cat"].apply(lambda s: int((s == "missing").sum())),
        "n_records_unmapped_invalid": g["cat"].apply(lambda s: int(s.isin(["unmapped", "invalid"]).sum())),
        "any_burned": g["cat"].apply(lambda s: bool((s == "burned").any())),
        "any_in_tol": g["in_tol"].any(),
    })
    agg["n_pixels"] = n_px(pd.Series(True, index=m.index))
    agg["n_px_burned_in_tol"] = n_px(m["in_tol"])
    agg["n_px_persistent_hotspot"] = n_px(m["persistent"])
    agg[["n_px_burned_in_tol", "n_px_persistent_hotspot"]] = (
        agg[["n_px_burned_in_tol", "n_px_persistent_hotspot"]].fillna(0).astype(int))

    status = np.select(
        [agg["n_records_missing"] == agg["n_records"], agg["any_in_tol"],
         (agg["n_records_missing"] + agg["n_records_unmapped_invalid"]) > 0, agg["any_burned"]],
        ["no_data", "burned_match", "unknown", "burned_other_time"], default="unburned")
    agg["status"] = status
    agg["matched"] = pd.array(np.where(np.isin(status, ["no_data", "unknown"]), None,
                                       status == "burned_match"), dtype="boolean")

    # en yakın yanma kaydı (varsa) → tarih/doy/belirsizlik/qa
    best = (m[burned].assign(absd=m.loc[burned, "days_diff"].abs())
            .sort_values(["det_id", "absd"]).drop_duplicates("det_id").set_index("det_id"))
    agg["burn_date"] = best["burn_dt"].dt.date
    agg["burn_doy"] = best["burn"].astype("Int64")
    agg["burn_uncertainty"] = best["unc"].astype("Int64")
    agg["qa"] = best["qa"].astype("Int64")
    agg["days_diff"] = best["days_diff"].astype("Int64")

    out = det.set_index("det_id").join(agg, how="left").reset_index()
    out["acq_date"] = out["acq_date"].dt.date
    out["tol_days"], out["ring"] = tol_days, ring
    if len(out) != len(det):
        raise ValueError(f"Satır sayısı değişti: {len(det)} → {len(out)}")
    return out[OUT_COLUMNS]


def summarize(out: pd.DataFrame) -> pd.DataFrame:
    order = ["burned_match", "burned_other_time", "unburned", "unknown", "no_data"]
    s = out.groupby(["group", "instrument", "status"]).size().unstack("status", fill_value=0)
    s = s.reindex(columns=order, fill_value=0)
    s.insert(0, "n", s.sum(axis=1))
    return s


# ================================================================ main

def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", type=Path, default=None, help="İbrahim'in MCD64A1 zip'i (gereken HDF'ler çıkarılır)")
    ap.add_argument("--ring", type=int, default=RING, help="piksel komşuluğu (0 = tek piksel, 1 = 3×3)")
    ap.add_argument("--tol-days", type=int, default=TOL_DAYS)
    ap.add_argument("--out", type=Path, default=OUT_PATH)
    a = ap.parse_args()
    if a.zip is not None and not a.zip.exists():
        raise FileNotFoundError(f"--zip bulunamadı: {a.zip}")

    df = pd.read_parquet(HOTSPOTS_PATH, columns=["latitude", "longitude", "acq_date", "datetime_utc", "year",
                                                 "month", "satellite", "instrument", "region"])
    det = select_detections(df)
    print(det.groupby(["group", "instrument"]).size().unstack(fill_value=0).to_string())
    px = detection_pixels(det, a.ring)
    print(f"\nMCD64A1 okuma ({MCD64_DIR.relative_to(ROOT)}):")
    rec = read_records(px, candidate_months(det, a.tol_days), a.zip)

    out = evaluate(det, rec, a.tol_days, a.ring)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(a.out, index=False)
    print(f"\nYazıldı → {a.out} ({len(out)} tespit; tol=±{a.tol_days} gün, ring={a.ring})\n")
    s = summarize(out)
    print(s.to_string())
    w = f"{2 * a.ring + 1}×{2 * a.ring + 1}"
    for grp, inst in s.index:
        r = s.loc[(grp, inst)]
        print(f"  {grp} {inst}: {r['n']} tespitten {r['burned_match']} tanesi MCD64A1'in ±{a.tol_days} gün "
              f"içinde yanmış işaretlediği piksellere ({w}) düşüyor; bilinmiyor/veri yok "
              f"{r['unknown'] + r['no_data']}")
    hit = out[out["status"] == "burned_match"]
    if len(hit):
        print("\nEşleşen yanma tarihleri (en yakın):")
        print(hit.groupby(["group", "burn_date"]).size().rename("tespit").to_string())


if __name__ == "__main__":
    main()
