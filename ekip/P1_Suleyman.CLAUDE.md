# P1 — Veri Mühendisi: Süleyman

Ortak kurallar ve takvim kök `CLAUDE.md`'de, şema **`docs/CONTRACT.md`** (güncel sürüm)'de. Bu dosya sadece senin rolün.

## Sahip olduğun dosyalar (Claude SADECE bunlara yazar)
- `pipeline/ingest.py`
- `data/sample/` (örnek çıktı)

## Girdi / çıktı (CONTRACT §7.1)
- Girdi: `data/raw/<region>/*.csv` — klasör adı = `region` değeri (`argentina`, `aachen_eifel`)
- Çıktı: `data/hotspots.parquet` — CONTRACT §1, yazmadan önce `validate_hotspots(df, "ingest")`
- Çıktı: `data/satellite_coverage.csv` — `satellite, source, first_date, last_date, n_rows, nrt_cutoff, n_nrt_dropped`

## Görev
1. **Veri** (CONTRACT §5) — takımın Drive arşivi (DL_FIRE, 4 kaynak, archive + NRT, 2000-11 → bugün):
   `data/raw/argentina/`, `data/raw/aachen_eifel/`. FIRMS ülke-yıl dosyaları KULLANILMAZ (2026 ve NOAA-21 yok).
   - Enstrüman = `SATELLITE_INSTRUMENT[satellite]` (DL_FIRE'da VIIRS de `brightness` sütununu kullanır).
   - archive/NRT cutoff **(region, satellite)** bazında; `satellite_coverage.csv`'ye `region` sütunu.
2. **Okuma** — sabitleri `contract.py`'den al, kendin yazma:
   - Enstrüman sütunlardan: `brightness` → MODIS, `bright_ti4` → VIIRS.
   - `satellite` → `SATELLITE_CODES` ile; bilinmeyen kod → `ValueError`.
   - `confidence` = **orijinal değer, string** (MODIS `"85"`, VIIRS `"n"`).
     `confidence_class`: MODIS → `modis_confidence_class()`, VIIRS → `VIIRS_CONFIDENCE_CLASS`.
   - `brightness` = MODIS `brightness` / VIIRS `bright_ti4`; `brightness_2` = `bright_t31` / `bright_ti5`.
   - `version` = FIRMS `version` (string), `type` = archive `type` (NRT'de `<NA>`).
   - `datetime_utc` = `acq_date` + `acq_time` (HHMM), UTC.
   - `source`: dosya adında `archive` → `"archive"`, `nrt` → `"nrt"`.
   - `weight_harm` = NaN (float32). Harmonize etme, P2'nin işi.
3. **Tekrar silme** (CONTRACT §4)
   - 4a: anahtar `(satellite, datetime_utc, round(latitude,4), round(longitude,4))` → ilki kalır.
   - 4b: her uydu için `cutoff = archive'deki son acq_date`; o uydunun `acq_date ≤ cutoff` NRT satırları atılır.
   - Farklı uydu ya da farklı zaman olan satırları **asla** birleştirme.
4. **Özet yazdır** — uydu × yıl satır sayısı, sebebe göre atılan satırlar,
   `satellite_coverage.csv` → Bahtiyar'a haber ver (S-NPP son tarihi ~2026-11-02 olmalı).

## İlk iş: başlık kontrolü
İlk gerçek CSV'yi indirince başlık satırını ve `satellite`, `confidence`, `version` alanlarındaki
farklı değerleri yazdır, CONTRACT §1/§3 ile karşılaştır. Fark varsa **önce Barış'a söyle**,
sonra koda geç (sözleşme belgeden yazıldı, gerçek dosya görülmedi).

## Teslimler
| Saat | Ne | Kime |
|---|---|---|
| 11:30 | `data/sample/hotspots_sample.parquet` (La Rioja 2020) + başlık kontrolü sonucu | herkes, Barış |
| 12:30 | `data/hotspots.parquet` tam veri (Drive/USB) | herkes |
| 12:30 | `data/satellite_coverage.csv` | Bahtiyar (P2) |

## Bitti kontrolü
- [ ] `validate_hotspots(df, "ingest")` hatasız geçiyor
- [ ] Anahtar üzerinde `duplicated().sum() == 0`; archive/NRT kesim tarihleri özette
- [ ] Hohes Venn (lon 5.95–6.25, lat 50.45–50.60) Nisan 2011'de MODIS tespiti var mı? → Barış'a söyle
- [ ] `python pipeline/ingest.py` temiz ortamda baştan sona çalışıyor

## Claude'a not
- `contract.py`'yi import et (kök CLAUDE.md §3.2), değiştirme. Sözleşmeye uymayan durum → Barış'a sor.
- Sadece pandas/pyarrow/numpy. Yeni paket gerekiyorsa yazma, "Barış'a söyle" de.
- Büyük CSV'leri `usecols` + `dtype` ile oku; `confidence`'ı **string** oku (`dtype={"confidence": str}`).
