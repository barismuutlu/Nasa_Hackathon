# P1 — Veri Mühendisi: Süleyman

Ortak kurallar, şema ve takvim kök `CLAUDE.md`'de. Bu dosya sadece senin rolün.

## Sahip olduğun dosyalar (Claude SADECE bunlara yazar)
- `pipeline/ingest.py`
- `data/sample/` (örnek çıktı)

## Görev
FIRMS CSV'lerini (`data/raw/`) okuyup tek ortak şemaya çevir → `data/hotspots.parquet`
(şema: kök `CLAUDE.md` §3.1 — sütun adı/tipi birebir).

1. **Okuma** — MODIS (C6.1) + VIIRS S-NPP / NOAA-20 / NOAA-21 (C2), hem `archive` hem `nrt`.
   - Enstrümanı dosya adından değil **sütunlardan** tanı: `brightness` → MODIS, `bright_ti4` → VIIRS.
   - `source`: dosya adında `archive` → `"archive"`, `nrt` → `"nrt"`; yoksa `type` sütunu varsa archive.
   - `satellite` normalizasyonu: `Terra/T` → Terra, `Aqua/A` → Aqua, `N/SNPP/Suomi NPP` → SNPP,
     `N20/1/J1/NOAA-20` → NOAA20, `N21/2/J2/NOAA-21` → NOAA21. Bilinmeyen değer → `ValueError`.
   - `confidence`: MODIS sayı → <30 low, 30–79 nominal, ≥80 high; VIIRS `l/n/h` → low/nominal/high.
   - `bright` = MODIS `brightness` / VIIRS `bright_ti4`.
2. **Birleştirme + tekrar silme** — archive ve nrt çakışır.
   Anahtar: `(satellite, round(lat,4), round(lon,4), acq_date, acq_time)`; çakışmada **archive kalır**.
3. **Yazma** — `weight_harm = NaN` (float32), kategorik sütunlar `category`, parquet `pyarrow`, `snappy`.
4. **Özet yazdır** — uydu × yıl satır sayısı tablosu + her uydunun ilk/son tarihi
   (P2 `n_active_viirs` için bunu kullanacak → Bahtiyar'a gönder).

## Kapsam (Barış ile teyit et)
Arjantin (eğitim, tam 2000–2026) + Almanya + Belçika (Venn/Eifel). Global indirme YAPMA.

## Teslimler
| Saat | Ne | Kime |
|---|---|---|
| 11:30 | `data/sample/hotspots_sample.parquet` (1 bölge, 1 yıl, ör. La Rioja 2020) — git'e commit | herkes |
| 12:30 | `data/hotspots.parquet` tam veri — Drive/USB | herkes |
| 12:30 | uydu ilk/son tarih tablosu | Bahtiyar (P2) |

## Bitti kontrolü
- [ ] Sütun adları/tipleri §3.1 ile birebir (`df.dtypes` yazdır, karşılaştır)
- [ ] Tekrar yok: anahtar üzerinde `duplicated().sum() == 0`
- [ ] Hohes Venn (lat 50.45–50.60, lon 5.95–6.25) Nisan 2011'de MODIS tespiti var mı? → sonucu Barış'a söyle
- [ ] `python pipeline/ingest.py` temiz ortamda baştan sona çalışıyor

## Claude'a not
- Sadece pandas/pyarrow/numpy kullan. Yeni paket gerekiyorsa yazma, "Barış'a söyle" de.
- Şema değişikliği gerekirse kod yazma; kullanıcıya P4'e sormasını söyle.
- CSV'ler büyükse `usecols` + `dtype` ile oku, dosya dosya işle, sonra `concat`.
